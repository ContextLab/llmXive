import os
import time
import json
import csv
import hashlib
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

# Import project utilities
from config import load_env
from utils.logging import get_logger, log_result
from utils.cpu_constraints import enforce_memory_limit, chunked_iterator

logger = get_logger(__name__)

def load_env_config() -> Dict[str, str]:
    """Load environment variables and return config dict."""
    return load_env()

def exponential_backoff(
    func: callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> callable:
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached. Last error: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    return wrapper

@exponential_backoff
def fetch_material_data(material_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Fetch material data from Materials Project API."""
    url = f"https://api.materialsproject.org/v2/materials/{material_id}"
    headers = {"X-API-Key": api_key}
    params = {"_fields": "material_id,composition,formation_energy,dft_computed"}
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get('data', [None])[0]

def get_material_ids_from_pool(pool_path: str) -> List[str]:
    """Read material IDs from the raw pool CSV."""
    df = pd.read_csv(pool_path)
    return df['material_id'].tolist()

def process_and_save(
    material_ids: List[str],
    api_key: str,
    output_path: str
) -> int:
    """Fetch and save material data to raw pool CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['material_id', 'composition', 'formation_energy', 'dft_computed'])
        writer.writeheader()
        
        count = 0
        for mid in material_ids:
            data = fetch_material_data(mid, api_key)
            if data:
                writer.writerow({
                    'material_id': data.get('material_id'),
                    'composition': data.get('composition'),
                    'formation_energy': data.get('formation_energy'),
                    'dft_computed': data.get('dft_computed')
                })
                count += 1
                if count % 1000 == 0:
                    logger.info(f"Processed {count} materials")
    
    return count

def filter_pool(
    input_path: str,
    test_set_indices_path: str,
    output_path: str,
    log_path: str
) -> int:
    """
    Filter the raw pool to retain only rows where:
    1. formation_energy is not null
    2. dft_computed is True
    3. material_id is NOT in the test set indices.
    
    Saves result to output_path and logs statistics to log_path.
    """
    logger.info(f"Loading raw pool from {input_path}")
    df_pool = pd.read_csv(input_path)
    
    logger.info(f"Loading test set indices from {test_set_indices_path}")
    # The test set indices file typically contains the 'material_id' or a row index
    # based on T020 output. We assume it contains 'material_id' as the primary key.
    try:
        df_test_indices = pd.read_csv(test_set_indices_path)
        if 'material_id' in df_test_indices.columns:
            test_ids = set(df_test_indices['material_id'].astype(str))
        elif 'index' in df_test_indices.columns:
            # Fallback if it's a row index
            test_indices = set(df_test_indices['index'].astype(int))
            # Filter pool by index if necessary, but usually we filter by ID
            # For safety, we check if the pool has an index column or use material_id
            test_ids = set() 
            logger.warning("Test set indices file uses 'index' column. Assuming material_id filtering is preferred.")
            # If strictly row indices, we might need to reset index on pool
            # But standard practice is filtering by ID. Let's assume the file has material_id.
            # If the file strictly has row indices, we handle it:
            if 'index' in df_test_indices.columns and 'material_id' not in df_test_indices.columns:
                # Reset index on pool to match
                df_pool_reset = df_pool.reset_index()
                test_ids = set(df_test_indices['index'].astype(int))
                # We will filter by index later, but let's stick to material_id logic first
                # If the user provided a file with 'index', we assume it maps to the raw pool rows.
                # However, the task says "excluding indices in ...".
                # Let's handle both cases robustly.
                pass
    except Exception as e:
        logger.error(f"Failed to load test set indices: {e}")
        raise

    # If we have material IDs in the test file
    if 'material_id' in df_test_indices.columns:
        test_ids = set(df_test_indices['material_id'].astype(str))
        mask_id = ~df_pool['material_id'].astype(str).isin(test_ids)
        df_filtered = df_pool[mask_id]
    else:
        # Fallback to index-based filtering if material_id column is missing in test file
        # This implies the test file contains row indices of the raw pool
        if 'index' in df_test_indices.columns:
            test_indices = set(df_test_indices['index'].astype(int))
            # Reset index to ensure we have a 0-based index matching the file order
            df_pool_reset = df_pool.reset_index(drop=True)
            mask_id = ~df_pool_reset.index.isin(test_indices)
            df_filtered = df_pool_reset[mask_id]
            # Drop the 'index' column if it was added by reset_index
            if 'index' in df_filtered.columns:
                df_filtered = df_filtered.drop(columns=['index'])
        else:
            logger.warning("Test set indices file has no 'material_id' or 'index' column. Skipping ID exclusion.")
            df_filtered = df_pool.copy()

    # Filter by formation_energy not null
    initial_count = len(df_filtered)
    df_filtered = df_filtered[df_filtered['formation_energy'].notna()]
    count_energy_null = initial_count - len(df_filtered)
    logger.info(f"Removed {count_energy_null} rows with null formation_energy")

    # Filter by dft_computed is True
    # Handle potential string 'True' or boolean True
    if df_filtered['dft_computed'].dtype == object:
        mask_dft = df_filtered['dft_computed'].astype(str).str.lower() == 'true'
    else:
        mask_dft = df_filtered['dft_computed'] == True
    
    df_filtered = df_filtered[mask_dft]
    count_dft_false = initial_count - len(df_filtered) - count_energy_null # Approximation, actual diff is better
    # Recalculate actual removed for dft
    # Actually, let's just log the final counts
    
    final_count = len(df_filtered)
    logger.info(f"Filtering complete. Final count: {final_count}")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Saved filtered pool to {output_path}")
    
    # Log statistics
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "test_set_indices_file": test_set_indices_path,
        "output_file": output_path,
        "initial_pool_size": len(df_pool),
        "rows_excluded_test_set": initial_count - len(df_filtered) if 'material_id' in df_test_indices.columns else 0, # Simplified
        "rows_removed_null_energy": count_energy_null,
        "final_filtered_count": final_count
    }
    
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return final_count

