"""
Data acquisition module for fetching FASTQ files from NCBI GEO/SRA.

This module implements FR-001: Real data acquisition.
- Real mode: Fetches actual FASTQ files from NCBI SRA.
- Synthetic mode: Loads pre-generated data from data/synthetic/ (does NOT generate).

Outputs:
- FASTQ files in data/raw/{accession_id}_R1.fastq.gz, ..._R2.fastq.gz
- Manifest in data/manifests/{study}_manifest.json with checksums
"""
import os
import sys
import json
import hashlib
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import requests
from tqdm import tqdm

# Import from project utilities
from src.utils.logger import get_logger
from src.utils.config import get_data_path
from src.utils.schemas import ManifestEntry, DataManifest, ProvenanceInfo

logger = get_logger(__name__)

# Constants
SRA_URL_BASE = "https://sra-download.blast.ncbi.nlm.nih.gov/traces/sra"
GEO_URL_BASE = "https://www.ncbi.nlm.nih.gov/geo/query/acc/download"
EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Pre-defined real study accession for testing/prototype
# Using a small, well-documented plant RNA-seq study: GSE12345 (example)
# In production, this would be a list from a configuration or manifest
REAL_STUDY_ACCESSIONS = [
    # Using a real, small plant study: GSE12345 is placeholder, replacing with real small study
    # Real study: GSE96395 - Arabidopsis thaliana defense response (small subset)
    "SRR5214625",  # R1
    "SRR5214626",  # R2 (paired)
]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_sra_accession_info(accession_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for an SRA accession from NCBI E-utilities.
    
    Args:
        accession_id: SRA accession (e.g., SRR123456)
        
    Returns:
        Dictionary with metadata including download URLs
        
    Raises:
        RuntimeError: If metadata fetch fails
    """
    params = {
        "db": "sra",
        "id": accession_id,
        "retmode": "json",
        "tool": "plant-defense-pipeline",
        "email": "pipeline@llmxive.local"
    }
    
    try:
        response = requests.get(EUTILS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" not in data or accession_id not in data["result"]:
            raise RuntimeError(f"No metadata found for accession {accession_id}")
        
        return data["result"][accession_id]
    except requests.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession_id}: {e}")
        raise RuntimeError(f"NCBI E-utilities request failed for {accession_id}") from e

def get_fastq_download_url(accession_id: str, run_number: int = 1) -> Optional[str]:
    """
    Construct the direct download URL for FASTQ files from SRA.
    
    Args:
        accession_id: SRA accession ID
        run_number: 1 for R1, 2 for R2
        
    Returns:
        Direct download URL or None if not found
    """
    # Use SRA Toolkit's prefetch/ftp approach for reliability
    # For direct HTTP, we construct the URL based on SRA structure
    base_url = f"https://sra-download.blast.ncbi.nlm.nih.gov/traces/sra/{accession_id[:3]}/{accession_id}"
    
    # Try to find the actual FTP path via E-utilities first
    try:
        info = fetch_sra_accession_info(accession_id)
        # Extract file URLs from the response
        if "files" in info:
            for file_info in info["files"]:
                if file_info.get("type") == "fastq" and file_info.get("ext") == "fastq":
                    # Determine R1 vs R2
                    if run_number == 1 and "1" in file_info.get("name", ""):
                        return file_info.get("url")
                    elif run_number == 2 and "2" in file_info.get("name", ""):
                        return file_info.get("url")
    except Exception as e:
        logger.warning(f"Could not extract direct URL for {accession_id}: {e}")
    
    # Fallback: construct standard SRA URL pattern
    # This pattern works for many recent SRA entries
    ftp_base = f"ftp://ftp.sra.ebi.ebi.ac.uk/vol1/fastq/{accession_id[:6]}/{accession_id}"
    return f"{ftp_base}_{run_number}.fastq.gz"

def download_file_with_progress(url: str, output_path: Path, chunk_size: int = 1024 * 1024) -> bool:
    """
    Download a file with progress bar and error handling.
    
    Args:
        url: Download URL
        output_path: Destination path
        chunk_size: Bytes per chunk
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True, timeout=600)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            desc=output_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def download_fastq_from_sra(accession_id: str, output_dir: Path, mode: str = "real") -> Tuple[Optional[Path], Optional[Path]]:
    """
    Download FASTQ files for a given SRA accession.
    
    Args:
        accession_id: SRA accession ID (e.g., SRR123456)
        output_dir: Directory to save files
        mode: "real" or "synthetic"
        
    Returns:
        Tuple of (R1_path, R2_path) or (None, None) on failure
        
    Raises:
        RuntimeError: If mode is "real" and download fails
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if mode == "synthetic":
        # Synthetic mode: do not download, just return None (caller handles loading)
        logger.info(f"Synthetic mode: skipping download for {accession_id}")
        return None, None
    
    # Real mode: fetch actual data
    logger.info(f"Fetching real FASTQ data for {accession_id}...")
    
    # Try to get metadata first
    try:
        metadata = fetch_sra_accession_info(accession_id)
        is_paired = metadata.get("library_layout", "").lower() == "paired"
    except Exception as e:
        logger.error(f"Failed to get metadata for {accession_id}: {e}")
        raise RuntimeError(f"Cannot fetch metadata for {accession_id}") from e
    
    r1_path = output_dir / f"{accession_id}_R1.fastq.gz"
    r2_path = output_dir / f"{accession_id}_R2.fastq.gz" if is_paired else None
    
    # Try direct download URL construction
    urls_to_try = []
    
    # Method 1: EBI FTP
    urls_to_try.append(f"ftp://ftp.sra.ebi.ebi.ac.uk/vol1/fastq/{accession_id[:6]}/{accession_id}/{accession_id}_1.fastq.gz")
    if is_paired:
        urls_to_try.append(f"ftp://ftp.sra.ebi.ebi.ac.uk/vol1/fastq/{accession_id[:6]}/{accession_id}/{accession_id}_2.fastq.gz")
    
    # Method 2: NCBI SRA direct
    urls_to_try.append(f"https://sra-download.blast.ncbi.nlm.nih.gov/traces/sra{accession_id[:3]}/{accession_id}/{accession_id}_1.fastq.gz")
    if is_paired:
        urls_to_try.append(f"https://sra-download.blast.ncbi.nlm.nih.gov/traces/sra{accession_id[:3]}/{accession_id}/{accession_id}_2.fastq.gz")
    
    success_r1 = False
    success_r2 = False
    
    for i in range(0, len(urls_to_try), 2):
        url_r1 = urls_to_try[i]
        url_r2 = urls_to_try[i+1] if i+1 < len(urls_to_try) else None
        
        logger.info(f"Attempting download from: {url_r1}")
        
        if download_file_with_progress(url_r1, r1_path):
            success_r1 = True
            logger.info(f"Successfully downloaded R1: {r1_path}")
            
            if url_r2 and r2_path:
                if download_file_with_progress(url_r2, r2_path):
                    success_r2 = True
                    logger.info(f"Successfully downloaded R2: {r2_path}")
                    break
                else:
                    # R2 failed, remove R1 and retry
                    r1_path.unlink()
                    success_r1 = False
        else:
            logger.warning(f"Failed to download from {url_r1}, trying next source...")
    
    if not success_r1:
        error_msg = f"Failed to download R1 for {accession_id} from all sources"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    if is_paired and not success_r2:
        error_msg = f"Failed to download R2 for {accession_id} from all sources"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    return r1_path, r2_path

def fetch_geosamples_study(study_id: str) -> List[str]:
    """
    Fetch sample accession IDs for a GEO study.
    
    Args:
        study_id: GEO study accession (e.g., GSE12345)
        
    Returns:
        List of sample accessions (SRR or GSM IDs)
    """
    # For this implementation, we work directly with SRA accessions
    # In a full implementation, this would resolve GSE -> GSM -> SRR
    logger.warning("fetch_geosamples_study: Direct SRA accession mode active")
    return [study_id]  # Treat input as SRA accession for now

def create_manifest_entry(
    accession_id: str,
    file_paths: List[Path],
    source: str = "ncbi_sra",
    mode: str = "real"
) -> ManifestEntry:
    """
    Create a manifest entry for downloaded files.
    
    Args:
        accession_id: SRA/GEO accession ID
        file_paths: List of downloaded file paths
        source: Data source identifier
        mode: "real" or "synthetic"
        
    Returns:
        ManifestEntry object
    """
    entries = []
    checksums = {}
    
    for path in file_paths:
        if path.exists():
            checksum = calculate_sha256(path)
            checksums[path.name] = checksum
            entries.append({
                "file_name": path.name,
                "file_path": str(path),
                "checksum": checksum,
                "size_bytes": path.stat().st_size
            })
    
    provenance = ProvenanceInfo(
        source=source,
        mode=mode,
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        accession_id=accession_id
    )
    
    return ManifestEntry(
        accession_id=accession_id,
        files=entries,
        checksums=checksums,
        provenance=provenance
    )

def save_manifest(manifest: DataManifest, output_path: Path) -> None:
    """
    Save manifest to JSON file.
    
    Args:
        manifest: DataManifest object
        output_path: Output file path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest.model_dump(), f, indent=2)
    
    logger.info(f"Manifest saved to {output_path}")

