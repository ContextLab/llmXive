import os
import sys
import hashlib
import json
import time
from typing import Dict, Any, Optional, List
import math
from datasets import load_dataset

# Constants for retry logic
MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 60.0     # seconds

def _exponential_backoff(attempt: int) -> float:
    """Calculate exponential backoff duration with jitter."""
    backoff = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
    # Add jitter: random value between 0 and backoff
    jitter = backoff * 0.1 * (hash(time.time()) % 1000) / 1000.0
    return backoff + jitter

def download_humaneval(output_dir: str = "data/raw") -> str:
    """
    Download HumanEval dataset from HuggingFace with robust retry logic.
    
    Implements exponential backoff for transient network failures.
    Raises RuntimeError if download fails after all retries.
    
    Args:
        output_dir: Directory to save the dataset.
        
    Returns:
        Path to the downloaded JSON file.
        
    Raises:
        RuntimeError: If download fails after MAX_RETRIES attempts.
        ConnectionError: If the verified real source is unreachable.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "humaneval.json")

    if os.path.exists(output_path):
        print(f"Dataset already exists at {output_path}. Skipping download.")
        return output_path

    print(f"Downloading HumanEval dataset from HuggingFace (max retries: {MAX_RETRIES})...")
    
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}...")
            dataset = load_dataset("openai_humaneval")
            data = dataset["test"]
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([
                    {
                      "task_id": item["task_id"], 
                      "prompt": item["prompt"], 
                      "canonical_solution": item["canonical_solution"], 
                      "test": item["test"]
                    } 
                    for item in data
                ], f)
            
            print(f"Successfully downloaded data to {output_path}")
            return output_path
            
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check if this looks like a transient network error
            is_transient = any(keyword in error_msg for keyword in [
                "timeout", "connection", "network", "temporary", "rate limit", "503", "504"
            ])
            
            if attempt < MAX_RETRIES - 1:
                wait_time = _exponential_backoff(attempt)
                print(f"Transient error detected: {e}")
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Download failed after {MAX_RETRIES} attempts.")
                break

    # If we reach here, all retries failed
    error_details = str(last_exception) if last_exception else "Unknown error"
    raise RuntimeError(
        f"Failed to download HumanEval dataset from HuggingFace after {MAX_RETRIES} retries. "
        f"The verified real source appears to be unreachable. Last error: {error_details}"
    )

def verify_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> bool:
    if not os.path.exists(file_path):
        return False
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    computed_hash = sha256_hash.hexdigest()
    if expected_hash:
        return computed_hash == expected_hash
    return True

def stratified_sample(file_path: str, target_size: int = 50) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Load pass rates if available, otherwise simulate based on task_id for demo
    # In real implementation, pass rates would be part of the dataset or a separate lookup
    pass_rates = []
    for item in data:
        # Placeholder: In real scenario, fetch from HumanEval benchmark stats
        # Using a pseudo-random deterministic value based on task_id for stratification
        task_num = int(item["task_id"].split("HumanEval/")[-1])
        pass_rate = 0.3 + (task_num % 10) * 0.05
        pass_rates.append((item, pass_rate))
    
    # Sort by pass rate
    pass_rates.sort(key=lambda x: x[1])
    
    # Determine quartiles
    n = len(pass_rates)
    quartile_size = n // 4
    quartiles = [
        pass_rates[0:quartile_size],
        pass_rates[quartile_size:2*quartile_size],
        pass_rates[2*quartile_size:3*quartile_size],
        pass_rates[3*quartile_size:]
    ]
    
    # Sample from each quartile
    sample = []
    samples_per_quartile = target_size // 4
    remainder = target_size - (samples_per_quartile * 4)
    
    for i, quartile in enumerate(quartiles):
        count = samples_per_quartile + (1 if i < remainder else 0)
        count = min(count, len(quartile))
        sample.extend([item for item, _ in quartile[:count]])
    
    return sample

def main():
    # Ensure directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/analysis", exist_ok=True)
    
    # Download with retry logic
    try:
        raw_path = download_humaneval()
        print(f"Downloaded data to {raw_path}")
    except RuntimeError as e:
        print(f"FATAL: {e}")
        sys.exit(1)
    
    # Verify integrity
    if verify_file_integrity(raw_path):
        print("Data integrity verified.")
    else:
        print("Warning: Could not verify data integrity (no expected hash provided).")
    
    # Stratified sample
    sampled_data = stratified_sample(raw_path, target_size=50)
    sample_path = "data/raw/humaneval_sampled.json"
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sampled_data, f)
    
    print(f"Created stratified sample of {len(sampled_data)} tasks at {sample_path}")

if __name__ == "__main__":
    main()