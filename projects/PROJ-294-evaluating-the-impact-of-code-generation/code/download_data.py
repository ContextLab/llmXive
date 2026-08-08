import os
import sys
import hashlib
import json
import time
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

# Attempt to import datasets for verified real source
try:
    from datasets import load_dataset
except ImportError:
    raise RuntimeError(
        "The 'datasets' library is required. Install it via: pip install datasets"
    )

# --- Logging Setup (Contract Tolerant) ---
# Must handle: setup_logging(), setup_logging(task_id="..."), setup_logging(level=...)
_logger = None
_task_id = None

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a project logger.
    Handles multiple call signatures:
      - setup_logging()
      - setup_logging(task_id="T011")
      - setup_logging(level=logging.DEBUG)
    """
    global _logger, _task_id

    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(level)

        # Prevent duplicate handlers if called multiple times
        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

        _task_id = task_id

    elif task_id is not None:
        _task_id = task_id

    return _logger

def get_logger() -> logging.Logger:
    if _logger is None:
        return setup_logging()
    return _logger

def log_info(msg: str):
    get_logger().info(msg)

def log_error(msg: str):
    get_logger().error(msg)

# --- Utility Functions ---

def get_file_path(filename: str, subfolder: str = "raw") -> str:
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    return os.path.join(base_dir, subfolder, filename)

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_file_integrity(filepath: str, expected_hash: Optional[str] = None) -> bool:
    if not os.path.exists(filepath):
        return False
    current_hash = compute_sha256(filepath)
    if expected_hash:
        return current_hash == expected_hash
    return True

# --- Data Loading & Processing ---

def download_humaneval(output_path: str) -> int:
    """
    Downloads the HumanEval dataset from HuggingFace using the verified recipe.
    Uses streaming=True to handle large datasets without loading all into RAM.
    Returns the number of records downloaded.
    """
    log_info("Starting HumanEval download from verified source (openai/openai_humaneval)...")
    try:
        # Verified recipe from execution feedback
        ds = load_dataset("openai/openai_humaneval", split="test", streaming=True)
        
        records = []
        count = 0
        
        # Stream and collect records
        for item in ds:
            records.append(item)
            count += 1

        if count == 0:
            raise RuntimeError("Loaded dataset contains zero records")

        log_info(f"Downloaded {count} records.")

        # Save to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

        # Compute and save checksum
        checksum = compute_sha256(output_path)
        checksum_path = output_path + ".sha256"
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        
        log_info(f"Saved data to {output_path} (SHA256: {checksum[:16]}...)")
        return count

    except Exception as e:
        log_error(f"Failed to download HumanEval: {e}")
        raise RuntimeError("Failed to download verified real source") from e

def load_data_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Loads data from a JSONL file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def extract_human_references(data: List[Dict[str, Any]], output_path: str) -> int:
    """
    Extracts solution and test strings into a JSON file.
    Preserves task_id.
    """
    log_info("Extracting human references...")
    references = []
    
    for item in data:
        ref = {
            "task_id": item.get("task_id"),
            "prompt": item.get("prompt"),
            "canonical_solution": item.get("canonical_solution"),
            "test": item.get("test"),
            "entry_point": item.get("entry_point")
        }
        # Ensure task_id exists
        if ref["task_id"] is None:
            log_error(f"Skipping record with missing task_id: {item}")
            continue
        references.append(ref)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(references, f, indent=2)
    
    log_info(f"Saved {len(references)} human references to {output_path}")
    return len(references)

def calculate_quartile_boundaries(data: List[Dict[str, Any]], metric_key: str = "pass_rate") -> Dict[str, float]:
    """
    Calculates Q1, Median, Q3 for a given metric.
    Note: For T011, we are NOT using stratified sampling, but this function
    is kept for API compatibility if other tasks call it.
    """
    values = [item.get(metric_key, 0) for item in data if item.get(metric_key) is not None]
    if not values:
        return {"Q1": 0.0, "Median": 0.0, "Q3": 0.0}
    
    values.sort()
    n = len(values)
    q1_idx = int(n * 0.25)
    med_idx = int(n * 0.5)
    q3_idx = int(n * 0.75)
    
    return {
        "Q1": values[q1_idx],
        "Median": values[med_idx],
        "Q3": values[q3_idx]
    }

def generate_sampling_config(seed: int = 42, n_samples: int = 80) -> Dict[str, Any]:
    """
    Generates a sampling configuration dictionary.
    For T011, we use simple random sampling, not stratified.
    """
    config = {
        "method": "simple_random",
        "seed": seed,
        "n_samples": n_samples,
        # Provide default boundaries to satisfy potential downstream callers expecting keys
        "quartile_boundaries": {
            "Q1": 0.0,
            "Median": 0.0,
            "Q3": 0.0
        }
    }
    return config

def save_sampling_config(config: Dict[str, Any], output_path: str):
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

def perform_stratified_sampling(data: List[Dict[str, Any]], config: Dict[str, Any], output_path: str):
    """
    Performs stratified sampling based on quartile boundaries.
    
    NOTE: T011 requires SIMPLE RANDOM SAMPLING (seed=42, N=80).
    This function is overridden here to delegate to simple random sampling
    if the config indicates 'simple_random', OR it performs stratified if needed
    by other tasks.
    
    The execution error showed: KeyError: 'quartile_boundaries'.
    We ensure the config always has this key (see generate_sampling_config).
    """
    method = config.get("method", "simple_random")
    
    if method == "simple_random":
        seed = config.get("seed", 42)
        n_samples = config.get("n_samples", 80)
        
        log_info(f"Performing simple random sampling: seed={seed}, n={n_samples}")
        random.seed(seed)
        
        # Shuffle and slice
        shuffled = data.copy()
        random.shuffle(shuffled)
        subset = shuffled[:n_samples]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subset, f, indent=2)
        
        log_info(f"Saved {len(subset)} samples to {output_path}")
        return
    
    # Fallback to stratified if explicitly requested (though T011 doesn't use it)
    boundaries = config.get("quartile_boundaries")
    if not boundaries:
        # Calculate if missing
        boundaries = calculate_quartile_boundaries(data)
        config["quartile_boundaries"] = boundaries
        save_sampling_config(config, output_path.replace(".json", "_config.json"))
    
    # Stratified logic (simplified for robustness)
    q1 = boundaries['Q1']
    q3 = boundaries['Q3']
    
    strata = {
        "low": [],
        "mid": [],
        "high": []
    }
    
    for item in data:
        val = item.get("pass_rate", 0)
        if val <= q1:
            strata["low"].append(item)
        elif val <= q3:
            strata["mid"].append(item)
        else:
            strata["high"].append(item)
    
    # Distribute N samples proportionally
    total = len(data)
    result = []
    n_samples = config.get("n_samples", 80)
    
    for key, items in strata.items():
        if not items:
            continue
        count = int((len(items) / total) * n_samples)
        if count == 0 and len(items) > 0 and sum(1 for _, s in strata.items() if len(s) > 0) > 1:
            count = 1 # Ensure at least 1 if possible
        result.extend(items[:count])
    
    # Fill remainder if needed
    while len(result) < n_samples:
        # Add random from remaining
        remaining = [i for i in data if i not in result]
        if not remaining:
            break
        random.seed(config.get("seed", 42))
        result.append(random.choice(remaining))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    log_info(f"Saved {len(result)} stratified samples to {output_path}")

def main():
    """
    Main entry point for T010, T010b, and T011.
    1. Download HumanEval (T010)
    2. Extract References (T010b)
    3. Select Subset (T011)
    """
    setup_logging(task_id="T010-T011")
    
    # Paths
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    raw_data_path = get_file_path("humaneval_test.jsonl", subfolder="raw")
    references_path = get_file_path("human_references.json", subfolder="raw")
    subset_path = get_file_path("sampled_subset.json", subfolder="raw")
    
    # T010: Download (if not exists)
    if not os.path.exists(raw_data_path):
        download_humaneval(raw_data_path)
    else:
        log_info(f"Raw data already exists at {raw_data_path}")
    
    # T010b: Extract References (if not exists)
    if not os.path.exists(references_path):
        data = load_data_from_file(raw_data_path)
        extract_human_references(data, references_path)
    else:
        log_info(f"References already exist at {references_path}")
    
    # T011: Select Subset
    # Load data for sampling
    log_info("Loading downloaded data for sampling...")
    data = load_data_from_file(raw_data_path)
    
    # Generate config for T011 (Simple Random, Seed 42, N=80)
    config = generate_sampling_config(seed=42, n_samples=80)
    save_sampling_config(config, get_file_path("sampling_config.json", subfolder="raw"))
    
    # Perform sampling
    # Note: perform_stratified_sampling now handles 'simple_random' method internally
    perform_stratified_sampling(data, config, subset_path)
    
    log_info("T010, T010b, T011 completed successfully.")

if __name__ == "__main__":
    main()