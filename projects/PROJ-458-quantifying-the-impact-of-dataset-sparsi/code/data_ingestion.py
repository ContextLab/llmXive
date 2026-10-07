import os
import time
import json
import csv
import hashlib
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dotenv import load_dotenv

# Import utilities from the project structure
from utils.logging import get_logger, log_result
from utils.cpu_constraints import enforce_memory_limit
from utils.checksum_utils import compute_sha256

# Initialize logger
logger = get_logger(__name__)

def load_env_config() -> Dict[str, Any]:
    """Load environment configuration."""
    load_dotenv()
    mp_api_key = os.getenv("MP_API_KEY")
    if not mp_api_key:
        raise RuntimeError("MP_API_KEY environment variable is missing. Cannot proceed.")
    
    return {
        "mp_api_key": mp_api_key,
        "raw_pool_path": os.getenv("RAW_POOL_PATH", "data/raw/raw_pool.csv"),
        "filtered_pool_path": os.getenv("FILTERED_POOL_PATH", "data/processed/filtered_pool.csv"),
        "test_indices_path": os.getenv("TEST_INDICES_PATH", "data/processed/test_set_indices.csv"),
        "descriptors_pool_path": os.getenv("DESCRIPTORS_POOL_PATH", "data/processed/descriptors_pool.csv"),
        "final_pool_path": os.getenv("FINAL_POOL_PATH", "data/processed/full_pool_final.csv"),
        "ingestion_log_path": os.getenv("INGESTION_LOG_PATH", "data/results/ingestion_log.json")
    }

def exponential_backoff(func, max_retries=5, base_delay=1.0):
    """Execute function with exponential backoff for rate limits."""
    delay = base_delay
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Rate limit hit. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    return None

def fetch_material_data(material_id: str, api_key: str) -> Optional[Dict]:
    """Fetch single material data from Materials Project API."""
    url = f"https://api.materialsproject.org/v2/materials/{material_id}"
    headers = {"X-API-Key": api_key}
    params = {"fields": "formula,prediction_analysis"}
    
    def _req():
        return requests.get(url, headers=headers, params=params, timeout=30)
    
    response = exponential_backoff(_req)
    if response and response.status_code == 200:
        return response.json().get("data", {})
    return None

def get_material_ids_from_pool(pool_path: str) -> List[str]:
    """Read material IDs from the raw pool CSV."""
    if not os.path.exists(pool_path):
        raise FileNotFoundError(f"Raw pool file not found: {pool_path}")
    
    df = pd.read_csv(pool_path)
    return df['material_id'].tolist()

def process_and_save(material_id: str, api_key: str, output_path: str):
    """Process a single material and append to output CSV."""
    data = fetch_material_data(material_id, api_key)
    if not data:
        return
    
    # Extract relevant fields
    formula = data.get("formula", "")
    prediction_analysis = data.get("prediction_analysis", {})
    dft_computed = prediction_analysis.get("dft_computed", False)
    formation_energy = prediction_analysis.get("formation_energy_per_atom", None)
    
    # Append to CSV
    file_exists = os.path.exists(output_path)
    with open(output_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['material_id', 'composition', 'formation_energy', 'dft_computed'])
        writer.writerow([material_id, formula, formation_energy, dft_computed])

