import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
from rdkit import RDLogger
import psutil

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TARGET_PROPS = ['logP', 'Solubility', 'Boiling Point']
RAW_DATA_PATH = Path('data/raw/pubchem_raw.csv')
QUALITY_REPORT_PATH = Path('data/derived/data_quality_report.csv')
DIVERSE_SUBSET_PATH = Path('data/derived/diverse_subset.csv')
TRAIN_SET_PATH = Path('data/derived/train_set.csv')
TEST_SET_PATH = Path('data/derived/test_set.csv')
SEED = 42

def ensure_dirs():
    """Ensure all required directories exist."""
    for path in [QUALITY_REPORT_PATH, DIVERSE_SUBSET_PATH, TRAIN_SET_PATH, TEST_SET_PATH]:
        path.parent.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data() -> pd.DataFrame:
    """Load the raw data fetched in T008."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}. Run T008 first.")
    df = pd.read_csv(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {RAW_DATA_PATH}")
    return df

def filter_high_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset to keep only high-confidence entries.
    Logic:
    1. Exclude entries where confidence_score < 0.8 (if available).
    2. Exclude entries where target properties (logP, Solubility, Boiling Point) are missing.
    """
    if 'confidence_score' in df.columns:
        df = df[df['confidence_score'] >= 0.8]
        logger.info(f"Filtered by confidence >= 0.8. Rows remaining: {len(df)}")

    # Check for target properties. The schema might have them as separate rows or columns.
    # Based on T008 output schema: 'smiles', 'property_name', 'value', 'source_type'
    # We need to pivot or filter to ensure we have rows for the specific properties.
    
    # If the data is in long format (property_name column), we need to ensure we have
    # entries for the specific properties we care about, but the task says "Exclude entries...
    # where target properties... are missing". This usually implies a wide format or
    # a check that for a given SMILES, the value exists.
    
    # Let's assume for this step we are working with a filtered set where we only keep
    # rows that HAVE a value for one of the target properties.
    # If the data is already in long format, we filter rows where property_name is in TARGET_PROPS.
    
    if 'property_name' in df.columns:
        valid_props = df['property_name'].isin(TARGET_PROPS)
        df = df[valid_props]
        logger.info(f"Filtered to target properties. Rows remaining: {len(df)}")
    else:
        # Wide format check
        valid_rows = df[TARGET_PROPS].notna().any(axis=1)
        df = df[valid_rows]
        logger.info(f"Filtered to rows with any target property. Rows remaining: {len(df)}")

    return df

def detect_missing_covariates(df: pd.DataFrame) -> List[str]:
    """
    Explicitly check for physical covariates: pH, temperature, pressure.
    Return a list of missing fields found in the dataset schema.
    """
    covariates = ['pH', 'temperature', 'pressure']
    missing = []
    for cov in covariates:
        if cov not in df.columns:
            missing.append(cov)
    if missing:
        logger.warning(f"Missing physical covariates in source data: {missing}")
    return missing

def generate_quality_report(df: pd.DataFrame, missing_covariates: List[str]) -> pd.DataFrame:
    """
    Generate the data quality report.
    Columns: smiles, exclusion_reason, missing_covariate_list, experimental_flag, experimental_ratio
    """
    ensure_dirs()
    
    # Calculate experimental ratio
    if 'source_type' in df.columns:
        total = len(df)
        experimental = len(df[df['source_type'] == 'Experimental'])
        experimental_ratio = experimental / total if total > 0 else 0.0
    else:
        # If source_type is missing, we can't calculate ratio, assume 0 or handle gracefully
        experimental_ratio = 0.0
        logger.warning("source_type column missing, setting experimental_ratio to 0.0")

    # Create report dataframe
    # Since we are filtering rows, we need to track why rows were excluded or included.
    # For this task, we generate a report for the CURRENT dataframe state.
    # The task asks for 'smiles', 'exclusion_reason', etc.
    # Since we are filtering IN, we can mark included rows.
    
    # To satisfy the schema requirement, we create a summary row or per-row status.
    # Given the context of T009, it likely wants a per-row status or a summary.
    # Let's create a summary report row as per the "flag" requirement.
    
    report_data = {
        'smiles': 'SUMMARY',
        'exclusion_reason': 'None (Data Quality Check)',
        'missing_covariate_list': missing_covariates,
        'experimental_flag': 'True' if experimental_ratio >= 0.5 else 'False',
        'experimental_ratio': experimental_ratio
    }
    
    report_df = pd.DataFrame([report_data])
    report_df.to_csv(QUALITY_REPORT_PATH, index=False)
    logger.info(f"Data quality report saved to {QUALITY_REPORT_PATH}")
    return report_df

def tanimoto_similarity(fp1, fp2) -> float:
    """Calculate Tanimoto similarity between two RDKit fingerprints."""
    return DataStructs.TanimotoSimilarity(fp1, fp2)

