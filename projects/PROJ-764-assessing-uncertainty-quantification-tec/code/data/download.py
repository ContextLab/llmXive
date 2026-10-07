import os
import sys
import logging
import time
import json
import hashlib
from pathlib import Path
import hashlib

# Attempt to import datasets. If missing, the script will fail loudly as per requirements.
try:
    from datasets import load_dataset, concatenate_datasets
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Please install it via 'pip install datasets'."
    )

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_oqmd_dataset(output_path: str, max_retries: int = 3):
    """
    Download the OQMD dataset from the verified HuggingFace source.
    Implements retry logic with exponential backoff.
    """
    # Verified source as per execution feedback
    dataset_name = "jablonkagroup/oqmd"
    config_name = "raw_data"
    
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Attempting to download {dataset_name} (Attempt {attempt + 1}/{max_retries})...")
            ds_dict = load_dataset(dataset_name, config_name, trust_remote_code=True)
            
            # Combine all splits into a single Dataset
            if isinstance(ds_dict, dict):
                ds = concatenate_datasets(list(ds_dict.values()))
            else:
                ds = ds_dict
            
            logger.info(f"Dataset loaded successfully. Total records: {len(ds)}")
            
            # Materialize to parquet
            logger.info(f"Materializing dataset to {output_path}...")
            ds.to_parquet(output_path)
            
            logger.info("Dataset materialization complete.")
            return True
            
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Download failed: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to download dataset after {max_retries} attempts: {e}")
                raise RuntimeError(f"Data download failed after {max_retries} attempts. Error: {e}")

def validate_structural_descriptors(df):
    """Check for presence of structural descriptors."""
    structural_features = ['radius', 'packing_fraction', 'volume_per_atom', 'spacegroup']
    present = [f for f in structural_features if f in df.columns]
    missing = [f for f in structural_features if f not in df.columns]
    return present, missing

def extract_structural_features(df):
    """Extract structural features if available."""
    structural_features = ['radius', 'packing_fraction']
    available = [f for f in structural_features if f in df.columns]
    if available:
        return df[available]
    return None

def update_validation_report(report_path: str, structural_features_present: bool, missing_features: list):
    """Update or create the validation report."""
    report = {
        "structural_features_available": structural_features_present,
        "available_features": [],
        "missing_features": missing_features
    }
    if structural_features_present:
        # This would be populated by extract_structural_features logic
        pass
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

def update_config_structural_flag(config_path: str, has_structural: bool):
    """Update config.yaml to reflect structural feature availability."""
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'data' not in config:
        config['data'] = {}
    config['data']['structural_features_available'] = has_structural
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

def materialize_dataset(dataset, output_path: str):
    """Save the dataset to a parquet file."""
    dataset.to_parquet(output_path)
    logger.info(f"Dataset saved to {output_path}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = str(raw_dir / "oqmd.parquet")
    checksum_path = str(raw_dir / "checksums.json")
    validation_report_path = "data/validation_report.json"
    config_path = "code/config.yaml"
    
    # Download and materialize
    success = download_oqmd_dataset(output_path)
    
    if success:
        # Calculate checksum
        sha256 = calculate_sha256(output_path)
        checksum_data = {
            "filename": "oqmd.parquet",
            "sha256": sha256
        }
        with open(checksum_path, 'w') as f:
            json.dump(checksum_data, f, indent=2)
        logger.info(f"Checksum saved to {checksum_path}: {sha256}")
        
        # Validate structural descriptors
        # Note: We need to load the parquet to check columns, but for the download script
        # we assume the schema based on the dataset description or load a sample.
        # To be safe and avoid full load in download script, we'll just note the check.
        # The actual validation is done in preprocess.py or a separate step.
        # For this task, we write a placeholder report indicating structural features
        # are to be checked in the next step, or we load a sample.
        # Let's load a sample to be rigorous.
        import pandas as pd
        sample_df = pd.read_parquet(output_path)
        present, missing = validate_structural_descriptors(sample_df)
        
        structural_available = len(present) > 0
        update_validation_report(validation_report_path, structural_available, missing)
        logger.info(f"Validation report saved to {validation_report_path}")
        
        # Update config if needed (optional step, but good for consistency)
        # update_config_structural_flag(config_path, structural_available)

if __name__ == "__main__":
    main()
