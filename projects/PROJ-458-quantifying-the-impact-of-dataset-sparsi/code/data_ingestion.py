import os
import time
import json
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from matminer.featurizers.composition import ElementalPropertyFeatureExtractor
from matminer.featurizers.base import MultipleFeaturizer
from sklearn.impute import SimpleImputer
from config import load_env
from utils.logging import get_logger
from utils.cpu_constraints import enforce_memory_limit

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
INGESTION_LOG_PATH = RESULTS_DIR / "ingestion_log.json"

logger = get_logger(__name__)

def load_env_config():
    """Load environment variables."""
    load_env()
    if not os.getenv("MP_API_KEY"):
        raise ValueError("MP_API_KEY not found in environment")

def exponential_backoff(func, max_retries=5, base_delay=1):
    """Execute function with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Failed after {max_retries} attempts")

def fetch_material_data():
    """
    Fetch material data from Materials Project API.
    NOTE: In a real execution, this would use the MP API.
    For this implementation, we assume T024 successfully populated data/raw/raw_pool.csv.
    This function validates the existence of that file.
    """
    raw_path = RAW_DIR / "raw_pool.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_path}. Ensure T024 has run.")
    logger.info(f"Loading raw data from {raw_path}")
    return pd.read_csv(raw_path)

def process_and_save(df: pd.DataFrame):
    """Basic processing (placeholder if needed, but T024 handles this)."""
    pass

def filter_pool(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the pool to retain only rows where:
    - formation_energy is not null
    - dft_computed is True
    """
    logger.info("Filtering pool: keeping non-null formation_energy and dft_computed=True")
    mask = df["formation_energy"].notna() & (df["dft_computed"] == True)
    filtered = df[mask].copy()
    logger.info(f"Filtered from {len(df)} to {len(filtered)} rows")
    return filtered

def generate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate descriptors using matminer ElementalPropertyFeatureExtractor.
    Properties: atomic_number, electronegativity, atomic_radius.
    """
    logger.info("Generating descriptors using matminer...")
    
    # Ensure we have composition column
    if "composition" not in df.columns:
        raise ValueError("Input DataFrame must have 'composition' column")

    # Setup featurizer
    featurizer = ElementalPropertyFeatureExtractor(
        props=["atomic_number", "electronegativity", "atomic_radius"]
    )
    
    # Apply featurizer
    # Note: This can be memory intensive. In production, use chunked_iterator.
    try:
        descriptors = featurizer.featurize_dataframe(df, col_id="composition", ignore_errors=True)
    except Exception as e:
        logger.error(f"Featurization failed: {e}")
        raise

    # Combine with original data
    # Select only the new descriptor columns (exclude any that might overlap if any)
    # matminer usually prefixes or creates new columns. We assume standard behavior.
    # We join on index.
    df_with_desc = pd.concat([df.reset_index(drop=True), descriptors.reset_index(drop=True)], axis=1)
    
    logger.info(f"Generated {len(df_with_desc.columns) - len(df.columns)} new descriptor columns")
    return df_with_desc

def impute_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement imputation logic:
    1. Mean-fill missing numeric descriptors.
    2. Drop rows with >50% missing values.
    3. Log count to data/results/ingestion_log.json.
    4. Output final dataset to data/processed/full_pool_final.csv.
    """
    logger.info("Starting imputation and finalization...")
    
    # Ensure output directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Identify numeric columns (excluding ID/Composition if present)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found for imputation.")
        final_df = df
    else:
        # Calculate missing percentage per row
        missing_mask = df[numeric_cols].isna()
        missing_counts = missing_mask.sum(axis=1)
        total_numeric = len(numeric_cols)
        missing_percent = (missing_counts / total_numeric) * 100

        # Drop rows with >50% missing values
        rows_to_drop = missing_percent > 50
        dropped_count = rows_to_drop.sum()
        df_dropped = df.dropna(subset=numeric_cols, thresh=int(total_numeric * 0.5))
        
        # Re-calculate missing mask for the remaining dataframe
        # Actually, SimpleImputer handles NaNs, but we need to drop rows with >50% first.
        # The logic above drops rows where >50% of NUMERIC columns are missing.
        
        logger.info(f"Dropped {dropped_count} rows due to >50% missing values.")

        # Mean imputation on remaining rows
        if not df_dropped.empty:
            imputer = SimpleImputer(strategy="mean")
            df_dropped[numeric_cols] = imputer.fit_transform(df_dropped[numeric_cols])
            final_df = df_dropped
        else:
            final_df = df_dropped

    # Save final dataset
    output_path = PROCESSED_DIR / "full_pool_final.csv"
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved final dataset to {output_path} ({len(final_df)} rows)")

    # Log to ingestion_log.json
    log_entry = {
        "task": "T027_imputation",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_rows": len(df),
        "dropped_rows": dropped_count,
        "final_rows": len(final_df),
        "imputation_strategy": "mean",
        "threshold_percent": 50,
        "output_file": str(output_path)
    }

    # Append or create log
    if INGESTION_LOG_PATH.exists():
        with open(INGESTION_LOG_PATH, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
        if not isinstance(logs, list):
            logs = [logs]
    else:
        logs = []
    
    logs.append(log_entry)

    with open(INGESTION_LOG_PATH, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"Logged imputation stats to {INGESTION_LOG_PATH}")

    return final_df

def main():
    """Main execution flow for T027."""
    logger.info("Starting T027: Imputation and Finalization")
    
    # Load config
    load_env_config()
    
    # Enforce memory limit if configured
    # enforce_memory_limit() # Optional, depends on system config

    # 1. Load raw data (Assuming T024 ran)
    df_raw = fetch_material_data()

    # 2. Filter (Assuming T025 ran, but we chain for robustness)
    # If T025 ran, data/processed/filtered_pool.csv exists.
    # We should ideally load from there if it exists, otherwise filter raw.
    filtered_path = PROCESSED_DIR / "filtered_pool.csv"
    if filtered_path.exists():
        logger.info("Loading filtered pool from disk (T025 output)")
        df_filtered = pd.read_csv(filtered_path)
    else:
        logger.warning("filtered_pool.csv not found. Filtering raw data on the fly.")
        df_filtered = filter_pool(df_raw)

    # 3. Generate descriptors (Assuming T026 ran)
    descriptors_path = PROCESSED_DIR / "descriptors_pool.csv"
    if descriptors_path.exists():
        logger.info("Loading descriptors from disk (T026 output)")
        df_descriptors = pd.read_csv(descriptors_path)
    else:
        logger.warning("descriptors_pool.csv not found. Generating on the fly.")
        df_descriptors = generate_descriptors(df_filtered)

    # 4. Impute and Finalize
    df_final = impute_and_finalize(df_descriptors)
    
    logger.info("T027 completed successfully.")
    return df_final

if __name__ == "__main__":
    main()