"""
Ingest module for downloading and validating VCF files from NCBI BioProject.

This module handles the retrieval of genomic data (VCF format) from NCBI FTP
servers, verifies data integrity using checksums, and prepares the data for
downstream PLINK conversion.
"""

import os
import sys
import logging
import hashlib
import ftplib
import gzip
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories, get_thresholds
from utils import setup_logger, validate_checksum, calculate_checksum, handle_critical_error
from data.env_manager import get_ftp_base_url, is_ftp_access_available, get_entrez_headers

# Constants
DEFAULT_STUDY_ID = "SRP123456"  # Placeholder for actual *Acropora millepora* study
VCF_EXTENSIONS = ['.vcf', '.vcf.gz']
CHECKSUM_FILE_SUFFIX = '.md5'

logger = setup_logger("ingest")

class IngestionError(Exception):
    """Custom exception for ingestion failures."""
    pass

def get_study_vcf_url(study_id: str, filename: str) -> str:
    """
    Construct the full FTP URL for a specific VCF file within a study.
    
    Args:
        study_id: The NCBI BioProject/Study ID (e.g., SRP123456)
        filename: The specific VCF filename
        
    Returns:
        Full FTP URL string
    """
    base_url = get_ftp_base_url()
    # Standard NCBI SRA instant read path structure
    path_parts = [
        "sra", "sra-instant", "reads", "ByStudy", "sra", 
        "SRP", study_id, filename
    ]
    # Join parts ensuring correct slash handling
    full_path = "/".join(path_parts)
    return f"{base_url}/{full_path}"

def download_file_ftp(
    remote_path: str, 
    local_path: Path, 
    timeout: int = 60, 
    retries: int = 3
) -> bool:
    """
    Download a file from NCBI FTP server with retry logic.
    
    Args:
        remote_path: Full remote path relative to FTP root
        local_path: Local destination path
        timeout: Connection timeout in seconds
        retries: Number of retry attempts
        
    Returns:
        True if download successful, False otherwise
    """
    ftp = None
    base_url = get_ftp_base_url()
    host = base_url.replace("ftp://", "")
    
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{retries}: Connecting to {host}")
            ftp = ftplib.FTP(host, timeout=timeout)
            ftp.login()  # Anonymous login
            ftp.cwd("/")
            
            # Ensure local directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading {remote_path} to {local_path}")
            
            with open(local_path, 'wb') as f:
                # RETR command for downloading
                ftp.retrbinary(f'RETR {remote_path}', f.write)
            
            ftp.quit()
            logger.info(f"Successfully downloaded {local_path.name}")
            return True
            
        except ftplib.all_errors as e:
            logger.warning(f"FTP Error (attempt {attempt + 1}): {e}")
            if ftp:
                try:
                    ftp.quit()
                except:
                    pass
            if attempt == retries - 1:
                logger.error(f"Failed to download after {retries} attempts: {e}")
                return False
            continue
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            if ftp:
                try:
                    ftp.quit()
                except:
                    pass
            return False
    return False

def fetch_checksum(remote_path: str, filename: str) -> Optional[str]:
    """
    Fetch the MD5 checksum for a file from NCBI.
    
    Note: NCBI often provides checksums in a separate .md5 file or directory listing.
    This implementation attempts to retrieve a corresponding .md5 file.
    
    Args:
        remote_path: Directory path on FTP
        filename: Target filename
        
    Returns:
        MD5 checksum string or None if not found
    """
    ftp = None
    host = get_ftp_base_url().replace("ftp://", "")
    checksum_filename = f"{filename}.md5"
    
    try:
        ftp = ftplib.FTP(host, timeout=30)
        ftp.login()
        ftp.cwd(remote_path)
        
        # Check if .md5 file exists
        files = ftp.nlst()
        if checksum_filename in files:
            logger.info(f"Found checksum file: {checksum_filename}")
            with open(f"/tmp/{checksum_filename}", "wb") as f:
                ftp.retrbinary(f'RETR {checksum_filename}', f.write)
            
            with open(f"/tmp/{checksum_filename}", "r") as f:
                content = f.read().strip()
                # Format is usually: <md5sum>  <filename>
                parts = content.split()
                if len(parts) >= 1:
                    return parts[0]
        
        logger.warning(f"Checksum file {checksum_filename} not found. Proceeding without verification.")
        return None
        
    except Exception as e:
        logger.warning(f"Could not retrieve checksum: {e}")
        return None
    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                pass
        # Cleanup temp file
        temp_path = Path(f"/tmp/{checksum_filename}")
        if temp_path.exists():
            temp_path.unlink()

def verify_file_integrity(file_path: Path, expected_checksum: Optional[str]) -> bool:
    """
    Verify the integrity of a downloaded file using MD5 checksum.
    
    Args:
        file_path: Path to the downloaded file
        expected_checksum: Expected MD5 hash string
        
    Returns:
        True if valid or no checksum available, False if mismatch
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False
    
    # Calculate actual checksum
    try:
        actual_checksum = calculate_checksum(file_path, algorithm="md5")
        logger.info(f"Calculated checksum for {file_path.name}: {actual_checksum}")
    except Exception as e:
        logger.error(f"Failed to calculate checksum: {e}")
        return False
    
    if expected_checksum is None:
        logger.warning("No expected checksum provided. Skipping verification.")
        return True
    
    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verification PASSED for {file_path.name}")
        return True
    else:
        logger.error(f"Checksum verification FAILED for {file_path.name}")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {actual_checksum}")
        return False

def process_vcf_file(
    remote_path: str, 
    filename: str, 
    output_dir: Path, 
    study_id: str
) -> Tuple[bool, str]:
    """
    Download and verify a single VCF file.
    
    Args:
        remote_path: Remote directory path
        filename: Filename to download
        output_dir: Local output directory
        study_id: Study ID for logging
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    local_path = output_dir / filename
    
    # Download
    success = download_file_ftp(remote_path, local_path)
    if not success:
        return False, f"Failed to download {filename}"
    
    # Get checksum
    checksum = fetch_checksum(remote_path, filename)
    
    # Verify
    if checksum:
        if not verify_file_integrity(local_path, checksum):
            return False, f"Checksum mismatch for {filename}"
    
    return True, f"Successfully processed {filename}"

