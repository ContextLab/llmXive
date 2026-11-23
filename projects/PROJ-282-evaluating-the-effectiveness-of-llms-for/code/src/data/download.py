import os
import sys
import subprocess
import hashlib
import shutil
from pathlib import Path
import requests
import tarfile
import zipfile
import json
from typing import Optional, Dict, List, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Configuration for datasets
DATASET_CONFIGS = {
    "vuldeepecker": {
        "type": "url",
        "url": "https://github.com/vuldeepecker/VulDeePecker-Dataset/archive/refs/heads/main.zip",
        "filename": "vuldeepecker_dataset.zip",
        "extract_dir": "VulDeePecker-Dataset-main",
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Placeholder - real checksum needed
        "description": "VulDeePecker vulnerability dataset"
    },
    "juliet": {
        "type": "git",
        "repo": "https://github.com/juliet-testing-suite/juliet-c-tests.git",
        "target_dir": "juliet-c-tests",
        "description": "NIST Juliet C Test Suite"
    },
    "juliet_java": {
        "type": "git",
        "repo": "https://github.com/juliet-testing-suite/juliet-java-tests.git",
        "target_dir": "juliet-java-tests",
        "description": "NIST Juliet Java Test Suite"
    }
}

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = compute_sha256(file_path)
    if actual_checksum.lower() != expected_checksum.lower():
        raise ValueError(
            f"Checksum mismatch for {file_path.name}:\n"
            f"  Expected: {expected_checksum}\n"
            f"  Actual:   {actual_checksum}"
        )
    return True

def download_via_wget(url: str, output_dir: Path, filename: str) -> Path:
    """Download file from URL using wget or requests."""
    output_path = output_dir / filename
    
    if output_path.exists():
        logger.info(f"File already exists: {output_path}")
        return output_path
    
    logger.info(f"Downloading from {url} to {output_path}")
    
    try:
        # Try using requests for better control
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {str(e)}")

def clone_via_git(repo_url: str, target_dir: Path) -> Path:
    """Clone a git repository to target directory."""
    if target_dir.exists():
        logger.info(f"Repository already exists: {target_dir}")
        return target_dir
    
    logger.info(f"Cloning {repo_url} to {target_dir}")
    
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Clone complete: {target_dir}")
        return target_dir
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone {repo_url}: {e.stderr}")

def validate_dataset(dataset_name: str, data_dir: Path) -> Tuple[bool, str]:
    """
    Validate that a dataset was successfully downloaded and contains expected files.
    
    Returns:
        Tuple of (is_valid, message)
    """
    if dataset_name not in DATASET_CONFIGS:
        return False, f"Unknown dataset: {dataset_name}"
    
    config = DATASET_CONFIGS[dataset_name]
    
    if config["type"] == "url":
        expected_file = data_dir / config["filename"]
        if not expected_file.exists():
            return False, f"Missing file: {expected_file}"
        
        # Check if extracted directory exists
        if "extract_dir" in config:
            extracted_dir = data_dir / config["extract_dir"]
            if not extracted_dir.exists():
                return False, f"Missing extracted directory: {extracted_dir}"
            
            # Check for some expected files in extracted directory
            # This is dataset-specific and should be customized
            sample_files = list(extracted_dir.rglob("*.json") + extracted_dir.rglob("*.c") + extracted_dir.rglob("*.java"))
            if not sample_files:
                return False, "No code files found in extracted dataset"
                
    elif config["type"] == "git":
        expected_dir = data_dir / config["target_dir"]
        if not expected_dir.exists():
            return False, f"Missing directory: {expected_dir}"
        
        # Check for .git directory to confirm it's a git clone
        git_dir = expected_dir / ".git"
        if not git_dir.exists():
            return False, f"Not a valid git repository: {expected_dir}"
        
        # Check for expected test files
        sample_files = list(expected_dir.rglob("*.c") + expected_dir.rglob("*.java"))
        if not sample_files:
            return False, "No test files found in repository"
    
    return True, f"Dataset {dataset_name} validated successfully"

def download_all_datasets(data_dir: Path, validate: bool = True) -> Dict[str, bool]:
    """
    Download all configured datasets to the specified directory.
    
    Args:
        data_dir: Directory to download datasets to
        validate: Whether to validate datasets after download
        
    Returns:
        Dictionary mapping dataset names to success status
    """
    results = {}
    
    for dataset_name, config in DATASET_CONFIGS.items():
        logger.info(f"Processing dataset: {dataset_name}")
        
        try:
            if config["type"] == "url":
                # Download and extract
                download_path = download_via_wget(
                    config["url"], 
                    data_dir, 
                    config["filename"]
                )
                
                # Verify checksum if provided
                if "checksum" in config and config["checksum"]:
                    verify_checksum(download_path, config["checksum"])
                
                # Extract archive
                extracted_dir = data_dir / config["extract_dir"]
                if not extracted_dir.exists():
                    logger.info(f"Extracting {download_path}")
                    if download_path.suffix == ".zip":
                        with zipfile.ZipFile(download_path, 'r') as zip_ref:
                            zip_ref.extractall(data_dir)
                    elif download_path.suffix == ".tar.gz":
                        with tarfile.open(download_path, 'r:gz') as tar_ref:
                            tar_ref.extractall(data_dir)
                    else:
                        raise ValueError(f"Unsupported archive format: {download_path.suffix}")
                
            elif config["type"] == "git":
                clone_via_git(config["repo"], data_dir / config["target_dir"])
            
            # Validate if requested
            if validate:
                is_valid, message = validate_dataset(dataset_name, data_dir)
                if is_valid:
                    results[dataset_name] = True
                    logger.info(f"✓ {message}")
                else:
                    results[dataset_name] = False
                    logger.error(f"✗ {message}")
                    
        except Exception as e:
            results[dataset_name] = False
            logger.error(f"Failed to process {dataset_name}: {str(e)}")
            raise  # Re-raise to fail loudly
    
    return results

def main():
    """Main entry point for dataset download."""
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "raw"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading datasets to {data_dir}")
    
    try:
        results = download_all_datasets(data_dir, validate=True)
        
        # Check if all downloads were successful
        if all(results.values()):
            logger.info("All datasets downloaded and validated successfully")
            return 0
        else:
            failed = [name for name, success in results.items() if not success]
            logger.error(f"Failed to download datasets: {failed}")
            return 1
            
    except Exception as e:
        logger.error(f"Download pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())
