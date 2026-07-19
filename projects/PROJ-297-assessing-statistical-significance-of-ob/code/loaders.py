import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import config

# Ensure output directories exist before any logging setup
def ensure_output_dirs():
    """Create necessary output directories if they don't exist."""
    dirs = [
        "output",
        "output/logs",
        "output/results",
        "output/plots",
        "output/plots/primary",
        "output/reports",
        "output/exploratory",
        "data/raw",
        "data/processed"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Initialize directories immediately on import
ensure_output_dirs()

def setup_loader_logging():
    """Set up logging for the loaders module."""
    logger = logging.getLogger('loaders')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler('output/logs/loader.log', mode='a')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_loader_logging()

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums() -> Dict[str, str]:
    """Load existing checksums from data/raw/checksums.json."""
    checksum_file = Path("data/raw/checksums.json")
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]):
    """Save checksums to data/raw/checksums.json."""
    checksum_file = Path("data/raw/checksums.json")
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(filepath: str, expected_hash: str) -> bool:
    """Verify file integrity against expected hash."""
    actual_hash = compute_file_hash(filepath)
    return actual_hash == expected_hash

def fetch_uci_dataset(url: str, filename: str) -> str:
    """Fetch dataset from URL and save to data/raw/."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    local_path = raw_dir / filename
    
    if local_path.exists():
        logger.info(f"Dataset {filename} already exists at {local_path}")
        return str(local_path)
    
    logger.info(f"Downloading {filename} from {url}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded {filename} successfully")
        return str(local_path)
    except requests.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        raise

def load_dataset_from_path(filepath: str) -> pd.DataFrame:
    """Load dataset from CSV or Excel file."""
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == '.csv':
        df = pd.read_csv(filepath)
    elif filepath.suffix.lower() in ['.xls', '.xlsx']:
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    logger.info(f"Loaded dataset with shape {df.shape}")
    return df

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_rows = len(df)
    df_clean = df.dropna()
    dropped = initial_rows - len(df_clean)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with missing values")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect variables that have only one unique value."""
    constant_vars = []
    for col in df.select_dtypes(include=['number']).columns:
        if df[col].nunique() == 1:
            constant_vars.append(col)
    return constant_vars

