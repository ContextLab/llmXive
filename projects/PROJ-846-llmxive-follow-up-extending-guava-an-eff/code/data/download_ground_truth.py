import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

from huggingface_hub import hf_hub_download
from utils.errors import DatasetUnavailableError

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_ground_truth(
    repo_id: str,
    filename: str,
    output_dir: Path,
    expected_checksum: Optional[str] = None
) -> Path:
    """
    Download ground truth annotation file from Hugging Face.
    
    Args:
        repo_id: Hugging Face repository ID (e.g., 'guava/guava-v1')
        filename: Name of the file to download
        output_dir: Directory to save the file
        expected_checksum: Optional expected SHA256 checksum for verification
    
    Returns:
        Path to the downloaded file
    
    Raises:
        DatasetUnavailableError: If download fails or checksum mismatch
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
    except Exception as e:
        raise DatasetUnavailableError(
            f"Failed to download ground truth annotations from {repo_id}/{filename}: {str(e)}"
        ) from e
    
    if not os.path.exists(downloaded_path):
        raise DatasetUnavailableError(
            f"Downloaded file not found at {downloaded_path}"
        )
    
    actual_checksum = calculate_sha256(Path(downloaded_path))
    
    if expected_checksum and actual_checksum != expected_checksum:
        raise DatasetUnavailableError(
            f"Checksum mismatch for {filename}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    
    return Path(downloaded_path)

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum matches expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def main():
    """Main entry point for downloading ground truth annotations."""
    # Configuration from tasks.md
    repo_id = "guava/guava-v1"
    remote_filename = "annotations.json"
    output_filename = "ground_truth_annotations.json"
    output_dir = Path("data/raw/guava")
    
    # Note: Checksum verification is performed if expected_checksum is provided.
    # For this task, we download and verify existence. If a checksum is known,
    # it should be passed via config or command line.
    expected_checksum = None  # Can be overridden via config if available
    
    print(f"Downloading {remote_filename} from {repo_id}...")
    
    try:
        downloaded_path = download_ground_truth(
            repo_id=repo_id,
            filename=remote_filename,
            output_dir=output_dir,
            expected_checksum=expected_checksum
        )
        
        print(f"Successfully downloaded to: {downloaded_path}")
        
        # Verify file exists and is readable
        if not downloaded_path.exists():
            raise DatasetUnavailableError("Downloaded file does not exist")
        
        # Log checksum for verification
        checksum = calculate_sha256(downloaded_path)
        print(f"File checksum (SHA256): {checksum}")
        
        # Save checksum to a sidecar file for future verification
        checksum_file = output_dir / "ground_truth_annotations.sha256"
        with open(checksum_file, "w") as f:
            json.dump({
                "file": output_filename,
                "checksum": checksum,
                "repo_id": repo_id
            }, f, indent=2)
        
        print(f"Checksum saved to: {checksum_file}")
        
    except DatasetUnavailableError as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()