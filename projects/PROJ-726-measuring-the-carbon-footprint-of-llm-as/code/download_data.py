import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def fetch_codexglue_dataset(sample_size: int = 200) -> List[Dict[str, Any]]:
    """
    Fetches the CodeXGLUE Python code-generation dataset subset.
    Samples up to `sample_size` prompts.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via pip.")
        raise

    logger.info(f"Fetching CodeXGLUE Python code-generation dataset (sample size: {sample_size})...")
    
    # Load the dataset
    # Using the 'code_x_glue_ct_code_to_code' dataset specifically for Python code generation
    # The specific subset for 'python' code generation is usually under 'code_x_glue_ct_code_to_code'
    # or 'code_x_glue_ct_text_to_code'. We use the standard CodeXGLUE python source.
    ds = load_dataset("code_x_glue_ct_text_to_code", "python", split="train", streaming=True)
    
    sample = []
    count = 0
    
    for item in ds:
        if count >= sample_size:
            break
        
        # Filter for valid prompts (non-empty text)
        if 'text' in item and item['text'] and len(item['text'].strip()) > 0:
            sample.append({
                "prompt_id": f"prompt_{count}",
                "text": item['text'],
                "source": "codexglue_python"
            })
            count += 1
    
    if count == 0:
        logger.error("Failed to retrieve any valid prompts from the dataset.")
        raise ValueError("No valid prompts found in the dataset.")
    
    logger.info(f"Successfully sampled {count} prompts from CodeXGLUE.")
    return sample

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    logger.info(f"Computing SHA-256 hash for: {file_path}")
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def validate_sample_size(actual_count: int, target: int) -> bool:
    """
    Validates if the actual sample size meets the target or explains reduction.
    """
    if actual_count >= target:
        return True
    else:
        logger.warning(f"Sample size ({actual_count}) is less than target ({target}).")
        logger.warning(f"Reason: The dataset may have fewer than {target} valid entries, or streaming limit was reached.")
        return True  # Allow running if we got something, but log the warning

def verify_baseline_exists(baseline_path: Path) -> bool:
    """
    Checks if the human baseline file exists.
    """
    if baseline_path.exists():
        logger.info(f"Baseline file found: {baseline_path}")
        return True
    else:
        logger.warning(f"Baseline file not found: {baseline_path}")
        return False

def save_dataset(data: List[Dict], output_path: Path) -> None:
    """
    Saves the dataset to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Dataset saved to: {output_path}")

def validate_checksum(file_path: Path, expected_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates the checksum of the downloaded raw data.
    
    If `expected_hash` is provided, compares against it.
    If not provided, computes the hash and logs it for future reference.
    Returns a dictionary with 'status' (valid/invalid/unknown), 'computed_hash', and 'message'.
    """
    if not file_path.exists():
        return {
            "status": "error",
            "computed_hash": None,
            "message": f"File not found: {file_path}"
        }
    
    try:
        computed_hash = compute_file_hash(file_path)
    except Exception as e:
        return {
            "status": "error",
            "computed_hash": None,
            "message": f"Error computing hash: {str(e)}"
        }
    
    if expected_hash:
        if computed_hash == expected_hash:
            logger.info(f"Checksum validation PASSED for {file_path}.")
            return {
                "status": "valid",
                "computed_hash": computed_hash,
                "message": "Checksum matches expected value."
            }
        else:
            logger.error(f"Checksum validation FAILED for {file_path}.")
            logger.error(f"Expected: {expected_hash}")
            logger.error(f"Computed: {computed_hash}")
            return {
                "status": "invalid",
                "computed_hash": computed_hash,
                "message": "Checksum mismatch!"
            }
    else:
        logger.info(f"Checksum computed for {file_path} (no expected hash provided for comparison): {computed_hash}")
        return {
            "status": "unknown",
            "computed_hash": computed_hash,
            "message": "Checksum computed but no reference hash provided for validation."
        }

def main():
    """
    Main execution flow for downloading data and validating checksums.
    """
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data" / "raw"
    output_file = data_dir / "codexglue_sample.json"
    checksum_file = data_dir / "codexglue_sample.sha256"
    
    # Step 1: Fetch data
    if not output_file.exists():
        logger.info("Dataset file not found. Fetching new data...")
        data = fetch_codexglue_dataset(sample_size=200)
        validate_sample_size(len(data), 200)
        save_dataset(data, output_file)
    else:
        logger.info(f"Dataset file already exists: {output_file}")
    
    # Step 2: Compute and save checksum if it doesn't exist
    if not checksum_file.exists():
        logger.info("Computing checksum for the downloaded file...")
        hash_val = compute_file_hash(output_file)
        checksum_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_file, "w") as f:
            f.write(f"{hash_val}  {output_file.name}\n")
        logger.info(f"Checksum saved to: {checksum_file}")
    else:
        logger.info(f"Checksum file already exists: {checksum_file}")
    
    # Step 3: Validate checksum
    # Read expected hash from file
    expected_hash = None
    if checksum_file.exists():
        with open(checksum_file, "r") as f:
            line = f.readline().strip()
            # Format: "hash  filename"
            parts = line.split()
            if len(parts) >= 1:
                expected_hash = parts[0]
    
    validation_result = validate_checksum(output_file, expected_hash)
    
    if validation_result["status"] == "invalid":
        logger.error("Data integrity check failed. The downloaded file may be corrupted.")
        sys.exit(1)
    elif validation_result["status"] == "valid":
        logger.info("Data integrity check passed.")
    else:
        logger.warning("Data integrity check inconclusive (no reference hash).")
    
    return validation_result

if __name__ == "__main__":
    main()