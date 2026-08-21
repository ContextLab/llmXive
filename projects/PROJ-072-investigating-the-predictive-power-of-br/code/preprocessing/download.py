import os
import hashlib
import requests
from urllib.parse import urljoin
import logging
import time
from pathlib import Path
import json
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OPENNEURO_BASE_URL = "https://openneuro.org/datasets"
DATASET_ID = "ds000030"
DATASET_VERSION = "1.0.4"  # Specific version to ensure reproducibility
RAW_DATA_DIR = Path("data/raw")
METADATA_DIR = Path("data/metadata")
PARTICIPANTS_FILE = "participants.tsv"
EXCLUSION_LOG_FILE = "exclusion_log.txt"
SUBJECT_STATUS_FILE = "subject_status.csv"

def download_url_exists(url: str) -> bool:
    """
    Check if a URL exists by sending a HEAD request.
    
    Args:
        url: The URL to check
        
    Returns:
        True if the URL exists (status 200), False otherwise
    """
    try:
        response = requests.head(url, timeout=30)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Error checking URL {url}: {e}")
        return False

def get_dataset_download_url() -> str:
    """
    Construct the download URL for the OpenNeuro dataset.
    
    Returns:
        The download URL for the dataset
    """
    # OpenNeuro provides download links via their API or direct tarballs
    # For ds000030, we construct the tarball URL
    base_url = f"{OPENNEURO_BASE_URL}/{DATASET_ID}/download"
    # The actual download is typically a tarball of the dataset
    # Using the versioned snapshot URL
    snapshot_url = f"{OPENNEURO_BASE_URL}/{DATASET_ID}/snapshots/{DATASET_VERSION}"
    
    # For programmatic access, we use the datalad or direct tarball approach
    # Since OpenNeuro doesn't provide a direct single-file download URL for the whole dataset,
    # we will use the participants.tsv and subject directories approach
    # The base URL for accessing files is:
    return f"https://openneuro.org/datasets/{DATASET_ID}/versions/{DATASET_VERSION}"

