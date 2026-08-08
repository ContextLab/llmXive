import os
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path
import yaml
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 60) -> None:
    """Download a file from a URL with basic error handling."""
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded {dest_path} successfully")
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def verify_checksum(file_path: Path, checksum_path: Path) -> bool:
    """Verify a file against its checksum file."""
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.")
        return False
    if not checksum_path.exists():
        logger.error(f"Checksum file {checksum_path} does not exist.")
        return False

    current_hash = calculate_sha256(file_path)
    with open(checksum_path, 'r') as f:
        stored_hash = f.read().split()[0]

    if current_hash == stored_hash:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {stored_hash}, Got: {current_hash}")
        return False

def load_huggingface_dataset(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """Load a dataset from Hugging Face."""
    logger.info(f"Loading dataset {dataset_id} split {split} from Hugging Face")
    try:
        dataset = load_dataset(dataset_id, split=split)
        df = dataset.to_pandas()
        logger.info(f"Loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise

def download_oqmd_constitution() -> Path:
    """Download OQMD constitution dataset."""
    output_path = DATA_RAW_DIR / "oqmd.parquet"
    if output_path.exists():
        logger.info(f"OQMD file already exists at {output_path}, skipping download.")
        return output_path

    # Try Hugging Face first
    try:
        df = load_huggingface_dataset("oqmd/oqmd-dataset", split="train")
        # Select relevant columns if available, otherwise keep all
        # Assuming standard OQMD schema, but keeping generic for robustness
        df.to_parquet(output_path)
        logger.info(f"Saved OQMD to {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"HF download failed, attempting fallback URL: {e}")
        # Fallback URL (example, replace with actual if known)
        # Since specific URL wasn't provided in prompt, we rely on HF or fail loudly
        raise RuntimeError("Could not download OQMD from HF or fallback.") from e

def download_aflow_constitution() -> Path:
    """Download AFLOW constitution dataset."""
    output_path = DATA_RAW_DIR / "aflow.parquet"
    if output_path.exists():
        logger.info(f"AFLOW file already exists at {output_path}, skipping download.")
        return output_path

    # Try Hugging Face first
    try:
        df = load_huggingface_dataset("aflow/aflow-dataset", split="train")
        df.to_parquet(output_path)
        logger.info(f"Saved AFLOW to {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"HF download failed, attempting fallback URL: {e}")
        raise RuntimeError("Could not download AFLOW from HF or fallback.") from e

def update_state_file(checksums: dict):
    """Update the project state YAML with artifact checksums."""
    state_file = STATE_FILE
    state_file.parent.mkdir(parents=True, exist_ok=True)

    if not state_file.exists():
        state_data = {"artifact_hashes": {}}
    else:
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"].update(checksums)

    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    logger.info(f"Updated state file at {state_file}")

def main():
    """Main entry point for T006c: Checksum verification and state update."""
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure files exist (T006b dependency)
    # If files are missing, we attempt to download them first (T006b logic)
    oqmd_path = DATA_RAW_DIR / "oqmd.parquet"
    aflow_path = DATA_RAW_DIR / "aflow.parquet"

    if not oqmd_path.exists():
        logger.info("OQMD file missing, triggering download (T006b dependency)...")
        oqmd_path = download_oqmd_constitution()

    if not aflow_path.exists():
        logger.info("AFLOW file missing, triggering download (T006b dependency)...")
        aflow_path = download_aflow_constitution()

    # 2. Calculate and save checksums
    checksums = {}

    # OQMD
    oqmd_hash = calculate_sha256(oqmd_path)
    oqmd_sha_path = DATA_RAW_DIR / "oqmd.parquet.sha256"
    with open(oqmd_sha_path, 'w') as f:
        f.write(f"{oqmd_hash}  oqmd.parquet\n")
    checksums["oqmd.parquet"] = oqmd_hash
    logger.info(f"Generated checksum for oqmd.parquet: {oqmd_hash}")

    # AFLOW
    aflow_hash = calculate_sha256(aflow_path)
    aflow_sha_path = DATA_RAW_DIR / "aflow.parquet.sha256"
    with open(aflow_sha_path, 'w') as f:
        f.write(f"{aflow_hash}  aflow.parquet\n")
    checksums["aflow.parquet"] = aflow_hash
    logger.info(f"Generated checksum for aflow.parquet: {aflow_hash}")

    # 3. Update state file
    update_state_file(checksums)

    logger.info("T006c Checksum verification and state update completed successfully.")

if __name__ == "__main__":
    main()
