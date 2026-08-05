import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import datasets library
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found. Please install it via 'pip install datasets'.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/download_data.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "code_x_glue_ct_code_to_text"
CONFIG_NAME = "python"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILENAME = "codexglue_python.parquet"
BASELINE_FILE = Path("data/raw/human_baseline_times.json")
MIN_SAMPLE_SIZE = 1  # Allow any size > 0, but log if < 200

def fetch_codexglue_dataset() -> Optional[Any]:
    """
    Fetches the CodeXGLUE Python code-generation subset from HuggingFace.
    Returns the dataset object or None if fetch fails.
    """
    logger.info(f"Attempting to fetch dataset: {DATASET_NAME} [{CONFIG_NAME}]")
    try:
        # Load dataset in streaming mode to handle large sizes efficiently
        # We only need the 'source' (prompt) and 'target' (code) columns
        dataset = load_dataset(DATASET_NAME, CONFIG_NAME, split="validation", streaming=True)
        logger.info("Dataset loaded successfully (streaming mode).")
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch CodeXGLUE dataset: {e}")
        return None

def compute_file_hash(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_sample_size(sample_count: int, reason: str = "") -> bool:
    """
    Validates the sample size against requirements.
    Logs the reason for reduction if count < 200.
    Returns True if count > 0, False otherwise.
    """
    if sample_count == 0:
        logger.error("Sample size is 0. Cannot proceed.")
        return False
    
    if sample_count < MIN_SAMPLE_SIZE:
        logger.warning(f"Sample size ({sample_count}) is below expected threshold.")
        if reason:
            logger.warning(f"Reason for sample size reduction: {reason}")
        return True # Still valid if > 0, but logged
    
    if sample_count < 200:
        logger.warning(f"Sample size ({sample_count}) is less than 200.")
        if reason:
            logger.info(f"Reason for sample size reduction: {reason}")
        return True
    
    logger.info(f"Sample size ({sample_count}) is sufficient.")
    return True

def verify_baseline_exists(prompt_ids: list) -> bool:
    """
    Verifies that the human baseline file exists and contains entries for the prompts.
    Returns True if valid, False otherwise.
    """
    if not BASELINE_FILE.exists():
        logger.warning(f"Baseline file not found at {BASELINE_FILE}. Proceeding without baseline matching.")
        return False
    
    try:
        with open(BASELINE_FILE, 'r') as f:
            baseline_data = json.load(f)
        
        if not isinstance(baseline_data, dict):
            logger.error("Baseline file format invalid. Expected a dictionary.")
            return False
        
        # Check if at least one prompt has a baseline entry
        matched_count = sum(1 for pid in prompt_ids if pid in baseline_data)
        if matched_count == 0:
            logger.warning("No prompt IDs from the dataset found in the baseline file.")
            return False
        
        logger.info(f"Baseline verification passed. {matched_count}/{len(prompt_ids)} prompts matched.")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse baseline file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during baseline verification: {e}")
        return False

def save_dataset(dataset: Any, output_path: Path, max_samples: int = 500) -> int:
    """
    Saves a subset of the dataset to a local parquet file.
    Returns the number of samples saved.
    """
    logger.info(f"Saving dataset to {output_path} (limit: {max_samples} samples)")
    count = 0
    try:
        # Convert streaming dataset to a list of dicts for saving
        # We only need 'source' and 'target'
        samples = []
        for item in dataset:
            if count >= max_samples:
                break
            samples.append({
                "prompt_id": f"prompt_{count}",
                "source": item.get("source", ""),
                "target": item.get("target", "")
            })
            count += 1
        
        if count == 0:
            logger.error("No samples collected from dataset.")
            return 0

        # Save as JSON for simplicity and compatibility with downstream scripts
        # (Parquet requires pyarrow which might be an extra dependency, JSON is safer)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(samples, f, indent=2)
        
        logger.info(f"Saved {count} samples to {output_path.with_suffix('.json')}")
        return count
    except Exception as e:
        logger.error(f"Failed to save dataset: {e}")
        return 0

def validate_checksum(filepath: Path) -> bool:
    """Validates the checksum of the downloaded file."""
    if not filepath.exists():
        logger.error(f"File not found for checksum validation: {filepath}")
        return False
    
    # For this task, we assume a known hash or skip if not provided
    # In a real scenario, we would compare against a known hash
    logger.info(f"Checksum validation skipped for {filepath} (no reference hash provided).")
    return True

def main():
    """Main entry point for data download and validation."""
    logger.info("Starting data download process...")
    
    # Fetch dataset
    dataset = fetch_codexglue_dataset()
    if dataset is None:
        # Fallback logic per T005: Do NOT switch to HumanEval/MBPP
        logger.error("CodeXGLUE fetch failed. Per Verified Fallback Protocol, NOT switching to HumanEval/MBPP.")
        logger.error("Failing gracefully with a clear error message.")
        sys.exit(1)
    
    # Save dataset (limit to 500 for this run, adjustable)
    output_path = OUTPUT_DIR / OUTPUT_FILENAME
    sample_count = save_dataset(dataset, output_path, max_samples=500)
    
    if sample_count == 0:
        logger.error("No samples saved. Exiting.")
        sys.exit(1)
    
    # Validate sample size
    reason = "Initial fetch limited to 500 samples for testing." if sample_count < 200 else ""
    if not validate_sample_size(sample_count, reason):
        sys.exit(1)
    
    # Verify baseline exists
    # Load prompt IDs from saved data to check against baseline
    saved_json_path = output_path.with_suffix('.json')
    if saved_json_path.exists():
        with open(saved_json_path, 'r') as f:
            saved_data = json.load(f)
        prompt_ids = [item["prompt_id"] for item in saved_data]
        verify_baseline_exists(prompt_ids)
    
    logger.info("Data download and initial validation completed successfully.")

if __name__ == "__main__":
    main()