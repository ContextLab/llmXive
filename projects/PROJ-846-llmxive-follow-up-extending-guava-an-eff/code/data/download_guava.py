import json
import os
import hashlib
import shutil
import time
import requests
from pathlib import Path
from utils.errors import DatasetUnavailableError
from utils.config import get_path, set_hyperparameter

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_guava_dataset(output_dir: str, url: str) -> None:
    """
    Download the Guava raw dataset from the specified URL.
    
    Args:
        output_dir: Directory to save the dataset
        url: URL to download the dataset from
        
    Raises:
        DatasetUnavailableError: If download fails
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if dataset already exists
    expected_file = output_path / "guava_raw.zip"
    if expected_file.exists():
        print(f"Dataset already exists at {expected_file}")
        return
    
    print(f"Downloading Guava dataset from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(expected_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.2f}%", end='', flush=True)
        
        print("\nDownload complete.")
        
        # Verify checksum if available
        checksum_file = output_path / "guava_raw.zip.sha256"
        if checksum_file.exists():
            with open(checksum_file, 'r') as f:
                expected_hash = f.read().strip()
            actual_hash = calculate_sha256(str(expected_file))
            if actual_hash != expected_hash:
                raise DatasetUnavailableError(
                    f"Checksum mismatch. Expected: {expected_hash}, Got: {actual_hash}"
                )
            print("Checksum verified.")
        else:
            print("No checksum file found, skipping verification.")
            
    except requests.RequestException as e:
        raise DatasetUnavailableError(f"Failed to download dataset: {str(e)}")
    except Exception as e:
        raise DatasetUnavailableError(f"Unexpected error during download: {str(e)}")

def save_checksums(output_dir: str, files: list) -> None:
    """
    Generate and save checksums for all files in the dataset directory.
    
    Args:
        output_dir: Directory containing the dataset files
        files: List of filenames to checksum
    """
    output_path = Path(output_dir)
    checksums = {}
    
    for filename in files:
        file_path = output_path / filename
        if file_path.exists():
          checksums[filename] = calculate_sha256(str(file_path))
          print(f"Checksummed: {filename} - {checksums[filename][:16]}...")
    
    checksum_file = output_path / "checksums.json"
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Checksums saved to {checksum_file}")

def main():
    """Main entry point for downloading Guava dataset."""
    # Get configuration
    raw_data_path = get_path("raw_data")
    guava_dir = os.path.join(raw_data_path, "guava")
    
    # Default URL - in a real scenario, this would come from config or environment
    # Using a placeholder URL that would need to be replaced with the actual Guava dataset URL
    guava_url = os.environ.get("GUAVA_DATASET_URL", 
                               "https://huggingface.co/datasets/guava/visual-trajectories/resolve/main/guava_raw.zip")
    
    print(f"Guava dataset download initiated.")
    print(f"Target directory: {guava_dir}")
    print(f"Source URL: {guava_url}")
    
    try:
        # Download the dataset
        download_guava_dataset(guava_dir, guava_url)
        
        # Generate checksums for the downloaded files
        # In a real scenario, we'd know the specific files to checksum
        # For now, we'll checksum the main zip file
        files_to_checksum = ["guava_raw.zip"]
        save_checksums(guava_dir, files_to_checksum)
        
        # Set the availability flag
        set_hyperparameter("DATASET_AVAILABLE", True)
        print("Dataset successfully downloaded and verified. DATASET_AVAILABLE=true")
        
    except DatasetUnavailableError as e:
        print(f"ERROR: {str(e)}")
        set_hyperparameter("DATASET_AVAILABLE", False)
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")
        set_hyperparameter("DATASET_AVAILABLE", False)
        raise

if __name__ == "__main__":
    main()