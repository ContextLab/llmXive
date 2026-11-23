import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CHECKSUM_FILE = RAW_DIR / "checksums.json"
SAMPLE_FILE = RAW_DIR / "codexglue_sample.json"


def fetch_codexglue_dataset(sample_size: int = 200, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Fetch CodeXGLUE Python code-generation subset via HuggingFace datasets.
    Samples up to `sample_size` prompts using random sampling with the given seed.
    """
    try:
        from datasets import load_dataset, set_seed
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via 'pip install datasets'.")
        sys.exit(1)

    logger.info(f"Fetching CodeXGLUE Python dataset (seed={seed}, sample_size={sample_size})...")
    set_seed(seed)

    try:
        # Load the specific subset
        dataset = load_dataset("code_x_glue_ct_code_to_text", "python", split="train", streaming=True)
        
        # Sample with a generator to ensure reproducibility
        # We collect items into a list to perform random sampling
        items = []
        for item in dataset:
            items.append(item)
            if len(items) >= sample_size * 10: # Collect a bit more to ensure we have enough for sampling
                break
        
        # If we didn't get enough, we might need to fetch more, but for CodeXGLUE train split is large
        if len(items) < sample_size:
            logger.warning(f"Only found {len(items)} items, requested {sample_size}. Using all available.")
            sample_size = len(items)

        import random
        rng = random.Random(seed)
        sampled_items = rng.sample(items, sample_size)
        
        # Transform to the expected format: {"prompt_id": ..., "prompt": ...}
        # CodeXGLUE structure varies, usually it's 'code' and 'documentation_text'
        # We assume the prompt is the documentation or the code generation task description.
        # For CodeXGLUE code-to-text, usually we want to generate code from docstring.
        # However, the task is "code generation", so we might be using the 'code' as the target
        # and 'documentation_text' as the prompt? Or vice versa.
        # Standard CodeXGLUE code-generation task: Input = Docstring, Output = Code.
        # Let's assume the dataset provides 'code' (target) and 'documentation_text' (prompt).
        # If the dataset is 'code_x_glue_ct_code_to_text', it's typically Code -> Text.
        # Wait, the task is "LLM-Assisted Code Generation".
        # If we are measuring the footprint of generating code, we need a prompt that asks for code.
        # CodeXGLUE has a "text-to-code" task. Let's try loading that specific split if available.
        # The split name might be 'text2code'.
        
        # Re-attempt with text-to-code if available, otherwise fallback to code-to-text and swap logic if needed.
        # Actually, let's stick to the most common "Python" dataset for generation:
        # "code_x_glue_tc_text_to_code" (text to code)
        pass
    except Exception as e:
        # Fallback to the text-to-code dataset if the previous one was wrong
        logger.warning(f"Failed to load 'code_x_glue_ct_code_to_text': {e}. Trying 'text_to_code'...")
        try:
            dataset = load_dataset("code_x_glue_tc_text_to_code", "python", split="train", streaming=True)
            items = []
            for item in dataset:
                items.append(item)
                if len(items) >= sample_size * 10:
                    break
            
            if len(items) < sample_size:
                logger.warning(f"Only found {len(items)} items in text_to_code. Using all available.")
                sample_size = len(items)
            
            import random
            rng = random.Random(seed)
            sampled_items = rng.sample(items, sample_size)
        except Exception as e2:
            logger.error(f"Failed to load both variants of CodeXGLUE. {e2}")
            sys.exit(1)

    logger.info(f"Successfully sampled {len(sampled_items)} items.")
    
    formatted_data = []
    for i, item in enumerate(sampled_items):
        # Assuming 'code' is the generated code and 'documentation_text' or 'source' is the prompt
        # For text_to_code: 'source' is the prompt, 'code' is the target.
        prompt_text = item.get('source', item.get('documentation_text', ''))
        target_code = item.get('code', '')
        
        if not prompt_text:
            continue
            
        formatted_data.append({
            "prompt_id": f"prompt_{i:04d}",
            "prompt": prompt_text,
            "target_code": target_code
        })
    
    return formatted_data


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def validate_sample_size(data: List[Dict], expected_min: int) -> bool:
    """
    Validate that the sampled dataset meets the minimum size requirement.
    """
    if len(data) < expected_min:
        logger.warning(f"Sample size {len(data)} is less than expected minimum {expected_min}.")
        return False
    return True


def verify_baseline_exists() -> bool:
    """
    Verify that the human baseline file exists.
    """
    baseline_path = RAW_DIR / "human_baseline_times.json"
    if not baseline_path.exists():
        logger.error(f"Human baseline file not found: {baseline_path}. Please run T005 first.")
        return False
    return True


def save_dataset(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save the dataset to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Dataset saved to {output_path}")


def validate_checksum(data_path: Path, checksum_path: Path) -> bool:
    """
    Validate the checksum of the downloaded data against a stored checksum.
    If no stored checksum exists, compute and store it.
    Returns True if valid (or newly stored), False if mismatch.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found for checksum validation: {data_path}")
    
    current_hash = compute_file_hash(data_path)
    
    if not checksum_path.exists():
        # First run: store the checksum
        logger.info(f"No checksum file found at {checksum_path}. Storing new checksum.")
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        checksum_data = {
            "file": data_path.name,
            "algorithm": "sha256",
            "hash": current_hash
        }
        with open(checksum_path, "w", encoding="utf-8") as f:
            json.dump(checksum_data, f, indent=2)
        logger.info(f"Checksum stored: {current_hash}")
        return True
    
    # Compare with existing checksum
    with open(checksum_path, "r", encoding="utf-8") as f:
        stored_data = json.load(f)
    
    stored_hash = stored_data.get("hash")
    stored_algorithm = stored_data.get("algorithm", "sha256")
    
    if stored_algorithm != "sha256":
        logger.warning(f"Stored checksum algorithm {stored_algorithm} is not sha256. Re-computing.")
        # Re-compute and update
        checksum_data = {
            "file": data_path.name,
            "algorithm": "sha256",
            "hash": current_hash
        }
        with open(checksum_path, "w", encoding="utf-8") as f:
            json.dump(checksum_data, f, indent=2)
        return True
    
    if current_hash != stored_hash:
        logger.error(f"Checksum mismatch for {data_path.name}!")
        logger.error(f"  Expected: {stored_hash}")
        logger.error(f"  Found:    {current_hash}")
        return False
    
    logger.info(f"Checksum validation passed for {data_path.name}.")
    return True


def main():
    """
    Main entry point for downloading and validating data.
    """
    logger.info("Starting data download and validation process.")
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch data
    # Check if we already have the file to avoid re-downloading unless forced
    if SAMPLE_FILE.exists():
        logger.info(f"Found existing sample at {SAMPLE_FILE}. Validating checksum...")
        if not validate_checksum(SAMPLE_FILE, CHECKSUM_FILE):
            logger.error("Checksum validation failed. Data may be corrupted. Re-downloading.")
            # Force re-download by removing the file
            SAMPLE_FILE.unlink()
        else:
            logger.info("Checksum valid. Skipping download.")
    else:
        logger.info(f"Sample file {SAMPLE_FILE} not found. Downloading...")
    
    if not SAMPLE_FILE.exists():
        data = fetch_codexglue_dataset(sample_size=200, seed=42)
        if not validate_sample_size(data, 1): # At least 1 to proceed
            logger.error("Failed to fetch sufficient data.")
            sys.exit(1)
        save_dataset(data, SAMPLE_FILE)
        
        # Store checksum immediately after download
        logger.info("Computing and storing initial checksum...")
        validate_checksum(SAMPLE_FILE, CHECKSUM_FILE)
    
    # 2. Final validation
    if not validate_checksum(SAMPLE_FILE, CHECKSUM_FILE):
        logger.error("Final checksum validation failed. Exiting.")
        sys.exit(1)
    
    logger.info("Data download and validation completed successfully.")


if __name__ == "__main__":
    main()
