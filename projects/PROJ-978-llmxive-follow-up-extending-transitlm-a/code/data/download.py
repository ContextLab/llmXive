import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it via: pip install datasets")


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_transitlm(
    output_dir: str = "data/raw",
    dataset_name: str = "llmXive/transitlm-sft",
    split: str = "train",
    streaming: bool = True,
    expected_sha256: Optional[str] = None
) -> str:
    """
    Download the TransitLM SFT dataset from Hugging Face.
    
    This function:
    1. Streams the dataset from Hugging Face (to avoid loading into memory).
    2. Converts the dataset to a list of dictionaries.
    3. Saves the data to a JSON file.
    4. Computes and verifies the SHA256 checksum if expected_sha256 is provided.
    
    Args:
        output_dir: Directory to save the downloaded file.
        dataset_name: Hugging Face dataset name.
        split: Dataset split to download (default: "train").
        streaming: Whether to stream the dataset (default: True).
        expected_sha256: Expected SHA256 hash for verification.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        RuntimeError: If SHA256 verification fails.
        Exception: If dataset download fails.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "transitlm_ground_truth.json"
    
    print(f"Downloading dataset: {dataset_name} (split: {split})...")
    print("Using streaming=True to handle large datasets efficiently.")
    
    try:
        # Load dataset with streaming
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
        
        # Convert to list of dicts and save
        print("Converting dataset to JSON...")
        data_list = []
        
        # If streaming, iterate directly; otherwise, convert to list
        if streaming:
            for item in dataset:
                data_list.append(item)
        else:
            data_list = list(dataset)
        
        # Write to JSON file
        print(f"Writing {len(data_list)} records to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Dataset saved to: {output_file}")
        
        # Verify SHA256 if expected hash is provided
        if expected_sha256:
            print("Verifying SHA256 checksum...")
            actual_sha256 = compute_sha256(str(output_file))
            
            if actual_sha256 != expected_sha256:
                raise RuntimeError(
                    f"SHA256 verification failed!\n"
                    f"Expected: {expected_sha256}\n"
                    f"Actual:   {actual_sha256}"
                )
            print(f"SHA256 verification passed: {actual_sha256}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"Error downloading dataset: {e}", file=sys.stderr)
        raise


def main():
    """Main entry point for dataset download."""
    # Default configuration
    output_dir = "data/raw"
    dataset_name = "llmXive/transitlm-sft"
    split = "train"
    streaming = True
    expected_sha256 = None  # Set this if you have a known hash
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    if len(sys.argv) > 2:
        dataset_name = sys.argv[2]
    if len(sys.argv) > 3:
        split = sys.argv[3]
    if len(sys.argv) > 4:
        streaming = sys.argv[4].lower() == 'true'
    if len(sys.argv) > 5:
        expected_sha256 = sys.argv[5]
    
    try:
        output_file = download_transitlm(
            output_dir=output_dir,
            dataset_name=dataset_name,
            split=split,
            streaming=streaming,
            expected_sha256=expected_sha256
        )
        print(f"Download completed successfully: {output_file}")
        sys.exit(0)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()