import pandas as pd
import requests
import os
import hashlib
import json
import logging
import rdkit.Chem as Chem
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Ensure we can import from sibling modules without relative import errors when run as script
import sys
import config
from utils import compute_tpsa, compute_morgan_fp, compute_hbond_count, compute_polarizability

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('logs/ingestion.log')]
)
logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    pass

def load_config() -> Dict[str, Any]:
    """Load configuration from config.py module."""
    return {
        'SEED': 42,
        'DATA_PATHS': {
            'raw': 'data/raw',
            'processed': 'data/processed',
            'validation': 'data/validation'
        },
        'MIN_FAMILY_SAMPLES': 10
    }

def verify_real_data_source(path: str) -> bool:
    """Verify that a data source exists and is non-empty."""
    if not os.path.exists(path):
        return False
    try:
        df = pd.read_parquet(path)
        return len(df) > 0
    except Exception:
        return False

def download_spice_dataset(url: Optional[str] = None) -> pd.DataFrame:
    """
    PRIMARY SOURCE: Fetch the SPICE dataset.
    Falls back to a verified public mirror if the config URL is missing or fails.
    """
    if url is None:
        url = os.getenv('SPICE_URL')
    
    # Fallback to a known public source if env var is missing
    if not url:
        logger.warning("SPICE_URL not set. Attempting to fetch from HuggingFace datasets (SPICE).")
        try:
            from datasets import load_dataset
            logger.info("Loading SPICE dataset from HuggingFace...")
            ds = load_dataset("matt-shen/SPICE", split="train", streaming=True)
            # Convert to DF and take a manageable sample if too large, but ensure real data
            # We stream and collect a representative set.
            # Note: The full SPICE dataset is large. We will take the first 10000 rows for this run
            # to ensure execution within time limits while maintaining real data integrity.
            # In a full run, one would stream all or save shards.
            rows = []
            for i, item in enumerate(ds):
                if i >= 10000:
                    break
                rows.append(item)
            df = pd.DataFrame(rows)
            # Ensure required columns exist or map them
            required_cols = ['cation_id', 'anion_id', 'smiles_cation', 'smiles_anion', 
                             'structural_family', 'electrostatic_energy', 'dispersion_energy', 'hbond_energy']
            
            # If the dataset structure differs, we might need to adapt. 
            # Assuming standard SPICE structure or adapting if needed.
            # If columns are missing, we raise an error to fail loud rather than fake.
            if not all(col in df.columns for col in required_cols):
                # Try to map common variations
                if 'cation_smiles' in df.columns: df['smiles_cation'] = df['cation_smiles']
                if 'anion_smiles' in df.columns: df['smiles_anion'] = df['anion_smiles']
                
                # If still missing, we cannot proceed with fake data.
                missing = [c for c in required_cols if c not in df.columns]
                raise DataIngestionError(f"SPICE dataset missing required columns: {missing}. Real data fetch failed or format mismatch.")

            path = os.path.join(config.DATA_PATHS['raw'], 'spice.parquet')
            df.to_parquet(path, index=False)
            logger.info(f"Saved SPICE dataset to {path} with {len(df)} rows.")
            return df
        except Exception as e:
            logger.error(f"Failed to load SPICE from HuggingFace: {e}")
            raise DataIngestionError(f"Could not fetch real SPICE data. {e}")

    # Standard HTTP fetch if URL provided
    try:
        response = requests.get(url, timeout=600)
        response.raise_for_status()
        df = pd.read_parquet(BytesIO(response.content))
        path = os.path.join(config.DATA_PATHS['raw'], 'spice.parquet')
        df.to_parquet(path, index=False)
        logger.info(f"Downloaded SPICE dataset to {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to download SPICE dataset: {e}")
        raise DataIngestionError(f"Failed to download SPICE data from {url}. {e}")

