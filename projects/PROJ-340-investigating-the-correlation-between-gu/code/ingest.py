import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Generator
import hashlib
import io
import time

# Attempt to import datasets for streaming; if not present, we cannot fulfill the real-data streaming requirement
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

# ----------------------------------------------------------------------
# Custom Exceptions
# ----------------------------------------------------------------------
class MissingDataError(Exception):
    """Raised when required data is missing or fetch fails."""
    pass

class StreamingNotSupportedError(Exception):
    """Raised when streaming is requested but the dataset/package is not available."""
    pass

# ----------------------------------------------------------------------
# Schema & Validation Helpers
# ----------------------------------------------------------------------
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_variables(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Validate that the dataframe contains all required variables defined in the schema.
    Returns: (percentage_loaded, list_of_missing_variables)
    """
    required_predictors = schema.get('predictors', {}).get('required', [])
    required_outcomes = schema.get('outcomes', {}).get('required', [])
    all_required = required_predictors + required_outcomes

    available_cols = set(df.columns)
    missing = [var for var in all_required if var not in available_cols]
    total = len(all_required)
    percentage = (total - len(missing)) / total * 100 if total > 0 else 100.0

    return percentage, missing

def save_variable_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save variable load metrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

# ----------------------------------------------------------------------
# Streaming Logic (T058 Implementation)
# ----------------------------------------------------------------------
def load_streamed_dataset(
    dataset_id: str,
    split: str = 'train',
    streaming: bool = True,
    config_name: Optional[str] = None,
    columns: Optional[List[str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Load a dataset in streaming mode to avoid loading the entire dataset into RAM.
    Yields chunks of the dataset as DataFrames.
    
    Args:
        dataset_id: HuggingFace dataset ID (e.g., 'username/dataset_name')
        split: Dataset split to load (default: 'train')
        streaming: Must be True for this function.
        config_name: Optional dataset configuration name.
        columns: Optional list of columns to select.
    
    Yields:
        pd.DataFrame: A chunk of the dataset.
    
    Raises:
        StreamingNotSupportedError: If datasets library is not installed.
        MissingDataError: If the dataset fetch fails.
    """
    if not DATASETS_AVAILABLE:
        raise StreamingNotSupportedError(
            "The 'datasets' library is required for streaming. "
            "Install it via: pip install datasets"
        )

    if not streaming:
        raise ValueError("load_streamed_dataset requires streaming=True")

    try:
        # Load dataset in streaming mode
        ds = load_dataset(
            dataset_id,
            name=config_name,
            split=split,
            streaming=True,
            trust_remote_code=True
        )

        # Iterate over the streaming dataset
        # HuggingFace streaming returns a generator of dicts
        # We buffer a reasonable number of rows before yielding a DataFrame
        buffer = []
        buffer_size = 1000  # Yield every 1000 rows

        for item in ds:
            if columns:
                # Filter columns if requested
                row = {k: v for k, v in item.items() if k in columns}
            else:
                row = item
            
            buffer.append(row)
            
            if len(buffer) >= buffer_size:
                yield pd.DataFrame(buffer)
                buffer = []
        
        # Yield remaining items
        if buffer:
            yield pd.DataFrame(buffer)

    except Exception as e:
        # Fail loudly: do not fallback to synthetic
        raise MissingDataError(f"Failed to stream dataset '{dataset_id}': {str(e)}")

def compute_online_statistics(
    dataset_id: str,
    target_columns: List[str],
    split: str = 'train',
    config_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute online statistics (mean, variance, zero-proportion) for a streaming dataset
    without loading it entirely into memory.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        target_columns: List of column names to compute stats for.
        split: Dataset split.
        config_name: Dataset config name.
    
    Returns:
        Dictionary containing computed statistics.
    """
    stats_result = {col: {'count': 0, 'sum': 0.0, 'sum_sq': 0.0, 'zeros': 0, 'min': None, 'max': None} 
                    for col in target_columns}
    total_rows = 0
    
    try:
        stream_gen = load_streamed_dataset(
            dataset_id, 
            split=split, 
            streaming=True, 
            config_name=config_name,
            columns=target_columns
        )
        
        for chunk in stream_gen:
            total_rows += len(chunk)
            for col in target_columns:
                if col not in chunk.columns:
                    continue
                
                values = chunk[col].dropna()
                count = len(values)
                if count == 0:
                    continue
                
                s = values.sum()
                s_sq = (values ** 2).sum()
                zeros = (values == 0).sum()
                min_val = values.min()
                max_val = values.max()
                
                stats_result[col]['count'] += count
                stats_result[col]['sum'] += s
                stats_result[col]['sum_sq'] += s_sq
                stats_result[col]['zeros'] += zeros
                
                if stats_result[col]['min'] is None or min_val < stats_result[col]['min']:
                    stats_result[col]['min'] = min_val
                if stats_result[col]['max'] is None or max_val > stats_result[col]['max']:
                    stats_result[col]['max'] = max_val
                    
    except MissingDataError as e:
        # Re-raise to ensure loud failure
        raise e
    except Exception as e:
        raise MissingDataError(f"Error during online statistics computation: {str(e)}")
    
    # Finalize statistics
    final_stats = {}
    for col in target_columns:
        count = stats_result[col]['count']
        if count > 0:
            mean = stats_result[col]['sum'] / count
            variance = (stats_result[col]['sum_sq'] / count) - (mean ** 2)
            zero_prop = stats_result[col]['zeros'] / count
            final_stats[col] = {
                'mean': mean,
                'variance': variance,
                'zero_proportion': zero_prop,
                'min': stats_result[col]['min'],
                'max': stats_result[col]['max'],
                'count': count
            }
        else:
            final_stats[col] = {'status': 'no_data'}
    
    return {
        'total_rows_processed': total_rows,
        'column_statistics': final_stats
    }

# ----------------------------------------------------------------------
# Existing Ingestion Functions (Preserved for compatibility)
# ----------------------------------------------------------------------
def load_data(data_path: str) -> pd.DataFrame:
    """
    Load data from a local file (CSV/TSV/Parquet).
    This is the standard loader for local files.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    suffix = path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix == '.tsv':
        return pd.read_csv(path, sep='\t')
    elif suffix == '.parquet':
        return pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Detect outliers using the IQR method.
    Returns a boolean mask indicating outliers.
    """
    mask = pd.Series([False] * len(df))
    for col in columns:
        if col not in df.columns:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        col_mask = (df[col] < lower) | (df[col] > upper)
        mask |= col_mask
    return mask

def filter_outliers(df: pd.DataFrame, outlier_mask: pd.Series) -> pd.DataFrame:
    """Remove rows flagged as outliers."""
    return df[~outlier_mask].reset_index(drop=True)

def calculate_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def register_checksum_in_state(checksum: str, file_path: str, state_file: str) -> None:
    """Register a checksum in the project state file."""
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = json.load(f)
    
    state_data[file_path] = checksum
    
    with open(state_path, 'w') as f:
        json.dump(state_data, f, indent=2)

def fetch_verified_real_dataset(dataset_id: str, output_path: str) -> None:
    """
    Fetch a verified real dataset.
    This function assumes the dataset_id is verified and available.
    For large datasets, it should ideally use streaming, but for now
    it attempts a direct download if streaming is not explicitly requested.
    """
    if not DATASETS_AVAILABLE:
        raise StreamingNotSupportedError("datasets library required")
    
    try:
        # Attempt to download the dataset
        # Note: This is a simplified fetch. In a real scenario, we might need to handle
        # specific file formats or splits.
        ds = load_dataset(dataset_id, streaming=False) # Download full to disk/cache
        # For this task, we assume the dataset has a 'train' split and we want to save it as CSV
        if 'train' in ds:
            df = ds['train'].to_pandas()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
        else:
            raise MissingDataError(f"No 'train' split found in dataset {dataset_id}")
    except Exception as e:
        raise MissingDataError(f"Failed to fetch verified real dataset {dataset_id}: {str(e)}")

def validate_loaded_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate loaded data against schema."""
    percentage, missing = validate_variables(df, schema)
    return percentage == 100.0

def main():
    """
    Main entry point for ingestion module.
    Demonstrates streaming usage if called directly.
    """
    if len(sys.argv) < 2:
        print("Usage: python code/ingest.py <dataset_id> [output_path]")
        return

    dataset_id = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/processed/streamed_stats.json"

    # Define columns of interest (example: taxa and sleep metrics)
    # In a real scenario, these would come from the schema
    target_cols = ['Bacteroides', 'Firmicutes', 'SWS duration', 'REM duration']
    
    print(f"Starting streaming analysis for dataset: {dataset_id}")
    print(f"Target columns: {target_cols}")
    
    try:
        stats = compute_online_statistics(dataset_id, target_cols)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Streaming analysis complete. Results saved to {output_path}")
        print(f"Total rows processed: {stats['total_rows_processed']}")
        
    except MissingDataError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()