def exclude_constant_variables(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Exclude constant variables from the dataset."""
    constant_vars = detect_constant_variables(df)
    if constant_vars:
        logger.info(f"Excluding constant variables: {constant_vars}")
        df_clean = df.drop(columns=constant_vars)
    else:
        df_clean = df
    return df_clean, constant_vars

def filter_continuous_variables(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Filter to keep only continuous (numeric) variables."""
    numeric_df = df.select_dtypes(include=['number'])
    count = len(numeric_df.columns)
    logger.info(f"Found {count} continuous variables")
    return numeric_df, count

def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool:
    """Validate that dataset has at least min_vars continuous variables."""
    _, count = filter_continuous_variables(df)
    return count >= min_vars

def apply_hygiene_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Apply full data hygiene pipeline."""
    # Drop missing values
    df = drop_missing_values(df)
    
    # Exclude constant variables
    df, constant_vars = exclude_constant_variables(df)
    
    # Filter continuous variables
    df, count = filter_continuous_variables(df)
    
    # Validate dimensions
    if not validate_dataset_dimensions(df):
        raise ValueError(f"Dataset has only {count} continuous variables, need >= {20}")
    
    return df

def load_and_hygiene_dataset(url: str, filename: str, min_vars: int = 20) -> pd.DataFrame:
    """Load dataset from URL and apply hygiene pipeline."""
    filepath = fetch_uci_dataset(url, filename)
    df = load_dataset_from_path(filepath)
    df = apply_hygiene_pipeline(df)
    return df

# Primary datasets from T004
PRIMARY_DATASETS = {
    "wine": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "filename": "wine.data"
    },
    "abalone": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data",
        "filename": "abalone.data"
    },
    "breast_cancer": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data",
        "filename": "breast-cancer-wisconsin.data"
    },
    "student_performance": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00298/student-mat.csv",
        "filename": "student-mat.csv"
    },
    "air_quality": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip",
        "filename": "AirQualityUCI.zip",
        "needs_unzip": True
    },
    "concrete": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls",
        "filename": "Concrete_Data.xls",
        "needs_excel": True
    }
}

# Fallback datasets from T080
FALLBACK_DATASETS = {
    "parkinsons": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data",
        "filename": "parkinsons.data"
    },
    "libras": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/libras/movements.data",
        "filename": "libras.data"
    },
    "isolet": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet1_train_data",
        "filename": "isolet1_train_data"
    }
}

def load_all_datasets(min_datasets: int = 3) -> Dict[str, pd.DataFrame]:
    """
    Load datasets from primary list, then fallback list if needed.
    Returns a dictionary of dataset_name -> DataFrame.
    
    Args:
        min_datasets: Minimum number of valid datasets required.
        
    Returns:
        Dictionary mapping dataset names to DataFrames.
        
    Raises:
        ValueError: If fewer than min_datasets valid datasets are found.
    """
    loaded_datasets = {}
    
    # Try primary datasets first
    logger.info("Attempting to load primary datasets...")
    for name, config_data in PRIMARY_DATASETS.items():
        try:
            url = config_data["url"]
            filename = config_data["filename"]
            needs_unzip = config_data.get("needs_unzip", False)
            needs_excel = config_data.get("needs_excel", False)
            
            # Handle special cases
            if needs_unzip:
                # For Air Quality, we need to unzip first
                # This is a simplified version - full implementation would extract CSV
                logger.warning(f"Dataset {name} requires unzip - skipping for now")
                continue
            elif needs_excel:
                # For Concrete, we need to handle Excel
                filepath = fetch_uci_dataset(url, filename)
                df = pd.read_excel(filepath)
            else:
                # Standard CSV loading
                df = load_and_hygiene_dataset(url, filename)
            
            # Validate variable count
            _, var_count = filter_continuous_variables(df)
            if var_count < 20:
                logger.warning(f"Dataset {name} has only {var_count} continuous variables (< 20), skipping")
                continue
            
            loaded_datasets[name] = df
            logger.info(f"Successfully loaded {name} with {var_count} variables")
            
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            continue
    
    # Check if we have enough datasets
    if len(loaded_datasets) >= min_datasets:
        logger.info(f"Loaded {len(loaded_datasets)} datasets from primary list, sufficient")
        return loaded_datasets
    
    # Need fallback datasets
    needed = min_datasets - len(loaded_datasets)
    logger.info(f"Primary list yielded {len(loaded_datasets)} datasets, need {needed} more from fallback list")
    
    fallback_count = 0
    for name, config_data in FALLBACK_DATASETS.items():
        if fallback_count >= needed:
            break
            
        try:
            url = config_data["url"]
            filename = config_data["filename"]
            
            df = load_and_hygiene_dataset(url, filename)
            
            # Validate variable count
            _, var_count = filter_continuous_variables(df)
            if var_count < 20:
                logger.warning(f"Fallback dataset {name} has only {var_count} continuous variables (< 20), skipping")
                continue
            
            loaded_datasets[name] = df
            fallback_count += 1
            logger.info(f"Successfully loaded fallback dataset {name} with {var_count} variables")
            
        except Exception as e:
            logger.error(f"Failed to load fallback dataset {name}: {e}")
            continue
    
    # Final check
    if len(loaded_datasets) < min_datasets:
        raise ValueError(
            f"Failed to load minimum required datasets. "
            f"Loaded {len(loaded_datasets)} datasets, need at least {min_datasets}. "
            f"Available: {list(loaded_datasets.keys())}"
        )
    
    logger.info(f"Successfully loaded {len(loaded_datasets)} datasets total")
    return loaded_datasets

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and process UCI datasets")
    parser.add_argument("--output", type=str, default="data/processed/",
                      help="Output directory for processed datasets")
    parser.add_argument("--min-datasets", type=int, default=3,
                      help="Minimum number of datasets to load")
    parser.add_argument("--save-all", action="store_true",
                      help="Save all loaded datasets to disk")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Load datasets with fallback logic
    datasets = load_all_datasets(min_datasets=args.min_datasets)
    
    # Save datasets if requested
    if args.save_all:
        for name, df in datasets.items():
            output_path = os.path.join(args.output, f"{name}_processed.csv")
            df.to_csv(output_path, index=False)
            logger.info(f"Saved processed {name} to {output_path}")
    
    logger.info(f"Loaded {len(datasets)} datasets successfully")
    return datasets

if __name__ == "__main__":
    main()