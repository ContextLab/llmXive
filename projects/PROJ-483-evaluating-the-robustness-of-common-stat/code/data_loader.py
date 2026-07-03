import os
import json
import hashlib
import pandas as pd
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load the datasets manifest from a YAML file."""
    with open(manifest_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('datasets', [])

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(url: str, output_path: str) -> bool:
    """Fetch a dataset from a URL and save it to the output path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return False

def validate_dataset(df: pd.DataFrame, dataset_info: Dict[str, Any]) -> bool:
    """
    Validate that the dataset contains continuous or categorical variables
    suitable for t-tests, ANOVA, or chi-squared tests.
    
    Requirements:
    - At least one numeric column (for t-test/ANOVA)
    - At least one categorical column OR target is categorical (for chi-squared)
    - Minimum 50 rows (FR-001)
    """
    if len(df) < 50:
        print(f"Dataset {dataset_info['name']} has fewer than 50 rows ({len(df)}). Skipping.")
        return False

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    has_numeric = len(numeric_cols) > 0
    has_categorical = len(categorical_cols) > 0

    if not has_numeric and not has_categorical:
        print(f"Dataset {dataset_info['name']} has no numeric or categorical columns. Skipping.")
        return False

    # For t-test/ANOVA we need numeric features
    # For chi-squared we need categorical features
    # We accept datasets that have at least one of these
    if not has_numeric:
        print(f"Warning: Dataset {dataset_info['name']} has no numeric columns. Chi-squared only.")
    
    if not has_categorical:
        print(f"Warning: Dataset {dataset_info['name']} has no categorical columns. T-test/ANOVA only.")

    return True

def load_datasets(manifest_path: str, data_raw_dir: str, checksums_path: str) -> Dict[str, str]:
    """
    Main entry point to fetch, validate, and save datasets.
    
    Returns:
        Dictionary mapping dataset name to its SHA-256 checksum.
    """
    datasets = load_manifest(manifest_path)
    checksums = {}
    
    data_raw_path = Path(data_raw_dir)
    data_raw_path.mkdir(parents=True, exist_ok=True)
    
    for dataset_info in datasets:
        name = dataset_info['name']
        url = dataset_info['url']
        output_filename = f"{name}.csv"
        output_path = str(data_raw_path / output_filename)
        
        print(f"Fetching {name} from {url}...")
        if not fetch_dataset(url, output_path):
            print(f"Skipping {name} due to fetch failure.")
            continue
        
        # Load and validate
        try:
            df = pd.read_csv(output_path)
            
            # Handle potential header issues in UCI datasets
            # Some UCI datasets have no header or specific separators
            if df.shape[1] == 1 and ',' in df.iloc[0, 0]:
                # Try re-reading with comma separator
                df = pd.read_csv(output_path, sep=',')
            
            if not validate_dataset(df, dataset_info):
                # Remove invalid file
                os.remove(output_path)
                continue
            
            # Recalculate checksum after ensuring clean read
            checksum = calculate_checksum(output_path)
            checksums[name] = checksum
            print(f"Saved {name}: {len(df)} rows, {df.shape[1]} columns. Checksum: {checksum[:16]}...")
            
        except Exception as e:
            print(f"Error processing {name}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            continue
    
    # Save checksums
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Checksums saved to {checksums_path}")
    return checksums
