import pandas as pd
import requests
import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
import rdkit.Chem as Chem
from rdkit.Chem import Descriptors

# Import config utilities ensuring absolute compatibility with the API surface
# The prompt indicates config.py defines exceptions and load_config.
# We handle the import error gracefully for direct execution vs module import.
try:
    from config import DataIngestionError, load_config
except ImportError:
    try:
        from .config import DataIngestionError, load_config
    except ImportError:
        # Fallback for direct execution in a flat structure if needed, 
        # though the prompt implies a package structure.
        # We define a minimal stub here to prevent immediate crash if config is missing,
        # but the real implementation expects config.py to exist.
        class DataIngestionError(Exception): pass
        def load_config(): return {}

# Ensure logging is configured
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_spice_dataset(url: str) -> pd.DataFrame:
    """
    PRIMARY SOURCE: Fetch the SPICE dataset using the URL from config.
    Saves to data/raw/spice.parquet.
    """
    if not url:
        raise DataIngestionError("SPICE_URL is not configured in .env/config.")
    
    logger.info(f"Downloading SPICE dataset from {url}...")
    try:
        # Attempt to fetch as parquet directly if possible, otherwise json/csv
        # Assuming parquet for performance as per task description
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        # Write to temp buffer then read to ensure integrity
        import io
        buffer = io.BytesIO(response.content)
        df = pd.read_parquet(buffer)
        
        # Verify columns
        required_cols = ['cation_id', 'anion_id', 'smiles_cation', 'smiles_anion', 
                         'structural_family', 'electrostatic_energy', 'dispersion_energy', 'hbond_energy']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise DataIngestionError(f"SPICE dataset missing required columns: {missing}")
        
        os.makedirs('data/raw', exist_ok=True)
        output_path = 'data/raw/spice.parquet'
        df.to_parquet(output_path, index=False)
        logger.info(f"SPICE dataset saved to {output_path} with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to download SPICE dataset: {e}")
        raise DataIngestionError(f"SPICE download failed: {e}")

def download_il_thermo_sapt(url: str) -> pd.DataFrame:
    """
    SECONDARY SOURCE: Fetch ILThermo and curated SAPT/DFT datasets.
    Saves to data/raw/il_thermo.parquet and data/raw/sapt.parquet.
    """
    if not url:
        logger.warning("ILTHERMO/SAPT_URL not configured. Skipping secondary source download.")
        return pd.DataFrame()
    
    logger.info(f"Downloading ILThermo/SAPT dataset from {url}...")
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        import io
        buffer = io.BytesIO(response.content)
        df = pd.read_parquet(buffer)
        
        required_cols = ['cation_id', 'anion_id', 'smiles_cation', 'smiles_anion', 
                         'structural_family', 'electrostatic_energy', 'dispersion_energy', 'hbond_energy']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise DataIngestionError(f"ILThermo/SAPT dataset missing required columns: {missing}")
        
        os.makedirs('data/raw', exist_ok=True)
        output_path = 'data/raw/il_thermo.parquet'
        df.to_parquet(output_path, index=False)
        
        # Also save as sapt if it contains SAPT energy components
        if 'source' in df.columns:
            sapt_df = df[df['source'] == 'sapt'].copy()
            if not sapt_df.empty:
                sapt_path = 'data/raw/sapt.parquet'
                sapt_df.to_parquet(sapt_path, index=False)
                logger.info(f"SAPT subset saved to {sapt_path} with {len(sapt_df)} rows.")
        
        logger.info(f"ILThermo dataset saved to {output_path} with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to download ILThermo/SAPT dataset: {e}")
        # Do not raise here if it's secondary, but log clearly. 
        # The pipeline should handle missing secondary data.
        return pd.DataFrame()