def download_il_thermo_sapt() -> Optional[pd.DataFrame]:
    """
    SECONDARY SOURCE (Conditional): Fetch ILThermo/SAPT dataset.
    Returns None if URL not defined or fetch fails.
    """
    url = os.getenv('IL_SAPT_URL')
    if not url:
        logger.info("IL_SAPT_URL not defined. Skipping secondary source download.")
        return None
    
    try:
        logger.info(f"Attempting to fetch ILThermo/SAPT from {url}")
        response = requests.get(url, timeout=600)
        response.raise_for_status()
        df = pd.read_parquet(BytesIO(response.content))
        path = os.path.join(config.DATA_PATHS['raw'], 'il_thermo.parquet')
        df.to_parquet(path, index=False)
        logger.info(f"Saved ILThermo/SAPT dataset to {path}")
        return df
    except Exception as e:
        logger.warning(f"Fetch failed or URL invalid: {e}. Skipping ILThermo/SAPT.")
        return None

def extract_structures_from_data(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique cation/anion SMILES and save to JSON."""
    structures = {
        'cation_smiles': [],
        'anion_smiles': [],
        'structural_family': []
    }
    
    seen = set()
    for _, row in df.iterrows():
        c_smiles = row.get('smiles_cation')
        a_smiles = row.get('smiles_anion')
        family = row.get('structural_family', 'unknown')
        
        if c_smiles and a_smiles:
            key = (c_smiles, a_smiles)
            if key not in seen:
                seen.add(key)
                structures['cation_smiles'].append(c_smiles)
                structures['anion_smiles'].append(a_smiles)
                structures['structural_family'].append(family)
    
    structures_df = pd.DataFrame(structures)
    path = os.path.join(config.DATA_PATHS['raw'], 'il_structures.json')
    structures_df.to_json(path, orient='records', indent=2)
    logger.info(f"Saved structures to {path}")
    return structures_df

def calculate_partial_charges_internal_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Gasteiger partial charges for internal consistency checks only.
    These values are NOT used for training.
    """
    logger.info("Calculating partial charges for internal consistency checks...")
    
    def get_gasteiger_charge(smiles: str) -> float:
        if not smiles or not isinstance(smiles, str):
            return 0.0
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.0
        try:
            Chem.ComputeGasteigerCharges(mol)
            charges = [float(atom.GetProp('_GasteigerCharge')) for atom in mol.GetAtoms() 
                       if atom.HasProp('_GasteigerCharge')]
            if charges:
                return sum(charges) / len(charges)
        except Exception:
            pass
        return 0.0

    # Apply to both cation and anion, then average or take max absolute? 
    # For consistency check, we just calculate the mean absolute charge magnitude.
    df['partial_charge_cation'] = df['smiles_cation'].apply(get_gasteiger_charge)
    df['partial_charge_anion'] = df['smiles_anion'].apply(get_gasteiger_charge)
    df['partial_charge'] = (df['partial_charge_cation'].abs() + df['partial_charge_anion'].abs()) / 2.0

    # Save internal consistency artifact
    output_path = os.path.join(config.DATA_PATHS['processed'], 'internal_consistency_checks.parquet')
    # Keep only relevant columns for the check
    check_df = df[['cation_id', 'anion_id', 'partial_charge', 'partial_charge_cation', 'partial_charge_anion']].copy()
    check_df.to_parquet(output_path, index=False)
    logger.info(f"Saved internal consistency checks to {output_path}")
    
    # Return df with partial_charge column (it will be dropped later for training)
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES, compute descriptors, and prepare training features.
    CRITICAL: partial_charge is calculated for internal checks but EXCLUDED from training features.
    """
    logger.info("Engineering features...")
    
    # Ensure partial charges are calculated first (T015a dependency)
    if 'partial_charge' not in df.columns:
        df = calculate_partial_charges_internal_only(df)
    
    # Compute other descriptors
    logger.info("Computing TPSA, Morgan FPs, H-bond counts, etc.")
    df['tpsa'] = df['smiles_cation'].apply(lambda x: compute_tpsa(x) if x else 0.0)
    df['molecular_surface_area'] = df['smiles_cation'].apply(lambda x: compute_morgan_fp(x) if x else 0.0) # Placeholder logic, actual implementation in utils
    # Note: compute_morgan_fp returns array. For DF column, we might need to flatten or use a summary.
    # For this task, we assume utils returns a scalar or we handle it.
    # Let's assume utils returns a scalar for surface area proxy or we take sum of bits.
    # Re-implementing simple surface area proxy if utils is complex:
    def get_surface_area(smiles):
        if not smiles: return 0.0
        mol = Chem.MolFromSmiles(smiles)
        if not mol: return 0.0
        # Using MolMR as proxy for polarizability/surface
        return compute_polarizability(smiles)
    
    df['molecular_surface_area'] = df['smiles_cation'].apply(get_surface_area)
    df['hbond_count'] = df['smiles_cation'].apply(lambda x: compute_hbond_count(x) if x else 0)
    df['polarizability'] = df['smiles_cation'].apply(lambda x: compute_polarizability(x) if x else 0.0)
    
    # Explicitly document: Partial charges excluded from training features
    training_features = df.drop(columns=['partial_charge', 'partial_charge_cation', 'partial_charge_anion'], errors='ignore')
    
    # Save training features (without partial charge)
    train_feat_path = os.path.join(config.DATA_PATHS['processed'], 'training_features.parquet')
    training_features.to_parquet(train_feat_path, index=False)
    logger.info(f"Saved training features (excluded partial_charge) to {train_feat_path}")
    
    # Return full df with partial_charge for later merging
    return df

def check_data_source_existence() -> Dict[str, bool]:
    """Check if required data files exist."""
    flags = {
        'spice': os.path.exists(os.path.join(config.DATA_PATHS['raw'], 'spice.parquet')),
        'sapt': os.path.exists(os.path.join(config.DATA_PATHS['raw'], 'sapt.parquet'))
    }
    return flags

def select_data_sources(flags: Dict[str, bool]) -> Dict[str, str]:
    """Select data sources based on availability."""
    selected = {}
    if flags.get('spice'):
        selected['primary'] = 'spice'
        selected['path'] = os.path.join(config.DATA_PATHS['raw'], 'spice.parquet')
    elif flags.get('sapt'):
        selected['primary'] = 'sapt'
        selected['path'] = os.path.join(config.DATA_PATHS['raw'], 'sapt.parquet')
    else:
        # Trigger synthetic fallback logic (T012c-TrainGen)
        # This task assumes T012c has run or will run.
        # For now, raise error if no data.
        raise DataIngestionError("No real data source found (SPICE or SAPT). Synthetic generation (T012c) must be run first.")
    return selected

def get_selected_paths() -> List[str]:
    """Return paths to selected data files."""
    flags = check_data_source_existence()
    selected = select_data_sources(flags)
    return [selected['path']]

def filter_raw_sapt(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataset to extract SAPT source subset."""
    if 'source' in df.columns:
        if 'sapt' in df['source'].values:
            subset = df[df['source'] == 'sapt']
        elif 'synthetic' in df['source'].values:
            subset = df[df['source'] == 'synthetic']
        else:
            subset = df
    else:
        subset = df
    
    path = os.path.join(config.DATA_PATHS['processed'], 'raw_sapt.parquet')
    subset.to_parquet(path, index=False)
    logger.info(f"Saved raw SAPT subset to {path}")
    return subset

def write_unified_dataset(df: pd.DataFrame, path: str) -> None:
    """Save the unified dataset to Parquet."""
    df.to_parquet(path, index=False)
    logger.info(f"Saved unified dataset to {path}")

def merge_consistency_artifacts() -> pd.DataFrame:
    """
    Read internal_consistency_checks.parquet (from T015a) and merge it into the final unified dataset.
    Ensures 'partial_charge' column is present in the final output file as required by Spec US-1.
    """
    logger.info("Merging consistency artifacts into unified dataset...")
    
    # 1. Load the internal consistency checks (contains partial_charge)
    internal_path = os.path.join(config.DATA_PATHS['processed'], 'internal_consistency_checks.parquet')
    if not os.path.exists(internal_path):
        raise DataIngestionError(f"Internal consistency checks file not found at {internal_path}. T015a must be run first.")
    
    internal_df = pd.read_parquet(internal_path)
    logger.info(f"Loaded internal consistency checks: {len(internal_df)} rows.")
    
    # 2. Load the main training features (T016a output, which dropped partial_charge)
    # Note: T016a produces 'training_features.parquet' without partial_charge.
    # We need the full dataset (with partial_charge) for the final unified output.
    # If 'training_features.parquet' is the only thing T016a produced, we must re-calculate or merge back.
    # However, T016a's logic was: calculate partial_charge, save internal checks, then DROP from training features.
    # So we need the original data or the 'training_features' + 'internal_checks' to reconstruct the unified set.
    
    # Let's assume we have a 'training_features.parquet' that has all columns EXCEPT partial_charge.
    # We will merge the 'partial_charge' column from internal_df back into it.
    train_feat_path = os.path.join(config.DATA_PATHS['processed'], 'training_features.parquet')
    if not os.path.exists(train_feat_path):
        raise DataIngestionError(f"Training features file not found at {train_feat_path}. T016a must be run first.")
    
    main_df = pd.read_parquet(train_feat_path)
    logger.info(f"Loaded training features: {len(main_df)} rows.")
    
    # 3. Merge
    # Key columns: cation_id, anion_id
    merge_keys = ['cation_id', 'anion_id']
    
    # Ensure keys exist in both
    if not all(k in main_df.columns for k in merge_keys):
        raise DataIngestionError("Missing key columns (cation_id, anion_id) in training features.")
    if not all(k in internal_df.columns for k in merge_keys):
        raise DataIngestionError("Missing key columns (cation_id, anion_id) in internal consistency checks.")
    
    # Merge on keys, taking 'partial_charge' from internal_df
    # We drop partial_charge from main_df if it exists (shouldn't, but safe)
    main_df = main_df.drop(columns=['partial_charge', 'partial_charge_cation', 'partial_charge_anion'], errors='ignore')
    
    # Select only the partial_charge columns we need from internal_df
    charge_cols = [c for c in internal_df.columns if 'partial_charge' in c]
    internal_subset = internal_df[merge_keys + charge_cols]
    
    unified_df = pd.merge(main_df, internal_subset, on=merge_keys, how='left')
    
    # Validate
    if unified_df['partial_charge'].isnull().any():
        logger.warning("Some rows missing partial_charge after merge. Filling with 0.0.")
        unified_df['partial_charge'] = unified_df['partial_charge'].fillna(0.0)
    
    # 4. Save Unified Dataset
    output_path = os.path.join(config.DATA_PATHS['processed'], 'unified_dataset.parquet')
    write_unified_dataset(unified_df, output_path)
    
    logger.info(f"Successfully merged consistency artifacts. Unified dataset saved to {output_path}.")
    return unified_df

def main():
    """Main execution flow for data ingestion tasks."""
    logger.info("Starting data ingestion pipeline...")
    
    # 1. Download/Check Data (Simplified for this task focus)
    # In a full run, we would call download_spice_dataset() etc.
    # Here we assume data exists or T012c has run.
    
    # 2. Extract Structures (if needed)
    # 3. Calculate Partial Charges (T015a) - if not done
    # 4. Engineer Features (T016a) - if not done
    # 5. Merge Consistency Artifacts (T016b)
    
    try:
        # Check if we need to run T015a/T016a first
        if not os.path.exists(os.path.join(config.DATA_PATHS['processed'], 'internal_consistency_checks.parquet')):
            logger.info("Internal consistency checks missing. Running T015a logic...")
            # We need a source DF. If raw data exists, load it.
            flags = check_data_source_existence()
            if not any(flags.values()):
                raise DataIngestionError("No raw data found. Cannot run T015a/T016a.")
            
            path = get_selected_paths()[0]
            df = pd.read_parquet(path)
            df = calculate_partial_charges_internal_only(df)
            df = engineer_features(df)
        else:
            # Just run T016a logic if internal checks exist but training features don't
            if not os.path.exists(os.path.join(config.DATA_PATHS['processed'], 'training_features.parquet')):
                logger.info("Training features missing. Running T016a logic...")
                flags = check_data_source_existence()
                path = get_selected_paths()[0]
                df = pd.read_parquet(path)
                # Ensure partial charges exist
                if 'partial_charge' not in df.columns:
                    df = calculate_partial_charges_internal_only(df)
                df = engineer_features(df)
            
        # 6. Run T016b: Merge Consistency Artifacts
        unified_df = merge_consistency_artifacts()
        
        logger.info("Data ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
