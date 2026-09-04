import json
import hashlib
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure config is available for paths
try:
    from config import get_data_dir, get_processed_dir
except ImportError:
    # Fallback if run directly without package context
    from pathlib import Path
    def get_data_dir():
        return Path("data")
    def get_processed_dir():
        return Path("data/processed")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/processed/download.log")
    ]
)
logger = logging.getLogger(__name__)

class ChecksumError(Exception):
    """Raised when checksum verification fails."""
    pass

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_dataset_ids(ids_file: Path) -> List[str]:
    """Read dataset IDs from file."""
    if not ids_file.exists():
        logger.error(f"Dataset IDs file not found: {ids_file}")
        return []
    
    with open(ids_file, 'r') as f:
        ids = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    logger.info(f"Read {len(ids)} dataset IDs from {ids_file}")
    return ids

def fetch_openml_dataset(dataset_id: str, target_dir: Path) -> Optional[Path]:
    """Fetch dataset from OpenML."""
    try:
        import openml
        import pandas as pd
        
        logger.info(f"Fetching OpenML dataset: {dataset_id}")
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, categorical, attribute_names = dataset.get_data(dataset_format="dataframe")
        
        output_file = target_dir / f"openml_{dataset_id}.csv"
        X.to_csv(output_file, index=False)
        
        logger.info(f"Saved OpenML dataset to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        return None

def fetch_huggingface_dataset(dataset_id: str, target_dir: Path) -> Optional[Path]:
    """Fetch dataset from HuggingFace."""
    try:
        from datasets import load_dataset
        
        logger.info(f"Fetching HuggingFace dataset: {dataset_id}")
        ds = load_dataset(dataset_id, split="train")
        
        output_file = target_dir / f"hf_{dataset_id}.csv"
        ds.to_csv(output_file)
        
        logger.info(f"Saved HuggingFace dataset to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace dataset {dataset_id}: {e}")
        return None

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    if not expected_checksum:
        # If no checksum provided, we cannot validate - FAIL as per spec
        logger.error(f"No checksum provided for {file_path} - cannot validate")
        return False
    
    actual_checksum = compute_sha256(file_path)
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False
    
    logger.info(f"Checksum validated for {file_path}")
    return True

def filter_dataset_columns(file_path: Path, required_columns: List[str]) -> bool:
    """Check if dataset has required columns."""
    try:
        import pandas as pd
        
        # Read just the header to check columns
        df = pd.read_csv(file_path, nrows=0)
        columns = df.columns.tolist()
        
        missing = [col for col in required_columns if col not in columns]
        if missing:
            logger.warning(f"Dataset {file_path} missing required columns: {missing}")
            return False
        
        logger.info(f"Dataset {file_path} has all required columns")
        return True
    except Exception as e:
        logger.error(f"Error checking columns for {file_path}: {e}")
        return False

def write_exclusion_log(exclusions: List[Dict[str, Any]], log_path: Path):
    """Write exclusion log to JSON file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Wrote exclusion log to {log_path}")

def write_blocked_status(reason: str, status_path: Path):
    """Write blocked status file."""
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "blocked",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Wrote blocked status to {status_path}")

def update_readme_status(exclusions: List[Dict[str, Any]], readme_path: Path):
    """Update README with dataset status information."""
    if not readme_path.exists():
        logger.warning(f"README not found at {readme_path}, creating new one")
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        with open(readme_path, 'w') as f:
            f.write("# Dataset Status\n\n")
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Append or update status section
    status_section = "\n## Dataset Exclusions\n\n"
    for exclusion in exclusions:
        status_section += f"- **{exclusion['dataset_id']}**: {exclusion['reason']}\n"
    
    if "## Dataset Exclusions" in content:
        # Update existing section
        content = content.split("## Dataset Exclusions")[0] + status_section
    else:
        content += status_section
    
    with open(readme_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Updated README at {readme_path}")

def run_download_pipeline():
    """Main pipeline for downloading and validating datasets."""
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Read dataset IDs
    ids_file = data_dir / "dataset_ids.txt"
    dataset_ids = parse_dataset_ids(ids_file)
    
    if not dataset_ids:
        logger.error("No dataset IDs found")
        write_blocked_status("No dataset IDs found in data/dataset_ids.txt", data_dir / "blocked_status.json")
        update_readme_status([{"dataset_id": "N/A", "reason": "No dataset IDs found"}], data_dir / "README.md")
        return False
    
    required_columns = ["duration_estimate", "stimulus_sequence", "participant_id"]
    exclusions = []
    valid_datasets = []
    
    # Checksums map - in a real scenario, this would come from a verified source
    # For now, we'll skip checksum validation if not provided and fail loudly if required
    checksums_map = {}  # Would be populated from a verified source file
    
    for dataset_id in dataset_ids:
        logger.info(f"Processing dataset: {dataset_id}")
        
        # Try to fetch from OpenML first, then HuggingFace
        downloaded_file = None
        
        # Attempt OpenML
        if dataset_id.isdigit():  # OpenML IDs are typically numeric
            downloaded_file = fetch_openml_dataset(dataset_id, processed_dir)
        
        # Attempt HuggingFace if OpenML failed
        if not downloaded_file:
            downloaded_file = fetch_huggingface_dataset(dataset_id, processed_dir)
        
        if not downloaded_file:
            exclusions.append({
                "dataset_id": dataset_id,
                "status": "excluded",
                "reason": "Failed to download from any source"
            })
            continue
        
        # Validate checksum if available
        expected_checksum = checksums_map.get(dataset_id)
        if expected_checksum:
            if not validate_checksum(downloaded_file, expected_checksum):
                exclusions.append({
                    "dataset_id": dataset_id,
                    "status": "excluded",
                    "reason": "Checksum validation failed"
                })
                continue
        else:
            # Spec says: "If a hash is missing in the source file, FAIL (do NOT generate)"
            # Since we have no source file with hashes, we cannot validate - exclude
            exclusions.append({
                "dataset_id": dataset_id,
                "status": "excluded",
                "reason": "No checksum available for validation"
            })
            continue
        
        # Filter for required columns
        if not filter_dataset_columns(downloaded_file, required_columns):
            exclusions.append({
                "dataset_id": dataset_id,
                "status": "excluded",
                "reason": f"Missing required columns: {required_columns}"
            })
            continue
        
        # Dataset is valid
        valid_datasets.append(str(downloaded_file))
        exclusions.append({
            "dataset_id": dataset_id,
            "status": "valid",
            "reason": "Passed all validations"
        })
    
    # Write exclusion log
    exclusion_log_path = processed_dir / "exclusion_log.json"
    write_exclusion_log(exclusions, exclusion_log_path)
    
    # Check if any valid datasets found
    if not valid_datasets:
        logger.error("No valid datasets found after filtering")
        write_blocked_status("No valid datasets found after download and validation", data_dir / "blocked_status.json")
        update_readme_status(exclusions, data_dir / "README.md")
        return False
    
    logger.info(f"Successfully processed {len(valid_datasets)} datasets")
    update_readme_status(exclusions, data_dir / "README.md")
    return True

def main():
    """Entry point for the download script."""
    success = run_download_pipeline()
    if not success:
        logger.error("Download pipeline failed - no valid datasets available")
        sys.exit(1)
    logger.info("Download pipeline completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()
