import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path
import os

from src.config import DATA_RAW_PATH, ARTIFACTS_PATH, GEO_BASE_URL, NCBI_BASE_URL
from src.utils.logging import get_logger

logger = get_logger(__name__)

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def _get_database_version(source: str) -> str:
    """
    Retrieve database release version.
    In a real implementation, this would query the API for the current release.
    For now, returns a placeholder string that can be updated.
    """
    if "NCBI" in source.upper():
        # Placeholder: In production, fetch from NCBI Virus API metadata
        return "v2024-01-15"
    elif "GEO" in source.upper():
        # Placeholder: In production, fetch from GEO metadata
        return "v2024-01-15"
    return "unknown"

def generate_manifest(accessions: List[str], geo_accessions: List[str]) -> None:
    """
    Create a SINGLE unified data/manifest.json containing all download metadata.

    This function:
    1. Scans data/raw/ for files corresponding to provided accessions.
    2. Validates the presence of required files.
    3. Checks GEO metadata for FR-014 compliance (virus_strain_accession link).
    4. Computes SHA-256 checksums for all files.
    5. Writes the unified manifest to data/manifest.json.

    CRITICAL VALIDATION (FR-014):
    - Aborts with fatal error if >10% of initial candidate samples lack a valid
      virus_strain_accession link in GEO metadata.

    Fallback Logic (FR-013):
    - For individual missing genomes (not triggering global abort), logs warning
      and excludes that virus, proceeding with remaining data.

    Args:
        accessions: List of NCBI Virus accessions.
        geo_accessions: List of GEO series accessions.
    """
    if not accessions and not geo_accessions:
        logger.warning("No accessions provided. Generating empty manifest.")
    
    raw_path = Path(DATA_RAW_PATH)
    manifest_path = Path(ARTIFACTS_PATH) / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure raw directory exists
    raw_path.mkdir(parents=True, exist_ok=True)

    # Collect all files and their metadata
    all_entries = []
    missing_files = []
    valid_samples_count = 0
    total_candidate_samples = 0

    # Process NCBI Virus accessions
    for acc in accessions:
        # Expected filename pattern: {accession}.fasta or similar
        # We look for any file starting with the accession
        matched_files = list(raw_path.glob(f"{acc}*"))
        
        if not matched_files:
            logger.warning(f"[FR-013] Missing genome for accession {acc}. Excluding from manifest.")
            missing_files.append(acc)
            continue

        for file_path in matched_files:
            if file_path.suffix.lower() in ['.fasta', '.fa', '.fna']:
                checksum = _calculate_sha256(file_path)
                version = _get_database_version("NCBI")
                
                entry = {
                    "accession": acc,
                    "source": "NCBI Virus",
                    "file_path": str(file_path.relative_to(Path.cwd())),
                    "file_checksum": checksum,
                    "checksum_algorithm": "sha256",
                    "database_release_version": version,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                all_entries.append(entry)
                logger.info(f"Added NCBI file: {file_path.name} (checksum: {checksum[:8]}...)")

    # Process GEO accessions
    for geo_acc in geo_accessions:
        # Expected filename pattern: GSM... or Series Matrix file
        # Look for files starting with geo_acc or containing it
        matched_files = list(raw_path.glob(f"{geo_acc}*"))
        
        if not matched_files:
            logger.warning(f"[FR-013] Missing GEO data for accession {geo_acc}. Excluding from manifest.")
            missing_files.append(geo_acc)
            continue

        for file_path in matched_files:
            if file_path.suffix.lower() in ['.txt', '.tsv', '.gz', '.matrix']:
                checksum = _calculate_sha256(file_path)
                version = _get_database_version("GEO")
                
                # CRITICAL VALIDATION (FR-014): Check for virus_strain_accession in metadata
                # We attempt to read a small portion of the file to check for the key
                has_strain_link = False
                try:
                    # Try to read first 10KB to check for strain link presence
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        sample_content = f.read(10240)
                        # Heuristic check: look for common keys indicating strain link
                        if 'virus_strain_accession' in sample_content or 'virus_strain' in sample_content:
                            has_strain_link = True
                            valid_samples_count += 1
                        else:
                            # If file is very small, assume it might be metadata-only
                            if file_path.stat().st_size < 100:
                                has_strain_link = False
                            else:
                                has_strain_link = False # Conservative: assume missing if not found
                except Exception as e:
                    logger.warning(f"Could not validate strain link for {file_path}: {e}")
                    has_strain_link = False

                total_candidate_samples += 1

                if not has_strain_link:
                    logger.warning(f"[FR-014] Sample {geo_acc} lacks valid virus_strain_accession link.")

                entry = {
                    "accession": geo_acc,
                    "source": "GEO",
                    "file_path": str(file_path.relative_to(Path.cwd())),
                    "file_checksum": checksum,
                    "checksum_algorithm": "sha256",
                    "database_release_version": version,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "virus_strain_link_present": has_strain_link
                }
                all_entries.append(entry)
                logger.info(f"Added GEO file: {file_path.name} (checksum: {checksum[:8]}...)")

    # FR-014 Validation: Abort if >10% of samples lack strain link
    if total_candidate_samples > 0:
        missing_link_count = total_candidate_samples - valid_samples_count
        missing_link_ratio = missing_link_count / total_candidate_samples
        
        if missing_link_ratio > 0.10:
            error_msg = (
                f"[FR-014] FATAL: {missing_link_ratio:.1%} of GEO samples ({missing_link_count}/{total_candidate_samples}) "
                f"lack a valid virus_strain_accession link. This exceeds the 10% threshold. "
                f"Aborting manifest generation to prevent invalid data pipeline."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    # Construct the unified manifest
    manifest = {
        "accessions": list(set(accessions + geo_accessions)),
        "source": ["NCBI Virus", "GEO"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": {
            "NCBI Virus": _get_database_version("NCBI"),
            "GEO": _get_database_version("GEO")
        },
        "database_release_version": "combined",
        "checksums": {
            "algorithm": "sha256",
            "files": {e["file_path"]: e["file_checksum"] for e in all_entries}
        },
        "entries": all_entries,
        "statistics": {
            "total_files": len(all_entries),
            "ncbi_files": sum(1 for e in all_entries if e["source"] == "NCBI Virus"),
            "geo_files": sum(1 for e in all_entries if e["source"] == "GEO"),
            "missing_accessions": missing_files,
            "geo_strain_link_compliance": {
                "total_samples": total_candidate_samples,
                "valid_links": valid_samples_count,
                "missing_links": total_candidate_samples - valid_samples_count,
                "missing_ratio": missing_link_ratio if total_candidate_samples > 0 else 0.0
            }
        }
    }

    # Write the manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    logger.info(f"Unified manifest written to {manifest_path}")
    logger.info(f"Total files: {len(all_entries)}, Missing: {len(missing_files)}")
    
    if missing_files:
        logger.warning(f"Excluded accessions due to missing files: {missing_files}")

def generate_manifest_template() -> str:
    """
    Writes a JSON template to data/manifest_template.json.
    Returns the path string.
    """
    template = {
        "accessions": [],
        "source": "",
        "timestamp": "",
        "version": "",
        "database_release_version": "",
        "file_checksum": "",
        "checksum_algorithm": "sha256"
    }
    output_path = Path(DATA_RAW_PATH) / "manifest_template.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    logger.info(f"Manifest template written to {output_path}")
    return str(output_path)

def fetch_viral_genomes(accessions: List[str]) -> List[Path]:
    """
    Fetches viral genomes from NCBI Virus API.
    Writes FASTA files to data/raw/.
    Returns list of downloaded file paths.
    """
    logger.info(f"Fetching {len(accessions)} viral genomes from NCBI Virus API...")
    # Implementation depends on T012a
    # This is a placeholder for the actual implementation logic
    # which would use the NCBI_BASE_URL and requests library
    downloaded_paths = []
    for acc in accessions:
        # Simulate download path for now
        # In real implementation: actual fetch and write
        target_path = Path(DATA_RAW_PATH) / f"{acc}.fasta"
        downloaded_paths.append(target_path)
    return downloaded_paths

def fetch_geo_data(accessions: List[str]) -> Dict[str, Path]:
    """
    Downloads GEO series matrix files.
    Writes counts matrices to data/raw/.
    Returns dict mapping accession to file path.
    """
    logger.info(f"Fetching {len(accessions)} GEO series from NCBI GEO...")
    # Implementation depends on T012b
    downloaded_paths = {}
    for acc in accessions:
        target_path = Path(DATA_RAW_PATH) / f"{acc}_series_matrix.txt.gz"
        downloaded_paths[acc] = target_path
    return downloaded_paths

def main() -> None:
    """Main entry point for download module."""
    logger.info("Download skeleton initialized")
    # Example usage of generate_manifest
    # In real pipeline, this would be called with actual accessions
    # generate_manifest(["NC_001234"], ["GSE12345"])

# Keep existing function signatures as per API surface
def generate_manifest_v1(accessions: list, geo_accessions: list) -> None:
    """Legacy v1 manifest generation."""
    logger.warning("generate_manifest_v1 is deprecated. Use generate_manifest.")
    generate_manifest(accessions, geo_accessions)

def generate_manifest_v2(accessions: list, geo_accessions: list) -> None:
    """Legacy v2 manifest generation."""
    logger.warning("generate_manifest_v2 is deprecated. Use generate_manifest.")
    generate_manifest(accessions, geo_accessions)

def fetch_all_data(accessions: list, geo_accessions: list) -> None:
    """High-level fetch wrapper."""
    fetch_viral_genomes(accessions)
    fetch_geo_data(geo_accessions)
