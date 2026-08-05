"""
Data loading utilities for the visual attention study.

This module handles fetching, validating, and managing the raw eye-tracking dataset.
It strictly adheres to the verified source defined in research.md.
"""
import os
import sys
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up from code/utils/ to root
    return current.parent.parent

def parse_research_md() -> str:
    """
    Parse research.md to extract the verified dataset URL.
    Looks for the 'Verified datasets' block as per spec.
    """
    project_root = get_project_root()
    research_path = project_root / "idea" / "research.md"
    
    if not research_path.exists():
        # Fallback to common locations if idea/research.md not found
        research_path = project_root / "research.md"
    
    if not research_path.exists():
        raise FileNotFoundError(f"Could not find research.md at {research_path}")

    content = research_path.read_text(encoding="utf-8")
    
    # Look for the "Verified datasets" block
    # Pattern: "Verified datasets" followed by a URL
    # We assume the format contains a line like: - [Dataset Name](URL) or just a URL
    # Based on the spec, we need to find the "Verified datasets" block specifically.
    
    # Regex to find the block content
    # We look for a section header or a specific marker if present, 
    # but primarily we search for the URL associated with the verified source.
    # A robust way is to look for the text "Verified datasets" and extract the URL nearby.
    
    lines = content.split('\n')
    in_verified_block = False
    url_candidate = None
    
    for line in lines:
        if "Verified datasets" in line:
            in_verified_block = True
            continue
        
        if in_verified_block:
            # Stop if we hit another major section (e.g., starts with #)
            if line.strip().startswith('#') and "Verified" not in line:
                break
            
            # Extract URL from markdown link or plain text
            # Pattern for [text](url)
            match = re.search(r'\((https?://[^\s]+)\)', line)
            if match:
                url_candidate = match.group(1)
                break
            # Pattern for plain URL
            match = re.search(r'(https?://[^\s]+)', line)
            if match:
                url_candidate = match.group(1)
                break
    
    if not url_candidate:
        raise ValueError("Could not find a verified dataset URL in the 'Verified datasets' block of research.md")
    
    logger.info(f"Extracted verified source URL: {url_candidate}")
    return url_candidate

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_hash_registry() -> Dict[str, str]:
    """Load the hash registry from state/data_hashes.json."""
    project_root = get_project_root()
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    hash_file = state_dir / "data_hashes.json"
    
    if hash_file.exists():
        with open(hash_file, "r") as f:
            return json.load(f)
    return {}

def save_hash_registry(registry: Dict[str, str]) -> None:
    """Save the hash registry to state/data_hashes.json."""
    project_root = get_project_root()
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    hash_file = state_dir / "data_hashes.json"
    
    with open(hash_file, "w") as f:
        json.dump(registry, f, indent=2)

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify the SHA-256 checksum of a file."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def fetch_eye_tracking_data() -> Path:
    """
    Fetch the eye-tracking data from the verified source in research.md.
    Downloads to a temporary location, verifies checksum, then moves to data/raw/.
    """
    url = parse_research_md()
    project_root = get_project_root()
    
    # Ensure directories exist
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine output filename
    # Try to extract filename from URL, default to eye_tracking_raw.parquet
    parsed = urlparse(url)
    path_name = os.path.basename(parsed.path)
    if not path_name.endswith('.parquet'):
        path_name = "eye_tracking_raw.parquet"
    
    output_path = raw_dir / path_name
    
    # Check if file already exists
    if output_path.exists():
        logger.info(f"File {output_path} already exists. Verifying checksum...")
        registry = load_hash_registry()
        if path_name in registry:
            if verify_checksum(output_path, registry[path_name]):
                logger.info("Checksum matches. Skipping download.")
                return output_path
            else:
                logger.warning("Checksum mismatch. Re-downloading.")
        else:
            logger.warning("File exists but no checksum record. Re-downloading to ensure integrity.")
    
    # Download
    logger.info(f"Downloading data from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save to temp first
        temp_path = raw_dir / f"{path_name}.tmp"
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Compute checksum
        actual_hash = compute_sha256(temp_path)
        logger.info(f"Downloaded. SHA-256: {actual_hash}")
        
        # Check against registry if it exists (for re-downloads)
        registry = load_hash_registry()
        if path_name in registry and registry[path_name] != actual_hash:
            temp_path.unlink()
            raise ValueError(f"Checksum mismatch after download. Expected: {registry[path_name]}, Got: {actual_hash}")
        
        # Move to final location
        temp_path.rename(output_path)
        
        # Update registry
        registry[path_name] = actual_hash
        save_hash_registry(registry)
        
        logger.info(f"Data saved to {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download data from {url}: {e}")

def validate_eye_tracking_schema(df: pd.DataFrame) -> None:
    """
    Validate that the loaded dataframe has the expected schema.
    Raises ValueError if columns are missing.
    """
    required_columns = ['participant_id', 'timestamp', 'x', 'y', 'duration', 'event_type']
    # Adjust based on actual expected schema from research.md if known
    # For now, we assume a standard eye-tracking format.
    # If the dataset is different, this should be adapted.
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def load_dundee_eye_tracking() -> pd.DataFrame:
    """
    Load the Dundee eye-tracking dataset (if available).
    This is a placeholder for specific dataset loading logic if the verified source is Dundee.
    """
    raise NotImplementedError("Specific dataset loader not implemented; use fetch_eye_tracking_data() for generic download.")

def load_boston_eye_tracking() -> pd.DataFrame:
    """
    Load the Boston eye-tracking dataset (if available).
    """
    raise NotImplementedError("Specific dataset loader not implemented; use fetch_eye_tracking_data() for generic download.")

def main():
    """Main entry point for data fetching."""
    logger.info("Starting data fetching process...")
    try:
        output_path = fetch_eye_tracking_data()
        logger.info(f"Successfully fetched data to: {output_path}")
        
        # Optional: Load and validate
        # df = pd.read_parquet(output_path)
        # validate_eye_tracking_schema(df)
        
    except Exception as e:
        logger.error(f"Data fetching failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()