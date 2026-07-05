"""
UCI Dataset Downloader and Preprocessor.

Downloads 5 public datasets from the UCI Machine Learning Repository,
identifies univariate continuous variables, and outputs clean CSV files
with baseline variance values.
"""
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
import yaml

# Add project root to path if running as script
if __package__ is None:
    root_dir = Path(__file__).resolve().parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from src.setup_dirs import setup_directories
from src.logger import get_logger, configure_logger
from src.validators import load_schema, validate_data, validate_type, validate_value

# Configure logging
logger = get_logger(__name__)

# UCI Dataset configurations (real, public datasets)
# Using raw GitHub URLs or direct HTTP links for reliability
UCI_DATASETS = [
    {
        "name": "uci_automobile",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/autos/cimports-automobile.data",
        "target_file": "data/raw/uci_automobile.csv",
        "processed_file": "data/processed/uci_clean_automobile.csv",
        "description": "Automobile dataset with continuous variables like price, engine-size, etc."
    },
    {
        "name": "uci_breast_cancer",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data",
        "target_file": "data/raw/uci_breast_cancer.csv",
        "processed_file": "data/processed/uci_clean_breast_cancer.csv",
        "description": "Wisconsin Breast Cancer dataset with continuous measurements."
    },
    {
        "name": "uci_iris",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        "target_file": "data/raw/uci_iris.csv",
        "processed_file": "data/processed/uci_clean_iris.csv",
        "description": "Classic Iris flower dataset with 4 continuous features."
    },
    {
        "name": "uci_wine",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "target_file": "data/raw/uci_wine.csv",
        "processed_file": "data/processed/uci_clean_wine.csv",
        "description": "Wine dataset with continuous chemical measurements."
    },
    {
        "name": "uci_diabetes",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/pima-indians-diabetes/pima-indians-diabetes.data",
        "target_file": "data/raw/uci_diabetes.csv",
        "processed_file": "data/processed/uci_clean_diabetes.csv",
        "description": "Pima Indians Diabetes dataset with continuous medical features."
    }
]

def setup_directories_for_download():
    """Ensure data directories exist."""
    setup_directories()
    logger.info("Data directories ensured.")

def download_dataset(url: str, target_path: Path) -> bool:
    """
    Download a dataset from a URL to a target path.
    Returns True on success, False on failure.
    """
    try:
        logger.info(f"Downloading from {url} to {target_path}...")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add headers to mimic a browser request to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(target_path, 'wb') as out_file:
                out_file.write(response.read())
        
        logger.info(f"Successfully downloaded {target_path.name}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} downloading {url}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL Error downloading {url}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def identify_continuous_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify univariate continuous variables in a DataFrame.
    Returns a list of column names that are numeric and have variance > 0.
    """
    continuous_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Check for variance > 0 to ensure it's not a constant
            if df[col].var() > 0:
                continuous_cols.append(col)
            else:
                logger.debug(f"Column {col} is numeric but constant (variance=0), skipping.")
        else:
            logger.debug(f"Column {col} is non-numeric ({df[col].dtype}), skipping.")
    return continuous_cols

def clean_and_process_dataset(
    df: pd.DataFrame, 
    continuous_cols: List[str], 
    output_path: Path
) -> Dict:
    """
    Clean the dataset by handling missing values and outliers (basic),
    then calculate baseline variance for continuous columns.
    Returns a dictionary of baseline variances.
    """
    logger.info(f"Processing dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Basic cleaning: drop rows with any NaN in continuous columns
    # For this task, we focus on continuous variables only
    if continuous_cols:
        df_clean = df[continuous_cols].dropna()
    else:
        logger.warning("No continuous columns found. Saving empty result.")
        df_clean = pd.DataFrame()

    # Save clean data
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved clean dataset to {output_path} with {df_clean.shape[0]} rows")

    # Calculate baseline variance
    baseline_variance = {}
    for col in continuous_cols:
        if col in df_clean.columns and df_clean[col].var() > 0:
            baseline_variance[col] = float(df_clean[col].var())
        else:
            baseline_variance[col] = 0.0

    return baseline_variance

def process_all_datasets():
    """Main execution function to download and process all datasets."""
    setup_directories_for_download()
    
    results = []
    success_count = 0

    for dataset_config in UCI_DATASETS:
        name = dataset_config["name"]
        url = dataset_config["url"]
        raw_path = Path(dataset_config["target_file"])
        clean_path = Path(dataset_config["processed_file"])

        logger.info(f"--- Processing {name} ---")

        # Download
        if not download_dataset(url, raw_path):
            logger.error(f"Failed to download {name}. Skipping.")
            continue

        # Load
        try:
            # Infer delimiter (comma or semicolon) and header presence
            # Most UCI datasets are comma-separated without headers
            df = pd.read_csv(raw_path, header=None)
            # Assign generic column names
            df.columns = [f"col_{i}" for i in range(df.shape[1])]
            logger.info(f"Loaded {name} with shape {df.shape}")
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            continue

        # Identify continuous columns
        continuous_cols = identify_continuous_columns(df)
        if not continuous_cols:
            logger.warning(f"No continuous columns found in {name}.")
            # Create empty output file to indicate processing attempt
            pd.DataFrame().to_csv(clean_path, index=False)
            results.append({
                "dataset": name,
                "status": "no_continuous_cols",
                "variance": {},
                "rows": 0
            })
            continue

        # Process and clean
        baseline_variance = clean_and_process_dataset(df, continuous_cols, clean_path)
        
        results.append({
            "dataset": name,
            "status": "success",
            "continuous_columns": continuous_cols,
            "variance": baseline_variance,
            "rows": len(df) if 'df' in locals() else 0
        })
        success_count += 1

    # Save summary of results
    summary_path = Path("data/processed/uci_baseline_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Processing complete. {success_count}/{len(UCI_DATASETS)} datasets processed successfully.")
    logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    # Initialize logging configuration if not already done
    # This assumes the project structure is set up as per T008
    try:
        configure_logger(level="INFO")
    except Exception:
        pass # Logger might already be configured

    process_all_datasets()
