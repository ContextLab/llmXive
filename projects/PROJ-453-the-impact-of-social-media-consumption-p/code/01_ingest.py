"""
Dataset Ingestion Script (T015).

This script handles the download, validation, and cleaning of the primary dataset
for the project. It strictly adheres to the "Fail Loudly" principle regarding
data availability and schema compliance.

Dependencies:
- code/config.py
- code/logging_config.py
- code/utils.py
- contracts/dataset.schema.yaml
- results/feasibility_status.json
"""

import os
import sys
import logging
import json
import yaml
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_ROOT, RESULTS_ROOT, DATA_URL, ensure_directories
from logging_config import setup_logging, get_logger
from utils import checksum_file

logger = get_logger(__name__)

# Constants
RAW_DIR = Path(DATA_ROOT) / "raw"
PROCESSED_DIR = Path(DATA_ROOT) / "processed"
FEASIBILITY_FILE = Path(RESULTS_ROOT) / "feasibility_status.json"
SCHEMA_FILE = Path("contracts") / "dataset.schema.yaml"
SAMPLE_SIZE = 1000  # Rows to load for validation before full processing

def load_schema_contract() -> Dict[str, Any]:
    """Load the dataset schema contract."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema contract not found at {SCHEMA_FILE}")
    with open(SCHEMA_FILE, "r") as f:
        return yaml.safe_load(f)

def validate_schema_structure(data_df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate that the dataframe columns match the schema.
    Raises ValueError if mismatch.
    """
    required_columns = schema.get("required_columns", [])
    current_columns = list(data_df.columns)
    
    missing = [col for col in required_columns if col not in current_columns]
    if missing:
        raise ValueError(f"Data Gap: Downloaded data schema mismatch. Missing columns: {missing}")
    
    logger.info(f"Schema validation passed. Found {len(current_columns)} columns.")
    return True

