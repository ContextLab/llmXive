import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests
from urllib.parse import urljoin
from Bio import SeqIO
from io import StringIO

from src.config import NCBI_BASE_URL, DATA_RAW_PATH, SEED
from src.utils.logging import get_logger

# Ensure NCBI_BASE_URL has a default if not set in .env
if not NCBI_BASE_URL:
    NCBI_BASE_URL = "https://ncbi.nlm.nih.gov"

logger = get_logger(__name__)

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Queries NCBI Virus API to fetch viral genome sequences.
    
    Args:
        accessions: List of NCBI accession numbers (e.g., ['NC_045512', 'MN908947'])
        
    Returns:
        List of dicts with keys: "accession", "sequence", "family"
        
    Raises:
        RuntimeError: If the API request fails or no data is returned.
    """
    if not accessions:
        logger.warning("No accessions provided to fetch_viral_genomes.")
        return []

    results = []
    missing = []

    # NCBI Virus API endpoint for FASTA download
    # Using the 'download' endpoint with 'format=fasta'
    base_url = "https://www.ncbi.nlm.nih.gov/nuccore"
    
    # Process in batches to avoid URL length limits (NCBI allows ~2000 chars)
    # We'll process individually for simplicity and robustness in this MVP
    for acc in accessions:
        acc = acc.strip()
        if not acc:
            continue
        
        # Construct URL for FASTA download
        # Using esearch/efetch pattern is more robust for specific IDs
        url = f"{base_url}?id={acc}&rettype=fasta&retmode=text"
        
        logger.info(f"Fetching genome for accession: {acc}")
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            if response.status_code == 200:
                fasta_content = response.text
                # Parse FASTA using Biopython
                # We need to handle the case where multiple records might be returned
                # or if the accession is invalid (returns empty or error message)
                
                # Check if content looks like FASTA
                if fasta_content.strip().startswith('>'):
                    # Parse the FASTA content
                    records = list(SeqIO.parse(StringIO(fasta_content), "fasta"))
                    
                    if not records:
                        logger.warning(f"Failed to parse FASTA for {acc}, but response was 200.")
                        missing.append(acc)
                        continue
                    
                    # Take the first record if multiple (should be one per accession)
                    record = records[0]
                    sequence = str(record.seq).upper()
                    
                    # Extract family from description if possible, else default
                    # NCBI FASTA headers usually look like: >accession|...|organism|...
                    # We try to infer family from the header or use a generic placeholder
                    # Since the API doesn't explicitly return 'family' in FASTA header reliably,
                    # we will attempt to extract it or use 'Unknown' if not found.
                    # A more robust approach would use E-utilities to get taxonomy, 
                    # but for MVP we parse the header.
                    header = record.description
                    family = "Unknown"
                    
                    # Heuristic: look for "viridae" or "virinae" in the header
                    # or just extract the organism name part.
                    # For the purpose of this task, we'll extract the text between 
                    # the accession and the first pipe or space, or use the organism name.
                    # Example: >NC_045512.2 Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1...
                    # We'll store the organism name as a proxy for family if "viridae" isn't explicit.
                    parts = header.split('|')
                    if len(parts) > 1:
                        # Often the second part contains organism info
                        org_part = parts[1]
                        if 'viridae' in org_part.lower():
                            family = org_part.split()[0] # Take first word if it ends in viridae
                        else:
                            # Try to find a word ending in viridae
                            words = org_part.split()
                            for w in words:
                                if 'viridae' in w.lower():
                                    family = w
                                    break
                            if family == "Unknown":
                                family = org_part.split()[0] # Just take the first word (genus/organism)
                    else:
                        # Fallback: use the first word after the accession
                        words = header.split()
                        if len(words) > 1:
                            family = words[1]
                    
                    results.append({
                        "accession": acc,
                        "sequence": sequence,
                        "family": family
                    })
                    logger.info(f"Successfully fetched {acc}, length: {len(sequence)}, family: {family}")
                else:
                    logger.warning(f"Invalid FASTA format for {acc} (response: {response.text[:100]})")
                    missing.append(acc)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {acc}: {e}")
            missing.append(acc)
        except Exception as e:
            logger.error(f"Unexpected error processing {acc}: {e}")
            missing.append(acc)

    if missing:
        logger.warning(f"Missing or failed to fetch {len(missing)} accessions: {missing}")

    # Generate manifest
    generate_manifest_v1(accessions, results)

    return results

def generate_manifest_v1(accessions: List[str], results: List[Dict[str, Any]]) -> None:
    """
    Generates data/manifest_v1.json with metadata about the fetched data.
    
    Args:
        accessions: Original list of requested accessions.
        results: List of successfully fetched genome dicts.
    """
    raw_path = Path(DATA_RAW_PATH)
    raw_path.mkdir(parents=True, exist_ok=True)
    
    manifest_path = raw_path / "manifest_v1.json"
    
    # Calculate checksums for the fetched data
    # We create a canonical string representation of the results for checksumming
    data_str = json.dumps(results, sort_keys=True)
    checksum = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    # Determine version (using current timestamp as a proxy for "database release" in this MVP)
    # In a real scenario, this might come from NCBI headers or a specific date.
    timestamp = datetime.utcnow().isoformat()
    
    manifest = {
        "accessions": accessions,
        "source": "NCBI Virus",
        "timestamp": timestamp,
        "version": "latest", # Placeholder, ideally from API
        "checksums": {
            "data": checksum
        },
        "fetched_count": len(results),
        "requested_count": len(accessions)
    }
    
    # Write manifest (overwrite if exists, as per "Do NOT append")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest generated at {manifest_path}")

def generate_manifest_template() -> str:
    """
    Generates a template manifest JSON file.
    (Retained from previous implementation for compatibility)
    """
    template = {
        "accessions": [],
        "source": "",
        "timestamp": "",
        "version": "",
        "checksum_algorithm": "sha256"
    }
    raw_path = Path(DATA_RAW_PATH)
    raw_path.mkdir(parents=True, exist_ok=True)
    path = raw_path / "manifest_template.json"
    with open(path, 'w') as f:
        json.dump(template, f, indent=2)
    return str(path)

def fetch_geo_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Placeholder for GEO data fetching.
    """
    raise NotImplementedError("fetch_geo_data is not yet implemented.")

def generate_manifest_v2(accessions: List[str], results: Dict[str, Any]) -> None:
    """
    Placeholder for GEO manifest generation.
    """
    raise NotImplementedError("generate_manifest_v2 is not yet implemented.")

def main():
    """
    Entry point for download script.
    """
    setup_log_file()
    logger.info("Download skeleton initialized")
    
    # Example usage for testing
    # test_accessions = ["NC_045512"] # SARS-CoV-2
    # if test_accessions:
    #     fetch_viral_genomes(test_accessions)

if __name__ == "__main__":
    main()
