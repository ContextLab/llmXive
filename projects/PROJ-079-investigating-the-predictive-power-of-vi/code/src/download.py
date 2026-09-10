import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests
from urllib.parse import urlencode

from src.config import NCBI_BASE_URL, DATA_RAW_PATH, SEED
from src.utils.logging import get_logger

# Set default NCBI base URL if not configured
if not NCBI_BASE_URL:
    NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

logger = get_logger(__name__)

def _fetch_genome_from_ncbi(accession: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single viral genome record from NCBI Virus API.
    Returns a dict with 'accession', 'sequence', 'family' or None if not found.
    """
    # NCBI Virus API via E-utilities
    # Using esearch to get IDs, then efetch to get FASTA
    # Alternatively, direct FASTA download via nucleotide API
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "nucleotide",
        "id": accession,
        "rettype": "fasta",
        "retmode": "text"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch accession {accession}: {e}")
        return None

    content = response.text
    if not content or ">error" in content.lower():
        logger.warning(f"Empty or error response for accession {accession}")
        return None

    # Parse FASTA
    lines = content.strip().split('\n')
    if not lines or not lines[0].startswith('>'):
        logger.warning(f"Invalid FASTA format for accession {accession}")
        return None

    header = lines[0]
    sequence_lines = lines[1:]
    sequence = "".join(sequence_lines).replace(" ", "").replace("\r", "")
    
    # Extract family from header if possible (often in format: ... [Family] ...)
    # Typical header: >gb|MN123456.1| ... Organism: Family Name ...
    family = "Unknown"
    if "[" in header and "]" in header:
        # Try to extract family from brackets
        start = header.find("[") + 1
        end = header.find("]")
        if end > start:
            family = header[start:end].strip()
    elif "Family" in header:
        parts = header.split("Family")
        if len(parts) > 1:
            family = parts[1].strip().split()[0]

    return {
        "accession": accession,
        "sequence": sequence,
        "family": family
    }

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Query NCBI Virus API for a list of accessions, parse FASTA, and return
    a list of dicts with keys: "accession", "sequence", "family".
    Logs warnings for missing accessions per FR-013.
    """
    if not accessions:
        logger.warning("No accessions provided to fetch_viral_genomes")
        return []

    results = []
    for acc in accessions:
        record = _fetch_genome_from_ncbi(acc)
        if record:
            results.append(record)
        else:
            logger.warning(f"Missing or failed to fetch accession: {acc}")

    logger.info(f"Successfully fetched {len(results)} of {len(accessions)} genomes")
    return results

def generate_manifest_v1(accessions: List[str], results: List[Dict[str, Any]]) -> Path:
    """
    Generate data/manifest_v1.json with keys:
    - accessions: list of requested accessions
    - source: "NCBI Virus"
    - timestamp: ISO8601 string
    - version: database release (simulated as 'latest' if not available)
    - checksums: dict mapping accession to SHA-256 of sequence bytes
    
    Overwrites existing file (does not append).
    """
    manifest_path = Path(DATA_RAW_PATH) / "manifest_v1.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"
    
    checksums = {}
    for record in results:
        seq_bytes = record["sequence"].encode('utf-8')
        checksum = hashlib.sha256(seq_bytes).hexdigest()
        checksums[record["accession"]] = checksum

    manifest = {
        "accessions": accessions,
        "source": "NCBI Virus",
        "timestamp": timestamp,
        "version": "latest",  # NCBI doesn't provide a simple release version in API
        "checksums": checksums
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Generated manifest at {manifest_path}")
    return manifest_path

def generate_manifest_template() -> str:
    """
    Writes a JSON file to data/manifest_template.json with keys:
    "accessions", "source", "timestamp", "version", "checksum_algorithm".
    Returns the path as a string.
    """
    manifest_path = Path(DATA_RAW_PATH) / "manifest_template.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    template = {
        "accessions": [],
        "source": "NCBI Virus",
        "timestamp": "",
        "version": "",
        "checksum_algorithm": "sha256"
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)

    logger.info(f"Generated manifest template at {manifest_path}")
    return str(manifest_path)

def fetch_geo_data(accessions: List[str]) -> Dict[str, str]:
    """
    Stub for fetching GEO data. 
    TODO: Implement GEO series matrix download and parsing.
    """
    raise NotImplementedError("fetch_geo_data not yet implemented")

def generate_manifest_v2(accessions: List[str], results: Dict[str, str]) -> Path:
    """
    Stub for generating manifest_v2.json.
    TODO: Implement checksum calculation for GEO data.
    """
    raise NotImplementedError("generate_manifest_v2 not yet implemented")

def main():
    """
    Entry point for download module.
    Demonstrates fetching a small set of viral genomes.
    """
    logger.info("Download skeleton initialized")
    
    # Example accessions (replace with real ones from config or args)
    # Using a few known viral accessions for demonstration
    test_accessions = [
        "NC_001802",  # Influenza A
        "NC_001477",  # Vaccinia virus
        "NC_002697"   # Herpes simplex virus 1
    ]

    logger.info(f"Fetching genomes for: {test_accessions}")
    results = fetch_viral_genomes(test_accessions)
    
    if results:
        manifest_path = generate_manifest_v1(test_accessions, results)
        logger.info(f"Manifest saved to {manifest_path}")
        
        # Log summary
        for r in results:
            logger.info(f"  - {r['accession']}: {len(r['sequence'])} bp, Family: {r['family']}")
    else:
        logger.error("No genomes fetched. Check network or accessions.")

if __name__ == "__main__":
    main()