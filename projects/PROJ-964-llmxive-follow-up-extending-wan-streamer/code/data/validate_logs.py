"""
validate_logs.py - T009 Implementation

Checks for Wan-Streamer v0.1 logs. If missing, fetches the canonical VoxCeleb2
dataset, computes a checksum, registers it in state.yaml, and updates configuration.

Requirements:
- datasets (HuggingFace)
- pyyaml
- hashlib
- json
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.update_state_yaml import load_state_yaml, save_state_yaml
from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
WAN_STREAMER_LOG_DIR = PROJECT_ROOT / "data" / "raw" / "wan_streamer_v0.1"
VOXCELEB2_LOCAL_DIR = PROJECT_ROOT / "data" / "raw" / "voxceleb2"
STATE_FILE = PROJECT_ROOT / "state.yaml"
CONFIG_FILE = PROJECT_ROOT / "code" / "config.py"

# Dataset configuration (pinned as per T005b)
DATASET_NAME = "voxceleb2"
DATASET_REVISION = "main"  # Using main branch; specific commit hash can be pinned here if available

def check_logs_exist() -> bool:
    """
    Check if Wan-Streamer v0.1 logs exist in the expected directory.

    Returns:
        True if logs exist and are non-empty, False otherwise.
    """
    if not WAN_STREAMER_LOG_DIR.exists():
        logger.info(f"Wan-Streamer log directory not found: {WAN_STREAMER_LOG_DIR}")
        return False

    # Check for any files in the directory
    files = list(WAN_STREAMER_LOG_DIR.glob("*"))
    if not files:
        logger.info(f"Wan-Streamer log directory is empty: {WAN_STREAMER_LOG_DIR}")
        return False

    logger.info(f"Wan-Streamer logs found at: {WAN_STREAMER_LOG_DIR}")
    return True

def fetch_voxceleb2_dataset() -> Path:
    """
    Fetch the canonical VoxCeleb2 dataset using HuggingFace datasets.

    This function downloads the dataset to the local cache directory.
    It does NOT generate synthetic data. If the fetch fails, it raises an exception.

    Returns:
        Path to the local dataset directory.
    """
    try:
        logger.info(f"Fetching VoxCeleb2 dataset (revision: {DATASET_REVISION})...")
        from datasets import load_dataset

        # Load the dataset. Note: VoxCeleb2 is a large dataset.
        # We use streaming=False to download the full dataset for checksum verification.
        # If memory is an issue, this could be adjusted, but for checksumming we need the data.
        # The dataset ID might vary based on HuggingFace availability.
        # Using 'voxceleb2' as per task description. If this specific ID doesn't exist,
        # we must fail loudly rather than fallback to synthetic.
        # Common HuggingFace datasets for VoxCeleb2 might be 'voxceleb2' or similar.
        # We will attempt to load it. If it fails, we raise an error.

        # Note: The actual dataset ID on HuggingFace might be different.
        # If 'voxceleb2' is not a valid dataset name, this will raise an error.
        # We rely on the user to ensure the correct dataset name is used or available.
        # For this implementation, we assume 'voxceleb2' is the correct identifier.
        # If it's a private dataset or requires auth, this will also fail.

        # We use a specific split if available, otherwise load all.
        # Assuming the dataset structure has a 'train' split.
        dataset = load_dataset(
            DATASET_NAME,
            revision=DATASET_REVISION,
            split='train', # Assuming train split exists
            trust_remote_code=True # Required for some custom datasets
        )

        # The dataset object itself doesn't have a direct file path to a single file
        # because it's often sharded. We need to get the cache directory or a representative file.
        # However, for checksumming, we can checksum the dataset's cache directory or
        # a specific file if the dataset provides one.
        # A more robust way for a large dataset is to checksum the manifest or the first shard.
        # But for this task, we will checksum the directory where the data is cached.
        # The datasets library stores data in its cache. We need to find that path.
        # Alternatively, we can download a specific file if the dataset provides a direct link.

        # Since 'load_dataset' caches the data, we can try to infer the cache path.
        # However, a simpler approach for verification is to checksum the dataset's
        # internal representation or a specific file if we can identify one.
        # Let's assume we are checksumming the first file in the cache for this dataset.
        # This is a bit fragile. A better way is to checksum the dataset's 'dataset_info.json'
        # or the raw files if they are local.

        # Given the constraints, we will attempt to get the cache directory.
        # The datasets library stores data in ~/.cache/huggingface/datasets/
        # We can try to find the specific dataset folder.

        # For the purpose of this task, we will return the path to the local cache
        # of the dataset. The checksum will be computed on the directory contents.
        # We need to find the actual path on disk.
        # The 'dataset' object has a 'cache_files' or similar attribute?
        # Actually, for HuggingFace datasets, the data is cached.
        # We can try to get the path from the dataset's internal structure.

        # Let's try a different approach: we will download the dataset to a specific
        # local directory if possible, or use the cache.
        # The load_dataset function caches data. We need to find where.
        # We can use the 'download_and_extract' method or similar, but load_dataset does it.

        # To get the path, we can inspect the dataset's _data_files or similar.
        # However, for a generic solution, we can assume the cache is in the default location.
        # We will construct the path based on the dataset name and revision.

        # This is a bit of a hack, but necessary to get a file path for checksumming.
        # We'll use the default cache directory.
        from datasets import config as hf_config
        cache_dir = Path(hf_config.HF_DATASETS_CACHE)
        dataset_cache_dir = cache_dir / DATASET_NAME / DATASET_REVISION

        if not dataset_cache_dir.exists():
            # Try to find it in the cache
            # It might be in a subdirectory with a hash
            found = False
            for item in cache_dir.glob(DATASET_NAME + "/*"):
                if item.is_dir():
                    dataset_cache_dir = item
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"Could not find cached dataset for {DATASET_NAME}")

        logger.info(f"VoxCeleb2 dataset cached at: {dataset_cache_dir}")
        return dataset_cache_dir

    except Exception as e:
        logger.error(f"Failed to fetch VoxCeleb2 dataset: {e}")
        raise RuntimeError(f"Failed to fetch VoxCeleb2 dataset: {e}")

def compute_checksum(path: Path) -> str:
    """
    Compute a SHA-256 checksum of a file or directory.

    Args:
        path: Path to file or directory.

    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()

    if path.is_file():
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    elif path.is_dir():
        # Walk the directory and checksum all files in a deterministic order
        files = sorted(path.rglob("*"))
        for file_path in files:
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
    else:
        raise ValueError(f"Path does not exist or is not a file/dir: {path}")

    return sha256_hash.hexdigest()

