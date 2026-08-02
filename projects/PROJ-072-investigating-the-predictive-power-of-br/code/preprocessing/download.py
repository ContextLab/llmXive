import os
import hashlib
import requests
from urllib.parse import urljoin
import logging
import time
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
OPENNEURO_BASE_URL = "https://openneuro.org/datasets"
DATASET_ID = "ds000030"
DATASET_VERSION = "1.0.0"  # Specific version to ensure reproducibility
RAW_DATA_DIR = Path("data/raw")
METADATA_DIR = Path("data/metadata")
EXCLUSION_LOG_FILE = METADATA_DIR / "exclusion_log.txt"
SUBJECT_LABELS_FILE = METADATA_DIR / "subject_labels.csv"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

def download_url_exists(url: str) -> bool:
    """Check if the dataset URL exists."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"URL check failed for {url}: {e}")
        return False

def get_dataset_download_url() -> str:
    """Construct the download URL for the OpenNeuro dataset."""
    # OpenNeuro datasets are typically hosted via their API or direct S3 buckets
    # For ds000030, we use the public download link structure
    # Note: In a real scenario, we might use the OpenNeuro API to get the latest version
    base_url = f"{OPENNEURO_BASE_URL}/{DATASET_ID}"
    # Assuming a standard download path for the dataset
    # This might need adjustment based on actual OpenNeuro structure
    download_url = f"{base_url}/archive?format=zip"
    return download_url

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the SHA-256 checksum of a downloaded file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        return actual_checksum == expected_checksum
    except FileNotFoundError:
        logger.error(f"File not found for checksum verification: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Checksum verification failed for {file_path}: {e}")
        return False

def download_dataset(url: str, output_path: Path) -> bool:
    """Download the dataset from the provided URL."""
    try:
        logger.info(f"Downloading dataset from {url} to {output_path}")
        response = requests.get(url, stream=True, timeout=3600)  # 1 hour timeout
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        logger.info(f"Download progress: {progress:.2f}%")
        
        logger.info(f"Download completed successfully: {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False

def process_metadata_and_exclude_subjects() -> None:
    """
    Process metadata to identify subjects with missing diagnostic labels.
    Exclude these subjects and log the count to exclusion_log.txt.
    """
    logger.info("Processing metadata and excluding subjects with missing labels...")
    
    # Path to the dataset's participants.tsv (standard BIDS format)
    # Adjust path based on actual dataset structure after download
    participants_file = RAW_DATA_DIR / DATASET_ID / "participants.tsv"
    
    if not participants_file.exists():
        logger.warning(f"Participants file not found at {participants_file}. Skipping exclusion logic.")
        # Log that no exclusion was performed due to missing metadata
        with open(EXCLUSION_LOG_FILE, 'w') as f:
            f.write("No participants.tsv found. No subjects excluded.\n")
        return

    excluded_subjects = []
    included_subjects = []
    
    try:
        import pandas as pd
        participants_df = pd.read_csv(participants_file, sep='\t')
        
        # Check if 'diagnosis' or similar column exists
        # Common BIDS columns: diagnosis, group, condition
        label_columns = [col for col in participants_df.columns if 'diagnosis' in col.lower() or 'group' in col.lower()]
        
        if not label_columns:
            logger.warning("No diagnostic label column found in participants.tsv. Excluding all subjects.")
            excluded_subjects = participants_df['participant_id'].tolist()
        else:
            label_col = label_columns[0]  # Use the first found label column
            # Identify subjects with missing or NaN values in the label column
            missing_mask = participants_df[label_col].isna() | (participants_df[label_col] == '')
            excluded_subjects = participants_df[missing_mask]['participant_id'].tolist()
            included_subjects = participants_df[~missing_mask]['participant_id'].tolist()
        
        # Write exclusion log
        with open(EXCLUSION_LOG_FILE, 'w') as f:
            f.write(f"Total subjects processed: {len(participants_df)}\n")
            f.write(f"Subjects excluded due to missing diagnostic labels: {len(excluded_subjects)}\n")
            f.write(f"Excluded subject IDs: {', '.join(excluded_subjects)}\n")
            f.write(f"Included subject IDs: {', '.join(included_subjects)}\n")
        
        logger.info(f"Exclusion log written to {EXCLUSION_LOG_FILE}")
        logger.info(f"Excluded {len(excluded_subjects)} subjects due to missing diagnostic labels.")
        
        # Save included subjects to a CSV for downstream use
        if included_subjects:
            included_df = pd.DataFrame({'participant_id': included_subjects})
            included_df.to_csv(SUBJECT_LABELS_FILE, index=False)
            logger.info(f"Saved {len(included_subjects)} included subjects to {SUBJECT_LABELS_FILE}")
        else:
            logger.warning("No subjects included after exclusion. Check metadata.")
            
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        # Fallback: exclude all if metadata processing fails
        with open(EXCLUSION_LOG_FILE, 'w') as f:
            f.write("Error processing metadata. All subjects excluded.\n")
        raise

def main():
    """Main entry point for the download and metadata processing pipeline."""
    logger.info("Starting download pipeline for OpenNeuro dataset ds000030")
    
    # Step 1: Check URL existence
    download_url = get_dataset_download_url()
    if not download_url_exists(download_url):
        logger.error(f"Dataset URL does not exist: {download_url}")
        return False
    
    # Step 2: Download dataset
    output_file = RAW_DATA_DIR / f"{DATASET_ID}.zip"
    if not download_dataset(download_url, output_file):
        logger.error("Failed to download dataset.")
        return False
    
    # Step 3: Verify checksum (if expected checksum is available)
    # For now, we skip checksum verification as the expected checksum is not provided
    # In a real scenario, this would be fetched from OpenNeuro's metadata
    logger.info("Skipping checksum verification (expected checksum not provided)")
    
    # Step 4: Process metadata and exclude subjects
    try:
        process_metadata_and_exclude_subjects()
    except Exception as e:
        logger.error(f"Metadata processing failed: {e}")
        return False
    
    logger.info("Download pipeline completed successfully.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
