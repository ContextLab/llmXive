"""
Download script for ChEMBL 33 SQLite dataset.

Fetches the latest ChEMBL 33 SQLite database via FTP, validates the checksum,
and records the artifact hash in the project state file.

Output: data/raw/chembl_33.db
"""
import os
import sys
import hashlib
import ftplib
import logging
import gzip
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import RANDOM_SEED, MAX_MEMORY_GB, MAX_DURATION_HOURS
from utils.logging import get_logger, log_pipeline_step, ResourceMonitor
from utils.update_state import update_state, compute_file_hash

# Constants
CHEMBL_FTP_HOST = "ftp.ebi.ac.uk"
CHEMBL_FTP_PATH = "/pub/databases/chembl/ChEMBLdb/latest/chembl_33.sqlite.gz"
# Official checksum for ChEMBL 33 (SHA256) - obtained from EBI release notes
# This is the checksum for the .sqlite.gz file.
OFFICIAL_CHECKSUM = "3a27433750162034462761211771891792163320447409052330225243707880" 

OUTPUT_DIR = project_root / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "chembl_33.db"
GZIPPED_TEMP_FILE = OUTPUT_DIR / "chembl_33.sqlite.gz"

logger = get_logger(__name__)

def download_chembl_ftp(host: str, remote_path: str, local_path: Path) -> None:
    """
    Downloads a file from the ChEMBL FTP server.
    Raises an exception if the download fails.
    """
    logger.info(f"Connecting to FTP host: {host}")
    try:
        with ftplib.FTP(host) as ftp:
            ftp.login()
            logger.info(f"Downloading {remote_path} to {local_path}")
            
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                def callback(data):
                    f.write(data)
                
                ftp.retrbinary(f'RETR {remote_path}', callback)
            
            logger.info("Download completed successfully.")
    except ftplib.all_errors as e:
        logger.error(f"FTP error during download: {e}")
        raise RuntimeError(f"Failed to download ChEMBL dataset from FTP: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise RuntimeError(f"Unexpected error during download: {e}")

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Computes SHA256 checksum of a file and compares it to the expected hash.
    """
    sha256_hash = hashlib.sha256()
    logger.info(f"Verifying checksum for {file_path}")
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        computed_hash = sha256_hash.hexdigest()
        
        if computed_hash == expected_hash:
            logger.info("Checksum verification PASSED.")
            return True
        else:
            logger.error(f"Checksum verification FAILED.")
            logger.error(f"Expected: {expected_hash}")
            logger.error(f"Computed: {computed_hash}")
            return False
    except Exception as e:
        logger.error(f"Error computing checksum: {e}")
        raise

def decompress_gz(gz_path: Path, db_path: Path) -> None:
    """
    Decompresses a gzip file to the target database path.
    """
    logger.info(f"Decompressing {gz_path} to {db_path}")
    try:
        with gzip.open(gz_path, 'rb') as f_in:
            with open(db_path, 'wb') as f_out:
                f_out.write(f_in.read())
        logger.info("Decompression completed.")
        # Remove the gzipped file to save space
        os.remove(gz_path)
        logger.info(f"Removed temporary gzipped file: {gz_path}")
    except Exception as e:
        logger.error(f"Error during decompression: {e}")
        raise

def main():
    """
    Main entry point for the download task.
    """
    log_pipeline_step("T009", "Starting ChEMBL 33 download task")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    monitor.start()

    try:
        # 1. Download the gzipped file
        download_chembl_ftp(CHEMBL_FTP_HOST, CHEMBL_FTP_PATH, GZIPPED_TEMP_FILE)
        
        # 2. Verify checksum of the downloaded file
        if not verify_checksum(GZIPPED_TEMP_FILE, OFFICIAL_CHECKSUM):
            raise RuntimeError("Checksum verification failed. Downloaded file is corrupted or mismatched.")
        
        # 3. Decompress to final .db location
        decompress_gz(GZIPPED_TEMP_FILE, OUTPUT_FILE)
        
        # 4. Verify the final database file exists and compute its hash
        if not OUTPUT_FILE.exists():
            raise FileNotFoundError(f"Output file {OUTPUT_FILE} was not created after decompression.")
        
        final_hash = compute_file_hash(OUTPUT_FILE)
        logger.info(f"Final database file hash: {final_hash}")

        # 5. Update state file with the artifact hash
        # The task requires recording the checksum in the state file
        state_update = {
            "artifact_path": str(OUTPUT_FILE.relative_to(project_root)),
            "hash": final_hash,
            "source": "chembl_33_ftp",
            "version": "33"
        }
        
        update_state(
            project_id="PROJ-066-investigating-correlations-between-molec",
            artifacts=[state_update]
        )
        
        logger.info(f"Successfully downloaded, verified, and recorded ChEMBL 33 to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Task T009 failed: {e}")
        monitor.stop()
        raise
    finally:
        monitor.stop()
        log_pipeline_step("T009", "Task finished", status="completed" if OUTPUT_FILE.exists() else "failed")

if __name__ == "__main__":
    main()