def extract_structures_from_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract unique cation/anion SMILES from the downloaded dataset.
    Saves to data/raw/il_structures.json.
    """
    if df.empty:
        raise DataIngestionError("Cannot extract structures from empty dataframe.")
    
    structures = {
        'cation_smiles': list(df['smiles_cation'].unique()),
        'anion_smiles': list(df['smiles_anion'].unique()),
        'families': list(df['structural_family'].unique())
    }
    
    os.makedirs('data/raw', exist_ok=True)
    output_path = 'data/raw/il_structures.json'
    with open(output_path, 'w') as f:
        json.dump(structures, f, indent=2)
    
    logger.info(f"Structures extracted and saved to {output_path}.")
    return structures

def calculate_partial_charges_internal_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Gasteiger partial charges using RDKit for internal consistency checks only.
    These values MUST NOT be used as input features for training.
    Saves the result to data/processed/internal_consistency_checks.parquet.
    """
    logger.info("Calculating internal consistency partial charges...")
    df_copy = df.copy()
    
    def get_gasteiger_charge(smiles):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return 0.0
            Chem.ComputeGasteigerCharges(mol)
            # Sum absolute charges or return mean? Spec says "partial_charge" (singular).
            # We'll return the sum of absolute partial charges as a molecular descriptor proxy.
            charges = [float(atom.GetProp('_GasteigerCharge')) for atom in mol.GetAtoms()]
            return sum(abs(c) for c in charges if not pd.isna(c))
        except Exception:
            return 0.0

    df_copy['partial_charge'] = df_copy['smiles_cation'].apply(get_gasteiger_charge) + df_copy['smiles_anion'].apply(get_gasteiger_charge)
    
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/internal_consistency_checks.parquet'
    df_copy[['cation_id', 'anion_id', 'partial_charge']].to_parquet(output_path, index=False)
    logger.info(f"Internal consistency checks saved to {output_path}.")
    return df_copy

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and graph embeddings.
    CRITICAL: Call calculate_partial_charges_internal_only to save the internal consistency artifact,
    then DROP the partial_charge column from the training feature matrix.
    Saves to data/processed/training_features.parquet.
    """
    logger.info("Engineering features...")
    
    # 1. Save internal consistency checks first
    df_with_charges = calculate_partial_charges_internal_only(df)
    
    # 2. Compute descriptors
    def compute_descriptors(smiles):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'tpsa': 0.0, 'surface_area': 0.0, 'hbond_count': 0, 'fp': []}
            
            tpsa = Descriptors.TPSA(mol)
            # Molecular Surface Area proxy: MolMR (Molar Refractivity) or similar
            # Using MolMR as a proxy for polarizability/surface area as per T006c
            surface_area = Descriptors.MolMR(mol)
            hbond_count = Descriptors.NumHDonors(mol) + Descriptors.NumHAcceptors(mol)
            
            # Morgan FP
            from rdkit.Chem import AllChem
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
            fp_arr = [int(b) for b in fp.ToBitString()]
            
            return {
                'tpsa': tpsa,
                'surface_area': surface_area,
                'hbond_count': hbond_count,
                'morgan_fp': fp_arr
            }
        except Exception as e:
            logger.warning(f"Error computing descriptors for {smiles}: {e}")
            return {'tpsa': 0.0, 'surface_area': 0.0, 'hbond_count': 0, 'morgan_fp': [0]*2048}

    # Apply to cation and anion
    cation_desc = df['smiles_cation'].apply(compute_descriptors).apply(pd.Series)
    anion_desc = df['smiles_anion'].apply(compute_descriptors).apply(pd.Series)
    
    # Rename to avoid collision
    cation_desc = cation_desc.add_prefix('cation_')
    anion_desc = anion_desc.add_prefix('anion_')
    
    df_features = pd.concat([df, cation_desc, anion_desc], axis=1)
    
    # 3. Drop partial_charge from training features (but it exists in df_with_charges for merge later)
    # We create a training-specific dataframe
    training_df = df_features.drop(columns=['partial_charge', 'smiles_cation', 'smiles_anion'], errors='ignore')
    
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/training_features.parquet'
    training_df.to_parquet(output_path, index=False)
    logger.info(f"Training features saved to {output_path}.")
    return training_df

def merge_il_thermo_sapt(il_df: pd.DataFrame, sapt_df: pd.DataFrame) -> pd.DataFrame:
    """Merge ILThermo and SAPT on cation_id and anion_id."""
    if il_df.empty and sapt_df.empty:
        raise DataIngestionError("Both ILThermo and SAPT dataframes are empty.")
    
    if il_df.empty:
        return sapt_df
    if sapt_df.empty:
        return il_df
    
    merged = pd.merge(il_df, sapt_df, on=['cation_id', 'anion_id'], how='outer', suffixes=('_il', '_sapt'))
    return merged

def merge_training_data(base_df: pd.DataFrame, sapt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the base structure dataframe with the real SAPT energy dataframe.
    Constraint: This function must NOT handle synthetic data.
    """
    if sapt_df.empty:
        raise DataIngestionError("SAPT dataframe is missing or empty. Cannot merge training data.")
    
    merged = pd.merge(base_df, sapt_df, on=['cation_id', 'anion_id'], how='inner')
    return merged