def filter_pool(config: Dict[str, Any]) -> None:
    """
    Filter the raw pool to retain only rows where:
    1. formation_energy is not null
    2. dft_computed is True
    Saves to filtered_pool.csv.
    """
    input_path = config['raw_pool_path']
    output_path = config['filtered_pool_path']
    
    logger.info(f"Filtering pool from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file missing: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure formation_energy is numeric
    df['formation_energy'] = pd.to_numeric(df['formation_energy'], errors='coerce')
    
    # Filter
    mask = df['formation_energy'].notna() & (df['dft_computed'] == True)
    filtered_df = df[mask].reset_index(drop=True)
    
    logger.info(f"Filtered pool: {len(df)} -> {len(filtered_df)} rows")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered pool to {output_path}")

def generate_descriptors(config: Dict[str, Any]) -> None:
    """
    Generate descriptors using matminer ElementalPropertyFeatureExtractor.
    Reads filtered_pool.csv, excludes test set indices, outputs descriptors_pool.csv.
    """
    input_path = config['filtered_pool_path']
    test_indices_path = config['test_indices_path']
    output_path = config['descriptors_pool_path']
    
    logger.info(f"Generating descriptors from {input_path}")
    
    # Load training pool
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file missing: {input_path}")
    train_df = pd.read_csv(input_path)
    
    # Load test indices to exclude
    if not os.path.exists(test_indices_path):
        raise FileNotFoundError(f"Test indices file missing: {test_indices_path}. "
                              "Ensure T020 has completed successfully.")
    test_indices_df = pd.read_csv(test_indices_path)
    test_indices_set = set(test_indices_df['index'].tolist())
    
    # Exclude test indices from training pool
    # Assuming the original index is preserved or we need to re-index based on row position
    # Since we read from CSV, we assume the 'index' column in test_indices.csv refers to
    # the row number in the filtered_pool.csv (0-indexed)
    train_df['original_index'] = train_df.index
    training_df = train_df[~train_df['original_index'].isin(test_indices_set)].copy()
    
    logger.info(f"Excluded {len(test_indices_set)} test indices. Training size: {len(training_df)}")
    
    if len(training_df) == 0:
        raise ValueError("Training pool is empty after excluding test indices.")
    
    # Import matminer features
    try:
        from matminer.featurizers.composition import ElementalPropertyFeatureExtractor
    except ImportError:
        raise ImportError("matminer is required. Install via: pip install matminer==0.9.2")
    
    # Initialize feature extractor
    # Properties: atomic_number, electronegativity, atomic_radius
    extractor = ElementalPropertyFeatureExtractor(
        properties=['atomic_number', 'electronegativity', 'atomic_radius']
    )
    
    logger.info("Computing elemental property features...")
    # Featurize composition
    # matminer expects a column of strings for composition
    X = extractor.featurize_dataframe(training_df, col_id="composition", ignore_errors=True)
    
    # Combine with original data (keep material_id, composition, etc.)
    final_df = pd.concat([training_df[['material_id', 'composition', 'formation_energy', 'dft_computed']], X], axis=1)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")
    logger.info(f"Descriptor columns: {list(final_df.columns)}")

def perform_imputation(config: Dict[str, Any]) -> None:
    """
    Perform mean-fill imputation on numeric descriptors.
    - Excludes test set indices (already done in generate_descriptors, but we read the clean pool)
    - Drops rows with >50% missing values
    - Logs count to ingestion_log.json
    - Outputs full_pool_final.csv
    
    Note: This function assumes the input is the descriptors_pool.csv generated by generate_descriptors,
    which already excludes test indices.
    """
    input_path = config['descriptors_pool_path']
    output_path = config['final_pool_path']
    log_path = config['ingestion_log_path']
    
    logger.info(f"Performing imputation on {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input descriptors file missing: {input_path}. "
                              "Ensure generate_descriptors has completed successfully.")
    
    df = pd.read_csv(input_path)
    
    # Identify numeric columns for imputation
    # Exclude non-numeric columns like material_id, composition, etc.
    # We assume the last columns are the generated descriptors
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.columns.difference(numeric_cols)
    
    if not numeric_cols:
        logger.warning("No numeric columns found for imputation.")
        # If no numeric columns, just save as is
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return
    
    # Calculate mean for each numeric column
    means = df[numeric_cols].mean()
    
    # Count missing values per row
    missing_per_row = df[numeric_cols].isna().sum(axis=1)
    total_numeric_cols = len(numeric_cols)
    
    # Drop rows with >50% missing values
    rows_to_drop_mask = missing_per_row > (0.5 * total_numeric_cols)
    dropped_count = rows_to_drop_mask.sum()
    df_clean = df[~rows_to_drop_mask].copy()
    
    # Mean-fill remaining missing values
    df_clean[numeric_cols] = df_clean[numeric_cols].fillna(means)
    
    # Final check: ensure no NaNs remain in numeric cols
    remaining_nans = df_clean[numeric_cols].isna().sum().sum()
    if remaining_nans > 0:
        logger.warning(f"Still {remaining_nans} NaNs after imputation. Dropping these rows.")
        df_clean = df_clean.dropna(subset=numeric_cols)
    
    # Prepare log data
    log_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_rows": len(df),
        "dropped_rows": dropped_count,
        "final_rows": len(df_clean),
        "imputation_method": "mean_fill",
        "threshold_percent": 50,
        "numeric_columns_processed": numeric_cols,
        "remaining_nans_after_imputation": int(remaining_nans)
    }
    
    # Save final dataset
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved final training dataset to {output_path}")
    
    # Save log
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved imputation log to {log_path}")
    
    return log_data

def main():
    """Main entry point for data ingestion pipeline."""
    logger.info("Starting data ingestion pipeline...")
    
    config = load_env_config()
    
    # 1. Filter Pool (T025)
    try:
        filter_pool(config)
    except FileNotFoundError as e:
        logger.error(f"Filter pool failed: {e}")
        # Do not proceed if raw pool is missing
        raise
    
    # 2. Generate Descriptors (T026)
    try:
        generate_descriptors(config)
    except FileNotFoundError as e:
        logger.error(f"Generate descriptors failed: {e}")
        raise
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        raise
    
    # 3. Perform Imputation (T027)
    try:
        imputation_log = perform_imputation(config)
        logger.info(f"Imputation completed. Dropped {imputation_log['dropped_rows']} rows.")
    except FileNotFoundError as e:
        logger.error(f"Imputation failed: {e}")
        raise
    
    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()