def validate_data_types_and_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Validate data types and basic constraints (e.g., non-negative ages).
    """
    constraints = schema.get("constraints", {})
    
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
        
        if "min_value" in rules:
            if df[col].min() < rules["min_value"]:
                logger.warning(f"Constraint violation: {col} has values < {rules['min_value']}")
        
        if "non_null" in rules and rules["non_null"]:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Constraint violation: {col} has {null_count} null values")

def download_data(url: str, output_path: Path) -> None:
    """
    Download data from URL using requests.
    FAILS LOUDLY if the download fails. No synthetic fallback.
    """
    logger.info(f"Attempting to download data from: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded data to {output_path}")
        logger.info(f"File size: {output_path.stat().st_size} bytes")
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error during download: {e}")
        raise RuntimeError(f"Data fetch failed: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download: {e}")
        raise RuntimeError(f"Data fetch failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise RuntimeError(f"Data fetch failed: {e}") from e

def load_fallback_data() -> None:
    """
    This function is explicitly NOT implemented.
    Per project constraints, we must NOT fall back to synthetic data.
    If the real fetch fails, the script must crash.
    """
    raise RuntimeError("Synthetic fallback is forbidden. Real data fetch must succeed.")

def validate_and_save(raw_df: pd.DataFrame, schema: Dict[str, Any], dataset_id: str) -> pd.DataFrame:
    """
    Perform final validation and save raw and cleaned versions.
    """
    # 1. Validate Schema
    validate_schema_structure(raw_df, schema)
    
    # 2. Validate Data Types/Constraints
    validate_data_types_and_constraints(raw_df, schema)
    
    # 3. Check for specific required variables mentioned in T015 logic
    required_vars = ["self_reported_switching_frequency", "cognitive_flexibility_score"]
    missing_vars = [v for v in required_vars if v not in raw_df.columns]
    if missing_vars:
        raise ValueError(f"Data Gap: Dataset lacks required variables: {missing_vars}")
    
    # 4. Save Raw
    raw_path = RAW_DIR / f"{dataset_id}_raw.csv"
    raw_df.to_csv(raw_path, index=False)
    logger.info(f"Raw data saved to {raw_path}")
    
    # 5. Clean Data (Basic cleaning: drop rows with critical missing values)
    # We drop rows where the outcome or primary predictor is missing
    critical_cols = ["cognitive_flexibility_score", "self_reported_switching_frequency"]
    cleaned_df = raw_df.dropna(subset=critical_cols)
    
    logger.info(f"Dropped {len(raw_df) - len(cleaned_df)} rows due to missing critical values.")
    
    # 6. Save Cleaned
    cleaned_path = PROCESSED_DIR / f"{dataset_id}_cleaned.csv"
    cleaned_df.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned data saved to {cleaned_path}")
    
    return cleaned_df

def write_instrument_sources(dataset_id: str, url: str) -> None:
    """
    Update instrument sources file with the verified dataset info.
    """
    sources_file = Path("data") / "instrument_sources.yaml"
    sources_dir = sources_file.parent
    sources_dir.mkdir(parents=True, exist_ok=True)
    
    source_data = {
        "dataset_id": dataset_id,
        "url": url,
        "verified_date": pd.Timestamp.now().isoformat(),
        "variables_mapped": ["self_reported_switching_frequency", "cognitive_flexibility_score"]
    }
    
    if sources_file.exists():
        with open(sources_file, "r") as f:
            existing = yaml.safe_load(f) or {}
        existing[dataset_id] = source_data
    else:
        existing = {dataset_id: source_data}
        
    with open(sources_file, "w") as f:
        yaml.dump(existing, f, default_flow_style=False)
    logger.info(f"Updated instrument sources at {sources_file}")

def main():
    """Main execution flow for T015."""
    setup_logging()
    ensure_directories()
    
    logger.info("Starting Dataset Ingestion Pipeline (T015).")
    
    # 1. Pre-flight Check: Verify feasibility status
    if not FEASIBILITY_FILE.exists():
        raise FileNotFoundError(f"Feasibility check file not found: {FEASIBILITY_FILE}. Run T001 first.")
    
    with open(FEASIBILITY_FILE, "r") as f:
        feasibility = json.load(f)
    
    if feasibility.get("status") != "PASS":
        raise RuntimeError(f"Feasibility check failed: {feasibility.get('message')}. Cannot proceed with ingestion.")
    
    dataset_id = feasibility.get("dataset_id")
    if not dataset_id:
        raise RuntimeError("Feasibility check passed but no dataset_id found.")
    
    logger.info(f"Feasibility check passed for dataset: {dataset_id}")
    
    # 2. Load Schema Contract
    schema = load_schema_contract()
    
    # 3. Fetch Data
    # The URL should be pinned in config.py as per T015 requirements
    if not DATA_URL:
        raise RuntimeError("DATA_URL is not defined in config.py. Cannot proceed.")
    
    raw_path = RAW_DIR / f"{dataset_id}_raw.csv"
    
    try:
        download_data(DATA_URL, raw_path)
    except RuntimeError as e:
        logger.error("Data fetch failed. Halting pipeline.")
        raise e
    
    # 4. Load and Validate
    try:
        # Load a sample first to check schema quickly
        sample_df = pd.read_csv(raw_path, nrows=SAMPLE_SIZE)
        validate_schema_structure(sample_df, schema)
        
        # Load full data (or large chunk) for processing
        logger.info(f"Loading full dataset from {raw_path}...")
        raw_df = pd.read_csv(raw_path)
        
        # Full validation
        cleaned_df = validate_and_save(raw_df, schema, dataset_id)
        
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        raise e
    
    # 5. Update Instrument Sources
    write_instrument_sources(dataset_id, DATA_URL)
    
    logger.info("Dataset Ingestion Pipeline (T015) completed successfully.")
    return cleaned_df

if __name__ == "__main__":
    main()
