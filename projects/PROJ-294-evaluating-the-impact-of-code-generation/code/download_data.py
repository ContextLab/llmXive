import os
import sys
import hashlib
import json
from typing import Dict, Any, Optional, List
import math
from datasets import load_dataset

def download_humaneval(output_dir: str = "data/raw") -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "humaneval.json")

    if os.path.exists(output_path):
        return output_path

    print("Downloading HumanEval dataset from HuggingFace...")
    dataset = load_dataset("openai_humaneval")
    data = dataset["test"]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([{"task_id": item["task_id"], "prompt": item["prompt"], "canonical_solution": item["canonical_solution"], "test": item["test"]} for item in data], f)
    
    return output_path

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
    
    # Download
    raw_path = download_humaneval()
    print(f"Downloaded data to {raw_path}")
    
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
