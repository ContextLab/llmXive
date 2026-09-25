"""
AGP Data Loader for American Gut Project.
Downloads raw data from Qiita, validates, and saves to data/raw/agp_raw.tsv.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import shared logger
from src.utils.logger import get_logger

# Constants
QIITA_API_BASE = "https://api.qiita.ucdavis.edu"
# AGP Study ID on Qiita (verified public study)
AGP_STUDY_ID = "10317"
# Endpoint for sample mapping (metadata)
SAMPLE_MAPPING_ENDPOINT = f"/api/v1/studies/{AGP_STUDY_ID}/mapping"
# Endpoint for OTU table (feature table)
OTU_TABLE_ENDPOINT = f"/api/v1/studies/{AGP_STUDY_ID}/otu_table"

# Output paths relative to project root
RAW_DATA_PATH = "data/raw/agp_raw.tsv"
STATE_PATH = "state/artifact_hashes.json"

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[2]

def verify_url(url: str) -> bool:
    """Verify if a URL is reachable."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def ensure_qiita_token() -> Optional[str]:
    """
    Retrieve Qiita API token from environment variable.
    Raises RuntimeError if not found.
    """
    token = os.getenv("QIITA_API_TOKEN")
    if not token:
        raise RuntimeError(
            "Qiita API token not found. Set QIITA_API_TOKEN environment variable."
        )
    return token

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksum(file_path: Path, checksum: str, state_file: Path) -> None:
    """Record file checksum in state/artifact_hashes.json."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = json.load(f)
    else:
        state_data = {}
    
    state_data[file_path.name] = checksum
    
    with open(state_file, "w") as f:
        json.dump(state_data, f, indent=2)

def fetch_sample_mapping(headers: Dict[str, str]) -> Dict[str, Any]:
    """Fetch sample mapping (metadata) from Qiita API."""
    url = f"{QIITA_API_BASE}{SAMPLE_MAPPING_ENDPOINT}"
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch sample mapping from Qiita: {e}")

def fetch_otu_table(headers: Dict[str, str]) -> Dict[str, Any]:
    """Fetch OTU table (feature data) from Qiita API."""
    url = f"{QIITA_API_BASE}{OTU_TABLE_ENDPOINT}"
    try:
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch OTU table from Qiita: {e}")

def fetch_agp_data(output_path: Path, state_file: Path) -> None:
    """
    Fetch AGP data from Qiita API and save to TSV.
    
    This function:
    1. Retrieves sample metadata and OTU table from Qiita
    2. Merges them into a unified TSV format
    3. Calculates and records checksum
    4. Ensures output directory exists
    
    Args:
        output_path: Path to save the raw TSV file
        state_file: Path to state file for checksums
    """
    logger = get_logger("agp_loader")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get API token
    token = ensure_qiita_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Fetching AGP data from Qiita study {AGP_STUDY_ID}")
    
    # Fetch data from Qiita
    logger.info("Fetching sample mapping...")
    sample_mapping = fetch_sample_mapping(headers)
    logger.info("Fetching OTU table...")
    otu_table = fetch_otu_table(headers)
    
    # Process and merge data
    # Sample mapping contains metadata
    # OTU table contains feature abundances
    # We'll create a unified TSV with sample_id, metadata, and OTU counts
    
    if not sample_mapping or "samples" not in sample_mapping:
        raise RuntimeError("Sample mapping is empty or missing 'samples' key")
    
    if not otu_table or "data" not in otu_table:
        raise RuntimeError("OTU table is empty or missing 'data' key")
    
    # Extract sample IDs from mapping
    sample_ids = list(sample_mapping["samples"].keys())
    logger.info(f"Found {len(sample_ids)} samples in AGP dataset")
    
    # Create unified data structure
    unified_data = []
    
    for sample_id in sample_ids:
        sample_row = {"sample_id": sample_id}
        
        # Add metadata from sample mapping
        if sample_id in sample_mapping["samples"]:
            metadata = sample_mapping["samples"][sample_id]
            for key, value in metadata.items():
                # Flatten nested structures if needed
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                sample_row[f"metadata_{key}"] = value
        
        # Add OTU counts if available
        if sample_id in otu_table["data"]:
          otu_counts = otu_table["data"][sample_id]
          for otu_id, count in otu_counts.items():
              sample_row[f"otu_{otu_id}"] = count
        
        unified_data.append(sample_row)
    
    # Write to TSV
    logger.info(f"Writing {len(unified_data)} samples to {output_path}")
    
    if not unified_data:
        raise RuntimeError("No data to write - AGP dataset appears empty")
    
    # Get all unique keys for column headers
    all_keys = set()
    for row in unified_data:
        all_keys.update(row.keys())
    
    sorted_keys = sorted(list(all_keys))
    
    with open(output_path, "w", encoding="utf-8") as f:
        # Write header
        f.write("\t".join(sorted_keys) + "\n")
        
        # Write data rows
        for row in unified_data:
            values = [str(row.get(key, "")) for key in sorted_keys]
            f.write("\t".join(values) + "\n")
    
    logger.info(f"Successfully wrote {output_path}")
    
    # Calculate and record checksum
    checksum = calculate_file_checksum(output_path)
    logger.info(f"File checksum: {checksum}")
    record_checksum(output_path, checksum, state_file)
    
    logger.info("AGP data ingestion completed successfully")

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for AGP loader."""
    parser = argparse.ArgumentParser(
        description="Download AGP data from Qiita API"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=RAW_DATA_PATH,
        help="Output path for raw AGP data (default: data/raw/agp_raw.tsv)"
    )
    parser.add_argument(
        "--state",
        type=str,
        default=STATE_PATH,
        help="Path to state file for checksums (default: state/artifact_hashes.json)"
    )
    return parser

def main():
    """Main entry point for AGP loader."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger("agp_loader")
    logger.info("Starting AGP data ingestion")
    
    project_root = get_project_root()
    output_path = project_root / args.output
    state_file = project_root / args.state
    
    try:
        fetch_agp_data(output_path, state_file)
        logger.info("AGP ingestion completed successfully")
        return 0
    except Exception as e:
        logger.error(f"AGP ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())