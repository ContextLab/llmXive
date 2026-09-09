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

# Ensure NCBI_BASE_URL is set to a real endpoint if not in .env
# NCBI Virus API endpoint for bulk FASTA retrieval
if not NCBI_BASE_URL:
    NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov/assembly/download"

logger = get_logger(__name__)

def _fetch_fasta_chunk(accession: str, timeout: int = 30) -> Optional[bytes]:
    """
    Fetch FASTA data for a single accession from NCBI.
    Returns bytes on success, None on failure.
    """
    # NCBI Assembly download API pattern
    # https://www.ncbi.nlm.nih.gov/assembly/download?accession=GCF_XXXXX
    url = f"{NCBI_BASE_URL}"
    params = {"accession": accession, "filetype": "fasta"}
    
    try:
        logger.info(f"Fetching FASTA for {accession} from {url}")
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch FASTA for {accession}: {e}")
        return None

def _parse_fasta_to_dict(fasta_bytes: bytes, accession: str) -> Optional[Dict[str, Any]]:
    """
    Parse raw FASTA bytes into a dictionary with accession, sequence, and family.
    Infers family from the FASTA header if possible, otherwise defaults to 'unknown'.
    """
    if not fasta_bytes:
        return None

    try:
        text = fasta_bytes.decode('utf-8')
    except UnicodeDecodeError:
        logger.warning(f"Could not decode FASTA for {accession} as UTF-8")
        return None

    lines = text.strip().split('\n')
    if not lines:
        return None

    header = lines[0]
    sequence_lines = lines[1:]
    sequence = "".join(sequence_lines).replace(" ", "").replace("\n", "").upper()

    if not sequence:
        logger.warning(f"Empty sequence for {accession}")
        return None

    # Parse family from header: >accession|...|Family=Name|...
    # Standard NCBI Assembly FASTA headers often look like:
    # >GCF_000001234.1|...|Organism=Virus Name|...|Family=Family Name|...
    family = "unknown"
    parts = header.split('|')
    for part in parts:
        if part.lower().startswith('family='):
            family = part.split('=', 1)[1].strip()
            break
    
    return {
        "accession": accession,
        "sequence": sequence,
        "family": family
    }

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Queries NCBI Virus API (via Assembly download) to fetch FASTA data.
    Returns a list of dicts with keys: "accession", "sequence", "family".
    Logs warnings for missing accessions per FR-013.
    
    Args:
        accessions: List of NCBI accession strings (e.g., GCF_XXXXX).
    
    Returns:
        List of dictionaries representing viral genome data.
    """
    if not accessions:
        logger.warning("No accessions provided to fetch_viral_genomes")
        return []

    results = []
    raw_files = []

    for acc in accessions:
        logger.info(f"Processing accession: {acc}")
        fasta_bytes = _fetch_fasta_chunk(acc)
        
        if fasta_bytes is None:
            logger.warning(f"Missing accession (no data returned): {acc}")
            # FR-013: Log warnings for missing accessions
            continue

        # Store raw bytes for checksum calculation
        raw_files.append((acc, fasta_bytes))

        parsed = _parse_fasta_to_dict(fasta_bytes, acc)
        if parsed:
            results.append(parsed)
        else:
            logger.warning(f"Failed to parse FASTA for {acc}, skipping")

    generate_manifest_v1(accessions, raw_files)
    
    logger.info(f"Successfully fetched {len(results)} viral genomes out of {len(accessions)} requested.")
    return results

def generate_manifest_v1(accessions: List[str], raw_files: List[tuple]) -> Path:
    """
    Generates data/manifest_v1.json with metadata and SHA-256 checksums.
    Does NOT append to existing files; overwrites if present.
    
    Args:
        accessions: List of requested accessions.
        raw_files: List of (accession, bytes) tuples for checksumming.
    
    Returns:
        Path to the generated manifest file.
    """
    manifest_path = Path(DATA_RAW_PATH) / "manifest_v1.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    checksums = {}
    for acc, data in raw_files:
        sha256_hash = hashlib.sha256(data).hexdigest()
        checksums[acc] = sha256_hash

    manifest = {
        "accessions": accessions,
        "source": "NCBI Virus",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "latest", # NCBI updates frequently; specific release ID would need API query
        "checksums": checksums
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {manifest_path}")
    return manifest_path

def generate_manifest_template() -> str:
    """
    Writes a JSON template to data/manifest_template.json.
    """
    template_path = Path(DATA_RAW_PATH) / "manifest_template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)

    template = {
        "accessions": [],
        "source": "",
        "timestamp": "",
        "version": "",
        "checksum_algorithm": "sha256"
    }

    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    logger.info(f"Manifest template written to {template_path}")
    return str(template_path)

def fetch_geo_data(accessions: List[str]) -> Dict[str, str]:
    """
    Placeholder for GEO data fetching.
    Implemented in T013.
    """
    logger.warning("fetch_geo_data is not yet implemented (T013).")
    raise NotImplementedError("fetch_geo_data is not yet implemented.")

def generate_manifest_v2(accessions: List[str], raw_files: List[tuple]) -> Path:
    """
    Placeholder for GEO manifest generation.
    Implemented in T013.
    """
    logger.warning("generate_manifest_v2 is not yet implemented (T013).")
    raise NotImplementedError("generate_manifest_v2 is not yet implemented.")

def main():
    """
    Entry point for download module.
    Logs initialization and can be used for CLI testing.
    """
    logger.info("Download skeleton initialized.")
    # Example usage for manual testing (commented out to prevent auto-run on import)
    # if __name__ == "__main__":
    #     test_accs = ["GCF_000001234.1"] # Replace with real test accession if available
    #     fetch_viral_genomes(test_accs)

if __name__ == "__main__":
    main()
