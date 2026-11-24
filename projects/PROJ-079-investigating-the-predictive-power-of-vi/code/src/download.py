import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import requests

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

def _calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _extract_strain_accession_from_metadata(metadata_path: Path) -> Optional[str]:
    """
    Extracts virus_strain_accession from the metadata JSON file.
    Searches for 'virus_strain_accession' key or parses
    'Sample_characteristics_ch1' if JSON structure varies.
    """
    try:
        with metadata_path.open('r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read metadata file {metadata_path}: {e}")
        return None

    # Direct key
    if isinstance(meta, dict):
        if 'virus_strain_accession' in meta:
            return meta['virus_strain_accession']

    # Fallback: look for a string containing "strain" in Sample_characteristics_ch1
    # This mirrors the parsing logic described in the task.
    # The metadata may be a dict with a key like 'Sample_characteristics_ch1'
    # containing a list or string.
    for key in ['Sample_characteristics_ch1', 'Sample_title']:
        val = meta.get(key)
        if isinstance(val, str):
            # Look for pattern "strain <accession>"
            parts = val.split()
            for i, part in enumerate(parts):
                if part.lower() == 'strain' and i + 1 < len(parts):
                    accession = parts[i + 1]
                    # Basic sanity check: accession strings are alphanumeric
                    if accession.isalnum():
                        return accession
    return None

def get_ncbi_version() -> str:
    """
    Query the NCBI Virus API for the current database release version.
    Returns a version string. Raises RuntimeError if the request fails.
    """
    api_url = "https://api.ncbi.nlm.nih.gov/datasets/v1.0/genome/virus"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # The exact field name may vary; attempt a few common possibilities.
        version = (
            data.get("metadata", {}).get("release_version")
            or data.get("release_version")
            or data.get("version")
            or "unknown"
        )
        logger.info(f"Retrieved NCBI Virus database version: {version}")
        return str(version)
    except Exception as exc:
        logger.error(f"Failed to retrieve NCBI Virus version: {exc}")
        raise RuntimeError("Unable to obtain NCBI Virus database release version") from exc

def generate_manifest(accessions: List[str], geo_accessions: List[str]) -> None:
    """
    Creates a SINGLE unified data/manifest.json containing:
    - accessions: list of all NCBI and GEO IDs
    - source: NCBI Virus / GEO
    - timestamp: ISO8601
    - version: database release versions (NCBI version)
    - file_checksum: SHA-256 checksums of each data file (FASTA, counts, metadata)
    - database_release_version: string from get_ncbi_version()
    - n_strains_initial: integer count of unique strains found in GEO metadata

    Critical validation:
    - Abort with RuntimeError("FATAL: Strain link validation failed") if >10%
      of initial candidate GEO samples lack a valid virus_strain_accession.
    - Missing individual genome files generate a warning and are excluded
      from the manifest (fallback logic).

    The manifest is written to data/manifest.json.
    """
    logger.info("Starting manifest generation")
    # Ensure output directory exists
    manifest_path = Path("data") / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Retrieve NCBI version
    ncbi_version = get_ncbi_version()

    # Prepare containers
    file_checksums: Dict[str, str] = {}
    valid_accessions: List[str] = []
    strain_accessions_set: set = set()
    missing_strain_count = 0
    total_geo_samples = 0

    # Process viral genome files
    for acc in list(accessions):  # copy to allow removal
        fasta_path = Path(DATA_RAW_PATH) / f"{acc}.fasta"
        if not fasta_path.is_file():
            logger.warning(f"FASTA file missing for accession {acc}; excluding from manifest")
            continue  # fallback: exclude this genome
        checksum = _calculate_sha256(fasta_path)
        file_checksums[str(fasta_path)] = checksum
        valid_accessions.append(acc)

    # Process GEO files (counts + metadata)
    for geo_acc in geo_accessions:
        counts_path = Path(DATA_RAW_PATH) / f"{geo_acc}_counts.tsv"
        metadata_path = Path(DATA_RAW_PATH) / f"{geo_acc}_metadata.json"

        # Counts file checksum (if present)
        if counts_path.is_file():
            file_checksums[str(counts_path)] = _calculate_sha256(counts_path)
        else:
            logger.warning(f"Counts file missing for GEO accession {geo_acc}")

        # Metadata processing
        if metadata_path.is_file():
            file_checksums[str(metadata_path)] = _calculate_sha256(metadata_path)
            strain = _extract_strain_accession_from_metadata(metadata_path)
            total_geo_samples += 1
            if strain:
                strain_accessions_set.add(strain)
            else:
                missing_strain_count += 1
        else:
            logger.warning(f"Metadata file missing for GEO accession {geo_acc}")

    # Validation of strain linkage
    if total_geo_samples == 0:
        logger.error("No GEO metadata files found; cannot validate strain links")
        raise RuntimeError("FATAL: Strain link validation failed")
    missing_fraction = missing_strain_count / total_geo_samples
    if missing_fraction > 0.10:
        logger.error(
            f"{missing_fraction:.2%} of GEO samples lack a valid strain link "
            f"({missing_strain_count}/{total_geo_samples})"
        )
        raise RuntimeError("FATAL: Strain link validation failed")

    # Build manifest dictionary
    manifest_dict = {
        "accessions": valid_accessions + geo_accessions,
        "source": "NCBI Virus / GEO",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": ncbi_version,
        "file_checksum": file_checksums,
        "database_release_version": ncbi_version,
        "n_strains_initial": len(strain_accessions_set)
    }

    # Write manifest
    with manifest_path.open('w', encoding='utf-8') as mf:
        json.dump(manifest_dict, mf, indent=2)

    logger.info(f"Manifest successfully written to {manifest_path}")

def main():
    """
    Entry point for the download module.
    Initializes the download skeleton and generates the manifest template.
    """
    logger.info("Download skeleton initialized")
    generate_manifest_template()

if __name__ == "__main__":
    main()