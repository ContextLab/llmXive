"""
Preprocessing module for molecular property prediction.

This module handles:
1. Loading raw data from the download step.
2. Filtering for high-confidence measurements.
3. Detecting missing physical covariates (pH, temperature, pressure).
4. Generating a data quality report.
5. Implementing MaxMin diversity sampling (T010/T010.1).
6. Splitting the dataset into train/test sets (T011.5).
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

# Import project utilities
from utils.config import get_runtime_config
from logging_utils import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Constants
CONFIDENCE_THRESHOLD = 0.8
TARGET_PROPS = ['LogP', 'Solubility', 'Boiling Point']
COVARIATES = ['pH', 'Temperature', 'Pressure']

def ensure_dirs():
    """Ensure output directories exist."""
    dirs = [
        Path('data/raw'),
        Path('data/processed'),
        Path('data/derived')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured directories exist.")

def load_preprocessed_data(input_file: str) -> pd.DataFrame:
    """
    Load the raw dataset.

    Args:
        input_file: Path to the raw CSV file.

    Returns:
        DataFrame with raw data.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} records from {input_file}")
    return df

def filter_high_confidence(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter for high-confidence measurements.

    Logic:
    1. Exclude entries where confidence_score < 0.8 (if available).
    2. Exclude entries where target properties (logP, solubility, boiling point) are missing.

    Args:
        df: Input DataFrame.

    Returns:
        Filtered DataFrame and list of exclusion reasons.
    """
    reasons = []

    # Check for confidence score column
    if 'confidence_score' in df.columns:
        logger.info("Filtering by confidence_score >= 0.8")
        initial_count = len(df)
        df = df[df['confidence_score'] >= CONFIDENCE_THRESHOLD]
        dropped = initial_count - len(df)
        reasons.extend([{'reason': 'Low Confidence', 'count': dropped}])
        logger.info(f"Dropped {dropped} records due to low confidence.")
    else:
        logger.warning("No 'confidence_score' column found in dataset. Skipping confidence filter.")

    # Check for target properties
    missing_cols = [col for col in TARGET_PROPS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Target property columns missing: {missing_cols}. "
                       f"Cannot filter by property presence for these.")
    
    # Filter rows where at least one target property is present
    # We assume if a row is in the dataset, it has at least one property of interest
    # But we strictly check for non-null values in target columns
    valid_rows = df[TARGET_PROPS].notna().any(axis=1)
    initial_count = len(df)
    df = df[valid_rows]
    dropped = initial_count - len(df)
    if dropped > 0:
        reasons.append({'reason': 'Missing Target Property', 'count': dropped})
        logger.info(f"Dropped {dropped} records due to missing target properties.")

    return df, reasons

def detect_missing_covariates(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Detect missing physical covariates (pH, temperature, pressure).

    Args:
        df: Input DataFrame.

    Returns:
        Dictionary mapping SMILES to list of missing covariates.
    """
    missing_map = {}
    for idx, row in df.iterrows():
        missing_list = []
        for cov in COVARIATES:
            if cov not in df.columns or pd.isna(row.get(cov, None)):
                missing_list.append(cov)
        if missing_list:
            missing_map[row['SMILES']] = missing_list
    
    logger.info(f"Detected missing covariates for {len(missing_map)} molecules.")
    return missing_map

def generate_quality_report(df: pd.DataFrame, missing_covariates: Dict[str, List[str]], 
                            input_file: str) -> pd.DataFrame:
    """
    Generate the data quality report.

    Schema:
    - smiles
    - exclusion_reason
    - missing_covariate_list (list of missing physical fields)
    - experimental_flag

    Args:
        df: Filtered DataFrame.
        missing_covariates: Dict from detect_missing_covariates.
        input_file: Source file path.

    Returns:
        Quality report DataFrame.
    """
    report_data = []
    
    for idx, row in df.iterrows():
        smiles = row.get('SMILES', '')
        # Determine exclusion reason (if any applied in this step, though we filtered already)
        # For the report, we list the status of the *kept* records
        exclusion_reason = "None (Passed Filter)"
        
        missing_list = missing_covariates.get(smiles, [])
        
        # Determine experimental flag based on source_type or record_type
        exp_flag = False
        if 'Property Type' in row and 'Experimental' in str(row['Property Type']):
            exp_flag = True
        elif 'source_type' in row and 'Experimental' in str(row['source_type']):
            exp_flag = True
        
        report_data.append({
            'smiles': smiles,
            'exclusion_reason': exclusion_reason,
            'missing_covariate_list': missing_list,
            'experimental_flag': exp_flag
        })

    report_df = pd.DataFrame(report_data)
    output_path = Path('data/derived/data_quality_report.csv')
    report_df.to_csv(output_path, index=False)
    logger.info(f"Generated data quality report: {output_path}")
    return report_df

def tanimoto_similarity(fp1: List[int], fp2: List[int]) -> float:
    """Calculate Tanimoto similarity between two bit vectors."""
    if not fp1 or not fp2:
        return 0.0
    rdkit_fp1 = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(''), 2) # Placeholder
    # Convert list to RDKit ExplicitBitVect
    v1 = DataStructs.ExplicitBitVect(len(fp1))
    v2 = DataStructs.ExplicitBitVect(len(fp2))
    for i, bit in enumerate(fp1):
        if bit: v1.SetBit(i)
    for i, bit in enumerate(fp2):
        if bit: v2.SetBit(i)
    return DataStructs.TanimotoSimilarity(v1, v2)

