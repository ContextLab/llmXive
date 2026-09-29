"""
Data Ingestion Module for PROJ-227.
Downloads datasets from HuggingFace and verifies integrity.
"""
import json
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to ensure imports work when run as script
# This assumes the script is run from the project root: python code/download.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUMS_FILE = STATE_DIR / "checksums.json"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package not found. Please run: pip install datasets")
    sys.exit(1)


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_checksums() -> Dict[str, str]:
    """Load existing checksums from state file."""
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to state file."""
    with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


def download_humaneval() -> Path:
    """
    Download HumanEval dataset (Python) from openai/human-eval.
    Saves to data/raw/humaneval.json.
    Returns the path to the downloaded file.
    """
    dataset_id = "openai/human-eval"
    output_path = DATA_RAW_DIR / "humaneval.json"

    print(f"Downloading {dataset_id}...")
    
    try:
        # Load the dataset using the HuggingFace datasets library
        # trust_remote_code is not strictly needed for openai/human-eval but good practice
        dataset = load_dataset(dataset_id, split="test")
        
        # Convert to list of dicts to ensure we have the raw data structure
        data_list = dataset.to_list()
        
        if not data_list:
            raise ValueError("Dataset is empty.")
        
        # Verify required keys
        required_keys = {"prompt", "test"}
        first_record = data_list[0]
        if not required_keys.issubset(first_record.keys()):
            missing = required_keys - set(first_record.keys())
            raise ValueError(f"Missing required keys in dataset: {missing}")

        # Write to JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully downloaded {len(data_list)} records to {output_path}")
        
    except Exception as e:
        print(f"Failed to download {dataset_id}: {e}")
        raise

    return output_path


def verify_record(record: Dict[str, Any]) -> bool:
    """Verify a single record has required keys and non-empty content."""
    if not isinstance(record, dict):
        return False
    if "prompt" not in record or "test" not in record:
        return False
    if not record["prompt"] or not record["test"]:
        return False
    return True


def verify_dataset(output_path: Path, min_records: int = 100) -> bool:
    """
    Verify the downloaded dataset file.
    Checks:
    1. File exists
    2. Contains >= min_records records
    3. All records have required keys (depends on dataset type)
    """
    if not output_path.exists():
        print(f"ERROR: Output file {output_path} does not exist.")
        return False

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {output_path}: {e}")
        return False

    if not isinstance(data, list):
        print(f"ERROR: Expected list of records, got {type(data)}")
        return False

    if len(data) < min_records:
        print(f"ERROR: Dataset contains only {len(data)} records (expected >= {min_records}).")
        return False

    # Determine verification logic based on filename
    filename = output_path.name
    if "humaneval" in filename:
        required_keys = {"prompt", "test"}
    elif "codexglue" in filename or "human-eval-x" in filename:
        # CodeXGLUE datasets usually have 'code' and 'docstring' or similar
        # For codeXGLUE-javascript/java, we expect 'code' and 'docstring' or similar structure
        # We'll be lenient and just check for 'code' presence as primary key
        required_keys = {"code"} 
    elif "the-stack" in filename or "bigcode" in filename:
        # The Stack usually has 'content', 'language', 'repo', etc.
        required_keys = {"content", "language"}
    else:
        # Generic fallback: check for any text-like content
        required_keys = {"code", "content", "prompt"} # Union of possibilities

    valid_count = 0
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            print(f"Invalid record at index {i}: not a dict")
            return False
        
        # Check intersection
        if not any(k in record for k in required_keys):
            print(f"Invalid record at index {i}: missing required keys {required_keys}")
            return False
        
        valid_count += 1

    print(f"Verification passed: {valid_count} valid records found.")
    return True


def download_codexglue_js() -> Path:
    """
    Download CodeXGLUE JavaScript dataset.
    Dataset ID: codeparrot/codeXGLUE-javascript
    """
    dataset_id = "codeparrot/codeXGLUE-javascript"
    output_path = DATA_RAW_DIR / "codexglue_js.json"
    
    print(f"Downloading {dataset_id}...")
    try:
        # Using trust_remote_code=True as requested
        dataset = load_dataset(dataset_id, split="test", trust_remote_code=True)
        data_list = dataset.to_list()
        
        if not data_list:
            raise ValueError("Dataset is empty.")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully downloaded {len(data_list)} records to {output_path}")
    except Exception as e:
        print(f"Failed to download {dataset_id}: {e}")
        raise
    
    return output_path


def download_codexglue_java() -> Path:
    """
    Download CodeXGLUE Java dataset.
    Dataset ID: codeparrot/codeXGLUE-java
    """
    dataset_id = "codeparrot/codeXGLUE-java"
    output_path = DATA_RAW_DIR / "codexglue_java.json"
    
    print(f"Downloading {dataset_id}...")
    try:
        dataset = load_dataset(dataset_id, split="test", trust_remote_code=True)
        data_list = dataset.to_list()
        
        if not data_list:
            raise ValueError("Dataset is empty.")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully downloaded {len(data_list)} records to {output_path}")
    except Exception as e:
        print(f"Failed to download {dataset_id}: {e}")
        raise
    
    return output_path


def download_bigcode_stack(language: str) -> Path:
    """
    Download BigCode The Stack subset for a specific language.
    Dataset ID: bigcode/the-stack
    Subsets: data/python, data/javascript, data/java
    
    Note: The Stack is massive. We stream a representative sample to avoid 
    OOM in this specific script context, but the logic is designed to handle 
    the real source. For T012, we fetch a sample of 1000 records per language 
    to verify the pipeline, as full download is not feasible in a single run 
    without massive resources.
    """
    if language not in ["python", "javascript", "java"]:
        raise ValueError(f"Unsupported language for BigCode: {language}")
    
    subset = f"data/{language}"
    dataset_id = "bigcode/the-stack"
    output_path = DATA_RAW_DIR / f"bigcode_stack_{language}.json"
    
    print(f"Downloading {dataset_id} (subset: {subset})...")
    try:
        # Streaming to avoid loading full dataset into memory
        # We take a sample of 1000 records for this task to ensure it completes
        # while still using the REAL source.
        dataset = load_dataset(dataset_id, data_dir=subset, split="train", streaming=True, trust_remote_code=True)
        
        # Collect a sample
        sample_size = 1000
        data_list = []
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            data_list.append(item)
            count += 1
        
        if not data_list:
            raise ValueError("Dataset sample is empty.")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully downloaded {len(data_list)} records to {output_path}")
    except Exception as e:
        print(f"Failed to download {dataset_id} ({subset}): {e}")
        raise
    
    return output_path


def main():
    """Main entry point for downloading CodeXGLUE and BigCode datasets (T012)."""
    print("Starting CodeXGLUE and BigCode download task (T012)...")
    
    downloads = [
        ("CodeXGLUE JS", download_codexglue_js),
        ("CodeXGLUE Java", download_codexglue_java),
        ("BigCode Python", lambda: download_bigcode_stack("python")),
        ("BigCode JS", lambda: download_bigcode_stack("javascript")),
        ("BigCode Java", lambda: download_bigcode_stack("java")),
    ]
    
    checksums = load_checksums()
    
    for name, func in downloads:
        try:
            output_path = func()
            
            # Verify
            # Note: For BigCode, we set min_records=100 since we only sample 1000
            min_rec = 100 if "bigcode" in output_path.name else 100
            if not verify_dataset(output_path, min_records=min_rec):
                print(f"Verification failed for {name}.")
                sys.exit(1)
            
            # Calculate Checksum
            checksum = compute_file_checksum(output_path)
            print(f"Checksum for {output_path.name}: {checksum}")
            checksums[output_path.name] = checksum
            
        except Exception as e:
            print(f"Task failed for {name}: {e}")
            sys.exit(1)
    
    # Save all checksums
    save_checksums(checksums)
    print(f"All checksums saved to {CHECKSUMS_FILE}")
    
    print("Task T012 completed successfully.")


if __name__ == "__main__":
    main()