def define_maxmin_strategy(df: pd.DataFrame) -> Tuple[int, str]:
    """
    Define the MaxMin strategy based on resource telemetry.
    Returns: (target_count, reason)
    """
    ram_available_gb = psutil.virtual_memory().available / (1024 ** 3)
    cpu_count = psutil.cpu_count(logical=False)
    
    target = 5000
    reason = "Standard target (RAM >= 6GB, CPU >= 2)"
    
    if ram_available_gb < 6.0 or (cpu_count is not None and cpu_count < 2):
        target = 2000
        reason = f"Reduced target due to resource constraints: RAM={ram_available_gb:.2f}GB, CPU={cpu_count}"
        
    logger.info(f"MaxMin Strategy: Target={target}, Reason={reason}")
    return target, reason

def maxmin_sampling(df: pd.DataFrame, target_count: int) -> pd.DataFrame:
    """
    Execute MaxMin sampling to select a diverse subset.
    Uses RDKit's MaxMinPicker.
    """
    if len(df) == 0:
        logger.error("Input dataframe is empty.")
        return pd.DataFrame()

    # Filter for unique SMILES if duplicates exist (MaxMinPicker needs unique molecules)
    # We assume the dataframe has 'smiles' and 'property_name', 'value'.
    # We need to pick diverse molecules, so we work on unique SMILES.
    unique_smiles = df['smiles'].unique()
    logger.info(f"Processing {len(unique_smiles)} unique molecules for diversity selection.")

    if len(unique_smiles) < target_count:
        logger.info(f"Total unique molecules ({len(unique_smiles)}) is less than target ({target_count}). Returning all.")
        return df

    # Convert SMILES to RDKit molecules and fingerprints
    mols = []
    valid_indices = []
    smiles_list = []
    
    for i, smiles in enumerate(unique_smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            mols.append(fp)
            valid_indices.append(i)
            smiles_list.append(smiles)
    
    logger.info(f"Converted {len(mols)} valid molecules to fingerprints.")
    
    if len(mols) == 0:
        logger.error("No valid molecules found for fingerprint generation.")
        return pd.DataFrame()

    # Use MaxMinPicker
    picker = AllChem.MaxMinPicker()
    # pickList returns indices into the list of molecules provided
    # We want to pick 'target_count' molecules
    picked_indices = picker.PickList(mols, len(mols), target_count)
    
    if len(picked_indices) == 0:
        logger.warning("MaxMinPicker returned empty list. Falling back to random sample.")
        picked_indices = list(range(min(target_count, len(mols))))
    
    selected_smiles = [smiles_list[i] for i in picked_indices]
    logger.info(f"Selected {len(selected_smiles)} diverse molecules.")
    
    # Filter original dataframe to these SMILES
    diverse_df = df[df['smiles'].isin(selected_smiles)].reset_index(drop=True)
    diverse_df.to_csv(DIVERSE_SUBSET_PATH, index=False)
    logger.info(f"Diverse subset saved to {DIVERSE_SUBSET_PATH}")
    
    return diverse_df

def split_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the diverse dataset into train and test sets.
    Stratified by source_type if available, otherwise random.
    """
    ensure_dirs()
    np.random.seed(SEED)
    
    if 'source_type' in df.columns:
        train_df, test_df = train_test_split(
            df, train_size=0.8, stratify=df['source_type'], random_state=SEED
        )
    else:
        train_df, test_df = train_test_split(
            df, train_size=0.8, random_state=SEED
        )
    
    train_df.to_csv(TRAIN_SET_PATH, index=False)
    test_df.to_csv(TEST_SET_PATH, index=False)
    logger.info(f"Train set: {len(train_df)}, Test set: {len(test_df)}")
    logger.info(f"Train set saved to {TRAIN_SET_PATH}")
    logger.info(f"Test set saved to {TEST_SET_PATH}")
    
    return train_df, test_df

def save_processed_data(df: pd.DataFrame, path: Path):
    """Helper to save processed data."""
    df.to_csv(path, index=False)

def main():
    """Main execution flow for T010 and T010.1."""
    ensure_dirs()
    
    # 1. Load raw data
    try:
        df = load_preprocessed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Filter high confidence
    df = filter_high_confidence(df)
    
    # 3. Detect missing covariates
    missing_covariates = detect_missing_covariates(df)
    
    # 4. Generate quality report (T009 dependency)
    generate_quality_report(df, missing_covariates)
    
    # 5. Define MaxMin Strategy (T010)
    target_count, strategy_reason = define_maxmin_strategy(df)
    logger.info(f"Strategy defined: {strategy_reason}")
    
    # 6. Execute MaxMin Sampling (T010.1)
    diverse_df = maxmin_sampling(df, target_count)
    
    if diverse_df.empty:
        logger.error("MaxMin sampling resulted in an empty dataset.")
        sys.exit(1)
    
    # 7. Split Dataset (T011.5)
    train_df, test_df = split_dataset(diverse_df)
    
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()