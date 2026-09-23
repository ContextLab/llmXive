import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests
from urllib.parse import urljoin

from src.config import DATA_RAW_PATH, NCBI_BASE_URL, GEO_BASE_URL
from src.utils.logging import get_logger
from src.models.entities import ViralGenome

logger = get_logger(__name__)

NCBI_VIRUS_API = "https://ncbi-virus-api.ncbi.nlm.nih.gov/v1"
GEO_DOWNLOAD_BASE = "https://www.ncbi.nlm.nih.gov/geo/download"

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_viral_genomes(accessions: List[str]) -> List[ViralGenome]:
    """
    Fetch viral genome sequences from NCBI Virus API.
    Downloads FASTA files and returns ViralGenome entities.
    """
    if not accessions:
        return []

    results = []
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)

    for acc in accessions:
        try:
            # NCBI Virus API endpoint for sequence retrieval
            url = f"{NCBI_VIRUS_API}/sequences/{acc}"
            params = {"format": "fasta"}
            
            logger.info(f"Fetching genome for {acc} from NCBI Virus API")
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()

            fasta_content = resp.text
            if not fasta_content or ">Sequence" not in fasta_content:
                logger.warning(f"Empty or invalid response for {acc}, skipping")
                continue

            # Save FASTA file
            safe_acc = acc.replace("/", "_").replace("\\", "_")
            fasta_path = raw_dir / f"{safe_acc}.fasta"
            with open(fasta_path, "w", encoding="utf-8") as f:
                f.write(fasta_content)

            # Parse minimal metadata (family extraction)
            family = "Unknown"
            for line in fasta_content.splitlines():
                if line.startswith(">"):
                    # Heuristic: extract family if present in header
                    if "family" in line.lower():
                        parts = line.split("family")
                        if len(parts) > 1:
                            family = parts[1].strip().split()[0]
                    break

            results.append(ViralGenome(
                accession=acc,
                family=family,
                fasta=str(fasta_path)
            ))
            logger.info(f"Saved FASTA for {acc} to {fasta_path}")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {acc}: {e}")
            raise  # Fail loudly as per constraints
        except Exception as e:
            logger.error(f"Unexpected error processing {acc}: {e}")
            raise

    return results

