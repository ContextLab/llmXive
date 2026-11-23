"""
Download and verify Acropora millepora reference transcriptome (NCBI RefSeq).

This script downloads the reference transcriptome for assembly GCF_000163615.2
(BioProject PRJNA321023), verifies its integrity using SHA256 checksums from
the NCBI RefSeq manifest, and builds a Salmon index for downstream quantification.
"""
import os
import sys
import json
import hashlib
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories, get_thresholds
from utils.logging import setup_logger, log_execution_time
from utils.errors import ChecksumError, ChecksumMismatchError, ChecksumFetchError

# Constants
ASSEMBLY_ACCESSION = "GCF_000163615.2"
BIOPROJECT_ID = "PRJNA321023"
ORGANISM_CODE = "ammi"  # Acropora millepora
REFSEQ_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/genomes/refseq"

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE_DIR = PROJECT_ROOT / "data" / "raw" / "reference"
INDEX_DIR = REFERENCE_DIR / "index"
CHECKSUM_FILE = REFERENCE_DIR / "checksum.json"

# Salmon index output directory name
SALMON_INDEX_NAME = "salmon_index"

def setup_logging() -> logging.Logger:
    """Configure logging for this script."""
    return setup_logger(
        name="download_reference",
        log_file=str(PROJECT_ROOT / "data" / "raw" / "reference_download.log"),
        level=logging.INFO
    )

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_ncbi_checksum(manifest_url: str) -> str:
    """
    Fetch the SHA256 checksum from NCBI RefSeq manifest.
    
    Args:
        manifest_url: URL to the assembly_manifest.txt file
        
    Returns:
        SHA256 checksum string
        
    Raises:
        ChecksumFetchError: If checksum cannot be retrieved
    """
    import urllib.request
    import urllib.error
    
    try:
        with urllib.request.urlopen(manifest_url, timeout=30) as response:
            content = response.read().decode('utf-8')
            
        # Parse the manifest to find the checksum for the transcriptome file
        # Format: assembly_accession bioproject submitter assembly_name ... sha256 ...
        for line in content.splitlines():
            if line.startswith(ASSEMBLY_ACCESSION):
                parts = line.split()
                # The SHA256 is typically near the end of the line
                # Look for the transcriptome file checksum
                for i, part in enumerate(parts):
                    if len(part) == 64 and all(c in '0123456789abcdef' for c in part.lower()):
                        return part.lower()
                        
        raise ChecksumFetchError(f"Could not find SHA256 checksum for {ASSEMBLY_ACCESSION} in manifest")
        
    except urllib.error.URLError as e:
        raise ChecksumFetchError(f"Failed to fetch NCBI manifest: {e}")
    except Exception as e:
        raise ChecksumFetchError(f"Error parsing NCBI manifest: {e}")

