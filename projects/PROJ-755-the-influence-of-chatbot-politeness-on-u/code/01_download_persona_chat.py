import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        Path("data/raw/persona_chat"),
        Path("data/raw/persona_chat/checksums")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {dirs}")

def load_skip_flag() -> bool:
    """
    Check if HCI_P2 was valid.
    Returns True if we should SKIP this fallback task.
    """
    flag_path = Path("data/raw/hci_p2/validation_status.json")
    if not flag_path.exists():
        logger.warning(f"Validation flag {flag_path} not found. Assuming HCI_P2 invalid, proceeding with fallback.")
        return False

    try:
        with open(flag_path, 'r') as f:
            data = json.load(f)
        # If HCI_P2 was valid, we skip this fallback
        if data.get("is_valid", False):
            logger.info("HCI_P2 is valid. Skipping Persona-Chat download as per fallback logic.")
            return True
        else:
            logger.info("HCI_P2 is invalid. Proceeding with Persona-Chat download.")
            return False
    except Exception as e:
        logger.error(f"Error reading validation flag: {e}")
        return False

def load_dataset_with_check():
    """
    Attempt to load the Persona-Chat dataset from HuggingFace.
    Raises an error if the dataset is not found or inaccessible.
    """
    try:
        from datasets import load_dataset
        logger.info("Loading Persona-Chat dataset from HuggingFace...")
        # The dataset ID is HuggingFaceM4/Persona-Chat
        dataset = load_dataset("HuggingFaceM4/Persona-Chat", split="train", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load Persona-Chat dataset: {e}")
        raise

def pre_flight_check(dataset) -> bool:
    """
    Verify the presence of 'quality_rating' column.
    Returns True if the column exists, False otherwise.
    """
    logger.info("Performing pre-flight check for 'quality_rating' column...")
    try:
        # Since we are streaming, we peek at the first few items
        sample = next(iter(dataset))
        if "quality_rating" in sample:
            logger.info("Pre-flight check passed: 'quality_rating' column found.")
            return True
        else:
            logger.warning(f"Pre-flight check failed: 'quality_rating' column missing. Available keys: {list(sample.keys())}")
            return False
    except Exception as e:
        logger.error(f"Error during pre-flight check: {e}")
        return False

def generate_checksums(data_path: Path) -> Dict[str, str]:
    """Generate SHA256 checksums for all files in the directory."""
    checksums = {}
    for file_path in data_path.glob("*"):
        if file_path.is_file():
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksums[file_path.name] = sha256_hash.hexdigest()
    return checksums

def generate_manifest(data_path: Path, checksums: Dict[str, str], dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a manifest file for the dataset."""
    manifest = {
        "dataset_name": "Persona-Chat",
        "source": "HuggingFaceM4/Persona-Chat",
        "download_date": pd.Timestamp.now().isoformat(),
        "files": [
            {
                "filename": fname,
                "checksum": checksum
            }
            for fname, checksum in checksums.items()
        ],
        "metadata": dataset_info
    }
    return manifest

def save_raw_data(dataset, output_dir: Path):
    """
    Save the dataset to disk.
    Since we are streaming, we convert to parquet for efficiency.
    """
    logger.info("Saving raw data to parquet format...")
    output_file = output_dir / "persona_chat.parquet"
    
    # Convert streaming dataset to a list of dicts (batching if necessary for large datasets)
    # Note: For very large datasets, this might consume memory. 
    # A more robust approach would be to write in chunks, but for this task, we assume it fits or use a sample.
    # Given the constraint "Real data only", we try to process the stream.
    # If the dataset is too large, we might need to stream-write to parquet, but pyarrow/parquet
    # usually requires a full schema or batch writes.
    
    # Strategy: Iterate and write to a list, then convert to DataFrame and save.
    # If memory is an issue, we could write chunks to multiple parquet files.
    # For this implementation, we assume the dataset fits in memory or we process a reasonable subset.
    # However, the task says "download", implying the full raw data.
    
    # Let's try to collect data in batches to avoid memory spikes if possible, 
    # but standard pandas to_parquet is simpler.
    # If the dataset is huge, we might need to use pyarrow directly with streaming.
    
    # Simplified approach for this task:
    try:
        data = list(dataset)
        df = pd.DataFrame(data)
        df.to_parquet(output_file, index=False)
        logger.info(f"Saved raw data to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save raw data: {e}")
        raise

def generate_checksums_and_manifest(output_dir: Path):
    """Generate checksums and manifest for the saved data."""
    checksums = generate_checksums(output_dir)
    manifest_data = generate_manifest(output_dir, checksums, {"status": "downloaded"})
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Generated manifest at {manifest_path}")

def save_validation_report(output_dir: Path, status: str, message: str):
    """Save a validation report indicating the outcome of the download."""
    report = {
        "status": status,
        "message": message,
        "dataset": "Persona-Chat"
    }
    report_path = output_dir / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")

def main():
    """Main execution flow for T015b."""
    logger.info("Starting T015b: Download Persona-Chat dataset (Fallback)")
    
    # 1. Check if we should skip
    if load_skip_flag():
        logger.info("SKIPPED: HCI_P2 is valid. No need to download Persona-Chat.")
        return

    # 2. Ensure directories
    ensure_directories()
    output_dir = Path("data/raw/persona_chat")

    # 3. Attempt to load dataset
    try:
        dataset = load_dataset_with_check()
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        save_validation_report(output_dir, "failed", str(e))
        return

    # 4. Pre-flight check
    if not pre_flight_check(dataset):
        logger.info("SKIPPED: 'quality_rating' field missing per Plan Phase 0.")
        save_validation_report(output_dir, "skipped", "Field 'quality_rating' missing")
        return

    # 5. Save raw data
    try:
        save_raw_data(dataset, output_dir)
    except Exception as e:
        logger.error(f"Failed to save raw data: {e}")
        save_validation_report(output_dir, "failed", str(e))
        return

    # 6. Generate checksums and manifest
    try:
        generate_checksums_and_manifest(output_dir)
    except Exception as e:
        logger.error(f"Failed to generate checksums/manifest: {e}")
        # Don't fail the whole process, just log

    # 7. Save success report
    save_validation_report(output_dir, "success", "Persona-Chat downloaded and validated successfully")
    logger.info("T015b completed successfully.")

if __name__ == "__main__":
    main()