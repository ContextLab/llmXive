import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import pandas as pd
from datasets import load_dataset

# Import from local modules using relative imports or absolute imports as per project structure
# Assuming code/ is in sys.path or this file is run as a module within the project
from config import get_config
from logging_config import get_logger, log_error

# Use config to get paths dynamically
def get_data_path(relative_path: str) -> Path:
    config = get_config()
    return Path(config.get("data_dir", "data")) / relative_path

def fetch_fda_drugs() -> pd.DataFrame:
    """
    Fetches FDA-approved drugs from HuggingFace dataset.
    Uses streaming to handle potential memory constraints.
    """
    logger = get_logger(__name__)
    logger.info("Fetching FDA-approved drugs dataset...")
    
    try:
        # Load dataset with streaming to avoid loading full dataset into memory
        dataset = load_dataset("Synthyra/FDA-Approved-Drugs", streaming=True)
        
        # Convert to DataFrame (limit to first few rows for initial check if needed, 
        # but for full processing we iterate)
        # Since streaming returns an IterableDataset, we need to handle it carefully
        # For now, we'll load a sample to check structure, then process fully if needed
        sample = next(iter(dataset['train']))
        df_sample = pd.DataFrame([sample])
        
        # If we need the full dataset, we would iterate and build chunks
        # For this implementation, we assume the dataset fits in memory or is processed in chunks
        # Let's load the full dataset for now, but with a warning if it's too large
        logger.info("Loading full dataset...")
        full_dataset = load_dataset("Synthyra/FDA-Approved-Drugs", split="train")
        df = full_dataset.to_pandas()
        
        logger.info(f"Loaded {len(df)} records from FDA-approved drugs dataset.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch FDA drugs: {str(e)}")
        raise

def check_degradation_columns(df: pd.DataFrame) -> bool:
    """
    Checks if the dataframe contains necessary degradation columns.
    """
    logger = get_logger(__name__)
    required_cols = ['half_life', 'degradation_rate'] # Adjust based on actual dataset schema
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        logger.warning(f"Missing degradation columns: {missing}")
        return False
    return True

def validate_smiles_series(smiles_series: pd.Series) -> Tuple[pd.Series, List[str]]:
    """
    Validates SMILES strings and returns valid series and list of invalid SMILES.
    """
    from rdkit import Chem
    logger = get_logger(__name__)
    valid_smiles = []
    invalid_smiles = []
    
    for i, smiles in enumerate(smiles_series):
        if pd.isna(smiles):
            invalid_smiles.append(f"Row {i}: NaN")
            continue
        try:
            mol = Chem.MolFromSmiles(str(smiles))
            if mol is None:
                invalid_smiles.append(f"Row {i}: {smiles}")
            else:
                valid_smiles.append(smiles)
        except Exception as e:
            invalid_smiles.append(f"Row {i}: {smiles} - Error: {str(e)}")
    
    return pd.Series(valid_smiles), invalid_smiles

def generate_insufficiency_report(n: int, min_n: int = 30) -> str:
    """
    Generates a report explaining data insufficiency.
    """
    report_path = get_data_path("data_insufficiency_report.md")
    with open(report_path, 'w') as f:
        f.write(f"# Data Insufficiency Report\n\n")
        f.write(f"## Summary\n")
        f.write(f"The dataset contains {n} records, which is below the minimum threshold of {min_n}.\n\n")
        f.write(f"## Recommendation\n")
        f.write(f"Unable to proceed with analysis due to insufficient data.\n")
    return str(report_path)

def run_data_availability_gate(df: pd.DataFrame, min_n: int = 30) -> bool:
    """
    Runs the data availability gate. Returns True if sufficient data, False otherwise.
    """
    logger = get_logger(__name__)
    n = len(df)
    logger.info(f"Data Availability Gate: {n} records found (min required: {min_n})")
    
    if n < min_n:
        generate_insufficiency_report(n, min_n)
        logger.error("Data insufficiency detected. Aborting pipeline.")
        return False
    return True

def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges structural and degradation dataframes.
    """
    logger = get_logger(__name__)
    try:
        merged = pd.merge(structural_df, degradation_df, on='smiles', how='inner')
        logger.info(f"Merged dataset size: {len(merged)} records.")
        return merged
    except Exception as e:
        logger.error(f"Failed to merge data: {str(e)}")
        raise

def filter_valid_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters records with valid SMILES and non-null degradation values.
    """
    logger = get_logger(__name__)
    initial_count = len(df)
    df = df.dropna(subset=['smiles', 'half_life']) # Adjust column names as needed
    df = df[df['smiles'].apply(lambda x: Chem.MolFromSmiles(str(x)) is not None)]
    final_count = len(df)
    logger.info(f"Filtered records: {initial_count} -> {final_count}")
    return df

def calculate_checksums(file_path: Path) -> str:
    """
    Calculates SHA256 checksum for a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> str:
    """
    Saves merged dataset to CSV and returns checksum.
    """
    logger = get_logger(__name__)
    df.to_csv(output_path, index=False)
    checksum = calculate_checksums(output_path)
    logger.info(f"Saved merged dataset to {output_path} with checksum {checksum}")
    return checksum

def main():
    """
    Main entry point for data ingestion.
    """
    logger = get_logger(__name__)
    logger.info("Starting data ingestion pipeline...")
    
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch data
    df = fetch_fda_drugs()
    
    # Check degradation columns
    if not check_degradation_columns(df):
        logger.error("Degradation columns missing. Aborting.")
        return
    
    # Run data availability gate
    if not run_data_availability_gate(df):
        return
    
    # Validate and filter
    df_valid, invalid_smiles = validate_smiles_series(df['smiles'])
    if invalid_smiles:
        error_log_path = get_data_path("errors.log")
        with open(error_log_path, 'w') as f:
            f.write("\n".join(invalid_smiles))
        logger.warning(f"Logged {len(invalid_smiles)} invalid SMILES to {error_log_path}")
    
    df_filtered = filter_valid_records(df)
    
    # Save merged dataset
    output_path = processed_dir / "merged_drugs.csv"
    checksum = save_merged_dataset(df_filtered, output_path)
    
    # Save checksums
    checksums_path = processed_dir / "checksums.txt"
    with open(checksums_path, 'w') as f:
        f.write(f"{output_path.name}: {checksum}\n")
    
    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
