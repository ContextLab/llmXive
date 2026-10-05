import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def fetch_codexglue_dataset(sample_size: int = 200) -> Dict[str, Any]:
    """
    Fetches the CodeXGLUE Python code-generation subset via HuggingFace datasets.
    Samples up to `sample_size` prompts.
    
    Returns a dictionary with 'prompt_id' and 'code' keys.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via pip.")
        raise

    logger.info(f"Fetching CodeXGLUE dataset (Python code-generation) with sample size {sample_size}...")
    
    try:
        # Load the specific CodeXGLUE subset
        dataset = load_dataset(
            "code_x_glue_ct_code_to_text", 
            "python", 
            split="train",
            streaming=True
        )
        
        # Sample the dataset
        sampled_data = []
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            
            # Extract prompt (docstring) and code
            # The dataset structure varies, but typically 'docstring' is the prompt
            # and 'code' is the target. For code-generation, we often use the docstring as prompt.
            if 'docstring' in item and 'code' in item:
                prompt_id = f"codexglue_{count}"
                prompt_text = item['docstring']
                
                # Ensure we have valid data
                if prompt_text and len(prompt_text.strip()) > 0:
                    sampled_data.append({
                        "prompt_id": prompt_id,
                        "prompt": prompt_text,
                        "reference_code": item['code']
                    })
                    count += 1
            
            # If the dataset structure is different, try to adapt
            elif 'text' in item:
                # Fallback for different dataset versions
                prompt_id = f"codexglue_{count}"
                sampled_data.append({
                    "prompt_id": prompt_id,
                    "prompt": item['text'],
                    "reference_code": "" # Reference might not be available in all splits
                })
                count += 1

        if count < sample_size:
            logger.warning(f"Only fetched {count} samples, requested {sample_size}.")
        
        logger.info(f"Successfully fetched {len(sampled_data)} samples from CodeXGLUE.")
        return {"samples": sampled_data, "count": len(sampled_data)}
        
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file using the specified algorithm.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_sample_size(data: Dict[str, Any], min_size: int = 1) -> bool:
    """
    Validates that the downloaded data meets the minimum sample size requirement.
    """
    count = data.get("count", 0)
    if count < min_size:
        logger.error(f"Sample size {count} is less than required minimum {min_size}.")
        return False
    return True

def verify_baseline_exists(baseline_path: Path) -> bool:
    """
    Checks if the human baseline file exists.
    This is a prerequisite check for downstream tasks.
    """
    if not baseline_path.exists():
        logger.warning(f"Baseline file not found at {baseline_path}. "
                       "This may indicate T005 has not been run or the file is missing.")
        return False
    return True

def save_dataset(data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the dataset to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Dataset saved to {output_path}")

def validate_checksum(input_path: Path, expected_hash_path: Optional[Path] = None) -> bool:
    """
    Validates the checksum of the downloaded raw data.
    
    If `expected_hash_path` is provided, it compares against the stored hash.
    If not, it computes and logs the hash for future verification.
    
    Returns True if validation passes or if no expected hash exists (logging only).
    Returns False if the hash does not match.
    """
    if not input_path.exists():
        logger.error(f"Cannot validate checksum: File not found at {input_path}")
        return False

    computed_hash = compute_file_hash(input_path)
    logger.info(f"Computed checksum for {input_path.name}: {computed_hash}")

    if expected_hash_path and expected_hash_path.exists():
        try:
            with open(expected_hash_path, "r", encoding="utf-8") as f:
                stored_hash = f.read().strip()
            
            if computed_hash != stored_hash:
                logger.error(f"Checksum mismatch for {input_path.name}!")
                logger.error(f"  Expected: {stored_hash}")
                logger.error(f"  Computed: {computed_hash}")
                return False
            else:
                logger.info(f"Checksum validation PASSED for {input_path.name}.")
                return True
        except Exception as e:
            logger.error(f"Error reading stored checksum: {e}")
            return False
    else:
        logger.info(f"No stored checksum found at {expected_hash_path}. "
                    "Computed hash logged for future verification.")
        # Create the hash file if it doesn't exist for future runs
        if expected_hash_path:
            try:
                expected_hash_path.parent.mkdir(parents=True, exist_ok=True)
                with open(expected_hash_path, "w", encoding="utf-8") as f:
                    f.write(computed_hash)
                logger.info(f"Stored checksum at {expected_hash_path} for future validation.")
            except Exception as e:
                logger.warning(f"Could not store checksum: {e}")
        
        return True

def main():
    """
    Main entry point for downloading data and validating checksums.
    """
    # Configuration
    base_dir = Path(__file__).parent.parent
    data_raw_dir = base_dir / "data" / "raw"
    output_file = data_raw_dir / "codexglue_sample.json"
    checksum_file = data_raw_dir / "codexglue_sample.sha256"
    baseline_file = data_raw_dir / "human_baseline_times.json"
    
    sample_size = 200

    # 1. Fetch Data
    try:
        data = fetch_codexglue_dataset(sample_size)
    except Exception as e:
        logger.critical(f"Data fetching failed: {e}")
        sys.exit(1)

    # 2. Validate Sample Size
    if not validate_sample_size(data, min_size=1):
        logger.critical("Sample size validation failed.")
        sys.exit(1)

    # 3. Save Data
    save_dataset(data, output_file)

    # 4. Validate Checksum
    # We validate immediately after saving to ensure integrity of the write
    if not validate_checksum(output_file, checksum_file):
        logger.critical("Checksum validation failed.")
        sys.exit(1)

    # 5. Verify Baseline (Optional but recommended for pipeline integrity)
    verify_baseline_exists(baseline_file)

    logger.info("Data download and checksum validation completed successfully.")

if __name__ == "__main__":
    main()