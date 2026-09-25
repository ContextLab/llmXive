import os
import sys
import hashlib
import tempfile
import logging
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logger import get_logger

logger = get_logger(__name__)

def load_config():
    """Load configuration from code/config/data_sources.yaml"""
    config_path = Path("code/config/data_sources.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_dataset(dataset_id: str, source_type: str):
    """
    Downloads or locates the dataset based on configuration.
    Returns a pandas DataFrame or a path to the CSV file.
    
    IMPORTANT: This function MUST fail loudly if the real data source is not found.
    No synthetic fallback is allowed.
    """
    logger.info(f"Attempting to load dataset: {dataset_id} from source: {source_type}")
    
    # Define expected paths
    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    if source_type == "local_csv":
        # Expect the file to be in data/raw/
        expected_file = raw_data_dir / "cyberbullying_2021.csv"
        
        if not expected_file.exists():
            raise RuntimeError(
                f"E-NO-REAL-SOURCE-001: Real data source not found at {expected_file}. "
                "Aborting to prevent synthetic data fabrication."
            )
        
        logger.info(f"Loading local CSV: {expected_file}")
        return pd.read_csv(expected_file)
    
    elif source_type == "huggingface":
        try:
            from datasets import load_dataset
            logger.info(f"Loading dataset from HuggingFace: {dataset_id}")
            ds = load_dataset(dataset_id, split="train")
            return ds.to_pandas()
        except Exception as e:
            raise RuntimeError(
                f"E-NO-REAL-SOURCE-001: Failed to load dataset from HuggingFace ({dataset_id}). "
                f"Error: {str(e)}. Aborting to prevent synthetic data fabrication."
            )
    
    elif source_type == "ucimlrepo":
        try:
            from ucimlrepo import fetch_ucirepo
            logger.info(f"Loading dataset from UCI: {dataset_id}")
            # Assuming dataset_id is the numeric ID
            dataset = fetch_ucirepo(id=int(dataset_id))
            return dataset.data.features  # Or .data.targets depending on structure
        except Exception as e:
            raise RuntimeError(
                f"E-NO-REAL-SOURCE-001: Failed to load dataset from UCI ({dataset_id}). "
                f"Error: {str(e)}. Aborting to prevent synthetic data fabrication."
            )
    
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def load_cyber_data():
    """Loads the Cyberbullying Survey 2021 dataset."""
    config = load_config()
    dataset_id = config.get('dataset_id')
    source_type = config.get('source')
    
    if not dataset_id or not source_type:
        raise RuntimeError("E-CONFIG-MISSING: dataset_id or source not found in config.")
    
    return download_dataset(dataset_id, source_type)

def load_gss_data():
    """
    Loads the GSS 2022 dataset.
    NOTE: This function is deprecated and should NOT be used per the Plan's Revised Approach.
    It is kept for reference but will raise an error if called.
    """
    raise NotImplementedError(
        "GSS data loading is excluded per the Plan's 'Revised Approach'. "
        "Do not use this function."
    )

def harmonize_datasets(df_cyber):
    """
    Harmonizes the loaded dataset to match the canonical column names.
    """
    # Mapping from raw columns to canonical names based on spec's Data Dictionary
    # This is a placeholder mapping; actual keys depend on the real dataset structure.
    # The real implementation should inspect the dataset and map accordingly.
    column_mapping = {
        # Example mappings - adjust based on actual dataset
        # 'raw_support_col': 'social_support',
        # 'raw_harassment_col': 'harassment_severity',
        # 'raw_depression_col': 'depression',
        # 'raw_anxiety_col': 'anxiety',
        # 'raw_ptsd_col': 'ptsd',
        # 'raw_platform_col': 'platform',
        # 'raw_age_col': 'age',
        # 'raw_gender_col': 'gender',
        # 'raw_education_col': 'education',
        # 'raw_income_col': 'income',
    }
    
    # Apply mapping if columns exist
    for old_name, new_name in column_mapping.items():
        if old_name in df_cyber.columns:
            df_cyber.rename(columns={old_name: new_name}, inplace=True)
            logger.info(f"Renamed column: {old_name} -> {new_name}")
    
    return df_cyber

def get_data_summary(df):
    """Generates a summary of the dataset."""
    summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_counts": df.isnull().sum().to_dict()
    }
    return summary

def validate_schema_presence(df):
    """
    Validates that essential columns are present.
    """
    essential_columns = [
        'social_support', 'harassment_severity', 'depression', 
        'anxiety', 'platform' # 'ptsd' is optional per T013c
    ]
    
    missing = [col for col in essential_columns if col not in df.columns]
    if missing:
        logger.warning(f"Missing essential columns: {missing}")
        # Do not raise here, as some might be optional or derived later
        return False
    return True

def run_ingestion_checks(df):
    """Runs checks on the ingested data."""
    checks_passed = True
    
    # Check for essential columns
    if not validate_schema_presence(df):
        checks_passed = False
    
    # Check for sufficient rows
    if len(df) < 30:
        logger.error("E-LOW-N: Dataset has fewer than 30 rows.")
        checks_passed = False
    
    return checks_passed

def main():
    """Entry point for ingestion script."""
    try:
        df = load_cyber_data()
        df = harmonize_datasets(df)
        
        if run_ingestion_checks(df):
            logger.info("Ingestion checks passed.")
            # Save raw data for verification
            raw_dir = Path("data/raw")
            raw_dir.mkdir(parents=True, exist_ok=True)
            output_path = raw_dir / "cyberbullying_2021.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved ingested data to {output_path}")
        else:
            logger.error("Ingestion checks failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()