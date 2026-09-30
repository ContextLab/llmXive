import os
import sys
import logging
import time
import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging for the download module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_oqmd_dataset(output_path: str, retry_attempts: int = 3) -> str:
    """
    Download the OQMD dataset from HuggingFace.
    Implements retry logic with exponential backoff.
    Materializes the dataset to parquet.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via pip.")
        raise

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while attempt < retry_attempts:
        try:
            logger.info(f"Loading OQMD dataset (attempt {attempt + 1}/{retry_attempts})...")
            # Load the dataset
            dataset = load_dataset("materials-toolkits/oqmd", split="train", streaming=False)
            
            # Materialize to parquet
            logger.info(f"Materializing dataset to {output_path}...")
            dataset.to_parquet(str(output_path))
            
            logger.info("Dataset download and materialization successful.")
            return str(output_path)
        
        except Exception as e:
            attempt += 1
            if attempt == retry_attempts:
                logger.error(f"Failed to download dataset after {retry_attempts} attempts: {e}")
                raise
            else:
                wait_time = 2 ** attempt
                logger.warning(f"Download failed: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    raise RuntimeError("Failed to download dataset after all retries.")

def validate_structural_descriptors(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Check for the presence of structural descriptors (radius, packing_fraction).
    Returns (has_structural, list_of_missing_columns).
    """
    structural_candidates = ['radius', 'packing_fraction', 'atomic_radius_mean', 'packing_fraction']
    present_cols = set(df.columns)
    missing_cols = []
    found_structural = False

    for col in structural_candidates:
        if col in present_cols:
            found_structural = True
        else:
            missing_cols.append(col)

    return found_structural, missing_cols

def update_config_structural_flag(config_path: str, structural_available: bool) -> None:
    """
    Update the config.yaml to set structural_features_available flag.
    """
    import yaml
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Skipping update.")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['structural_features_available'] = structural_available

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    logger.info(f"Updated config: structural_features_available={structural_available}")

def extract_structural_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract radius and packing_fraction if present.
    If not present, returns the dataframe unchanged (handled by fallback logic upstream).
    """
    structural_cols = ['radius', 'packing_fraction']
    available_cols = [c for c in structural_cols if c in df.columns]
    
    if not available_cols:
        logger.info("No structural features found to extract.")
        return df

    logger.info(f"Extracting structural features: {available_cols}")
    
    # Ensure they are float64
    for col in available_cols:
        df[col] = df[col].astype('float64')
    
    return df

def update_validation_report(output_path: str, structural_count: int, missing_columns: List[str], extracted: bool) -> None:
    """
    Update data/validation_report.json with counts of rows where structural descriptors
    were extracted and a list of missing columns if any.
    
    Args:
        output_path: Path to the validation_report.json file.
        structural_count: Number of rows with structural descriptors extracted.
        missing_columns: List of structural columns that were missing.
        extracted: Boolean indicating if extraction was attempted/completed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "structural_descriptors_extracted": {
            "count": structural_count,
            "extracted": extracted
        },
        "missing_columns": missing_columns,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report updated at {output_path}")

def main():
    """
    Main orchestration function for T005d: Validation Update.
    
    This function assumes T005a (download), T005b (validation), and T005c (extraction)
    have already run and produced the necessary artifacts (oqmd.parquet, validation_report.json).
    
    It reads the parquet file, checks the status of structural features,
    and updates the validation_report.json with the required counts.
    """
    # Define paths
    data_dir = Path("data/raw")
    parquet_path = data_dir / "oqmd.parquet"
    validation_report_path = Path("data/validation_report.json")
    
    if not parquet_path.exists():
        logger.error(f"Data file not found: {parquet_path}. Run T005a first.")
        sys.exit(1)

    logger.info(f"Loading dataset from {parquet_path} for validation update...")
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)

    # Validate structural descriptors again to ensure consistency
    has_structural, missing_cols = validate_structural_descriptors(df)
    
    # Determine count of rows with structural data
    structural_count = 0
    extracted = False
    
    if has_structural:
        # Check for specific columns defined in T005c
        target_cols = ['radius', 'packing_fraction']
        available = [c for c in target_cols if c in df.columns]
        
        if available:
            # Count non-null rows for these columns
            structural_count = df[available].notna().all(axis=1).sum()
            extracted = True
            logger.info(f"Structural features extracted for {structural_count} rows.")
        else:
            structural_count = 0
            extracted = False
            logger.warning("Structural features present but required columns (radius, packing_fraction) not found.")
    else:
        structural_count = 0
        extracted = False
        logger.info("No structural features available.")

    # Update the validation report
    update_validation_report(
        str(validation_report_path),
        structural_count=structural_count,
        missing_columns=missing_cols,
        extracted=extracted
    )

    # Update config flag if structural features were NOT available (T005b requirement)
    if not has_structural:
        config_path = Path("code/config.yaml")
        if config_path.exists():
            update_config_structural_flag(str(config_path), False)
        else:
            logger.warning("config.yaml not found, skipping structural flag update.")

    logger.info("T005d Validation Update completed successfully.")

if __name__ == "__main__":
    main()