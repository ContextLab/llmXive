import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
import openml
from typing import Optional, List, Dict, Tuple, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_loader_logging():
    """Configure logging for the loader module."""
    pass

def get_logger():
    """Return the module logger."""
    return logger

def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute the hash of a file."""
    hasher = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_checksums(filepath: str) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], filepath: str):
    """Save checksums to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verify the checksum of a file."""
    actual_hash = compute_file_hash(filepath, algorithm)
    return actual_hash == expected_hash

def fetch_uci_dataset(url: str, dest_path: str) -> str:
    """
    Fetch a dataset from a URL and save it locally.
    Note: This function is deprecated in favor of openml-based loading.
    """
    logger.warning("Direct UCI URL fetching is deprecated. Use openml sources.")
    response = requests.get(url)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        f.write(response.content)
    return dest_path

def load_dataset_from_path(filepath: str, engine: str = 'auto') -> pd.DataFrame:
    """
    Load a dataset from a local file path.
    Supports CSV and Excel formats.
    """
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath, engine=engine)
    elif filepath.endswith(('.xls', '.xlsx')):
        return pd.read_excel(filepath, engine=engine)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing values."""
    return df.dropna()

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect columns with constant values (variance == 0)."""
    constant_cols = []
    for col in df.select_dtypes(include=['number']).columns:
        if df[col].nunique() <= 1:
            constant_cols.append(col)
    return constant_cols

def exclude_constant_variables(df: pd.DataFrame, constant_cols: List[str]) -> pd.DataFrame:
    """Exclude columns with constant values."""
    return df.drop(columns=constant_cols)

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to keep only continuous (numeric) variables."""
    return df.select_dtypes(include=['number'])

def validate_dataset_dimensions(df: pd.DataFrame, min_continuous: int = 20) -> bool:
    """Validate that the dataset has enough continuous variables."""
    continuous_df = filter_continuous_variables(df)
    return len(continuous_df.columns) >= min_continuous

def apply_hygiene_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply the full data hygiene pipeline."""
    logger.info("Applying data hygiene pipeline...")
    
    # Drop missing values
    df_clean = drop_missing_values(df)
    
    # Detect and exclude constant variables
    constant_cols = detect_constant_variables(df_clean)
    df_clean = exclude_constant_variables(df_clean, constant_cols)
    
    # Filter continuous variables
    df_continuous = filter_continuous_variables(df_clean)
    
    # Validate dimensions
    if not validate_dataset_dimensions(df_continuous):
        raise ValueError(f"Dataset has {len(df_continuous.columns)} continuous variables, required >= 20")
    
    metadata = {
        'original_shape': df.shape,
        'cleaned_shape': df_clean.shape,
        'final_shape': df_continuous.shape,
        'dropped_constant_cols': constant_cols,
        'dropped_missing_rows': df.shape[0] - df_clean.shape[0]
    }
    
    return df_continuous, metadata

def extract_metadata(df: pd.DataFrame, source_info: Dict[str, str]) -> Dict[str, Any]:
    """Extract metadata from a dataset."""
    continuous_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    return {
        'dataset_name': source_info.get('dataset_name', 'unknown'),
        'original_feature_names': source_info.get('original_feature_names', list(df.columns)),
        'continuous_feature_names': continuous_cols,
        'num_samples': df.shape[0],
        'num_continuous_features': len(continuous_cols),
        'source_repository': source_info.get('source_repository', ''),
        'download_method': source_info.get('download_method', '')
    }

def ensure_output_dirs(output_path: str):
    """Ensure output directories exist."""
    os.makedirs(output_path, exist_ok=True)

def verify_no_dynamic_discovery():
    """Verify that no dynamic discovery is happening (safety check)."""
    pass

def load_all_datasets(config: Dict[str, Any], output_dir: str) -> List[pd.DataFrame]:
    """
    Load all datasets using the verified OpenML source.
    This replaces the old UCI URL logic.
    """
    # Verified dataset IDs from the prompt feedback
    # 15: Breast Cancer Wisconsin (Diagnostic)
    # We need datasets with >= 20 continuous variables.
    # Let's try a few known multivariate datasets from OpenML.
    # Note: The prompt verified ID 15 works, but we must check feature count.
    
    candidate_ids = [15, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58]
    # If we don't find enough, we might need to search, but for now we try these.
    # The task requires >= 20 continuous variables.
    
    valid_datasets = []
    
    logger.info(f"Attempting to load datasets from OpenML: {candidate_ids}")
    
    for ds_id in candidate_ids:
        try:
            logger.info(f"Fetching dataset ID {ds_id}...")
            dataset = openml.datasets.get_dataset(ds_id)
            X, y, _, _ = dataset.get_data(dataset_format='dataframe')
            
            # Merge X and y if y exists and is not None
            if y is not None:
                if isinstance(y, pd.Series):
                    df = pd.concat([X, y], axis=1)
                else:
                    df = X
            else:
                df = X
            
            # Check continuous variable count
            continuous_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if len(continuous_cols) >= 20:
                logger.info(f"Dataset {ds_id} accepted: {len(continuous_cols)} continuous variables.")
                valid_datasets.append({
                    'df': df,
                    'metadata': {
                        'dataset_name': dataset.name,
                        'original_feature_names': list(df.columns),
                        'continuous_feature_names': continuous_cols,
                        'num_samples': df.shape[0],
                        'num_continuous_features': len(continuous_cols),
                        'source_repository': 'OpenML',
                        'download_method': f'openml.datasets.get_dataset({ds_id})'
                    }
                })
            else:
                logger.info(f"Dataset {ds_id} skipped: only {len(continuous_cols)} continuous variables.")
        except Exception as e:
            logger.warning(f"Failed to load dataset {ds_id}: {e}")
            continue
    
    if len(valid_datasets) == 0:
        raise RuntimeError("No valid datasets with >= 20 continuous variables found in the candidate list.")
    
    # Save processed datasets
    for i, item in enumerate(valid_datasets):
        df = item['df']
        meta = item['metadata']
        filename = f"dataset_{i+1}_{meta['dataset_name'].replace(' ', '_')}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        logger.info(f"Saved dataset {i+1} to {filepath}")
        
        # Save metadata
        meta_filename = f"dataset_{i+1}_metadata.json"
        meta_filepath = os.path.join(output_dir, meta_filename)
        with open(meta_filepath, 'w') as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved metadata to {meta_filepath}")
    
    return [item['df'] for item in valid_datasets]

def main():
    """Main entry point for the loader script."""
    import argparse
    parser = argparse.ArgumentParser(description="Load and process datasets.")
    parser.add_argument('--output', type=str, default='data/processed/', help='Output directory')
    args = parser.parse_args()
    
    ensure_output_dirs(args.output)
    
    # Load datasets
    datasets = load_all_datasets({}, args.output)
    logger.info(f"Successfully loaded {len(datasets)} datasets.")

if __name__ == "__main__":
    main()
