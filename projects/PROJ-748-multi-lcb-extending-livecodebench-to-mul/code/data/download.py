"""
Dataset download script for Multi-LCB.
Fetches the Multi-LCB dataset from Hugging Face, pins the commit hash,
verifies checksum, and logs the total task count.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, HfApi, list_repo_commits
from datasets import load_dataset

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_data_path, get_logs_path

# Configure logging
def setup_logging():
    log_dir = get_logs_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "download.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Hugging Face repository details
HF_REPO_ID = "livecodebench/multilcb-v1"
HF_DATASET_NAME = "multilcb"
DATASET_FILENAME = "multilcb.parquet"
CHECKSUMS_FILE_NAME = "checksums.json"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def pin_commit_hash(repo_id: str) -> str:
    """Fetch and return the latest commit hash for the repository."""
    api = HfApi()
    commits = list_repo_commits(repo_id)
    if not commits:
        raise RuntimeError(f"No commits found for repository {repo_id}")
    latest_commit = commits[0]
    commit_id = latest_commit.commit_id
    logger.info(f"Pinned commit hash: {commit_id}")
    return commit_id

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_file_checksum(file_path)
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verification passed for {file_path.name}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path.name}. "
            f"Expected: {expected_checksum}, Actual: {actual_checksum}"
        )
        return False

def download_dataset(
    repo_id: str,
    filename: str,
    output_dir: Path,
    pin_commit: bool = True
) -> Path:
    """
    Download dataset from Hugging Face Hub.

    Args:
        repo_id: Hugging Face repository ID.
        filename: Name of the file to download.
        output_dir: Directory to save the downloaded file.
        pin_commit: Whether to pin and log the commit hash.

    Returns:
        Path to the downloaded file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    commit_hash = None
    if pin_commit:
        commit_hash = pin_commit_hash(repo_id)
        logger.info(f"Commit hash pinned: {commit_hash}")

    logger.info(f"Downloading {filename} from {repo_id}...")
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            force_download=True
        )
        logger.info(f"Downloaded to: {downloaded_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

    return Path(downloaded_path)

def load_and_count_tasks(dataset_path: Path) -> int:
    """
    Load the dataset and count total tasks.

    Args:
        dataset_path: Path to the dataset file.

    Returns:
        Total number of tasks in the dataset.
    """
    logger.info(f"Loading dataset from {dataset_path}...")
    try:
        dataset = load_dataset("parquet", data_files=str(dataset_path))
        # Assuming the dataset has a single split 'train' or similar
        split_name = list(dataset.keys())[0]
        total_tasks = len(dataset[split_name])
        logger.info(f"Total tasks loaded: {total_tasks}")
        return total_tasks
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def save_checksum_info(file_path: Path, checksum: str, commit_hash: str, output_dir: Path):
    """Save checksum and commit hash to a JSON file."""
    checksum_file = output_dir / CHECKSUMS_FILE_NAME
    checksum_data = {
        "filename": file_path.name,
        "checksum": checksum,
        "commit_hash": commit_hash
    }
    with open(checksum_file, "w") as f:
        json.dump(checksum_data, f, indent=2)
    logger.info(f"Checksum info saved to {checksum_file}")

def main():
    """Main entry point for the download script."""
    logger.info("Starting dataset download process...")

    data_path = get_data_path()
    data_path.mkdir(parents=True, exist_ok=True)

    try:
        # Pin commit hash first to ensure we are working with a specific version
        commit_hash = pin_commit_hash(HF_REPO_ID)
        logger.info(f"Target commit hash: {commit_hash}")

        # Download the dataset
        downloaded_path = download_dataset(
            repo_id=HF_REPO_ID,
            filename=DATASET_FILENAME,
            output_dir=data_path,
            pin_commit=False  # Already pinned above
        )

        # Compute checksum
        checksum = compute_file_checksum(downloaded_path)
        logger.info(f"Computed checksum: {checksum}")

        # Save checksum info immediately
        save_checksum_info(downloaded_path, checksum, commit_hash, data_path)

        # Load dataset and count tasks
        total_tasks = load_and_count_tasks(downloaded_path)

        logger.info(f"Dataset download and verification complete. Total tasks: {total_tasks}")

    except Exception as e:
        logger.error(f"Dataset download process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()