def download_file(url: str, output_path: Path, logger: logging.Logger) -> bool:
    """
    Download a file from URL with progress logging.
    
    Args:
        url: Download URL
        output_path: Destination path
        logger: Logger instance
        
    Returns:
        True if download successful, False otherwise
    """
    import urllib.request
    import urllib.error
    
    try:
        logger.info(f"Downloading from {url}...")
        with urllib.request.urlopen(url, timeout=120) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
                        
        logger.info(f"Download completed: {output_path}")
        return True
        
    except urllib.error.URLError as e:
        logger.error(f"Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False

def verify_checksum(file_path: Path, expected_checksum: str, logger: logging.Logger) -> bool:
    """
    Verify file integrity against expected SHA256 checksum.
    
    Args:
        file_path: Path to downloaded file
        expected_checksum: Expected SHA256 hash
        logger: Logger instance
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        ChecksumMismatchError: If checksums do not match
    """
    logger.info("Verifying file integrity...")
    actual_checksum = calculate_sha256(file_path)
    
    logger.info(f"Expected: {expected_checksum}")
    logger.info(f"Actual:   {actual_checksum}")
    
    if actual_checksum.lower() != expected_checksum.lower():
        error_msg = f"Checksum mismatch! Expected {expected_checksum}, got {actual_checksum}"
        logger.error(error_msg)
        raise ChecksumMismatchError(error_msg)
        
    logger.info("Checksum verification passed!")
    return True

def build_salmon_index(transcriptome_path: Path, index_dir: Path, logger: logging.Logger) -> bool:
    """
    Build Salmon index from transcriptome FASTA file.
    
    Args:
        transcriptome_path: Path to transcriptome FASTA file
        index_dir: Directory to store the index
        logger: Logger instance
        
    Returns:
        True if index built successfully, False otherwise
    """
    import shutil
    
    # Ensure index directory exists
    index_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if salmon is available
    try:
        result = subprocess.run(
            ["salmon", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.error("Salmon not found or not executable")
            return False
        logger.info(f"Found Salmon: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("Salmon executable not found. Please install Salmon.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout checking Salmon version")
        return False
    
    # Build the index
    cmd = [
        "salmon", "index",
        "-t", str(transcriptome_path),
        "-i", str(index_dir),
        "-k", "31"  # k-mer size for transcriptome
    ]
    
    logger.info("Building Salmon index...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout for indexing
        )
        
        if result.returncode != 0:
            logger.error(f"Salmon index build failed: {result.stderr}")
            return False
            
        logger.info("Salmon index built successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout building Salmon index")
        return False
    except Exception as e:
        logger.error(f"Error building Salmon index: {e}")
        return False

def save_checksum_record(
    file_path: Path,
    expected_checksum: str,
    actual_checksum: str,
    assembly: str,
    bioproject: str,
    download_url: str
) -> None:
    """Save checksum verification record to JSON file."""
    record = {
        "assembly_accession": assembly,
        "bioproject_id": bioproject,
        "file_path": str(file_path),
        "download_url": download_url,
        "expected_sha256": expected_checksum,
        "actual_sha256": actual_checksum,
        "verification_status": "PASSED",
        "timestamp": None  # Will be set by caller if needed
    }
    
    with open(CHECKSUM_FILE, 'w') as f:
        json.dump(record, f, indent=2)
    
    logging.getLogger().info(f"Checksum record saved to {CHECKSUM_FILE}")

@log_execution_time
def main():
    """Main entry point for reference transcriptome download and verification."""
    logger = setup_logging()
    logger.info("Starting reference transcriptome download and verification")
    
    # Ensure directories exist
    ensure_directories()
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Construct URLs
    # NCBI RefSeq FTP structure for assembly
    base_ftp = f"{REFSEQ_BASE_URL}/eukaryotes/Assemblage/{ASSEMBLY_ACCESSION}_RNA"
    manifest_url = f"{base_ftp}/assembly_manifest.txt"
    
    # The transcriptome file is typically named like:
    # GCF_000163615.2_Amillepora_v1.0_rna.fa.gz
    transcriptome_filename = f"{ASSEMBLY_ACCESSION}_rna.fa.gz"
    transcriptome_url = f"{base_ftp}/{transcriptome_filename}"
    
    output_path = REFERENCE_DIR / transcriptome_filename
    
    try:
        # Step 1: Fetch checksum from NCBI manifest
        logger.info(f"Fetching checksum from {manifest_url}")
        expected_checksum = fetch_ncbi_checksum(manifest_url)
        logger.info(f"Retrieved expected checksum: {expected_checksum}")
        
        # Step 2: Download the transcriptome file
        logger.info(f"Downloading transcriptome from {transcriptome_url}")
        if not download_file(transcriptome_url, output_path, logger):
            raise ChecksumFetchError("Failed to download transcriptome file")
        
        # Step 3: Verify checksum
        actual_checksum = calculate_sha256(output_path)
        verify_checksum(output_path, expected_checksum, logger)
        
        # Step 4: Save verification record
        save_checksum_record(
            output_path,
            expected_checksum,
            actual_checksum,
            ASSEMBLY_ACCESSION,
            BIOPROJECT_ID,
            transcriptome_url
        )
        
        # Step 5: Build Salmon index
        if not build_salmon_index(output_path, INDEX_DIR, logger):
            raise RuntimeError("Failed to build Salmon index")
        
        logger.info("Reference transcriptome download, verification, and indexing completed successfully!")
        return 0
        
    except ChecksumMismatchError as e:
        logger.critical(f"Checksum verification failed: {e}")
        # Clean up corrupted file
        if output_path.exists():
            output_path.unlink()
        return 1
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