def verify_checksum(file_path: str, expected_sha256: str) -> bool:
    """
    Verify the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to verify
        expected_sha256: Expected SHA-256 hash
        
    Returns:
        True if checksum matches, False otherwise
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_sha256 = sha256_hash.hexdigest()
        return actual_sha256 == expected_sha256
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error verifying checksum: {e}")
        return False

def download_dataset():
    """
    Download the OpenNeuro dataset ds000030.
    
    This function downloads the dataset using the OpenNeuro API.
    Since OpenNeuro doesn't provide a simple direct download link for the entire dataset,
    we use a combination of their API and direct file access.
    
    For this implementation, we will download the participants.tsv file first
    to get subject information, then download individual subject directories.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download of dataset {DATASET_ID}")
    
    # First, try to get the participants.tsv file
    participants_url = f"https://openneuro.org/datasets/{DATASET_ID}/files/participants.tsv"
    participants_path = RAW_DATA_DIR / PARTICIPANTS_FILE
    
    if not participants_path.exists():
        logger.info(f"Downloading participants file from {participants_url}")
        try:
            response = requests.get(participants_url, timeout=120)
            response.raise_for_status()
            with open(participants_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Successfully downloaded participants file to {participants_path}")
        except requests.RequestException as e:
            logger.error(f"Failed to download participants file: {e}")
            # If we can't get participants, we can't proceed
            raise RuntimeError(f"Cannot proceed without participants file: {e}")
    else:
        logger.info(f"Participants file already exists at {participants_path}")
    
    # Now we need to download subject data
    # OpenNeuro dataset structure: sub-<label>/func/, sub-<label>/anat/, etc.
    # We'll download subject directories that have functional imaging data
    
    # Load participants to get subject IDs
    try:
        df_participants = pd.read_csv(participants_path, sep='\t')
        subject_ids = df_participants['participant_id'].tolist()
        logger.info(f"Found {len(subject_ids)} subjects in participants file")
    except Exception as e:
        logger.error(f"Error reading participants file: {e}")
        raise RuntimeError(f"Cannot parse participants file: {e}")
    
    # Download each subject's functional data
    # Note: This is a simplified approach. In production, you might want to use
    # datalad or the OpenNeuro API more comprehensively
    for i, subject_id in enumerate(subject_ids):
        logger.info(f"Downloading subject {i+1}/{len(subject_ids)}: {subject_id}")
        
        # Construct URL for subject's functional data
        # OpenNeuro file structure: sub-<label>/func/sub-<label>_task-<task>_bold.nii.gz
        # We'll download the first available BOLD file for each subject
        
        subject_dir = RAW_DATA_DIR / subject_id
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to find and download a BOLD file
        # This is a simplified approach - in reality, you'd need to query the dataset structure
        bold_filename = f"{subject_id}_task-rest_bold.nii.gz"
        bold_url = f"https://openneuro.org/datasets/{DATASET_ID}/files/{subject_id}/func/{bold_filename}"
        bold_path = subject_dir / "func" / bold_filename
        bold_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not bold_path.exists():
            try:
                logger.info(f"Downloading {bold_url}")
                response = requests.get(bold_url, timeout=300)
                if response.status_code == 404:
                    # Try alternative naming convention
                    bold_filename_alt = f"{subject_id}_task-rest_bold.nii"
                    bold_url_alt = f"https://openneuro.org/datasets/{DATASET_ID}/files/{subject_id}/func/{bold_filename_alt}"
                    logger.info(f"Trying alternative URL: {bold_url_alt}")
                    response = requests.get(bold_url_alt, timeout=300)
                    if response.status_code == 404:
                        logger.warning(f"No BOLD file found for {subject_id}, skipping")
                        continue
                    bold_filename = bold_filename_alt
                    bold_path = subject_dir / "func" / bold_filename
                
                response.raise_for_status()
                with open(bold_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Successfully downloaded {bold_filename}")
            except requests.RequestException as e:
                logger.warning(f"Failed to download {subject_id}: {e}")
                # Continue with next subject rather than failing completely
                continue
        else:
            logger.info(f"Subject {subject_id} data already exists")
    
    logger.info("Dataset download completed")
    return True

def process_metadata_and_exclude_subjects():
    """
    Process metadata to identify and exclude subjects with missing diagnostic labels.
    
    This function:
    1. Reads the participants.tsv file
    2. Identifies subjects missing diagnostic labels (e.g., 'group', 'diagnosis', 'status')
    3. Excludes these subjects from further processing
    4. Logs the exclusion count and reasons to data/metadata/exclusion_log.txt
    5. Creates subject_status.csv with inclusion/exclusion flags
    """
    participants_path = RAW_DATA_DIR / PARTICIPANTS_FILE
    exclusion_log_path = METADATA_DIR / EXCLUSION_LOG_FILE
    subject_status_path = METADATA_DIR / SUBJECT_STATUS_FILE
    
    if not participants_path.exists():
        logger.error(f"Participants file not found: {participants_path}")
        raise FileNotFoundError(f"Participants file not found: {participants_path}")
    
    # Read participants file
    try:
        df_participants = pd.read_csv(participants_path, sep='\t')
    except Exception as e:
        logger.error(f"Error reading participants file: {e}")
        raise RuntimeError(f"Cannot parse participants file: {e}")
    
    # Identify diagnostic label columns
    # Common column names for diagnostic information
    diagnostic_columns = ['group', 'diagnosis', 'status', 'diagnostic_group', 'patient_status', 'dx']
    diagnostic_column = None
    
    for col in diagnostic_columns:
        if col in df_participants.columns:
            diagnostic_column = col
            break
    
    if not diagnostic_column:
        # If no standard column found, check for any column with 'group' or 'diag' in name
        for col in df_participants.columns:
            if 'group' in col.lower() or 'diag' in col.lower():
                diagnostic_column = col
                break
    
    excluded_subjects = []
    included_subjects = []
    
    if not diagnostic_column:
        logger.warning("No diagnostic label column found in participants file")
        logger.warning("All subjects will be excluded due to missing diagnostic information")
        excluded_subjects = df_participants['participant_id'].tolist()
        included_subjects = []
    else:
        # Check for missing values in diagnostic column
        for _, row in df_participants.iterrows():
            subject_id = row['participant_id']
            diagnostic_value = row[diagnostic_column]
            
            # Check if diagnostic value is missing (NaN, None, empty string, 'unknown', 'n/a')
            if pd.isna(diagnostic_value) or \
               str(diagnostic_value).strip().lower() in ['', 'nan', 'none', 'unknown', 'n/a', 'na']:
                excluded_subjects.append({
                    'subject_id': subject_id,
                    'reason': f'Missing diagnostic label in column "{diagnostic_column}"',
                    'value': str(diagnostic_value)
                })
            else:
                included_subjects.append({
                    'subject_id': subject_id,
                    'diagnostic_label': diagnostic_value,
                    'reason': 'Has valid diagnostic label'
                })
    
    # Log exclusions
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(exclusion_log_path, 'w', encoding='utf-8') as f:
        f.write(f"Exclusion Log for Dataset {DATASET_ID}\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Diagnostic column used: {diagnostic_column if diagnostic_column else 'None (no diagnostic column found)'}\n")
        f.write(f"Total subjects processed: {len(df_participants)}\n")
        f.write(f"Subjects excluded: {len(excluded_subjects)}\n")
        f.write(f"Subjects included: {len(included_subjects)}\n")
        f.write("\n")
        f.write("Excluded Subjects:\n")
        f.write("-" * 50 + "\n")
        
        for exc in excluded_subjects:
            f.write(f"Subject: {exc['subject_id']}\n")
            f.write(f"  Reason: {exc['reason']}\n")
            f.write(f"  Value: {exc['value']}\n")
            f.write("\n")
    
    logger.info(f"Exclusion log written to {exclusion_log_path}")
    logger.info(f"Excluded {len(excluded_subjects)} subjects due to missing diagnostic labels")
    
    # Create subject_status.csv
    status_data = []
    
    # Add included subjects
    for inc in included_subjects:
        status_data.append({
            'subject_id': inc['subject_id'],
            'status': 'included',
            'diagnostic_label': inc['diagnostic_label'],
            'reason': inc['reason']
        })
    
    # Add excluded subjects
    for exc in excluded_subjects:
        status_data.append({
            'subject_id': exc['subject_id'],
            'status': 'excluded',
            'diagnostic_label': '',
            'reason': exc['reason']
        })
    
    df_status = pd.DataFrame(status_data)
    df_status.to_csv(subject_status_path, index=False)
    
    logger.info(f"Subject status written to {subject_status_path}")
    logger.info(f"Total included subjects: {len(included_subjects)}")
    logger.info(f"Total excluded subjects: {len(excluded_subjects)}")
    
    return len(excluded_subjects), len(included_subjects)

def main():
    """
    Main function to run the download and metadata processing pipeline.
    """
    logger.info("Starting download pipeline for OpenNeuro dataset ds000030")
    
    try:
        # Download the dataset
        download_dataset()
        
        # Process metadata and exclude subjects with missing labels
        excluded_count, included_count = process_metadata_and_exclude_subjects()
        
        logger.info(f"Pipeline completed successfully")
        logger.info(f"Excluded subjects: {excluded_count}")
        logger.info(f"Included subjects: {included_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
