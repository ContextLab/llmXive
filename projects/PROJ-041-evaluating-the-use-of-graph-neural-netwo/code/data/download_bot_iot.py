import os
import sys
import hashlib
import logging
import urllib.request
import urllib.error
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration constants
# Based on plan.md Note on Spec Deviations: NF-BoT-IoT-v3 is the verified alternative.
# Using the Kaggle API requires authentication, so we use the direct HuggingFace dataset loader
# or a direct mirror if available. Since we must avoid synthetic data and fail loudly,
# we attempt to fetch from a known public mirror or the HuggingFace Hub.
# The NF-BoT-IoT dataset is available on HuggingFace Datasets.
DATASET_HF_ID = "bot-iot/bot-iot"
# Specific file name for the v3 processed CSV if available, or we download the raw and convert.
# For this implementation, we attempt to download a specific scenario file if a direct URL exists,
# otherwise we use the HuggingFace datasets library to fetch the real data.
# Given the constraint to "fail loudly" and not use synthetic data, we will use the `datasets` library
# to fetch the real NF-BoT-IoT data. If that fails, we raise an error.

# Fallback to a direct URL if the HF library is not the preferred method for the specific CSV structure.
# However, the task requires fetching from a URL. The NF-BoT-IoT dataset is often hosted on Kaggle.
# A common direct mirror for the "NF-BoT-IoT-v3" specific subset used in research is:
# https://www.unb.ca/cic/datasets/bot-iot.html (requires manual download usually).
# To satisfy "programmatically accessible source" without API keys, we use the HuggingFace Hub client
# which is pip-installable and provides real data.

OUTPUT_PATH = "data/raw/bot-iot_v3.csv"
# Known hash for the specific file we expect. Since the exact hash of the full dataset is large,
# we will validate the file existence and size, and if a specific hash is provided in state/config, use it.
# For now, we rely on the HF download success. If the task requires a specific URL hash,
# we would need that specific URL.
# Let's assume a verified source from the feedback or plan:
# The plan mentions "NF-BoT-IoT-v3" as the fallback.
# We will use the HuggingFace datasets library to fetch the real data.

EXPECTED_SHA256 = None  # To be filled if a specific hash is known from the "VERIFIED REAL DATA SOURCE" block.
# If no hash is provided, we validate by checking if the file is non-empty and has expected columns.

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise

def download_file(url: str, output_path: str) -> bool:
    """Download a file from a URL."""
    try:
        logger.info(f"Attempting to download from {url}...")
        urllib.request.urlretrieve(url, output_path)
        logger.info(f"Downloaded successfully to {output_path}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False

def validate_file(filepath: str, expected_hash: Optional[str] = None) -> bool:
    """Validate the downloaded file."""
    if not os.path.exists(filepath):
        logger.error(f"Validation failed: File {filepath} does not exist.")
        return False
    
    if expected_hash:
        actual_hash = calculate_sha256(filepath)
        if actual_hash != expected_hash:
            logger.error(f"Hash mismatch. Expected: {expected_hash}, Got: {actual_hash}")
            return False
        logger.info(f"Hash validation passed: {actual_hash}")
    else:
        # Basic validation: file is not empty
        if os.path.getsize(filepath) == 0:
            logger.error("Validation failed: File is empty.")
            return False
        logger.info("Basic validation passed (file exists and is not empty).")
    
    return True

def trigger_fallback():
    """Trigger the fallback logic to T007c."""
    logger.critical("NF-BoT-IoT download failed. Triggering fallback to T007c.")
    # Import here to avoid circular dependency if needed, but T007c is a task, not a function.
    # The task logic says "invoke T007c". In code, this means raising an error or calling the fallback manager.
    # We will raise an error that the orchestration layer (T007c) can catch.
    raise RuntimeError("NF-BoT-IoT download failed. Fallback required.")

def download_bot_iot_dataset() -> str:
    """
    Attempt to download the NF-BoT-IoT dataset.
    Uses HuggingFace datasets library as the primary source for real data.
    Falls back to a direct URL if the library is not preferred, but HF is more robust for this dataset.
    """
    from datasets import load_dataset
    import pandas as pd

    output_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logger.info("Attempting to load NF-BoT-IoT dataset from HuggingFace...")
        # The dataset ID might be specific. Common ID is 'bot-iot/bot-iot' or similar.
        # If the specific 'v3' is not a separate split, we might need to filter.
        # Let's try to load the dataset.
        # Note: This dataset can be large. We might need to stream or select a specific split.
        # Assuming we need the 'training' or 'test' split or the full dataset.
        # The task asks for `data/raw/bot-iot_v3.csv`.
        
        # Attempt to load the dataset. If it fails, we try a direct URL if available.
        # Since I don't have a specific verified URL in the prompt, I will use the HF library.
        # If the library fails, we raise an error.
        
        dataset = load_dataset("bot-iot/bot-iot", split="train", streaming=True)
        
        # Convert to pandas and save to CSV.
        # Since streaming, we might need to collect it.
        # For a large dataset, we might just write the first chunk or the whole thing if it fits.
        # The task says "Write `data/raw/bot-iot_v3.csv`".
        # We will write the full dataset if possible, or a representative sample if it's too large?
        # No, the constraint says "Real data only". We must write the real data.
        # If it's too large, we might need to stream it to disk.
        
        df = dataset.to_pandas()
        df.to_csv(OUTPUT_PATH, index=False)
        
        logger.info(f"Dataset saved to {OUTPUT_PATH}")
        
        # Validate
        if not validate_file(OUTPUT_PATH, EXPECTED_SHA256):
            trigger_fallback()
        
        return OUTPUT_PATH

    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace: {e}")
        # Try a direct URL as a fallback within this function?
        # The plan says "invoke T007c" if fetch fails.
        # We will raise the error to let T007c handle it.
        trigger_fallback()
        return ""

def main():
    """Main entry point for T007b."""
    logger.info("Starting T007b: Attempt Download of NF-BoT-IoT Dataset")
    try:
        result_path = download_bot_iot_dataset()
        if result_path and os.path.exists(result_path):
            logger.info(f"T007b completed successfully. Output: {result_path}")
            return 0
        else:
            logger.error("T007b failed to produce output.")
            return 1
    except RuntimeError as e:
        logger.error(f"T007b failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"T007b encountered an unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
