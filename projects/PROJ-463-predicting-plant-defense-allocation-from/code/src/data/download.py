"""
Module for downloading FASTQ files from NCBI GEO/SRA.

This module implements strict real-data acquisition with no synthetic fallbacks.
It fetches metadata from NCBI E-utilities and downloads files using prefetch/ fasterq-dump.
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
import requests
from urllib.parse import urljoin

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_data_path, get_config
from src.utils.schemas import ManifestEntry, DataManifest, ProvenanceInfo
from src.utils.provenance import get_provenance_tracker, record_provenance

logger = get_logger(__name__)

# Constants
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SRA_RUN_SELECTOR_URL = "https://www.ncbi.nlm.nih.gov/Traces/study/?acc={study}&o=acc_s_1&s=acc_s_1"
# Using SRA Toolkit tools: prefetch and fasterq-dump
# These must be installed separately (see T003)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_sra_accession_info(accession: str) -> Dict[str, Any]:
    """
    Fetch metadata for an SRA accession from NCBI.
    
    Args:
        accession: SRA accession ID (e.g., SRX123456 or SRR123456)
        
    Returns:
        Dictionary containing metadata
        
    Raises:
        RuntimeError: If fetch fails
    """
    # Determine if it's a study (SRP/SRX) or run (SRR)
    if accession.startswith('SRR'):
        # It's a run, fetch directly
        url = f"{NCBI_EUTILS_BASE}/efetch.fcgi?db=sra&id={accession}&retmode=json"
    elif accession.startswith('SRX'):
        # It's an experiment, fetch experiment details
        url = f"{NCBI_EUTILS_BASE}/efetch.fcgi?db=sra&id={accession}&retmode=json"
    elif accession.startswith('SRP') or accession.startswith('SRG'):
        # It's a study, fetch study details and then runs
        url = f"{NCBI_EUTILS_BASE}/esummary.fcgi?db=sra&id={accession}&retmode=json"
    else:
        raise ValueError(f"Unsupported accession type: {accession}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession}: {e}")
        raise RuntimeError(f"Failed to fetch metadata for {accession}: {e}")

def get_fastq_download_url(accession: str) -> str:
    """
    Get the FASTQ download URL for an SRA accession.
    
    Note: For large-scale downloads, we use the SRA Toolkit (prefetch/fasterq-dump)
    rather than direct HTTP downloads. This function returns the SRA location.
    
    Args:
        accession: SRA accession ID
        
    Returns:
        SRA location string for prefetch
    """
    # For SRA Toolkit, we use the accession directly
    # The actual download is handled by prefetch command
    return accession

def download_file_with_progress(url: str, output_path: str, chunk_size: int = 8192) -> Tuple[str, int]:
    """
    Download a file with progress logging.
    
    Args:
        url: Download URL
        output_path: Local output path
        chunk_size: Chunk size for reading
        
    Returns:
        Tuple of (checksum, file_size)
        
    Raises:
        RuntimeError: If download fails
    """
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {percent:.1f}%")
        
        checksum = calculate_sha256(output_path)
        file_size = os.path.getsize(output_path)
        return checksum, file_size
        
    except requests.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(f"Download failed for {url}: {e}")

def fetch_geosamples_study(study_id: str) -> List[str]:
    """
    Fetch all SRR accessions for a given GEO/SRA study.
    
    Args:
        study_id: Study accession (e.g., SRP123456)
        
    Returns:
        List of SRR accession IDs
        
    Raises:
        RuntimeError: If fetch fails or no runs found
    """
    try:
        # Use esearch to find all runs in the study
        search_url = f"{NCBI_EUTILS_BASE}/esearch.fcgi?db=sra&term={study_id}&retmode=json&retmax=1000"
        response = requests.get(search_url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if 'esearchresult' not in data or 'idlist' not in data['esearchresult']:
            raise RuntimeError(f"No runs found for study {study_id}")
        
        run_ids = data['esearchresult']['idlist']
        logger.info(f"Found {len(run_ids)} runs for study {study_id}")
        return run_ids
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch study {study_id}: {e}")
        raise RuntimeError(f"Failed to fetch study {study_id}: {e}")

def download_fastq_from_sra(accession: str, output_dir: str, use_prefetch: bool = True) -> str:
    """
    Download FASTQ file for an SRA accession using SRA Toolkit.
    
    This function uses the SRA Toolkit's prefetch and fasterq-dump utilities
    to download and convert SRA files to FASTQ format.
    
    Args:
        accession: SRA accession ID (SRR)
        output_dir: Directory to save FASTQ files
        use_prefetch: If True, use prefetch tool; otherwise try direct download
        
    Returns:
        Path to downloaded FASTQ file
        
    Raises:
        RuntimeError: If download fails
        FileNotFoundError: If SRA Toolkit is not installed
    """
    output_path = Path(output_dir) / f"{accession}.fastq.gz"
    
    if use_prefetch:
        # Check if prefetch is available
        try:
            subprocess.run(['which', 'prefetch'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("SRA Toolkit 'prefetch' not found. Please install SRA Toolkit.")
            raise FileNotFoundError("SRA Toolkit 'prefetch' not found. Install via: conda install -c bioconda sra-tools")
        
        # Create temporary directory for SRA files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prefetch the SRA file
            logger.info(f"Prefetching {accession}...")
            prefetch_cmd = ['prefetch', '-O', temp_dir, accession]
            try:
                result = subprocess.run(prefetch_cmd, capture_output=True, text=True, timeout=3600)
                if result.returncode != 0:
                    logger.error(f"Prefetch failed: {result.stderr}")
                    raise RuntimeError(f"Prefetch failed for {accession}: {result.stderr}")
                
                # Find the .sra file
                sra_files = list(Path(temp_dir).glob(f"{accession}*.sra"))
                if not sra_files:
                    raise RuntimeError(f"No .sra file found after prefetch for {accession}")
                
                sra_file = sra_files[0]
                
                # Convert to FASTQ using fasterq-dump
                logger.info(f"Converting {accession} to FASTQ...")
                dump_cmd = [
                    'fasterq-dump',
                    '--split-files',  # Split paired-end reads
                    '--gzip',          # Compress output
                    '-O', str(output_dir),
                    str(sra_file)
                ]
                
                result = subprocess.run(dump_cmd, capture_output=True, text=True, timeout=7200)
                if result.returncode != 0:
                    logger.error(f"fasterq-dump failed: {result.stderr}")
                    raise RuntimeError(f"fasterq-dump failed for {accession}: {result.stderr}")
                
                # Find the generated FASTQ file(s)
                fastq_files = list(output_dir.glob(f"{accession}_*.fastq.gz"))
                if not fastq_files:
                    # Try without split files (single end)
                    fastq_files = list(output_dir.glob(f"{accession}.fastq.gz"))
                
                if not fastq_files:
                    raise RuntimeError(f"No FASTQ file generated for {accession}")
                
                # Return the first FASTQ file (or concatenate if paired)
                fastq_path = str(fastq_files[0])
                logger.info(f"Successfully downloaded {accession} to {fastq_path}")
                return fastq_path
                
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Download timeout for {accession}")
    
    else:
        # Fallback to direct download (not recommended for large files)
        # This path is rarely used as prefetch is more reliable
        raise NotImplementedError("Direct HTTP download not implemented. Use SRA Toolkit.")

def create_manifest_entry(file_path: str, source_info: Dict[str, Any], study_id: str) -> ManifestEntry:
    """
    Create a manifest entry for a downloaded file.
    
    Args:
        file_path: Path to the downloaded file
        source_info: Metadata about the source
        study_id: Original study ID
        
    Returns:
        ManifestEntry object
    """
    checksum = calculate_sha256(file_path)
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    return ManifestEntry(
        file_name=file_name,
        file_path=file_path,
        checksum=checksum,
        checksum_algorithm="SHA256",
        file_size=file_size,
        source_type="ncbi_sra",
        source_id=source_info.get('accession', ''),
        study_id=study_id,
        downloaded_at=datetime.now().isoformat(),
        provenance={
            "tool": "src/data/download.py",
            "version": "1.0.0",
            "parameters": source_info
        }
    )

def save_manifest(manifest: DataManifest, output_path: str):
    """
    Save manifest to JSON file.
    
    Args:
        manifest: DataManifest object
        output_path: Path to save manifest
    """
    with open(output_path, 'w') as f:
        json.dump(manifest.model_dump(), f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def validate_downloaded_files(manifest_entries: List[ManifestEntry]) -> List[str]:
    """
    Validate downloaded files against their checksums.
    
    Args:
        manifest_entries: List of manifest entries
        
    Returns:
        List of invalid file paths
    """
    invalid_files = []
    for entry in manifest_entries:
        if not os.path.exists(entry.file_path):
            invalid_files.append(entry.file_path)
            logger.error(f"File missing: {entry.file_path}")
            continue
        
        current_checksum = calculate_sha256(entry.file_path)
        if current_checksum != entry.checksum:
            invalid_files.append(entry.file_path)
            logger.error(f"Checksum mismatch for {entry.file_path}")
    
    return invalid_files

from datetime import datetime

def download_study(study_id: str, output_dir: str = None, use_prefetch: bool = True) -> DataManifest:
    """
    Download all FASTQ files for a given study.
    
    Args:
        study_id: Study accession (e.g., SRP123456)
        output_dir: Output directory (defaults to config)
        use_prefetch: Use SRA Toolkit prefetch
        
    Returns:
        DataManifest object containing all downloaded files
        
    Raises:
        RuntimeError: If no files can be downloaded or critical errors occur
    """
    if output_dir is None:
        output_dir = str(get_data_path() / "raw")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download for study {study_id}")
    
    # Fetch all run accessions for the study
    run_ids = fetch_geosamples_study(study_id)
    if not run_ids:
        raise RuntimeError(f"No runs found for study {study_id}")
    
    manifest_entries = []
    download_errors = []
    
    for run_id in run_ids:
        try:
            logger.info(f"Downloading run {run_id}...")
            fastq_path = download_fastq_from_sra(run_id, str(output_path), use_prefetch)
            
            # Get metadata for this run
            run_info = fetch_sra_accession_info(run_id)
            
            # Create manifest entry
            entry = create_manifest_entry(fastq_path, run_info, study_id)
            manifest_entries.append(entry)
            
            logger.info(f"Successfully downloaded {run_id}")
            
        except Exception as e:
            logger.error(f"Failed to download {run_id}: {e}")
            download_errors.append({"run_id": run_id, "error": str(e)})
    
    if not manifest_entries:
        error_msg = f"Failed to download any files for study {study_id}. Errors: {download_errors}"
        logger.critical(error_msg)
        # Trigger human input needed state
        logger.critical("CRITICAL: Real data fetch failed. Triggering human_input_needed state.")
        raise RuntimeError(error_msg)
    
    # Create manifest
    provenance = ProvenanceInfo(
        created_at=datetime.now().isoformat(),
        tool="src/data/download.py",
        version="1.0.0",
        parameters={"study_id": study_id, "use_prefetch": use_prefetch}
    )
    
    manifest = DataManifest(
        study_id=study_id,
        source="NCBI SRA",
        files=manifest_entries,
        provenance=provenance,
        errors=download_errors
    )
    
    # Save manifest
    manifest_path = Path(output_dir).parent / "manifests" / f"{study_id}_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    save_manifest(manifest, str(manifest_path))
    
    logger.info(f"Download complete. {len(manifest_entries)} files downloaded.")
    return manifest

def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download FASTQ files from NCBI SRA")
    parser.add_argument("study_id", help="Study accession (e.g., SRP123456)")
    parser.add_argument("--output", "-o", help="Output directory", default=None)
    parser.add_argument("--no-prefetch", action="store_true", help="Disable SRA Toolkit prefetch")
    
    args = parser.parse_args()
    
    try:
        manifest = download_study(
            study_id=args.study_id,
            output_dir=args.output,
            use_prefetch=not args.no_prefetch
        )
        print(f"Successfully downloaded {len(manifest.files)} files for study {args.study_id}")
        print(f"Manifest saved to: {args.output or get_data_path()}/manifests/{args.study_id}_manifest.json")
    except RuntimeError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()