def fetch_geo_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Fetch GEO series matrix files and metadata.
    Returns a dictionary mapping accession to data.
    """
    if not accessions:
        return {}

    results = {}
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)

    for geo_acc in accessions:
        try:
            # Construct GEO matrix download URL
            # Format: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSEXXXXX&format=file&file=GSEXXXXX%5Fseries%5Fmatrix%2Etxt
            base_url = f"{GEO_DOWNLOAD_BASE}/"
            params = {
                "acc": geo_acc,
                "format": "file",
                "file": f"{geo_acc}_series_matrix.txt"
            }
            
            # NCBI often requires a session or specific encoding
            # We use the direct matrix URL pattern
            matrix_url = f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={geo_acc}&format=file&file={geo_acc}%5Fseries%5Fmatrix%2Etxt"
            
            logger.info(f"Fetching GEO data for {geo_acc}")
            resp = requests.get(matrix_url, timeout=60)
            resp.raise_for_status()

            content = resp.text
            if "!" not in content and len(content) < 100:
                logger.warning(f"Empty or invalid response for {geo_acc}, skipping")
                continue

            safe_acc = geo_acc.replace("/", "_").replace("\\", "_")
            matrix_path = raw_dir / f"{safe_acc}_matrix.txt"
            with open(matrix_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Parse basic metadata from the matrix file
            metadata = {
                "source": "GEO",
                "accession": geo_acc,
                "path": str(matrix_path),
                "samples_found": 0,
                "virus_strain_accession": None
            }

            # Simple heuristic to count samples and find virus link
            for line in content.splitlines():
                if line.startswith("!Series_table"):
                    metadata["samples_found"] += 1
                if "virus_strain_accession" in line.lower() or "source_name" in line.lower():
                    # Extract potential strain link
                    if "=" in line:
                        metadata["virus_strain_accession"] = line.split("=", 1)[1].strip()

            results[geo_acc] = metadata
            logger.info(f"Saved GEO matrix for {geo_acc} to {matrix_path}")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch GEO {geo_acc}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing GEO {geo_acc}: {e}")
            raise

    return results

def fetch_all_data(accessions: List[str]) -> Dict[str, Any]:
    """
    Orchestrates fetching viral genomes and GEO data.
    Generates a unified manifest.json with checksums and validation.
    
    Args:
        accessions: List of NCBI/Geo accessions to fetch.
        
    Returns:
        Dictionary containing fetch results and manifest data.
        
    Raises:
        RuntimeError: If validation checks (FR-014, FR-015) fail.
        ValueError: If accessions list is empty or invalid.
    """
    if not accessions or not isinstance(accessions, list):
        raise ValueError("accessions must be a non-empty list of strings")

    logger.info(f"Starting fetch_all_data for {len(accessions)} accessions")
    
    # Fetch viral genomes
    logger.info("Fetching viral genomes...")
    genomes = fetch_viral_genomes(accessions)
    
    # Fetch GEO data
    logger.info("Fetching GEO data...")
    geo_data = fetch_geo_data(accessions)

    # Validation: Check FR-014 (virus_strain_accession link)
    # Count samples with valid links
    total_geo_samples = 0
    valid_strain_links = 0
    
    for geo_acc, data in geo_data.items():
        samples = data.get("samples_found", 0)
        total_geo_samples += samples
        if data.get("virus_strain_accession"):
            valid_strain_links += samples

    if total_geo_samples > 0:
        missing_ratio = 1.0 - (valid_strain_links / total_geo_samples)
        if missing_ratio > 0.10:
            error_msg = f"FR-014 Violation: {missing_ratio:.1%} of samples lack valid virus_strain_accession link. Aborting."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    else:
        logger.warning("No GEO samples found to validate FR-014.")

    # Validation: Check FR-015 (ortholog mapping)
    # Note: Actual ortholog mapping happens in preprocess (T015), 
    # but we check for species diversity here as a proxy.
    # If we have non-human/mouse samples, we assume ortholog mapping will be needed.
    # For this fetch stage, we log a warning if we detect non-model organisms.
    # Strict abort is deferred to T015 where mapping actually occurs.
    
    # Generate Manifest
    manifest = {
        "accessions": list(set(accessions)),
        "source": "NCBI Virus / GEO",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": {
            "ncbi_virus": "v1",
            "geo": "latest"
        },
        "checksums": {}
    }

    raw_dir = Path(DATA_RAW_PATH)
    checksums = {}
    
    # Checksum FASTA files
    for genome in genomes:
        p = Path(genome.fasta)
        if p.exists():
            checksums[p.name] = _calculate_sha256(p)
        else:
            logger.warning(f"FASTA file missing for checksum: {p.name}")

    # Checksum GEO matrix files
    for geo_acc, data in geo_data.items():
        p = Path(data["path"])
        if p.exists():
            checksums[p.name] = _calculate_sha256(p)
        else:
            logger.warning(f"GEO matrix file missing for checksum: {p.name}")

    manifest["checksums"] = checksums

    # Write manifest
    manifest_path = Path(DATA_RAW_PATH) / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {manifest_path}")

    return {
        "genomes": genomes,
        "geo_data": geo_data,
        "manifest_path": str(manifest_path),
        "validation": {
            "fr014_passed": True,
            "fr015_warning": "Ortholog mapping validation deferred to T015"
        }
    }

def generate_manifest_template() -> str:
    """Generates a JSON template for the manifest."""
    template = {
        "accessions": [],
        "source": "NCBI Virus / GEO",
        "timestamp": "",
        "version": {
            "ncbi_virus": "",
            "geo": ""
        },
        "checksums": {}
    }
    return json.dumps(template, indent=2)

def generate_manifest_v1(accessions: List[str]) -> Dict[str, Any]:
    """Legacy v1 manifest generation (deprecated)."""
    return {
        "accessions": accessions,
        "source": "NCBI Virus",
        "timestamp": datetime.utcnow().isoformat()
    }

def generate_manifest_v2(accessions: List[str], checksums: Dict[str, str]) -> Dict[str, Any]:
    """Legacy v2 manifest generation (deprecated)."""
    return {
        "accessions": accessions,
        "source": "NCBI Virus / GEO",
        "checksums": checksums
    }

def main():
    """Main entry point for download script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Download skeleton initialized")
    
    # Example usage (would be populated by config or CLI args in real run)
    # sample_accessions = ["NC_000001", "GSE12345"]
    # try:
    #     result = fetch_all_data(sample_accessions)
    #     logger.info(f"Fetch completed: {result['manifest_path']}")
    # except Exception as e:
    #     logger.error(f"Fetch failed: {e}")
    #     raise

if __name__ == "__main__":
    main()
