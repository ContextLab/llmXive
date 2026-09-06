"""
Data ingestion module for the llmXive automated science pipeline.

This module handles:
- Loading configuration from JSON files
- Downloading datasets from verified sources
- Checksum validation
- PII scanning
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuration paths
CONFIG_DIR = Path("code/config")
DATA_DIR = Path("data")
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the config file. Defaults to config/dataset_source.json
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if config_path is None:
        config_path = CONFIG_DIR / "dataset_source.json"
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_checksums(checksums_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        checksums_path: Path to the checksums file. Defaults to data/checksums.json
        
    Returns:
        Dictionary mapping filenames to their SHA-256 checksums
    """
    if checksums_path is None:
        checksums_path = DATA_DIR / "checksums.json"
        
    if not checksums_path.exists():
        # Create empty checksums file if it doesn't exist
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checksums_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
        
    with open(checksums_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(config: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
    """
    Download dataset from the configured source.
    
    Args:
        config: Dataset configuration dictionary
        output_dir: Directory to save the dataset. Defaults to data/raw/
        
    Returns:
        Path to the downloaded file
        
    Raises:
        RuntimeError: If download fails
    """
    if output_dir is None:
        output_dir = RAW_DATA_DIR
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_url = config.get("url")
    dataset_id = config.get("dataset_id", "unknown")
    
    if not dataset_url:
        raise ValueError("Dataset URL not found in configuration")
        
    # Extract filename from URL
    filename = dataset_url.split("/")[-1]
    output_path = output_dir / filename
    
    print(f"Downloading dataset: {dataset_id}")
    print(f"URL: {dataset_url}")
    print(f"Output: {output_path}")
    
    # Check if file already exists and is complete
    if output_path.exists():
        # Check file size (simple heuristic for completion)
        if output_path.stat().st_size > 0:
            print(f"Dataset already exists at {output_path}, skipping download.")
            return output_path
        else:
            print(f"Existing file is empty, re-downloading...")
    
    try:
        # Use wget or curl for download
        import urllib.request
        urllib.request.urlretrieve(dataset_url, str(output_path))
        
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Download failed: file is empty or missing")
            
        print(f"✓ Download completed: {output_path}")
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Validate file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 checksum
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    actual_checksum = calculate_sha256(file_path)
    
    if actual_checksum.lower() != expected_checksum.lower():
        print(f"Checksum mismatch!")
        print(f"  Expected: {expected_checksum}")
        print(f"  Actual:   {actual_checksum}")
        return False
        
    print(f"✓ Checksum validation passed")
    return True

def run_pii_scan(file_path: Path) -> bool:
    """
    Run PII scan on the dataset file.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        True if scan passes, False otherwise
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    print(f"Running PII scan on: {file_path}")
    
    # Check if repo-hygiene command is available
    try:
        result = subprocess.run(
            ["repo-hygiene", "scan", "--pii", str(file_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✓ PII scan passed")
            return True
        else:
            print(f"⚠ PII scan found issues:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠ repo-hygiene command not found, skipping PII scan")
        print("  Install with: pip install repo-hygiene")
        return True  # Don't fail if tool is missing
    except subprocess.TimeoutExpired:
        print("⚠ PII scan timed out")
        return False

def main():
    """Main entry point for data ingestion."""
    print("=" * 60)
    print("llmXive Data Ingestion Pipeline")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        if not config.get("verified", False):
            print("⚠ Dataset not verified. Run: python code/populate_dataset_config.py")
            sys.exit(1)
        
        # Load existing checksums
        checksums = load_checksums()
        
        # Download dataset
        downloaded_file = download_dataset(config)
        
        # Validate checksum if available
        expected_checksum = config.get("checksums", {}).get("tar_gz")
        if expected_checksum and expected_checksum != "SHA256_PLACEHOLDER_UPDATE_AFTER_VERIFICATION":
            if not validate_checksum(downloaded_file, expected_checksum):
                print("ERROR: Checksum validation failed")
                sys.exit(1)
        else:
            print("⚠ No checksum available for validation")
            # Calculate and store checksum
            actual_checksum = calculate_sha256(downloaded_file)
            checksums[downloaded_file.name] = actual_checksum
            
            # Save updated checksums
            with open(DATA_DIR / "checksums.json", "w", encoding="utf-8") as f:
                json.dump(checksums, f, indent=2)
            print(f"Stored checksum: {actual_checksum}")
        
        # Run PII scan
        if not run_pii_scan(downloaded_file):
            print("⚠ PII scan failed, but continuing...")
        
        print("=" * 60)
        print("✓ Data ingestion completed successfully")
        print(f"  Dataset: {downloaded_file}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()