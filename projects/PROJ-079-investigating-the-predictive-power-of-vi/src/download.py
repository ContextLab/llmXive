import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import hashlib
from pathlib import Path

from src.config import DATA_RAW_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_manifest_template() -> str:
    """
    Creates a JSON manifest template file at data/manifest_template.json.
    
    The manifest includes keys: accessions, source, timestamp, version, 
    and checksum_algorithm (set to 'sha256').
    
    Returns:
        str: Path to the generated manifest file.
    """
    # Ensure the data directory exists
    data_dir = Path(DATA_RAW_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_path = data_dir / "manifest_template.json"
    
    manifest_data = {
        "accessions": [],
        "source": "NCBI Virus / GEO",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v1.0.0",
        "checksum_algorithm": "sha256"
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Generated manifest template at: {manifest_path}")
    return str(manifest_path)

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Stub function to fetch viral genomes from NCBI.
    Raises NotImplementedError until T012 is implemented.
    """
    raise NotImplementedError("T012: Implement NCBI Virus API fetch logic")

def fetch_geo_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Stub function to fetch GEO data.
    Raises NotImplementedError until T013 is implemented.
    """
    raise NotImplementedError("T013: Implement GEO download and parsing logic")

def generate_manifest_v2(accessions: List[str], source: str, version: str) -> str:
    """
    Generates a manifest file for a specific download run (T012/T013).
    
    Args:
        accessions: List of accessions used.
        source: Data source (e.g., 'NCBI Virus', 'GEO').
        version: Database version.
        
    Returns:
        str: Path to the generated manifest file.
    """
    data_dir = Path(DATA_RAW_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine filename based on source
    if "NCBI" in source:
        manifest_path = data_dir / "manifest_v1.json"
    else:
        manifest_path = data_dir / "manifest_v2.json"
        
    # Placeholder for checksum calculation
    checksums = {}
    
    manifest_data = {
        "accessions": accessions,
        "source": source,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": version,
        "checksums": checksums
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
        
    logger.info(f"Generated {source} manifest at: {manifest_path}")
    return str(manifest_path)

def main():
    """
    Entry point for the download module.
    Initializes the download skeleton and generates the manifest template.
    """
    logger.info("Download skeleton initialized")
    generate_manifest_template()

if __name__ == "__main__":
    main()
