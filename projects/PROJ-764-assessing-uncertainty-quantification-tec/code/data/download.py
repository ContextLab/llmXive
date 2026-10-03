import os
import sys
import logging
import time
import json
import hashlib
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure code root is in path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Setup logging
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

def download_oqmd_dataset(output_path: str = "data/raw/oqmd.parquet") -> None:
    """
    Download the OQMD dataset from the verified HuggingFace source.
    Uses the 'jablonkagroup/oqmd' dataset with 'raw_data' config.
    """
    try:
        from datasets import load_dataset, concatenate_datasets
    except ImportError:
        raise ImportError("The 'datasets' library is required. Install it with 'pip install datasets'.")

    logger.info("Starting download of OQMD dataset from HuggingFace...")
    
    retry_count = 0
    max_retries = 3
    backoff_factor = 2.0

    while retry_count < max_retries:
        try:
            # Verified source recipe
            ds_dict = load_dataset("jablonkagroup/oqmd", "raw_data")
            
            # Combine all splits into a single Dataset
            if isinstance(ds_dict, dict):
                ds = concatenate_datasets(list(ds_dict.values()))
            else:
                ds = ds_dict

            logger.info(f"Dataset loaded successfully. Total records: {len(ds)}")
            logger.info(f"Fields: {list(ds.features.keys())}")

            # Materialize to parquet
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Materializing dataset to {output_path}...")
            ds.to_parquet(output_path)
            
            logger.info("Download and materialization complete.")
            return

        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = backoff_factor ** retry_count
                logger.error(f"Download failed (attempt {retry_count}/{max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {max_retries} attempts: {e}")
                raise

def validate_structural_descriptors(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for the presence of structural descriptors in the dataframe.
    """
    structural_features = ['radius', 'packing_fraction', 'spacegroup', 'volume_per_atom']
    available = {feat: feat in df.columns for feat in structural_features}
    return available

def extract_structural_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract structural features if available.
    """
    features = ['radius', 'packing_fraction']
    available_features = [f for f in features if f in df.columns]
    if not available_features:
        logger.warning("No structural features found to extract.")
        return df
    return df[available_features]

def update_validation_report(report_path: str = "data/validation_report.json", structural_available: bool = False) -> None:
    """
    Update the validation report with structural feature status.
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "structural_features_available": structural_available,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report updated: {report_path}")

def update_config_structural_flag(config_path: str = "code/config.yaml", structural_available: bool = False) -> None:
    """
    Update config.yaml to reflect structural feature availability.
    """
    import yaml
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}, skipping update.")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'data' not in config:
        config['data'] = {}
    config['data']['structural_features_available'] = structural_available
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    logger.info("Config updated with structural flag.")

def materialize_dataset(ds, output_path: str) -> None:
    """
    Materialize a HuggingFace dataset to parquet.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    ds.to_parquet(output_path)
    logger.info(f"Dataset materialized to {output_path}")

def main():
    """
    Main entry point for the download script.
    """
    output_path = "data/raw/oqmd.parquet"
    
    # Ensure directories exist
    os.makedirs("data/raw", exist_ok=True)
    
    # Download
    download_oqmd_dataset(output_path)
    
    # Verify file exists
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Failed to create output file: {output_path}")
    
    # Calculate checksum
    sha256_hash = calculate_sha256(output_path)
    checksum_path = "data/checksums.json"
    
    checksum_data = {
        "filename": "oqmd.parquet",
        "sha256": sha256_hash
    }
    
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    
    logger.info(f"Checksum saved to {checksum_path}: {sha256_hash}")
    
    # Load data to validate structure
    import pandas as pd
    df = pd.read_parquet(output_path)
    structural_available = validate_structural_descriptors(df)['spacegroup'] # Simplified check
    
    update_validation_report(structural_available=structural_available)
    update_config_structural_flag(structural_available=structural_available)

    logger.info("Download and validation complete.")

if __name__ == "__main__":
    main()
