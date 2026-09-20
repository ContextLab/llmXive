"""
Download script for the S-AgentK dataset.
Fetches data from HuggingFace Hub.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str):
    """Verify file checksum."""
    actual_checksum = compute_sha256(file_path)
    if actual_checksum != expected_checksum:
        raise ValueError(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")

def download_dataset():
    """Download the S-AgentK dataset from HuggingFace Hub."""
    config = Config()
    logger = config.logger
    
    # Using a verified real data source as per instructions
    # Since the specific dataset 'llmXive/S-AgentK' was reported as missing in the error log,
    # we must use a real, available dataset that matches the schema or a verified source.
    # However, the task requires "Real data only". 
    # If the specified dataset is truly missing, we must fail loudly.
    # BUT, the error log says "Dataset llmXive/S-AgentK not found".
    # To make this runnable on REAL data, we will attempt to fetch a known public dataset 
    # that fits the spatial reasoning schema if the specific one is missing, 
    # OR we strictly follow the "Fail Loudly" rule if the SPEC requires this exact dataset.
    # The prompt says: "If the dataset (not individual scenes) is missing or corrupted, raise FileNotFoundError".
    # Since the execution failed because it was not found, and we cannot fake it,
    # we must assume the dataset name in the code was incorrect or the dataset is private.
    # However, to provide a WORKING implementation that fetches REAL data, 
    # we will switch to a known public dataset 'llmXive/s-agent-spatial-reasoning' if available,
    # or a generic placeholder if we cannot find a real one. 
    # Given the constraints, I will use a standard public dataset that has spatial reasoning tasks
    # if the specific one is unavailable, but the code MUST fail if it can't find ANY valid source.
    
    # For this implementation, we assume a dataset 'llmXive/S-AgentK' is the target.
    # If it doesn't exist, we raise an error as per spec.
    # To make the code run for the user who has this task, I will use a known public dataset 
    # that is similar: 'llmXive/spatial-reasoning-benchmark' or similar.
    # However, without a verified source in the prompt, I must use the one in the error log 
    # and let it fail, OR use a real one I know exists.
    # I will use 'llmXive/S-AgentK' and let it fail loudly if not found, as per strict instructions.
    # WAIT: The instruction says "If no real source is reachable, return verdict: failed".
    # But I am implementing code. I must write code that tries to fetch REAL data.
    # I will use a real dataset that is known to exist: 'llmXive/spatial-reasoning-samples' 
    # (hypothetical) or a real one like 'huggingface/datasets' if available.
    # Actually, to be safe and compliant with "Real data only", I will use a dataset 
    # that is guaranteed to exist: 'llmXive/s-agent-k-spatial' (if it exists) or fallback to 
    # a known public one like 'allenai/spatial-benchmark'.
    # Since I cannot verify existence at runtime without the library, I will write the code
    # to fetch from HuggingFace and let the runtime error handle the "not found" case.
    
    dataset_id = "llmXive/S-AgentK" # As per the error log, this is what was expected.
    
    try:
        from huggingface_hub import hf_hub_download, HfApi
        api = HfApi()
        
        # Check if repo exists
        try:
            api.repo_info(repo_id=dataset_id)
        except Exception:
            raise FileNotFoundError(f"Dataset {dataset_id} not found at HuggingFace Hub")
        
        # Download the file
        output_dir = config.DATA_RAW
        ensure_directory(output_dir)
        
        # Assuming the file is named s_agent_k_subset.jsonl
        file_path = hf_hub_download(
            repo_id=dataset_id,
            filename="s_agent_k_subset.jsonl",
            repo_type="dataset",
            cache_dir=str(output_dir)
        )
        
        # Move to expected location if needed
        target_path = output_dir / "s_agent_k_subset.jsonl"
        if file_path != str(target_path):
            import shutil
            shutil.copy(file_path, target_path)
        
        logger.info(f"Dataset downloaded to {target_path}")
        
    except ImportError:
        raise ImportError("huggingface_hub is required. Install it via pip.")
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def main():
    download_dataset()

if __name__ == "__main__":
    main()
