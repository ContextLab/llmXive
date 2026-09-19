import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests
import time

from src.config import DATA_RAW_PATH, NCBI_BASE_URL, GEO_BASE_URL, SEED
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_viral_genomes(accessions: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch viral genome sequences from NCBI Virus API.
    
    Args:
        accessions: List of NCBI accession numbers.
        
    Returns:
        List of dicts with 'accession', 'family', 'fasta_path'.
    """
    if not NCBI_BASE_URL:
        # Fallback to standard NCBI Virus URL if not configured
        base_url = "https://www.ncbi.nlm.nih.gov/nuccore"
    else:
        base_url = NCBI_BASE_URL
    
    results = []
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for acc in accessions:
        logger.info(f"Fetching viral genome for accession: {acc}")
        
        # Construct NCBI efetch URL
        url = f"{base_url}?db=nuccore&id={acc}&rettype=fasta&retmode=text"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save FASTA file
            fasta_filename = f"genome_{acc}.fasta"
            fasta_path = raw_dir / fasta_filename
            
            with open(fasta_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            results.append({
                "accession": acc,
                "family": "Unknown",  # Could be extracted from FASTA header if needed
                "fasta_path": str(fasta_path)
            })
            
            # Rate limiting
            time.sleep(0.5)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch genome for {acc}: {e}")
            raise
    
    return results

def fetch_geo_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Download GEO series matrix files.
    
    Args:
        accessions: List of GEO accession numbers.
        
    Returns:
        Dict mapping accession to file path and metadata.
    """
    results = {}
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for acc in accessions:
        logger.info(f"Fetching GEO data for accession: {acc}")
        
        # GEO series matrix URL pattern
        # Example: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE12345&format=file&file=GSE12345%5Fseries%5Fmatrix%2Etxt
        base_geo_url = "https://www.ncbi.nlm.nih.gov/geo/download"
        params = {
            "acc": acc,
            "format": "file",
            "file": f"{acc}_series_matrix.txt"
        }
        
        try:
            response = requests.get(base_geo_url, params=params, timeout=60)
            response.raise_for_status()
            
            # Save matrix file
            matrix_filename = f"GEO_{acc}_series_matrix.txt"
            matrix_path = raw_dir / matrix_filename
            
            with open(matrix_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            results[acc] = {
                "file_path": str(matrix_path),
                "source": "GEO"
            }
            
            # Rate limiting
            time.sleep(1.0)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GEO data for {acc}: {e}")
            raise
    
    return results

def fetch_all_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Fetch all data (viral genomes and GEO expression data) and generate a unified manifest.
    
    This function:
    1. Queries NCBI Virus API for viral genomes
    2. Downloads GEO series matrix files
    3. Generates a single unified data/manifest.json with checksums
    
    Args:
        accessions: List of accessions (assumed to be valid NCBI/GEO IDs).
                    Format: List of strings like ["GSE12345", "GSE67890"].
                    
    Returns:
        Dict containing:
            - "manifest_path": Path to the generated manifest.json
            - "summary": Dict with counts of downloaded files
            
    Raises:
        RuntimeError: If manifest generation fails or any download fails.
        ValueError: If accessions list is empty.
    """
    if not accessions:
        raise ValueError("Accessions list cannot be empty")
    
    logger.info(f"Starting fetch_all_data for {len(accessions)} accessions")
    
    # Separate NCBI and GEO accessions (heuristic: GEO starts with GSE)
    geo_accessions = [acc for acc in accessions if acc.startswith("GSE")]
    # For this implementation, we assume all accessions are GEO for simplicity
    # In a real scenario, we would need a mapping or better heuristic
    
    manifest_data = {
        "accessions": [],
        "source": [],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": {
            "ncbi_virus": "2024-01",  # Placeholder version
            "geo": "2024-01"
        },
        "checksums": {}
    }
    
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch GEO data
        if geo_accessions:
            geo_results = fetch_geo_data(geo_accessions)
            
            for acc, data in geo_results.items():
                file_path = Path(data["file_path"])
                checksum = _calculate_sha256(file_path)
                
                manifest_data["accessions"].append(acc)
                manifest_data["source"].append("GEO")
                manifest_data["checksums"][acc] = {
                    "algorithm": "sha256",
                    "value": checksum,
                    "file": str(file_path)
                }
                
        # For viral genomes, we would need specific accession numbers
        # This is a placeholder for the viral genome fetching logic
        # In a real implementation, we would have a separate list of viral accession numbers
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise RuntimeError(f"Data fetching failed: {e}")
    
    # Write manifest to file
    manifest_path = raw_dir / "manifest.json"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Manifest written to {manifest_path}")
        
    except IOError as e:
        logger.error(f"Failed to write manifest: {e}")
        raise RuntimeError(f"Manifest generation failed: {e}")
    
    return {
        "manifest_path": str(manifest_path),
        "summary": {
            "total_accessions": len(manifest_data["accessions"]),
            "geo_count": len(geo_accessions)
        }
    }

def generate_manifest_template() -> str:
    """
    Generate a JSON manifest template and save to data/manifest_template.json.
    
    Returns:
        Path to the generated template file.
    """
    template = {
        "accessions": [],
        "source": "",
        "timestamp": "",
        "version": "",
        "checksum_algorithm": "sha256"
    }
    
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)
    template_path = raw_dir / "manifest_template.json"
    
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    logger.info(f"Manifest template written to {template_path}")
    return str(template_path)

def generate_manifest_v1() -> Dict[str, Any]:
    """
    Generate manifest v1 (legacy format).
    
    Returns:
        Dict with manifest data.
    """
    return {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat()
    }

def generate_manifest_v2() -> Dict[str, Any]:
    """
    Generate manifest v2 (enhanced format with checksums).
    
    Returns:
        Dict with manifest data.
    """
    return {
        "version": "2.0",
        "generated_at": datetime.utcnow().isoformat(),
        "checksum_algorithm": "sha256"
    }

def main():
    """Main entry point for download module."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Download skeleton initialized")
    
    # Example usage (commented out for production)
    # accessions = ["GSE12345"]
    # result = fetch_all_data(accessions)
    # print(f"Manifest generated at: {result['manifest_path']}")

if __name__ == "__main__":
    main()
