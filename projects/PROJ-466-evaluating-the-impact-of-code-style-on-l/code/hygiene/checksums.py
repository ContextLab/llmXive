"""
Hygiene module for data integrity verification.
Computes SHA256 checksums for raw datasets and records them in state/checksums.json.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from config.loader import load_config

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA256 hash of a file by reading it in chunks.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without loading entirely into memory
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise

def get_raw_data_files(data_dir: Path) -> list:
    """
    Identifies raw data files in the specified directory.
    Currently targets the HumanEval dataset downloaded by T012.
    
    Args:
        data_dir: Path to the data/raw directory.
        
    Returns:
        List of Path objects pointing to raw data files.
    """
    raw_dir = data_dir / "raw" / "humaneval"
    files = []
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return files
        
    # Look for common dataset file extensions or specific parquet/jsonl files
    # The datasets library often caches to parquet or jsonl
    for ext in ["*.parquet", "*.jsonl", "*.json"]:
        files.extend(raw_dir.glob(ext))
    
    # If no specific extensions found, take all non-hidden files
    if not files:
        for item in raw_dir.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                files.append(item)
                
    return files

def record_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Writes the checksum dictionary to a JSON file.
    Creates the directory if it doesn't exist.
    
    Args:
        checksums: Dictionary mapping file paths to their SHA256 hashes.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums recorded to {output_path}")

def load_existing_checksums(output_path: Path) -> Dict[str, str]:
    """
    Loads existing checksums if the file exists, otherwise returns empty dict.
    
    Args:
        output_path: Path to the checksums JSON file.
        
    Returns:
        Dictionary of existing checksums.
    """
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing checksums: {e}. Starting fresh.")
    return {}

def run_checksum_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Orchestrates the checksum generation and recording process.
    
    1. Loads configuration to find data paths.
    2. Identifies raw data files.
    3. Computes SHA256 for each file.
    4. Merges with existing checksums (optional strategy, here we overwrite/append).
    5. Writes to state/checksums.json.
    
    Args:
        config: Optional pre-loaded config dict. If None, loads from default.
        
    Returns:
        The final dictionary of checksums.
    """
    if config is None:
        config = load_config()
    
    data_root = Path(config.get("data_root", "data"))
    state_root = Path(config.get("state_root", "state"))
    output_file = state_root / "checksums.json"
    
    logger.info(f"Starting checksum pipeline for raw data in {data_root}")
    
    raw_files = get_raw_data_files(data_root)
    
    if not raw_files:
        logger.warning("No raw data files found to checksum. Ensure T012 has run.")
        # Still record an empty state or skip? We record empty to show we checked.
        record_checksums({}, output_file)
        return {}
    
    checksums = {}
    for file_path in raw_files:
        try:
            rel_path = file_path.relative_to(data_root)
            hash_val = compute_sha256(file_path)
            checksums[str(rel_path)] = hash_val
            logger.info(f"Checksummed {rel_path}: {hash_val[:16]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            # Decide whether to fail loudly or skip. 
            # Per "Fail loudly", we raise if critical, but here we log and continue if one file fails?
            # The prompt says "Fail loudly, never silently". If a file is critical, we should probably stop.
            # However, if it's just a dataset shard, maybe we skip? 
            # Let's raise for now to ensure integrity.
            raise RuntimeError(f"Checksum verification failed for {file_path}: {e}")
    
    record_checksums(checksums, output_file)
    return checksums

if __name__ == "__main__":
    # Simple entry point for testing
    logging.basicConfig(level=logging.INFO)
    run_checksum_pipeline()