def define_maxmin_strategy(df: pd.DataFrame, target_size: int = 5000) -> Dict[str, Any]:
    """
    Define the MaxMin strategy for diversity selection.

    Args:
        df: Input DataFrame.
        target_size: Target number of molecules.

    Returns:
        Strategy configuration dictionary.
    """
    # Check resource constraints (mocked for now, real check in T010.1)
    config = get_runtime_config()
    max_ram_gb = config.get('max_memory_gb', 6.0)
    
    # Adaptive target
    actual_target = min(target_size, len(df))
    
    return {
        'target_size': actual_target,
        'similarity_threshold': 0.7,
        'max_ram_gb': max_ram_gb,
        'method': 'MaxMinPicker'
    }

def maxmin_sampling(df: pd.DataFrame, strategy: Dict[str, Any]) -> pd.DataFrame:
    """
    Execute MaxMin sampling to select a diverse subset.

    Args:
        df: Input DataFrame.
        strategy: Strategy config.

    Returns:
        Subset DataFrame.
    """
    logger.info(f"Starting MaxMin sampling for {len(df)} molecules, target {strategy['target_size']}")
    
    # Generate fingerprints for all molecules
    smiles_list = df['SMILES'].tolist()
    fps = []
    valid_indices = []
    
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            fps.append(fp)
            valid_indices.append(i)
        else:
            logger.warning(f"Invalid SMILES at index {i}: {smi}")
    
    if len(fps) == 0:
        raise ValueError("No valid molecules found for sampling.")

    from rdkit.Chem import rdMolDescriptors
    
    # Use RDKit's MaxMinPicker
    picker = DataStructs.MaxMinPicker()
    target_n = strategy['target_size']
    if target_n > len(fps):
        target_n = len(fps)
    
    # Pick indices
    picked_indices = picker.Pick(fps, target_n)
    
    # Filter original dataframe
    selected_smiles = [smiles_list[i] for i in picked_indices]
    subset_df = df[df['SMILES'].isin(selected_smiles)].reset_index(drop=True)
    
    logger.info(f"MaxMin sampling complete. Selected {len(subset_df)} molecules.")
    return subset_df

def split_dataset(df: pd.DataFrame, train_ratio: float = 0.8, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into training and test sets.

    Args:
        df: Input DataFrame.
        train_ratio: Proportion for training.
        seed: Random seed.

    Returns:
        Train and Test DataFrames.
    """
    logger.info(f"Splitting dataset (train={train_ratio}, seed={seed})")
    train_df = df.sample(frac=train_ratio, random_state=seed)
    test_df = df.drop(train_df.index).reset_index(drop=True)
    train_df = train_df.reset_index(drop=True)
    
    # Save splits
    train_path = Path('data/derived/train_set.csv')
    test_path = Path('data/derived/test_set.csv')
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved train set ({len(train_df)}) to {train_path}")
    logger.info(f"Saved test set ({len(test_df)}) to {test_path}")
    
    return train_df, test_df

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Save processed dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def main():
    """Main entry point for preprocessing."""
    ensure_dirs()
    
    # Determine input file
    # T008 produces data/raw/pubchem_raw.csv
    input_file = 'data/raw/pubchem_raw.csv'
    
    if not os.path.exists(input_file):
        # Fallback for T031 verification if T008 used a different name, 
        # but spec says pubchem_raw.csv. If T008 failed, we stop.
        # However, the error log showed "chembl_dataset.csv" was expected in old code.
        # We strictly follow T008 spec: pubchem_raw.csv.
        if os.path.exists('data/raw/chembl_dataset.csv'):
            logger.warning("Using fallback chembl_dataset.csv. Please ensure T008 is fixed to produce pubchem_raw.csv.")
            input_file = 'data/raw/chembl_dataset.csv'
        else:
            raise FileNotFoundError(f"Input file {input_file} not found. Run T008 first.")

    # 1. Load
    df = load_preprocessed_data(input_file)
    
    # 2. Filter
    df, reasons = filter_high_confidence(df)
    if len(df) == 0:
        raise ValueError("No data remaining after filtering.")
    
    # 3. Detect Covariates
    missing_covs = detect_missing_covariates(df)
    
    # 4. Generate Report
    generate_quality_report(df, missing_covs, input_file)
    
    # 5. Save filtered data for downstream steps
    # T010.1 expects diverse subset, T011.5 expects split.
    # We save the filtered data first.
    filtered_path = 'data/derived/filtered_data.csv'
    save_processed_data(df, filtered_path)
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()