"""
T011: Dataset Download & Checksum Verification for BigVul.

Fetches the BigVul dataset (C, C++, JavaScript) from the Hugging Face Hub.
Computes SHA-256 checksums and verifies them against data/raw/checksums.json.
Saves raw files to data/raw/ in Parquet format.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.config import get_project_root

# Ensure datasets is available
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

LOGGER = get_logger(__name__)

# Configuration
DATASET_NAME = "codeX/bigvul"
LANGUAGES = ["c", "cpp", "js"]
OUTPUT_DIR = None
CHECKSUM_FILE = None
LOG_FILE = None

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums() -> Dict[str, str]:
    """Load expected checksums from data/raw/checksums.json."""
    if not CHECKSUM_FILE.exists():
        LOGGER.warning(f"Checksum file {CHECKSUM_FILE} not found. Creating empty manifest.")
        return {}
    try:
        with open(CHECKSUM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse checksum file: {e}")
        return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to data/raw/checksums.json."""
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

def log_errors(errors: Dict[str, str]) -> None:
    """Log download/verification errors to data/logs/download_errors.json."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, default=str)

def download_language_subset(lang: str, split: str = "train") -> Optional[Any]:
    """
    Download a specific language subset of the BigVul dataset.
    Returns the dataset object or None if failed.
    """
    LOGGER.info(f"Downloading BigVul {lang} subset (split={split})...")
    try:
        # Load from Hugging Face Hub
        # The BigVul dataset on HF is structured with 'train', 'test', 'validation' splits
        # We load the specific configuration for the language if available, 
        # or filter after loading the full dataset if the HF config is generic.
        # Checking HF docs: BigVul usually has configs for languages or a single config with language column.
        # Let's try loading the specific config first, falling back to filtering.
        
        # Attempt to load as a specific config (e.g., codeX/bigvul/c)
        # If that fails, load the whole dataset and filter.
        try:
            ds = load_dataset(DATASET_NAME, lang, split=split, trust_remote_code=True)
            LOGGER.info(f"Loaded BigVul {lang} directly as config.")
        except Exception:
            # Fallback: Load generic and filter
            LOGGER.info(f"Loading BigVul generic dataset and filtering for {lang}...")
            ds = load_dataset(DATASET_NAME, split=split, trust_remote_code=True)
            if 'language' in ds.column_names:
                ds = ds.filter(lambda x: x['language'] == lang)
                LOGGER.info(f"Filtered to {len(ds)} samples for {lang}.")
            else:
                LOGGER.error(f"Dataset does not have a 'language' column and config '{lang}' failed.")
                return None

        return ds
    except Exception as e:
        LOGGER.error(f"Failed to download BigVul {lang}: {e}")
        return None

def save_to_parquet(ds: Any, output_path: Path) -> None:
    """Save HuggingFace dataset to Parquet."""
    LOGGER.info(f"Saving to {output_path}...")
    ds.to_parquet(str(output_path))
    if not output_path.exists():
        raise FileNotFoundError(f"Failed to write parquet file: {output_path}")

def main():
    global OUTPUT_DIR, CHECKSUM_FILE, LOG_FILE
    
    project_root = get_project_root()
    OUTPUT_DIR = project_root / "data" / "raw"
    CHECKSUM_FILE = OUTPUT_DIR / "checksums.json"
    LOG_FILE = project_root / "data" / "logs" / "download_errors.json"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "logs").mkdir(parents=True, exist_ok=True)

    log_stage_start("T011_Download_BigVul")

    errors = {}
    current_checksums = load_checksums()
    all_verified = True

    for lang in LANGUAGES:
        file_name = f"bigvul_{lang}.parquet"
        output_path = OUTPUT_DIR / file_name
        
        # Check if file exists and verify checksum if present
        if output_path.exists():
            LOGGER.info(f"File {file_name} exists. Verifying checksum...")
            computed_hash = compute_sha256(output_path)
            expected_hash = current_checksums.get(file_name)
            
            if expected_hash and computed_hash == expected_hash:
                LOGGER.info(f"Checksum verified for {file_name}.")
                continue
            else:
                LOGGER.warning(f"Checksum mismatch or missing for {file_name}. Re-downloading.")
                if not expected_hash:
                    errors[file_name] = "Checksum missing in manifest"
                else:
                    errors[file_name] = f"Checksum mismatch: expected {expected_hash}, got {computed_hash}"
                os.remove(output_path)
        
        # Download
        ds = download_language_subset(lang)
        if ds is None:
            errors[file_name] = "Download failed"
            all_verified = False
            continue

        # Save
        try:
            save_to_parquet(ds, output_path)
            computed_hash = compute_sha256(output_path)
            current_checksums[file_name] = computed_hash
            LOGGER.info(f"Successfully downloaded and saved {file_name} (SHA-256: {computed_hash})")
        except Exception as e:
            errors[file_name] = str(e)
            all_verified = False
            LOGGER.error(f"Failed to save {file_name}: {e}")

    # Update checksums file
    save_checksums(current_checksums)

    # Log errors if any
    if errors:
        log_errors(errors)
        log_stage_failure(f"Download completed with errors: {list(errors.keys())}")
        sys.exit(1)
    else:
        log_stage_complete("T011_Download_BigVul", "All datasets downloaded and verified.")
        print("SUCCESS: BigVul dataset downloaded and verified.")

if __name__ == "__main__":
    main()
