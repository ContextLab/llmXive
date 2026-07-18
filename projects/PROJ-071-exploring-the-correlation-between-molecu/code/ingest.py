import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import pandas as pd
from datasets import load_dataset
from rdkit import Chem

from config import get_config
from logging_config import get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_failure

# Use config to resolve paths instead of hardcoding
def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

logger = get_logger(__name__)

def fetch_fda_drugs():
    """
    Fetch FDA-approved drugs from HuggingFace dataset.
    Uses streaming to handle large datasets efficiently.
    """
    dataset_name = "Synthyra/FDA-Approved-Drugs"
    logger.info(f"Fetching dataset: {dataset_name}")
    try:
        # Use streaming to avoid loading entire dataset into memory
        dataset = load_dataset(dataset_name, streaming=True)
        # Convert to list for processing (or iterate if streaming is sufficient)
        # For this implementation, we assume we need to process all records
        # If memory is a concern, we would iterate chunk by chunk
        data = list(dataset['train'])
        df = pd.DataFrame(data)
        logger.info(f"Fetched {len(df)} records from {dataset_name}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def check_degradation_columns(df: pd.DataFrame) -> bool:
    """
    Check if the dataframe contains necessary degradation columns.
    """
    required_cols = ['half_life', 'degradation_rate']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.warning(f"Missing degradation columns: {missing}")
        return False
    return True

def validate_smiles_series(smiles_series: pd.Series) -> pd.Series:
    """
    Validate a series of SMILES strings and return a filtered series.
    """
    valid_smiles = []
    for idx, smi in smiles_series.items():
        if pd.isna(smi):
            continue
        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            valid_smiles.append(smi)
        else:
            logger.debug(f"Invalid SMILES at index {idx}: {smi}")
    return pd.Series(valid_smiles)

def generate_insufficiency_report(reason: str, output_path: Path):
    """
    Generate a report when data is insufficient.
    """
    report_content = f"""
    # Data Insufficiency Report

    **Reason**: {reason}
    **Timestamp**: {pd.Timestamp.now()}

    The data availability gate was not met. The pipeline cannot proceed.
    """
    with open(output_path, 'w') as f:
        f.write(report_content.strip())
    logger.info(f"Generated insufficiency report at {output_path}")

def run_data_availability_gate(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Check if the dataset meets the minimum size requirement (N >= 30).
    Returns (passed, reason_if_failed).
    """
    n = len(df)
    if n < 30:
        reason = f"Dataset size (N={n}) is below the minimum threshold of 30."
        return False, reason
    return True, None

def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge structural and degradation dataframes on a common key (e.g., 'smiles' or 'id').
    """
    # Assuming 'smiles' is the common key
    common_key = 'smiles'
    if common_key not in structural_df.columns or common_key not in degradation_df.columns:
        raise ValueError(f"Common key '{common_key}' not found in both dataframes")
    
    merged = pd.merge(structural_df, degradation_df, on=common_key, how='inner')
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged

def filter_valid_records(df: pd.DataFrame, valid_smiles: pd.Series) -> pd.DataFrame:
    """
    Filter dataframe to only include records with valid SMILES.
    """
    valid_set = set(valid_smiles.dropna().unique())
    filtered = df[df['smiles'].isin(valid_set)]
    logger.info(f"Filtered dataset size: {len(filtered)}")
    return filtered

def calculate_checksums(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_merged_dataset(df: pd.DataFrame, output_path: Path):
    """
    Save the merged dataset to CSV and generate checksums.
    """
    df.to_csv(output_path, index=False)
    checksum = calculate_checksums(output_path)
    checksum_file = output_path.parent / "checksums.txt"
    with open(checksum_file, 'a') as f:
        f.write(f"{output_path.name}: {checksum}\n")
    logger.info(f"Saved merged dataset to {output_path} with checksum {checksum}")

def main():
    config = get_config()
    log_pipeline_start("ingest")
    
    try:
        # Fetch data
        df = fetch_fda_drugs()
        
        # Check for degradation columns
        if not check_degradation_columns(df):
            insufficiency_path = get_data_path() / "data_insufficiency_report.md"
            generate_insufficiency_report("Missing degradation columns", insufficiency_path)
            log_pipeline_failure("Missing degradation columns")
            return
        
        # Validate SMILES
        valid_smiles = validate_smiles_series(df['smiles'])
        
        # Filter valid records
        df_valid = filter_valid_records(df, valid_smiles)
        
        # Run data availability gate
        passed, reason = run_data_availability_gate(df_valid)
        if not passed:
            insufficiency_path = get_data_path() / "data_insufficiency_report.md"
            generate_insufficiency_report(reason, insufficiency_path)
            log_pipeline_failure(reason)
            return
        
        # Save merged dataset
        output_path = get_data_path() / "processed" / "merged_drugs.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_merged_dataset(df_valid, output_path)
        
        log_pipeline_complete("ingest")
    except Exception as e:
        log_pipeline_failure(str(e))
        raise

if __name__ == "__main__":
    main()