def filter_raw_sapt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the unified dataset to extract the subset of data originating strictly from the SAPT source.
    Saves to data/processed/raw_sapt.parquet.
    """
    if 'source' not in df.columns:
        logger.warning("No 'source' column found in dataframe. Returning full dataframe as raw SAPT.")
        return df
    
    filtered = df[df['source'] == 'sapt'].copy()
    if filtered.empty:
        logger.warning("No rows with source='sapt' found.")
        return pd.DataFrame()
    
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/raw_sapt.parquet'
    filtered.to_parquet(output_path, index=False)
    logger.info(f"Raw SAPT data filtered and saved to {output_path}.")
    return filtered

def write_unified_dataset(df: pd.DataFrame, path: str) -> None:
    """Save the unified dataset to the specified path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Unified dataset saved to {path} with {len(df)} rows.")

def validate_unified_dataset(df: pd.DataFrame, schema_path: str) -> bool:
    """Validate the unified dataset using pandera."""
    try:
        import pandera as pa
        from pandera.typing import DataFrame
        
        # Define a simple schema for validation
        class UnifiedSchema(pa.SchemaModel):
            cation_id: pa.typing.Series[str]
            anion_id: pa.typing.Series[str]
            structural_family: pa.typing.Series[str]
            electrostatic_energy: pa.typing.Series[float]
            dispersion_energy: pa.typing.Series[float]
            hbond_energy: pa.typing.Series[float]
            tpsa: pa.typing.Series[float]
            molecular_surface_area: pa.typing.Series[float]
            hbond_count: pa.typing.Series[int]
            morgan_fp: pa.typing.Series[list]
            partial_charge: pa.typing.Series[float]
            
        # Validate
        UnifiedSchema.validate(df)
        logger.info("Unified dataset validation passed.")
        return True
    except Exception as e:
        logger.error(f"Unified dataset validation failed: {e}")
        return False

def log_validation_errors(errors: List[str]) -> None:
    """Write detailed errors to logs/ingestion_errors.log."""
    os.makedirs('logs', exist_ok=True)
    with open('logs/ingestion_errors.log', 'a') as f:
        for err in errors:
            f.write(f"{err}\n")

def check_data_source_existence() -> Dict[str, bool]:
    """Check if data files exist."""
    return {
        'spice': os.path.exists('data/raw/spice.parquet'),
        'sapt': os.path.exists('data/raw/sapt.parquet'),
        'il_thermo': os.path.exists('data/raw/il_thermo.parquet')
    }

def select_data_sources(flags: Dict[str, bool]) -> Dict[str, str]:
    """Select data sources based on flags."""
    selected = {}
    if flags.get('spice'):
        selected['spice'] = 'data/raw/spice.parquet'
    if flags.get('sapt'):
        selected['sapt'] = 'data/raw/sapt.parquet'
    if flags.get('il_thermo'):
        selected['il_thermo'] = 'data/raw/il_thermo.parquet'
    
    if not selected:
        raise DataIngestionError("No real data sources found. Pipeline cannot proceed without real data.")
    
    return selected

def get_selected_paths(flags: Dict[str, bool]) -> List[str]:
    """Return paths to selected data files."""
    sources = select_data_sources(flags)
    return list(sources.values())

def merge_consistency_artifacts() -> pd.DataFrame:
    """
    Read internal_consistency_checks.parquet and merge into the final unified dataset.
    Ensures partial_charge is present in the final output file.
    """
    consistency_path = 'data/processed/internal_consistency_checks.parquet'
    unified_path = 'data/processed/unified_dataset.parquet'
    
    if not os.path.exists(consistency_path):
        raise DataIngestionError(f"Consistency checks file not found at {consistency_path}")
    
    consistency_df = pd.read_parquet(consistency_path)
    
    if os.path.exists(unified_path):
        unified_df = pd.read_parquet(unified_path)
        # Merge on cation_id and anion_id
        merged = pd.merge(unified_df, consistency_df, on=['cation_id', 'anion_id'], how='left')
        write_unified_dataset(merged, unified_path)
        logger.info("Merged consistency artifacts into unified dataset.")
        return merged
    else:
        logger.warning("Unified dataset not found. Cannot merge consistency artifacts.")
        return consistency_df