def validate_downloaded_files(entry: ManifestEntry) -> bool:
    """
    Validate that downloaded files match their checksums.
    
    Args:
        entry: ManifestEntry with file paths and checksums
        
    Returns:
        True if all files validate, False otherwise
    """
    for file_info in entry.files:
        file_path = Path(file_info["file_path"])
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            return False
        
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != file_info["checksum"]:
            logger.error(f"Checksum mismatch for {file_path}: expected {file_info['checksum']}, got {actual_checksum}")
            return False
    
    logger.info(f"All files validated for {entry.accession_id}")
    return True

def download_study(
    accession_ids: List[str],
    output_dir: Path,
    manifest_dir: Path,
    mode: str = "real"
) -> DataManifest:
    """
    Download multiple studies/accessions and create a manifest.
    
    Args:
        accession_ids: List of SRA/GEO accession IDs
        output_dir: Directory for FASTQ files (data/raw)
        manifest_dir: Directory for manifest files (data/manifests)
        mode: "real" or "synthetic"
        
    Returns:
        DataManifest with all entries
    """
    output_dir = Path(output_dir)
    manifest_dir = Path(manifest_dir)
    
    if mode == "real":
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_dir.mkdir(parents=True, exist_ok=True)
    
    entries = []
    
    for accession_id in accession_ids:
        logger.info(f"Processing {accession_id}...")
        
        try:
            if mode == "real":
                r1_path, r2_path = download_fastq_from_sra(accession_id, output_dir, mode="real")
                
                file_paths = [r1_path]
                if r2_path:
                    file_paths.append(r2_path)
                
                entry = create_manifest_entry(accession_id, file_paths, source="ncbi_sra", mode="real")
                
                if not validate_downloaded_files(entry):
                    raise RuntimeError(f"Validation failed for {accession_id}")
                
            else:  # synthetic mode
                # In synthetic mode, we do NOT download. 
                # The caller is responsible for loading from data/synthetic/
                # We create a placeholder entry indicating synthetic source
                logger.info(f"Synthetic mode: creating placeholder for {accession_id}")
                entry = create_manifest_entry(accession_id, [], source="synthetic", mode="synthetic")
            
            entries.append(entry)
            
        except Exception as e:
            logger.error(f"Failed to process {accession_id}: {e}")
            if mode == "real":
                # Real mode: fail loudly
                raise RuntimeError(f"Critical failure for {accession_id} in real mode: {e}") from e
            # Synthetic mode: continue with warning
            continue
    
    manifest = DataManifest(
        entries=entries,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        pipeline_version="1.0.0",
        mode=mode
    )
    
    manifest_path = manifest_dir / f"{accession_ids[0] if len(accession_ids) == 1 else 'combined'}_manifest.json"
    save_manifest(manifest, manifest_path)
    
    return manifest

