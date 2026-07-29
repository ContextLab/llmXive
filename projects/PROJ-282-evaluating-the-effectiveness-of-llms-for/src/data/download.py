import os
import sys
import subprocess
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# Add parent to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
else:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.validate_urls import parse_research_manifest, validate_url_pattern, check_url_accessibility, validate_dataset_urls

logger = get_logger(__name__)

# Configuration for datasets based on research.md requirements
# Note: Using BigVul for C-code as NIST Juliet raw code is unavailable per Plan Complexity Tracking
DATASET_CONFIG = {
    "vuldeepecker": {
        "name": "VulDeePecker",
        "language": "Python",
        "url_key": "vuldeepecker_url",
        "output_dir": "data/raw/vuldeepecker",
        "file_pattern": "*.jsonl",
        "type": "download"
    },
    "bigvul_c": {
        "name": "BigVul C",
        "language": "C",
        "url_key": "bigvul_c_url",
        "output_dir": "data/raw/bigvul_c",
        "file_pattern": "*.json",
        "type": "download"
    },
    "bigvul_js": {
        "name": "BigVul JavaScript",
        "language": "JavaScript",
        "url_key": "bigvul_js_url",
        "output_dir": "data/raw/bigvul_js",
        "file_pattern": "*.json",
        "type": "download"
    }
}

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def download_via_wget(url: str, dest_dir: str) -> str:
    """Download file via wget and return local path."""
    os.makedirs(dest_dir, exist_ok=True)
    output_path = os.path.join(dest_dir, os.path.basename(url.split('?')[0]))
    
    # Use wget with verbose output for logging
    result = subprocess.run(
        ["wget", "-q", "--show-progress", "-P", dest_dir, url],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Download failed: {result.stderr}")
    
    return output_path

def clone_via_git(repo_url: str, dest_dir: str) -> str:
    """Clone git repository and return local path."""
    os.makedirs(dest_dir, exist_ok=True)
    repo_name = repo_url.rstrip('/').split('/')[-1]
    clone_path = os.path.join(dest_dir, repo_name)
    
    result = subprocess.run(
        ["git", "clone", repo_url, clone_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr}")
    
    return clone_path

def validate_dataset(dataset_config: Dict[str, Any], research_manifest: Dict[str, Any]) -> bool:
    """Validate dataset configuration against research manifest."""
    url_key = dataset_config.get("url_key")
    if not url_key:
        raise ValueError(f"Missing url_key in dataset config: {dataset_config['name']}")
    
    if url_key not in research_manifest:
        raise ValueError(f"URL key '{url_key}' not found in research manifest for {dataset_config['name']}")
    
    url = research_manifest[url_key]
    if not validate_url_pattern(url):
        raise ValueError(f"Invalid URL pattern for {dataset_config['name']}: {url}")
    
    if not check_url_accessibility(url):
        raise RuntimeError(f"URL not accessible for {dataset_config['name']}: {url}")
    
    return True

def download_all_datasets(research_manifest_path: Optional[str] = None) -> Dict[str, str]:
    """
    Download all datasets defined in DATASET_CONFIG.
    
    Args:
        research_manifest_path: Path to research.md manifest file. If None, uses default location.
        
    Returns:
        Dictionary mapping dataset names to local paths.
        
    Raises:
        RuntimeError: If any dataset download fails or validation fails.
    """
    # Default path if not provided
    if research_manifest_path is None:
        research_manifest_path = "research.md"
    
    # Parse and validate research manifest
    logger.info(f"Parsing research manifest from: {research_manifest_path}")
    research_manifest = parse_research_manifest(research_manifest_path)
    
    # Validate all dataset URLs first (T005 dependency)
    logger.info("Validating dataset URLs against research manifest...")
    validate_dataset_urls(research_manifest)
    
    downloaded_paths = {}
    
    for dataset_id, config in DATASET_CONFIG.items():
        dataset_name = config["name"]
        logger.info(f"Processing dataset: {dataset_name}")
        
        try:
            # Validate dataset configuration
            validate_dataset(config, research_manifest)
            
            # Get URL from manifest
            url = research_manifest[config["url_key"]]
            output_dir = config["output_dir"]
            
            logger.info(f"Downloading {dataset_name} from {url} to {output_dir}")
            
            # Download based on type
            if config["type"] == "download":
                local_path = download_via_wget(url, output_dir)
            elif config["type"] == "git":
                local_path = clone_via_git(url, output_dir)
            else:
                raise ValueError(f"Unknown dataset type: {config['type']}")
            
            downloaded_paths[dataset_id] = local_path
            logger.info(f"Successfully downloaded {dataset_name}: {local_path}")
            
        except Exception as e:
            logger.error(f"Failed to download {dataset_name}: {str(e)}")
            raise RuntimeError(f"Dataset download failed for {dataset_name}: {str(e)}")
    
    logger.info(f"All datasets downloaded successfully: {list(downloaded_paths.keys())}")
    return downloaded_paths

def main():
    """Main entry point for dataset download."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download security vulnerability datasets")
    parser.add_argument(
        "--manifest",
        type=str,
        default="research.md",
        help="Path to research manifest file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate URLs only without downloading"
    )
    
    args = parser.parse_args()
    
    try:
        if args.dry_run:
            logger.info("Running in dry-run mode - validating URLs only")
            research_manifest = parse_research_manifest(args.manifest)
            validate_dataset_urls(research_manifest)
            logger.info("All URLs validated successfully")
        else:
            downloaded_paths = download_all_datasets(args.manifest)
            logger.info(f"Downloaded datasets: {downloaded_paths}")
            
    except Exception as e:
        logger.error(f"Download process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()