"""
Task T004: Download ESOL dataset from MoleculeNet or verified mirror.

Fetches the 'delaney-processed.csv' file, validates the 'logS' column,
saves it to data/raw/, computes SHA-256 checksum, and updates the state manifest.

Constraints:
- NO synthetic fallbacks. If both sources fail, raise an exception.
- Must record checksum in state/projects/PROJ-351-predicting-the-solubility-of-pharmaceuti.yaml
"""
import os
import sys
import json
import hashlib
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logger

# Configuration
PRIMARY_SOURCE = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv"
FALLBACK_SOURCE = "https://huggingface.co/datasets/deepchem/delaney-processed/resolve/main/delaney-processed.csv"
OUTPUT_FILENAME = "delaney-processed.csv"
OUTPUT_DIR = "data/raw"
STATE_MANIFEST_PATH = "state/projects/PROJ-351-predicting-the-solubility-of-pharmaceuti.yaml"
REQUIRED_COLUMNS = ["logS"]

# Setup logging
logger = setup_logger("download_esol")

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_url(url: str, output_path: Path) -> None:
    """Fetch a file from a URL and save it."""
    logger.info(f"Attempting to fetch from: {url}")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(output_path, 'wb') as out_file:
                # Read in chunks to handle large files gracefully
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        logger.info(f"Successfully downloaded to: {output_path}")
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} fetching {url}: {e.reason}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"URL Error fetching {url}: {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise

def validate_csv(filepath: Path) -> bool:
    """Validate that the CSV contains required columns."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath, nrows=5) # Read header and a few rows
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error(f"Validation failed: Missing required columns: {missing_cols}")
            return False
        logger.info("Validation passed: Required columns present.")
        return True
    except Exception as e:
        logger.error(f"Validation failed: Could not read CSV: {e}")
        return False

def load_yaml_manifest(filepath: Path) -> Dict[str, Any]:
    """Load a YAML file safely without external dependencies if possible, or use yaml."""
    try:
        import yaml
        if not filepath.exists():
            return {"artifact_hashes": {}}
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {"artifact_hashes": {}}
    except ImportError:
        # Fallback if pyyaml not installed (unlikely given T002) but handle gracefully
        logger.warning("PyYAML not installed. Attempting simple parse or failing.")
        if not filepath.exists():
            return {"artifact_hashes": {}}
        # Simple parser for the specific expected format if yaml is missing
        # This is a last resort; ideally pyyaml is installed.
        return {"artifact_hashes": {}} 

def save_yaml_manifest(filepath: Path, data: Dict[str, Any]) -> None:
    """Save data to a YAML file."""
    try:
        import yaml
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        logger.info(f"Updated state manifest at {filepath}")
    except ImportError:
        logger.error("PyYAML is required to update the state manifest.")
        raise

def update_state_manifest(output_file: Path, checksum: str) -> None:
    """Update the project state manifest with the new checksum."""
    manifest_path = project_root / STATE_MANIFEST_PATH
    data = load_yaml_manifest(manifest_path)
    
    # Ensure artifact_hashes key exists
    if "artifact_hashes" not in data:
        data["artifact_hashes"] = {}
    
    # Update the specific hash
    relative_path = str(output_file.relative_to(project_root))
    data["artifact_hashes"][relative_path] = f"sha256:{checksum}"
    
    save_yaml_manifest(manifest_path, data)

def fetch_esol_dataset(output_dir: Path) -> Path:
    """
    Fetch ESOL dataset from primary source, fallback to mirror if needed.
    Raises RuntimeError if both fail.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME

    sources = [PRIMARY_SOURCE, FALLBACK_SOURCE]
    
    for url in sources:
        try:
            fetch_url(url, output_path)
            if validate_csv(output_path):
                return output_path
            else:
                logger.warning(f"Validation failed for {url}, removing file.")
                output_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to fetch or validate from {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            continue

    raise RuntimeError(
        f"CRITICAL: Could not fetch real ESOL data from any source. "
        f"Primary: {PRIMARY_SOURCE}, Fallback: {FALLBACK_SOURCE}. "
        "Aborting. No synthetic data allowed."
    )

def main():
    """Main entry point for the download task."""
    logger.info("Starting ESOL dataset download (Task T004)...")
    
    output_path = project_root / OUTPUT_DIR
    try:
        csv_path = fetch_esol_dataset(output_path)
        
        # Compute checksum
        checksum = compute_sha256(csv_path)
        logger.info(f"SHA-256 Checksum: {checksum}")
        
        # Update manifest
        update_state_manifest(csv_path, checksum)
        
        logger.info("Task T004 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T004 failed: {e}")
        raise

if __name__ == "__main__":
    main()