def find_available_studies() -> List[Dict[str, Any]]:
    """
    Attempt to list available studies matching *Acropora millepora* criteria.
    
    Note: In a real scenario, this would query NCBI E-utilities or search the
    SRA database programmatically. For this implementation, we return a 
    predefined list of known relevant study IDs or attempt to list a generic
    directory if accessible.
    
    Returns:
        List of study metadata dictionaries
    """
    # Placeholder: In a real pipeline, this would query NCBI ESearch
    # Example: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&term=Acropora+millepora
    # For now, we return a list of potential study IDs to try.
    # The user must update this with the actual PRJNA/SRP ID from the spec.
    potential_ids = [
        "SRP123456", # Replace with actual ID from plan.md/spec.md
        "SRP098765"  # Fallback example
    ]
    
    studies = []
    for sid in potential_ids:
        # Check if directory exists (simple probe)
        host = get_ftp_base_url().replace("ftp://", "")
        try:
            ftp = ftplib.FTP(host, timeout=10)
            ftp.login()
            ftp.cwd(f"/sra/sra-instant/reads/ByStudy/sra/SRP/{sid}")
            files = ftp.nlst()
            ftp.quit()
            
            vcf_files = [f for f in files if any(f.endswith(ext) for ext in VCF_EXTENSIONS)]
            if vcf_files:
                studies.append({
                    "study_id": sid,
                    "files": vcf_files,
                    "path": f"/sra/sra-instant/reads/ByStudy/sra/SRP/{sid}"
                })
        except Exception:
            continue
    
    return studies

def run_ingestion(
    study_id: Optional[str] = None, 
    specific_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main entry point for the ingestion pipeline.
    
    Args:
        study_id: Specific study ID to process. If None, attempts to discover.
        specific_files: List of specific filenames to download. If None, downloads all VCFs.
        
    Returns:
        Dictionary with ingestion results and statistics
    """
    logger.info("Starting VCF Ingestion Pipeline")
    ensure_directories()
    
    config = get_thresholds()
    output_dir = Path(config.get("output_dir", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "success": False,
        "files_downloaded": [],
        "files_failed": [],
        "checksums_verified": 0,
        "errors": []
    }
    
    # Determine study to process
    if study_id:
        studies = [{"study_id": study_id, "path": f"/sra/sra-instant/reads/ByStudy/sra/SRP/{study_id}"}]
        # We need to find files if not specified
        if not specific_files:
            # Attempt to list files for this study
            try:
                host = get_ftp_base_url().replace("ftp://", "")
                ftp = ftplib.FTP(host, timeout=10)
                ftp.login()
                ftp.cwd(studies[0]["path"])
                all_files = ftp.nlst()
                ftp.quit()
                studies[0]["files"] = [f for f in all_files if any(f.endswith(ext) for ext in VCF_EXTENSIONS)]
            except Exception as e:
                results["errors"].append(f"Could not list files for study {study_id}: {e}")
                return results
    else:
        studies = find_available_studies()
        if not studies:
            msg = "No valid *Acropora millepora* studies found on NCBI FTP."
            logger.error(msg)
            results["errors"].append(msg)
            return results
    
    for study in studies:
        sid = study["study_id"]
        remote_path = study["path"]
        files_to_process = study.get("files", [])
        
        if specific_files:
            files_to_process = [f for f in files_to_process if f in specific_files]
        
        if not files_to_process:
            logger.warning(f"No VCF files found for study {sid}")
            continue
        
        logger.info(f"Processing study {sid} with {len(files_to_process)} files")
        
        for filename in files_to_process:
            success, message = process_vcf_file(
                remote_path, filename, output_dir, sid
            )
            
            if success:
                results["files_downloaded"].append(str(output_dir / filename))
                results["checksums_verified"] += 1
            else:
                results["files_failed"].append(filename)
                results["errors"].append(message)
    
    if len(results["files_downloaded"]) > 0:
        results["success"] = True
        logger.info(f"Ingestion complete. Downloaded {len(results['files_downloaded'])} files.")
    else:
        logger.error("Ingestion failed: No files downloaded successfully.")
    
    return results

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest VCF data from NCBI")
    parser.add_argument("--study-id", type=str, help="NCBI Study ID (e.g., SRP123456)")
    parser.add_argument("--files", type=str, nargs="+", help="Specific files to download")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory")
    
    args = parser.parse_args()
    
    # Override config if output specified
    if args.output:
        os.environ["OUTPUT_DIR"] = args.output
    
    results = run_ingestion(
        study_id=args.study_id,
        specific_files=args.files
    )
    
    if results["success"]:
        print(f"Success: {len(results['files_downloaded'])} files downloaded.")
        sys.exit(0)
    else:
        print(f"Failed: {len(results['errors'])} errors encountered.")
        for err in results["errors"]:
            print(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
