import os
import json
import hashlib
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLE_SIZE = 30
RAM_LIMIT_GB = 6.0  # Conservative limit for GitHub Actions free tier

class RAMExceededError(Exception):
    """Raised when a dataset exceeds available memory limits."""
    pass

class LowNumericColumnsError(Exception):
    """Raised when a dataset has fewer than 5 numeric columns."""
    pass

class LowPowerError(Exception):
    """Raised when a dataset has fewer than MIN_SAMPLE_SIZE rows."""
    pass

def estimate_memory_usage(df: pd.DataFrame) -> float:
    """
    Estimate memory usage of a DataFrame in GB.
    """
    # pandas memory_usage returns bytes, convert to GB
    mem_bytes = df.memory_usage(deep=True).sum()
    return mem_bytes / (1024 ** 3)

def validate_numeric_columns(df: pd.DataFrame, min_cols: int = 5) -> Tuple[bool, List[str]]:
    """
    Validate that the DataFrame has at least `min_cols` numeric columns.
    Returns (is_valid, list_of_numeric_columns).
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < min_cols:
        return False, numeric_cols
    return True, numeric_cols

def fetch_dataset_from_hf(dataset_id: str, config_name: str = None, split: str = "train") -> pd.DataFrame:
    """
    Fetch a dataset from Hugging Face Hub.
    Returns a pandas DataFrame.
    """
    from datasets import load_dataset
    logger.info(f"Loading dataset from HF: {dataset_id}")
    try:
        ds = load_dataset(dataset_id, name=config_name, split=split, trust_remote_code=True)
        return ds.to_pandas()
    except Exception as e:
        logger.error(f"Failed to load HF dataset {dataset_id}: {e}")
        raise

def fetch_dataset_from_url(url: str) -> pd.DataFrame:
    """
    Fetch a dataset from a URL (CSV, JSON, etc.).
    Returns a pandas DataFrame.
    """
    logger.info(f"Fetching dataset from URL: {url}")
    try:
        if url.endswith('.csv'):
            return pd.read_csv(url)
        elif url.endswith('.json') or url.endswith('.jsonl'):
            return pd.read_json(url, lines=url.endswith('.jsonl'))
        else:
            # Try to infer format, fallback to csv
            return pd.read_csv(url)
    except Exception as e:
        logger.error(f"Failed to fetch dataset from {url}: {e}")
        raise

def check_sample_size(df: pd.DataFrame) -> None:
    """
    CRITICAL: Validate sample size per FR-006 and T005b.
    If n < 30, raise LowPowerError immediately.
    """
    n = len(df)
    logger.info(f"Dataset sample size check: n={n} (min required: {MIN_SAMPLE_SIZE})")
    if n < MIN_SAMPLE_SIZE:
        error_msg = f"Low Power Error: Dataset has {n} rows, which is less than the minimum required {MIN_SAMPLE_SIZE}. Pipeline halted per FR-006."
        logger.error(error_msg)
        # Log report details to stderr/console as per requirement
        print(f"REPORT: Sample size validation failed. n={n} < {MIN_SAMPLE_SIZE}.")
        raise LowPowerError(error_msg)

def process_and_validate(
    df: pd.DataFrame,
    dataset_name: str,
    skip_large: bool = True
) -> Optional[pd.DataFrame]:
    """
    Core processing pipeline:
    1. Check sample size (T005b) - HALTS if < 30
    2. Check memory usage
    3. Check numeric columns
    4. Return cleaned DataFrame
    """
    # T005b: Sample size validation - CRITICAL
    check_sample_size(df)

    # Check memory usage
    mem_gb = estimate_memory_usage(df)
    if mem_gb > RAM_LIMIT_GB:
        if skip_large:
            logger.warning(f"Dataset {dataset_name} exceeds RAM limit ({mem_gb:.2f} GB > {RAM_LIMIT_GB} GB). Skipping.")
            return None
        else:
            raise RAMExceededError(f"Dataset {dataset_name} exceeds RAM limit.")

    # Check numeric columns
    is_valid, numeric_cols = validate_numeric_columns(df)
    if not is_valid:
        raise LowNumericColumnsError(
            f"Dataset {dataset_name} has only {len(numeric_cols)} numeric columns "
            f"(minimum required: 5). Columns found: {numeric_cols}"
        )

    logger.info(f"Dataset {dataset_name} passed all validations. Rows: {len(df)}, "
                f"Numeric cols: {len(numeric_cols)}, Memory: {mem_gb:.2f} GB")
    return df

def load_all_datasets(
    registry_path: str,
    output_dir: str = "data/processed"
) -> List[Dict[str, Any]]:
    """
    Load and validate all datasets from the registry.
    Returns a list of results (success or error info).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []

    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)

    for entry in registry.get('datasets', []):
        name = entry.get('name')
        source_type = entry.get('source_type')
        source_id = entry.get('source_id')
        config_name = entry.get('config_name')
        
        logger.info(f"Processing dataset: {name}")
        try:
            if source_type == 'hf':
                df = fetch_dataset_from_hf(source_id, config_name=config_name)
            elif source_type == 'url':
                df = fetch_dataset_from_url(source_id)
            else:
                logger.error(f"Unknown source type for {name}: {source_type}")
                results.append({'name': name, 'status': 'error', 'message': 'Unknown source type'})
                continue

            processed_df = process_and_validate(df, name)
            
            if processed_df is not None:
                output_path = os.path.join(output_dir, f"{name}_processed.csv")
                processed_df.to_csv(output_path, index=False)
                results.append({
                    'name': name,
                    'status': 'success',
                    'rows': len(processed_df),
                    'output_path': output_path
                })
            else:
                results.append({'name': name, 'status': 'skipped', 'message': 'RAM limit exceeded'})

        except LowPowerError as e:
            # T005b: Halt pipeline immediately on low power
            logger.critical(f"Pipeline halted due to LowPowerError for {name}: {e}")
            raise  # Re-raise to stop execution immediately
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            results.append({'name': name, 'status': 'error', 'message': str(e)})

    return results

def main():
    """
    CLI entry point for data loading and validation.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Load and validate datasets")
    parser.add_argument('--registry', type=str, default='data/dataset_registry.yaml',
                        help='Path to dataset registry YAML')
    parser.add_argument('--output', type=str, default='data/processed',
                        help='Output directory for processed data')
    args = parser.parse_args()

    if not os.path.exists(args.registry):
        logger.error(f"Registry file not found: {args.registry}")
        return

    try:
        results = load_all_datasets(args.registry, args.output)
        print(json.dumps(results, indent=2))
    except LowPowerError as e:
        print(f"CRITICAL FAILURE: {e}")
        exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