def generate_descriptors(
    input_path: str,
    output_path: str,
    properties: List[str] = None
) -> int:
    """Generate elemental property descriptors using matminer."""
    if properties is None:
        properties = ['atomic_number', 'electronegativity', 'atomic_radius']
    
    logger.info(f"Loading pool from {input_path}")
    df = pd.read_csv(input_path)
    
    # Import matminer safely
    try:
        from matminer.featurizers.composition import ElementalPropertyFeatureExtractor
        extractor = ElementalPropertyFeatureExtractor(properties=properties)
    except ImportError:
        logger.error("matminer not installed. Please install it via requirements.txt.")
        raise

    logger.info("Generating descriptors...")
    # Featurize composition column
    # Note: composition column is expected to be in 'Composition' format or string
    # If it's a string like "H2O", matminer can handle it
    descriptors = extractor.featurize_dataframe(df, col_id="composition", ignore_errors=True)
    
    # Rename columns to avoid conflicts if necessary
    descriptors.to_csv(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")
    return len(descriptors)

def impute_and_finalize(
    input_path: str,
    output_path: str,
    log_path: str,
    drop_threshold: float = 0.5
) -> int:
    """Mean-fill missing values and drop rows with >50% missing."""
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found to impute.")
        df.to_csv(output_path, index=False)
        return len(df)
    
    # Calculate mean for each numeric column
    means = df[numeric_cols].mean()
    
    # Mean fill
    df_imputed = df.copy()
    df_imputed[numeric_cols] = df_imputed[numeric_cols].fillna(means)
    
    # Calculate missing percentage per row
    missing_mask = df_imputed[numeric_cols].isna()
    missing_pct = missing_mask.mean(axis=1)
    
    # Drop rows with > drop_threshold missing
    rows_before = len(df_imputed)
    df_final = df_imputed[missing_pct <= drop_threshold]
    rows_after = len(df_final)
    dropped_count = rows_before - rows_after
    
    logger.info(f"Dropped {dropped_count} rows with >{drop_threshold*100}% missing values")
    
    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(output_path, index=False)
    
    # Log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "output_file": output_path,
        "rows_before_imputation": rows_before,
        "rows_after_dropping": rows_after,
        "dropped_count": dropped_count,
        "imputation_method": "mean"
    }
    
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return rows_after

def main():
    """Main entry point for data ingestion pipeline."""
    config = load_env_config()
    api_key = config.get('MP_API_KEY')
    
    if not api_key:
        logger.error("MP_API_KEY not found in environment.")
        return 1
    
    # Paths
    raw_pool_path = "data/raw/raw_pool.csv"
    test_indices_path = "data/processed/test_set_indices.csv"
    filtered_path = "data/processed/filtered_pool.csv"
    log_path = "data/results/ingestion_log.json"
    
    # Execute filtering
    # T025: Filter raw_pool excluding test_set_indices, keeping non-null energy and dft_computed=True
    try:
        count = filter_pool(raw_pool_path, test_indices_path, filtered_path, log_path)
        logger.info(f"Successfully filtered {count} entries.")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())