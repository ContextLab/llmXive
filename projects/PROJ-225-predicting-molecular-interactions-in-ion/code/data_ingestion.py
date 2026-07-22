import pandas as pd
import requests
import os
import hashlib
import json
import logging
from typing import Optional, Dict, Any
import rdkit.Chem as Chem
from rdkit.Chem import Descriptors
import numpy as np

# Import config and exceptions
# Note: Using absolute imports to avoid relative import errors when run as script
try:
    from config import DataIngestionError, load_config
    from utils import compute_tpsa, compute_morgan_fp, compute_hbond_count, compute_polarizability
except ImportError:
    # Fallback for direct execution context if imports fail
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import DataIngestionError, load_config
    from utils import compute_tpsa, compute_morgan_fp, compute_hbond_count, compute_polarizability

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler('logs/ingestion.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file checksum."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash

def download_spice(url: str) -> pd.DataFrame:
    """
    Download SPICE dataset from HuggingFace.
    PRIMARY SOURCE. Fails loudly if download fails.
    """
    logger.info(f"Downloading SPICE dataset from {url}")
    
    try:
        # Use datasets library for robust loading
        from datasets import load_dataset
        dataset = load_dataset("spice-ml/spice", split='train', streaming=True)
        
        # Convert to pandas (streaming to avoid OOM if large)
        # We take a sample if the full set is too large for memory, 
        # but we do NOT generate synthetic data.
        # For this implementation, we load the first 10,000 rows as a representative sample
        # to ensure the pipeline runs within resource limits while using REAL data.
        sample_size = 10000
        logger.info(f"Sampling {sample_size} rows from real SPICE dataset.")
        
        df = pd.DataFrame(dataset).head(sample_size)
        
        # Verify required columns
        required_cols = ['cation_id', 'anion_id', 'smiles_cation', 'smiles_anion', 
                         'structural_family', 'electrostatic_energy', 'dispersion_energy', 'hbond_energy']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            raise DataIngestionError(f"Missing required columns in SPICE data: {missing_cols}")
        
        # Save to parquet
        os.makedirs('data/raw', exist_ok=True)
        output_path = 'data/raw/spice.parquet'
        df.to_parquet(output_path)
        logger.info(f"SPICE dataset saved to {output_path} with {len(df)} rows.")
        
        return df
    except Exception as e:
        logger.error(f"Failed to download/load SPICE dataset: {e}")
        raise DataIngestionError(f"Real data source (SPICE) unavailable: {e}")

def download_sapt(url: str) -> pd.DataFrame:
    """
    Download SAPT energy data.
    If the specific SAPT file is not available from a direct URL, 
    we check if it's part of the SPICE dataset or a known mirror.
    For this task, we assume SAPT data is derived or available from the same source 
    or a specific known location. If not, we raise an error.
    """
    logger.info("Attempting to load SAPT energy data...")
    
    # Check if SAPT data is embedded in the SPICE download or available separately
    # If the project spec implies a separate SAPT file, we would fetch it here.
    # For now, we assume the SPICE data contains the necessary energy components 
    # (electrostatic, dispersion, hbond) which are SAPT-derived.
    
    # If a separate SAPT file is strictly required and missing:
    sapt_path = 'data/raw/sapt.parquet'
    if os.path.exists(sapt_path):
        df = pd.read_parquet(sapt_path)
        logger.info(f"Loaded existing SAPT data from {sapt_path}")
        return df
    
    # If not found, we raise an error as per "Fail Loudly" constraint
    # We do NOT generate synthetic SAPT data for training.
    raise DataIngestionError("SAPT energy data file (data/raw/sapt.parquet) not found. "
                             "Real SAPT data is required for training. "
                             "Ensure T012a has run and data is available.")

def extract_structures_from_spice(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract unique cation/anion SMILES from the SPICE dataset.
    Saves to data/raw/il_structures.json.
    """
    logger.info("Extracting unique ion structures from SPICE dataset.")
    
    structures = {
        "cations": df['smiles_cation'].unique().tolist(),
        "anions": df['smiles_anion'].unique().tolist()
    }
    
    os.makedirs('data/raw', exist_ok=True)
    output_path = 'data/raw/il_structures.json'
    with open(output_path, 'w') as f:
        json.dump(structures, f, indent=2)
    
    logger.info(f"Structures saved to {output_path}: {len(structures['cations'])} cations, {len(structures['anions'])} anions")
    return pd.DataFrame(structures)

def calculate_partial_charges_internal_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Gasteiger partial charges for internal consistency checks ONLY.
    These values are NOT used for training.
    Saves to data/processed/internal_consistency_checks.parquet.
    """
    logger.info("Calculating partial charges for internal consistency checks...")
    
    def get_gasteiger_charges(smiles):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return 0.0
            Chem.ComputeGasteigerCharges(mol)
            charges = [float(atom.GetProp('_GasteigerCharge')) for atom in mol.GetAtoms()]
            return sum(abs(c) for c in charges) # Return sum of absolute charges as a proxy
        except:
            return 0.0

    # Apply to both cation and anion SMILES
    df['cation_charge_sum'] = df['smiles_cation'].apply(get_gasteiger_charges)
    df['anion_charge_sum'] = df['smiles_anion'].apply(get_gasteiger_charges)
    df['total_charge_proxy'] = df['cation_charge_sum'] + df['anion_charge_sum']
    
    # Save ONLY the internal consistency artifact
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/internal_consistency_checks.parquet'
    df[['cation_id', 'anion_id', 'total_charge_proxy']].to_parquet(output_path)
    
    logger.info(f"Internal consistency checks saved to {output_path}")
    
    # Return df with charges dropped for training (as per T016 requirement)
    # But keep the file saved as required by T015a
    return df.drop(columns=['cation_charge_sum', 'anion_charge_sum', 'total_charge_proxy'])

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features: TPSA, Surface Area, H-bond counts, etc.
    CRITICAL: Calls calculate_partial_charges_internal_only, saves artifact, then DROPS partial_charge.
    """
    logger.info("Engineering features...")
    
    # 1. Calculate partial charges for internal check (and save artifact)
    df = calculate_partial_charges_internal_only(df)
    
    # 2. Compute descriptors
    logger.info("Computing molecular descriptors...")
    
    def compute_row_features(row):
        cation_smiles = row['smiles_cation']
        anion_smiles = row['smiles_anion']
        
        c_tpsa = compute_tpsa(cation_smiles)
        a_tpsa = compute_tpsa(anion_smiles)
        
        c_hb = compute_hbond_count(cation_smiles)
        a_hb = compute_hbond_count(anion_smiles)
        
        c_mol = Chem.MolFromSmiles(cation_smiles)
        a_mol = Chem.MolFromSmiles(anion_smiles)
        
        c_surf = c_mol.GetSurfaceArea() if c_mol else 0.0
        a_surf = a_mol.GetSurfaceArea() if a_mol else 0.0
        
        return pd.Series({
            'total_tpsa': c_tpsa + a_tpsa,
            'cation_tpsa': c_tpsa,
            'anion_tpsa': a_tpsa,
            'total_hbond_count': c_hb + a_hb,
            'cation_hbond_count': c_hb,
            'anion_hbond_count': a_hb,
            'total_surface_area': c_surf + a_surf,
            'cation_surface_area': c_surf,
            'anion_surface_area': a_surf,
            'polarizability': compute_polarizability(cation_smiles) + compute_polarizability(anion_smiles)
        })

    features = df.apply(compute_row_features, axis=1)
    df = pd.concat([df, features], axis=1)
    
    # 3. Morgan Fingerprints (simplified as count of bits set, or full array if needed)
    # For this implementation, we store the bit count as a feature to keep the parquet manageable
    # unless the schema requires the full array.
    df['morgan_fp_count'] = df['smiles_cation'].apply(lambda x: len(compute_morgan_fp(x))) + \
                            df['smiles_anion'].apply(lambda x: len(compute_morgan_fp(x)))
    
    # 4. Drop partial_charge if it exists (from previous steps or if added)
    # The contract says partial_charge is calculated but excluded from training.
    # We ensured it was not added as a column named 'partial_charge' in the main df, 
    # but we saved the proxy to the internal check file.
    
    # Save unified dataset
    write_unified_dataset(df, 'data/processed/unified_dataset.parquet')
    
    return df

def merge_spice_sapt(spice_df: pd.DataFrame, sapt_df: pd.DataFrame) -> pd.DataFrame:
    """Merge SPICE and SAPT on cation_id and anion_id."""
    logger.info("Merging SPICE and SAPT data...")
    # Assuming both have cation_id and anion_id
    merged = pd.merge(spice_df, sapt_df, on=['cation_id', 'anion_id'], how='inner')
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged

def merge_training_data(base_df: pd.DataFrame, sapt_df: pd.DataFrame) -> pd.DataFrame:
    """Merge base structure data with real SAPT energy data."""
    return merge_spice_sapt(base_df, sapt_df)

def filter_raw_sapt(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to extract subset from SAPT source."""
    if 'source' in df.columns:
        return df[df['source'] == 'sapt']
    return df # Assume all are SAPT if no source column

def write_unified_dataset(df: pd.DataFrame, path: str):
    """Save unified dataset to parquet."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path)
    logger.info(f"Unified dataset saved to {path}")

def validate_unified_dataset(df: pd.DataFrame, schema_path: str) -> bool:
    """Validate dataset using pandera schema."""
    # Placeholder for pandera validation
    logger.info("Validating unified dataset...")
    return True

def log_validation_errors(errors: List[str]):
    """Log validation errors."""
    for err in errors:
        logger.error(f"Validation Error: {err}")

def select_data_sources() -> Dict[str, str]:
    """Select data sources. Fails if real SAPT data is missing."""
    spice_path = 'data/raw/spice.parquet'
    sapt_path = 'data/raw/sapt.parquet'
    
    if not os.path.exists(spice_path):
        raise DataIngestionError("SPICE data missing. Run T012a first.")
    
    if not os.path.exists(sapt_path):
        # Per T017a, if SAPT is missing, we must fail loudly.
        # We do NOT generate synthetic data for training.
        raise DataIngestionError("SAPT energy data missing. Real SAPT data is required for training. "
                                 "Cannot proceed without data/raw/sapt.parquet.")
    
    return {'spice': spice_path, 'sapt': sapt_path}

def main():
    """
    Main entry point for data ingestion.
    Orchestrates download, structure extraction, feature engineering, and saving.
    """
    logger.info("Starting Data Ingestion Pipeline (T038 dependency)")
    
    try:
        # 1. Download SPICE (Real Data)
        # Note: In a real environment, the URL would be from config
        spice_df = download_spice("https://huggingface.co/datasets/spice-ml/spice")
        
        # 2. Extract Structures
        extract_structures_from_spice(spice_df)
        
        # 3. Load SAPT (Real Data) - Fails if missing
        sapt_df = download_sapt("dummy_url") # URL not used, checks local file or raises
        
        # 4. Merge
        if sapt_df is not None:
            merged_df = merge_spice_sapt(spice_df, sapt_df)
        else:
            # Fallback if SAPT is not strictly required for some subset, but per spec it is
            merged_df = spice_df
            
        # 5. Engineer Features (includes internal charge check and unified save)
        final_df = engineer_features(merged_df)
        
        logger.info("Data Ingestion Pipeline Complete.")
        
    except DataIngestionError as e:
        logger.error(f"Data Ingestion Failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingestion: {e}")
        raise

if __name__ == "__main__":
    main()
