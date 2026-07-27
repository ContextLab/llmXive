"""
Orchestrates data acquisition for the plant defense allocation pipeline.

Handles both real data fetching (via T011-real logic) and synthetic data
generation (via T015) based on the --mode flag.

Implements the fallback logic: if real data fetch fails, triggers synthetic
generation for prototype validation, logging a warning but not halting.
"""
import os
import sys
import json
import hashlib
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Import from existing project modules
from src.utils.logger import get_logger
from src.utils.config import get_data_path, get_seed
from src.data.synthetic_generator import generate_synthetic_tpm_study, save_synthetic_manifest

# Logger setup
logger = get_logger(__name__)

# Configuration constants
REAL_DATA_TIMEOUT = 300  # 5 minutes for download attempts
REAL_DATA_RETRIES = 3

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_sra_accession_info(accession_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an SRA accession using NCBI E-utilities.
    Returns metadata dict or None if not found.
    """
    try:
        # Use NCBI E-utilities to fetch SRA metadata
        cmd = [
            "esearch", "-db", "sra", "-query", accession_id,
            "|", "efetch", "-format", "docsum"
        ]
        # Note: In a real environment, this would use the full command
        # For now, we simulate the check by attempting a simple HTTP request
        # In production, this would require the NCBI Entrez Direct tools
        
        # Fallback: Try to fetch via E-utilities API directly
        import urllib.request
        import urllib.parse
        
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "sra",
            "term": accession_id,
            "retmode": "json"
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if "esearchresult" in data and "idlist" in data["esearchresult"]:
                if data["esearchresult"]["idlist"]:
                    return {
                        "accession_id": accession_id,
                        "found": True,
                        "id": data["esearchresult"]["idlist"][0]
                    }
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch SRA metadata for {accession_id}: {e}")
        return None

def get_fastq_download_url(accession_id: str) -> Optional[str]:
    """
    Get the direct FASTQ download URL for an SRA accession.
    Uses SRA Toolkit's prefetch logic or direct FTP.
    """
    try:
        # Construct the FTP URL pattern for SRA
        # Pattern: ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/
        base_ftp = f"https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=run_browser&cache={accession_id}&data=fastq&read_type=paired"
        
        # For real implementation, we would use prefetch or fasterq-dump
        # Here we return a placeholder URL structure
        # In production, this would be resolved by the SRA Toolkit
        return f"https://sra-download-batch.ncbi.nlm.nih.gov/sra/{accession_id}/{accession_id}.fastq.gz"
    except Exception as e:
        logger.warning(f"Failed to construct download URL for {accession_id}: {e}")
        return None

def download_file_with_progress(url: str, output_path: str, timeout: int = REAL_DATA_TIMEOUT) -> bool:
    """
    Download a file from URL with progress reporting.
    Returns True if successful, False otherwise.
    """
    try:
        import urllib.request
        import shutil
        
        logger.info(f"Downloading {url} to {output_path}")
        
        with urllib.request.urlopen(url, timeout=timeout) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            block_size = 8192
            
            with open(output_path, 'wb') as out_file:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    out_file.write(buffer)
                    downloaded += len(buffer)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        # Log progress every 10%
                        if int(progress) % 10 == 0 and int(progress) > 0:
                            logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download completed: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def download_fastq_from_sra(accession_id: str, output_dir: Path) -> Optional[str]:
    """
    Download FASTQ files for an SRA accession.
    Returns the path to the downloaded file or None if failed.
    """
    try:
        # Check if prefetch is available (part of SRA Toolkit)
        try:
            result = subprocess.run(
                ["prefetch", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            has_prefetch = result.returncode == 0
        except:
            has_prefetch = False
        
        if has_prefetch:
            # Use prefetch to download the SRA object
            output_path = output_dir / f"{accession_id}.sra"
            result = subprocess.run(
                ["prefetch", "-O", str(output_dir), accession_id],
                capture_output=True,
                text=True,
                timeout=REAL_DATA_TIMEOUT
            )
            
            if result.returncode == 0:
                logger.info(f"Prefetch successful: {output_path}")
                # Convert to FASTQ using fasterq-dump if needed
                # For now, return the .sra file path
                return str(output_path)
            else:
                logger.error(f"Prefetch failed: {result.stderr}")
                return None
        else:
            # Fallback to direct HTTP download
            url = get_fastq_download_url(accession_id)
            if not url:
                logger.error(f"No download URL available for {accession_id}")
                return None
            
            output_path = output_dir / f"{accession_id}_R1.fastq.gz"
            if download_file_with_progress(url, str(output_path)):
                return str(output_path)
            return None
    except Exception as e:
        logger.error(f"Failed to download FASTQ for {accession_id}: {e}")
        return None

def fetch_geosamples_study(study_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch study metadata from NCBI GeoSamples.
    Returns study metadata or None if not found.
    """
    try:
        import urllib.request
        import urllib.parse
        
        base_url = "https://www.ebi.ac.uk/ena/browser/api/xml"
        # Note: This is a simplified version; real implementation would use ENA API
        url = f"{base_url}/{study_id}"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            # Parse XML response (simplified)
            return {"study_id": study_id, "found": True}
    except Exception as e:
        logger.warning(f"Failed to fetch GeoSamples data for {study_id}: {e}")
        return None

def create_manifest_entry(
    accession_id: str,
    file_path: str,
    source_url: str,
    source_type: str = "real"
) -> Dict[str, Any]:
    """
    Create a manifest entry for a downloaded or generated file.
    """
    checksum = calculate_sha256(file_path) if os.path.exists(file_path) else "N/A"
    
    return {
        "accession_id": accession_id,
        "file_path": file_path,
        "checksum": checksum,
        "source_url": source_url,
        "source_type": source_type,
        "downloaded_at": datetime.utcnow().isoformat() + "Z",
        "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }

def save_manifest(manifest_entries: List[Dict[str, Any]], manifest_path: Path) -> None:
    """
    Save a list of manifest entries to a JSON file.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        "manifest_version": "1.0",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "entries": manifest_entries
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Manifest saved to {manifest_path}")

def validate_downloaded_files(accession_ids: List[str], data_dir: Path) -> List[str]:
    """
    Validate that downloaded files exist and are non-empty.
    Returns list of invalid accession IDs.
    """
    invalid_ids = []
    for accession_id in accession_ids:
        file_path = data_dir / f"{accession_id}.fastq.gz"
        if not file_path.exists() or file_path.stat().st_size == 0:
            invalid_ids.append(accession_id)
            logger.warning(f"Invalid or empty file for {accession_id}")
        else:
            logger.info(f"Validated file for {accession_id}: {file_path.stat().st_size} bytes")
    return invalid_ids

def download_study(accession_id: str, data_dir: Path) -> bool:
    """
    Attempt to download a single study.
    Returns True if successful, False if failed.
    """
    logger.info(f"Attempting to download study: {accession_id}")
    
    # Try to get metadata first
    metadata = fetch_sra_accession_info(accession_id)
    if not metadata:
        logger.warning(f"Study {accession_id} not found in SRA")
        return False
    
    # Download FASTQ
    fastq_path = download_fastq_from_sra(accession_id, data_dir)
    if not fastq_path:
        logger.error(f"Failed to download FASTQ for {accession_id}")
        return False
    
    # Create manifest entry
    source_url = get_fastq_download_url(accession_id) or "sra://unknown"
    entry = create_manifest_entry(accession_id, fastq_path, source_url)
    
    # Save to temporary list (actual saving happens in main)
    logger.info(f"Successfully downloaded {accession_id}")
    return True

def run_real_mode(accession_ids: List[str], data_dir: Path, manifest_path: Path) -> bool:
    """
    Execute real data download mode.
    Tries to download all specified accession IDs.
    Returns True if at least one download succeeded, False otherwise.
    """
    logger.info("Starting real data download mode")
    
    manifest_entries = []
    successful_downloads = 0
    
    for accession_id in accession_ids:
        if download_study(accession_id, data_dir):
            # Create manifest entry for successful download
            fastq_path = data_dir / f"{accession_id}.fastq.gz"
            if fastq_path.exists():
                source_url = get_fastq_download_url(accession_id) or "sra://unknown"
                entry = create_manifest_entry(accession_id, str(fastq_path), source_url)
                manifest_entries.append(entry)
                successful_downloads += 1
    
    if successful_downloads > 0:
        save_manifest(manifest_entries, manifest_path)
        logger.info(f"Real mode completed: {successful_downloads}/{len(accession_ids)} studies downloaded")
        return True
    else:
        logger.error("Real mode failed: No studies could be downloaded")
        return False

def run_synthetic_mode(data_dir: Path, manifest_path: Path) -> bool:
    """
    Execute synthetic data generation mode.
    Uses T015 (synthetic_generator) to generate prototype data.
    """
    logger.info("Starting synthetic data generation mode")
    
    try:
        # Generate synthetic study
        seed = get_seed()
        study_data = generate_synthetic_tpm_study(seed=seed)
        
        # Save the synthetic data
        synthetic_file = data_dir / "synthetic_study.tsv"
        study_data.to_csv(synthetic_file, sep='\t', index=False)
        
        # Create and save manifest
        manifest_entry = save_synthetic_manifest(
            file_name=str(synthetic_file),
            seed=seed,
            data_dir=data_dir.parent  # data/synthetic directory
        )
        
        # Update manifest to point to correct location
        manifest_entry["file_path"] = str(synthetic_file)
        manifest_entry["source_url"] = "synthetic://generator"
        
        save_manifest([manifest_entry], manifest_path)
        
        logger.info("Synthetic mode completed successfully")
        return True
    except Exception as e:
        logger.error(f"Synthetic mode failed: {e}")
        return False

def main():
    """
    Main entry point for data acquisition orchestration.
    
    Usage:
      python src/data/download.py --mode real --accessions GSE12345,GSE67890
      python src/data/download.py --mode synthetic
    """
    parser = argparse.ArgumentParser(description="Orchestrate data acquisition")
    parser.add_argument(
        "--mode",
        choices=["real", "synthetic"],
        default="real",
        help="Data acquisition mode: 'real' for real data, 'synthetic' for synthetic"
    )
    parser.add_argument(
        "--accessions",
        type=str,
        default="SRP123456",  # Default test accession
        help="Comma-separated list of SRA accession IDs (for real mode)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override default data directory"
    )
    
    args = parser.parse_args()
    
    # Setup directories
    data_path = Path(get_data_path())
    raw_dir = data_path / "raw"
    synthetic_dir = data_path / "synthetic"
    manifests_dir = data_path / "manifests"
    
    # Determine actual directories based on mode
    if args.mode == "real":
        target_dir = raw_dir
        manifest_file = manifests_dir / "real_data_manifest.json"
    else:
        target_dir = synthetic_dir
        manifest_file = manifests_dir / "synthetic_manifest.json"
    
    # Ensure directories exist
    target_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Data directory: {target_dir}")
    logger.info(f"Manifest file: {manifest_file}")
    
    success = False
    
    if args.mode == "real":
        accession_ids = [acc.strip() for acc in args.accessions.split(",") if acc.strip()]
        
        if not accession_ids:
            logger.error("No accession IDs provided for real mode")
            sys.exit(1)
        
        success = run_real_mode(accession_ids, target_dir, manifest_file)
        
        # Fallback to synthetic if real mode fails
        if not success:
            logger.warning("Real data acquisition failed. Switching to synthetic mode for prototype validation.")
            success = run_synthetic_mode(synthetic_dir, manifests_dir / "synthetic_manifest.json")
            if success:
                logger.info("Synthetic fallback successful. Pipeline can proceed with synthetic data.")
    else:
        success = run_synthetic_mode(target_dir, manifest_file)
    
    if success:
        logger.info("Data acquisition completed successfully")
        sys.exit(0)
    else:
        logger.error("Data acquisition failed completely")
        sys.exit(1)

if __name__ == "__main__":
    main()