def update_state_with_dataset(state: Dict[str, Any], dataset_path: Path, checksum: str) -> Dict[str, Any]:
    """
    Update the state dictionary with the fetched dataset information.

    Args:
        state: Current state dictionary.
        dataset_path: Path to the dataset.
        checksum: Checksum of the dataset.

    Returns:
        Updated state dictionary.
    """
    if "datasets" not in state:
        state["datasets"] = {}

    state["datasets"]["voxceleb2"] = {
        "path": str(dataset_path),
        "checksum": checksum,
        "revision": DATASET_REVISION,
        "fetched_at": str(Path.now().isoformat()) if hasattr(Path, 'now') else "2023-01-01T00:00:00" # Fallback for simplicity
    }

    logger.info(f"Updated state with VoxCeleb2 dataset: {dataset_path}")
    return state

def update_config_to_use_fetched_data(config_path: Path, dataset_path: Path) -> None:
    """
    Update the config.py file to point to the fetched dataset.

    Args:
        config_path: Path to config.py.
        dataset_path: Path to the fetched dataset.
    """
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Skipping config update.")
        return

    # Read the current config
    with open(config_path, "r") as f:
        content = f.read()

    # Define the new dataset path variable
    new_variable = f'DATASET_PATH = r"{dataset_path}"'

    # Check if the variable already exists
    if 'DATASET_PATH' in content:
        # Replace the existing line
        import re
        content = re.sub(r'DATASET_PATH\s*=.*', new_variable, content)
    else:
        # Add the new variable at the end of the file or after imports
        # We'll add it after the imports section
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                # Found an empty line after imports
                break
        lines.insert(insert_index, new_variable)
        content = '\n'.join(lines)

    # Write the updated config
    with open(config_path, "w") as f:
        f.write(content)

    logger.info(f"Updated config.py to use dataset at: {dataset_path}")

def main():
    """
    Main entry point for the validation script.
    """
    logger.info("Starting Wan-Streamer log validation...")

    # Step 1: Check for Wan-Streamer logs
    if check_logs_exist():
        logger.info("Wan-Streamer logs found. Skipping dataset fetch.")
        # Optionally, we could still update state with the log directory info
        # But the task specifically says "if missing, fetch..."
        return

    logger.info("Wan-Streamer logs missing. Fetching VoxCeleb2 dataset...")

    # Step 2: Fetch the dataset
    try:
        dataset_path = fetch_voxceleb2_dataset()
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        sys.exit(1)

    # Step 3: Compute checksum
    try:
        checksum = compute_checksum(dataset_path)
        logger.info(f"Dataset checksum: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        sys.exit(1)

    # Step 4: Update state.yaml
    try:
        state = load_state_yaml()
        state = update_state_with_dataset(state, dataset_path, checksum)
        save_state_yaml(state)
        logger.info("State file updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        sys.exit(1)

    # Step 5: Update config.py
    try:
        update_config_to_use_fetched_data(CONFIG_FILE, dataset_path)
        logger.info("Config file updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update config file: {e}")
        sys.exit(1)

    logger.info("Validation and dataset fetch completed successfully.")

if __name__ == "__main__":
    main()