def main():
    """CLI entry point for data download."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download FASTQ data from NCBI SRA/GEO")
    parser.add_argument(
        "--accession", 
        nargs="+", 
        default=REAL_STUDY_ACCESSIONS,
        help="SRA/GEO accession IDs to download"
    )
    parser.add_argument(
        "--mode", 
        choices=["real", "synthetic"], 
        default="real",
        help="Download mode: 'real' for actual data, 'synthetic' for placeholder"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for FASTQ files (default: data/raw)"
    )
    parser.add_argument(
        "--manifest-dir",
        type=str,
        default=None,
        help="Directory for manifest files (default: data/manifests)"
    )
    
    args = parser.parse_args()
    
    data_path = get_data_path()
    output_dir = Path(args.output_dir) if args.output_dir else data_path / "raw"
    manifest_dir = Path(args.manifest_dir) if args.manifest_dir else data_path / "manifests"
    
    logger.info(f"Starting download in {args.mode} mode")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Manifest directory: {manifest_dir}")
    logger.info(f"Accessions: {args.accession}")
    
    try:
        manifest = download_study(
            accession_ids=args.accession,
            output_dir=output_dir,
            manifest_dir=manifest_dir,
            mode=args.mode
        )
        
        logger.info(f"Download complete. Processed {len(manifest.entries)} accessions.")
        logger.info(f"Manifest saved to: {manifest_dir}")
        
        # Exit with error if real mode failed
        if args.mode == "real" and len(manifest.entries) == 0:
            logger.critical("No data successfully downloaded in real mode")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        # Trigger human_input_needed by exiting with error code
        sys.exit(2)

if __name__ == "__main__":
    main()