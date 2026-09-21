import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
import json
from src.setup_dirs import setup_directories
from src.logger import get_logger

logger = get_logger(__name__)

# Specific UCI datasets selected for univariate continuous analysis
# We target direct CSV data links.
DATASETS_CONFIG = [
    {
        "name": "Wine",
        "csv_name": "uci_wine.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "description": "Chemical constituents of wines. All 13 features are continuous."
    },
    {
        "name": "Iris",
        "csv_name": "uci_iris.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        "description": "Flower measurements. All 4 features are continuous."
    },
    {
        "name": "Breast_Cancer",
        "csv_name": "uci_breast_cancer.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data",
        "description": "Wisconsin Breast Cancer. Several continuous features."
    },
    {
        "name": "Diabetes",
        "csv_name": "uci_diabetes.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/pima-indians-diabetes/pima-indians-diabetes.data",
        "description": "Pima Indians Diabetes. All 8 features are continuous."
    },
    {
        "name": "Heart",
        "csv_name": "uci_heart.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
        "description": "Cleveland Heart Disease. Mix of types, we filter for continuous."
    }
]

def setup_directories_for_download():
    """Ensure raw and processed directories exist."""
    setup_directories()
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, processed_dir

def download_dataset(dataset_info: Dict, raw_dir: Path) -> Optional[Path]:
    """Download a dataset from UCI to the raw directory."""
    url = dataset_info["url"]
    csv_name = dataset_info["csv_name"]
    save_path = raw_dir / csv_name

    if save_path.exists():
        logger.info(f"Dataset {csv_name} already exists at {save_path}. Skipping download.")
        return save_path

    logger.info(f"Downloading {dataset_info['name']} from {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            with open(save_path, 'wb') as f:
                f.write(content)
        
        if save_path.stat().st_size == 0:
            logger.error(f"Downloaded file {csv_name} is empty.")
            save_path.unlink()
            return None

        logger.info(f"Successfully downloaded {csv_name} ({save_path.stat().st_size} bytes).")
        return save_path
    except urllib.error.URLError as e:
        logger.error(f"Failed to download {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return None

def identify_continuous_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that are purely numeric (continuous or discrete integers).
    We treat all numeric columns as continuous for the purpose of variance estimation.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    logger.info(f"Identified {len(numeric_cols)} numeric columns: {numeric_cols}")
    return numeric_cols

def clean_and_process_dataset(df: pd.DataFrame, name: str, raw_path: Path) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean the dataset:
    1. Identify continuous columns.
    2. Handle missing values (represented as '?' in some UCI datasets).
    3. Calculate baseline variance for each continuous column.
    4. Return clean dataframe and metadata.
    """
    # Handle '?' as NaN
    df = df.replace('?', np.nan)
    
    # Identify continuous columns
    continuous_cols = identify_continuous_columns(df)
    
    if not continuous_cols:
        logger.warning(f"No continuous columns found in {name}. Skipping processing.")
        return pd.DataFrame(), {}

    # Filter dataframe to only continuous columns
    df_clean = df[continuous_cols].copy()
    
    # Convert to numeric, coercing errors to NaN
    for col in continuous_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Drop rows with any NaN in continuous columns
    initial_rows = len(df_clean)
    df_clean = df_clean.dropna()
    dropped_rows = initial_rows - len(df_clean)
    if dropped_rows > 0:
        logger.info(f"Dropped {dropped_rows} rows with missing values in {name}.")

    if len(df_clean) == 0:
        logger.error(f"No valid data remaining for {name} after cleaning.")
        return pd.DataFrame(), {}

    # Calculate baseline variance
    variances = df_clean.var().to_dict()
    metadata = {
        "dataset_name": name,
        "source_file": raw_path.name,
        "continuous_columns": continuous_cols,
        "rows_before_cleaning": initial_rows,
        "rows_after_cleaning": len(df_clean),
        "dropped_rows": dropped_rows,
        "baseline_variances": variances
    }

    return df_clean, metadata

def process_all_datasets():
    """Main entry point to download, clean, and process all 5 datasets."""
    raw_dir, processed_dir = setup_directories_for_download()
    all_metadata = []

    for ds in DATASETS_CONFIG:
        name = ds["name"]
        logger.info(f"Processing dataset: {name}")
        
        # 1. Download
        raw_path = download_dataset(ds, raw_dir)
        if raw_path is None:
            logger.error(f"Skipping {name} due to download failure.")
            continue

        # 2. Load
        try:
            # Most UCI data files don't have headers.
            df = pd.read_csv(raw_path, header=None)
        except Exception as e:
            logger.error(f"Failed to load {raw_path}: {e}")
            continue

        # 3. Clean and Process
        df_clean, metadata = clean_and_process_dataset(df, name, raw_path)
        
        if df_clean.empty:
            logger.warning(f"Dataset {name} resulted in empty clean dataframe.")
            continue

        # 4. Save Clean CSV
        output_filename = f"uci_clean_{name.lower()}.csv"
        output_path = processed_dir / output_filename
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Saved clean dataset to {output_path}")

        # 5. Save Variance Metadata
        meta_filename = f"uci_clean_{name.lower()}_variance.json"
        meta_path = processed_dir / meta_filename
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved variance metadata to {meta_path}")

        all_metadata.append(metadata)

    # Save a summary of all variances
    summary_path = processed_dir / "uci_all_variances.json"
    with open(summary_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    logger.info(f"Saved summary to {summary_path}")

    return all_metadata

def main():
    """Entry point for the script."""
    logger.info("Starting UCI Dataset Download and Processing...")
    try:
        results = process_all_datasets()
        logger.info(f"Successfully processed {len(results)} datasets.")
        print(f"Completed. Processed {len(results)} datasets.")
    except Exception as e:
        logger.critical(f"Fatal error in UCI Downloader: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