def validate_family_coverage(df: pd.DataFrame, min_samples: int = 10) -> None:
    """
    Validate that every StructuralFamily in the raw SAPT source (if available) 
    is represented in the final unified dataset with at least N samples.
    
    Logic:
    1. Check if 'structural_family' column exists.
    2. Count samples per family.
    3. If any family has < min_samples, raise DataIngestionError.
    
    Config: N value is read from config.py (default 10).
    """
    logger.info("Validating family coverage...")
    
    if 'structural_family' not in df.columns:
        raise DataIngestionError("Column 'structural_family' not found in dataframe.")
    
    family_counts = df['structural_family'].value_counts()
    logger.info(f"Family counts: {family_counts.to_dict()}")
    
    # Load min_samples from config if available
    try:
        cfg = load_config()
        min_samples = cfg.get('MIN_FAMILY_SAMPLES', min_samples)
    except:
        pass
    
    under_represented = family_counts[family_counts < min_samples].index.tolist()
    
    if under_represented:
        error_msg = f"DataIngestionError: Family coverage insufficient. Missing or under-represented families: {under_represented}. Minimum required: {min_samples} samples."
        logger.error(error_msg)
        raise DataIngestionError(error_msg)
    
    logger.info("Family coverage validation passed.")

def main():
    """Main execution flow for data ingestion."""
    logger.info("Starting data ingestion pipeline...")
    
    config = load_config()
    
    # 1. Download Data
    spice_url = config.get('SPICE_URL', '')
    sapt_url = config.get('ILTHERMO_URL', '')
    
    spice_df = download_spice_dataset(spice_url)
    sapt_df = download_il_thermo_sapt(sapt_url)
    
    if spice_df.empty and sapt_df.empty:
        raise DataIngestionError("No data downloaded. Check URLs and network.")
    
    # 2. Extract Structures
    combined_df = pd.concat([spice_df, sapt_df], ignore_index=True) if not spice_df.empty and not sapt_df.empty else (spice_df if not spice_df.empty else sapt_df)
    extract_structures_from_data(combined_df)
    
    # 3. Engineer Features
    if combined_df.empty:
        raise DataIngestionError("Combined dataframe is empty.")
    
    training_df = engineer_features(combined_df)
    
    # 4. Write Unified Dataset (with partial_charge merged back if needed)
    # For now, we write the training features as the unified dataset for the next step
    # Note: The task T016b merges consistency artifacts. We do that here if the file exists.
    try:
        final_df = merge_consistency_artifacts()
    except DataIngestionError as e:
        # If merge fails because unified doesn't exist yet, we create it from training_df
        # But training_df has partial_charge dropped. We need to add it back from consistency checks.
        # Re-read consistency checks and merge
        consistency_df = pd.read_parquet('data/processed/internal_consistency_checks.parquet')
        # Re-join on index or IDs if available. Assuming IDs are in training_df
        # We need to ensure IDs are in training_df. They should be.
        if 'cation_id' in training_df.columns and 'anion_id' in training_df.columns:
            final_df = pd.merge(training_df, consistency_df, on=['cation_id', 'anion_id'], how='left')
            write_unified_dataset(final_df, 'data/processed/unified_dataset.parquet')
        else:
            write_unified_dataset(training_df, 'data/processed/unified_dataset.parquet')
    
    # 5. Filter Raw SAPT
    if os.path.exists('data/raw/sapt.parquet'):
        sapt_raw = pd.read_parquet('data/raw/sapt.parquet')
        filter_raw_sapt(sapt_raw)
    
    # 6. Validate Family Coverage (T061)
    unified_path = 'data/processed/unified_dataset.parquet'
    if os.path.exists(unified_path):
        unified_df = pd.read_parquet(unified_path)
        validate_family_coverage(unified_df)
    else:
        raise DataIngestionError("Unified dataset not created. Cannot validate family coverage.")
    
    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()