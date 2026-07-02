import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests
from Bio import SeqIO
from src.config import DATA_RAW_PATH, NCBI_BASE_URL, SEED
from src.utils.logging import get_logger

logger = get_logger(__name__)

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Queries NCBI Virus API to fetch viral genome sequences.
    Returns a list of dicts with keys: "accession", "sequence", "family".
    Logs warnings for missing accessions per FR-013.
    """
    if not accessions:
        logger.warning("No accessions provided to fetch_viral_genomes")
        return []

    results = []
    failed_accessions = []

    # NCBI Virus API endpoint for bulk download or individual queries
    # Using the E-utilities (EFetch) interface for reliable FASTA retrieval
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    # Default parameters for NCBI Virus (viral_genome)
    params = {
        "db": "nuccore",
        "rettype": "fasta",
        "retmode": "text"
    }

    # Batch processing to avoid URL length limits and rate limits
    # NCBI recommends max 200 IDs per request, but we'll do smaller batches for safety
    batch_size = 50
    
    for i in range(0, len(accessions), batch_size):
        batch = accessions[i:i+batch_size]
        params["id"] = ",".join(batch)
        
        try:
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            fasta_text = response.text
            
            # Parse FASTA text
            records = list(SeqIO.parse(fasta_text.splitlines(), "fasta"))
            
            for record in records:
                accession = record.id.split("|")[0] if "|" in record.id else record.id
                # Try to extract family from description if available
                description = record.description.lower()
                family = "unknown"
                if "family" in description:
                    # Simple heuristic: look for "family: name" pattern
                    parts = description.split("family:")
                    if len(parts) > 1:
                        family = parts[1].split()[0].strip()
                
                results.append({
                    "accession": accession,
                    "sequence": str(record.seq),
                    "family": family
                })
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching batch {batch}: {e}")
            failed_accessions.extend(batch)
        except Exception as e:
            logger.error(f"Error parsing batch {batch}: {e}")
            failed_accessions.extend(batch)

    # Log warnings for missing accessions
    missing = set(accessions) - set(r["accession"] for r in results)
    for acc in missing:
        logger.warning(f"Accession {acc} not found or could not be retrieved")
        failed_accessions.append(acc)

    if failed_accessions:
        logger.warning(f"Failed to retrieve {len(failed_accessions)} accessions: {failed_accessions}")

    # Generate manifest
    _generate_manifest_v1(accessions, results)

    return results

def _generate_manifest_v1(requested_accessions: List[str], results: List[Dict[str, Any]]) -> None:
    """
    Generates data/manifest_v1.json with keys:
    - accessions: list of requested accessions
    - source: "NCBI Virus"
    - timestamp: ISO8601
    - version: database release (from headers or default)
    - checksums: SHA-256 of file bytes
    """
    # Create data/raw directory if it doesn't exist
    raw_path = Path(DATA_RAW_PATH)
    raw_path.mkdir(parents=True, exist_ok=True)
    
    # Calculate checksums for the raw FASTA file we would have downloaded
    # Since we're streaming, we'll compute checksum of the concatenated sequences
    manifest_path = raw_path / "manifest_v1.json"
    
    # For this implementation, we'll create a manifest of the retrieved data
    # In a real scenario, we'd checksum the actual FASTA file
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # We need to reconstruct what the FASTA content would be for checksum
    fasta_content = ""
    for r in results:
        fasta_content += f">{r['accession']}\n{r['sequence']}\n"
    
    checksum = hashlib.sha256(fasta_content.encode('utf-8')).hexdigest()
    
    manifest = {
        "accessions": requested_accessions,
        "source": "NCBI Virus",
        "timestamp": timestamp,
        "version": "latest",  # NCBI doesn't provide explicit version in API, using "latest"
        "checksums": {
            "sha256": checksum
        }
    }
    
    # Write manifest - DO NOT append, overwrite
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest written to {manifest_path}")

def generate_manifest_template() -> str:
    """
    Creates a JSON template for the manifest file.
    """
    template = {
        "accessions": [],
        "source": "",
        "timestamp": "",
        "version": "",
        "checksum_algorithm": "sha256"
    }
    return json.dumps(template, indent=2)

def fetch_geo_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Downloads GEO series matrix files and parses metadata.
    Returns dict mapping sample_id to strain_accession.
    Raises NotImplementedError as per original stub.
    """
    raise NotImplementedError("fetch_geo_data not yet implemented")

def generate_manifest_v2() -> None:
    """
    Generates data/manifest_v2.json for GEO data.
    """
    raw_path = Path(DATA_RAW_PATH)
    manifest_path = raw_path / "manifest_v2.json"
    
    manifest = {
        "accessions": [],
        "source": "GEO",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "latest",
        "checksums": {}
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"GEO manifest written to {manifest_path}")

def main():
    """
    Entry point for download module.
    """
    logger.info("Download module initialized")
    
    # Example usage with a small test set
    test_accessions = ["NC_001802", "NC_001803"]  # Small test set
    results = fetch_viral_genomes(test_accessions)
    logger.info(f"Retrieved {len(results)} viral genomes")

if __name__ == "__main__":
    main()
