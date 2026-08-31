"""
Task T015c: Download EmpatheticDialogues dataset (Conditional Fallback).

This script implements the conditional download of the EmpatheticDialogues dataset
as a fallback if HCI_P2 is determined to be invalid.

Logic:
1. Check for SKIP_SECONDARY flag. If true, exit gracefully.
2. Attempt to fetch 'HuggingFaceM4/EmpatheticDialogues'.
3. Perform pre-flight check for 'quality_rating' field.
4. If missing, log stop condition and exit.
5. If present, save raw data to data/raw/empathetic_dialogues/ with checksums.
"""
import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/empathetic_dialogues_download.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories."""
    output_dir = Path("data/raw/empathetic_dialogues")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_skip_flag() -> bool:
    """
    Load the SKIP_SECONDARY flag from the state file or environment.
    Returns True if we should skip this download (because HCI_P2 was valid).
    """
    # Check environment variable first
    if os.getenv("SKIP_SECONDARY", "").lower() == "true":
        return True
    
    # Check state file if it exists
    state_file = Path("state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml")
    if state_file.exists():
        try:
            import yaml
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            # Check if HCI_P2 is marked valid
            if state.get("hci_p2_status") == "HCI_P2_VALID":
                return True
        except Exception as e:
            logger.warning(f"Could not parse state file: {e}")
    
    return False

def load_dataset_with_check(dataset_name: str, split: str = "train") -> Optional[Any]:
    """
    Load a dataset from HuggingFace with error handling.
    Returns the dataset object or None if loading fails.
    """
    try:
        logger.info(f"Attempting to load dataset: {dataset_name}")
        dataset = load_dataset(dataset_name, split=split, trust_remote_code=True)
        logger.info(f"Successfully loaded {dataset_name}: {len(dataset)} rows")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        return None

def pre_flight_check(dataset: Any, required_fields: list) -> bool:
    """
    Check if the dataset contains the required fields.
    Returns True if all fields are present, False otherwise.
    """
    if dataset is None:
        return False
    
    features = dataset.features
    missing_fields = [f for f in required_fields if f not in features]
    
    if missing_fields:
        logger.error(f"Pre-flight check FAILED. Missing fields: {missing_fields}")
        return False
    
    logger.info(f"Pre-flight check PASSED. Found required fields: {required_fields}")
    return True

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums(data_dir: Path) -> Dict[str, str]:
    """Generate checksums for all files in the data directory."""
    checksums = {}
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
          rel_path = file_path.relative_to(data_dir)
          checksums[str(rel_path)] = compute_file_checksum(file_path)
    return checksums

def generate_manifest(dataset_name: str, checksums: Dict[str, str], row_count: int) -> Dict[str, Any]:
    """Generate a manifest file for the dataset."""
    return {
        "dataset_name": dataset_name,
        "source": "HuggingFaceM4/EmpatheticDialogues",
        "row_count": row_count,
        "checksums": checksums,
        "timestamp": str(pd.Timestamp.now()),
        "status": "downloaded"
    }

def save_raw_data(dataset: Any, output_dir: Path):
    """Save the dataset to parquet format."""
    # Convert to pandas for easier saving
    df = dataset.to_pandas()
    output_path = output_dir / "raw_empathetic_dialogues.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved dataset to {output_path}")
    return output_path

def generate_checksums_and_manifest(output_dir: Path, dataset_name: str, row_count: int):
    """Generate checksums and manifest for the saved data."""
    checksums = generate_checksums(output_dir)
    manifest = generate_manifest(dataset_name, checksums, row_count)
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Generated manifest at {manifest_path}")

def save_validation_report(output_dir: Path, status: str, message: str):
    """Save a validation report indicating the outcome."""
    report = {
        "dataset": "EmpatheticDialogues",
        "status": status,
        "message": message,
        "timestamp": str(pd.Timestamp.now())
    }
    report_path = output_dir / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")

def main():
    """Main entry point for the EmpatheticDialogues download task."""
    logger.info("Starting T015c: EmpatheticDialogues Download")
    
    # 1. Check Skip Condition
    if load_skip_flag():
        logger.info("SKIPPED: HCI_P2 is valid, skipping EmpatheticDialogues download.")
        # Still create a validation report indicating skip
        output_dir = ensure_directories()
        save_validation_report(output_dir, "skipped", "HCI_P2 is valid, fallback not needed.")
        return 0
    
    # 2. Prepare Output Directory
    output_dir = ensure_directories()
    
    # 3. Load Dataset
    dataset_name = "HuggingFaceM4/EmpatheticDialogues"
    dataset = load_dataset_with_check(dataset_name)
    
    if dataset is None:
        logger.error("Failed to load EmpatheticDialogues dataset.")
        save_validation_report(output_dir, "failed", "Could not load dataset from HuggingFace.")
        return 1
    
    # 4. Pre-flight Check for 'quality_rating'
    # Note: EmpatheticDialogues typically has 'sentiment', 'context', 'utterance'
    # We check for 'quality_rating' as per the task spec. If missing, we stop.
    required_fields = ['quality_rating']
    
    # In case the dataset structure is different, we check available columns
    available_cols = list(dataset.features.keys())
    logger.info(f"Available columns in EmpatheticDialogues: {available_cols}")
    
    # The task spec requires 'quality_rating'. If not present, we must stop per Plan Phase 0.
    # However, EmpatheticDialogues might not have this exact field. 
    # We will attempt to map 'sentiment' or other fields if 'quality_rating' is missing,
    # BUT the strict instruction says: "If quality_rating is missing, log stop condition and exit".
    
    if 'quality_rating' not in available_cols:
        logger.error("STOP CONDITION MET: 'quality_rating' field missing in EmpatheticDialogues.")
        logger.error("Per Plan Phase 0: Skipping download of this dataset.")
        save_validation_report(output_dir, "stopped", "Field 'quality_rating' missing.")
        return 0
    
    # 5. Save Raw Data
    row_count = len(dataset)
    save_raw_data(dataset, output_dir)
    
    # 6. Generate Checksums and Manifest
    generate_checksums_and_manifest(output_dir, "EmpatheticDialogues", row_count)
    
    # 7. Save Success Report
    save_validation_report(output_dir, "success", "Dataset downloaded and validated successfully.")
    
    logger.info("T015c: EmpatheticDialogues download completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())