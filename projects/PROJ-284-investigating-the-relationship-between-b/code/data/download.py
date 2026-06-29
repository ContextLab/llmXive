import os
import time
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import logging

from config import get_hcp_credentials, get_config
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
HCP_API_VERSION = "v1"
BEHAVIORAL_DATA_FIELDS = [
    "motor_score",  # Primary metric of interest
    "age",
    "sex",
    "fd"  # Framewise Displacement
]

def get_subject_list_with_behavioral_data(
    subjects: List[str],
    credentials: Dict[str, str],
    api_version: str = HCP_API_VERSION
) -> List[str]:
    """
    Filter a list of subject IDs to those that have complete behavioral data.
    
    This implements the subject exclusion logic for missing behavioral data (T016).
    It checks the HCP API for the availability of required behavioral fields
    (motor_score, age, sex, fd) for each subject.
    
    Args:
        subjects: List of subject IDs to check.
        credentials: Dictionary containing HCP API credentials.
        api_version: HCP API version string.
        
    Returns:
        List of subject IDs that have all required behavioral data available.
        
    Raises:
        ValueError: If credentials are missing or invalid.
        requests.RequestException: If API connection fails.
    """
    if not credentials:
        raise ValueError("HCP credentials are required to fetch behavioral data.")
    
    base_url = f"https://api.humanconnectome.org/{api_version}"
    auth = (credentials.get('username', ''), credentials.get('password', ''))
    
    valid_subjects = []
    excluded_subjects = []
    
    logger.info(f"Checking behavioral data availability for {len(subjects)} subjects...")
    
    for subject_id in subjects:
        try:
            # Construct the URL for subject behavioral data
            # HCP API typically exposes subject data at /subjects/{subject_id}/data
            url = f"{base_url}/subjects/{subject_id}/data"
            
            # Add a small delay to respect rate limits
            time.sleep(0.1)
            
            response = requests.get(
                url, 
                auth=auth, 
                headers={"Accept": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required behavioral fields
                # The API response structure might vary, but we look for 'behavioral' or 'phenotypic' keys
                behavioral_data = data.get('behavioral', data.get('phenotypic', data))
                
                has_all_fields = True
                missing_fields = []
                
                for field in BEHAVIORAL_DATA_FIELDS:
                    # Check if the field exists and is not null/empty
                    if field not in behavioral_data or behavioral_data[field] is None:
                        has_all_fields = False
                        missing_fields.append(field)
                
                if has_all_fields:
                    valid_subjects.append(subject_id)
                    logger.debug(f"Subject {subject_id}: All behavioral data present.")
                else:
                    excluded_subjects.append(subject_id)
                    logger.warning(f"Subject {subject_id}: Missing fields {missing_fields}. Excluded.")
                    
            elif response.status_code == 404:
                logger.warning(f"Subject {subject_id}: Not found in HCP database. Excluded.")
                excluded_subjects.append(subject_id)
            elif response.status_code == 401:
                raise ValueError("Invalid HCP credentials provided.")
            else:
                logger.error(f"Subject {subject_id}: API error {response.status_code}. Excluded.")
                excluded_subjects.append(subject_id)
                
        except requests.RequestException as e:
            logger.error(f"Subject {subject_id}: Network error {str(e)}. Excluded.")
            excluded_subjects.append(subject_id)
        except json.JSONDecodeError:
            logger.error(f"Subject {subject_id}: Invalid JSON response. Excluded.")
            excluded_subjects.append(subject_id)
        
    logger.info(f"Subject exclusion complete: {len(valid_subjects)} valid, {len(excluded_subjects)} excluded.")
    return valid_subjects

def fetch_subject_data(
    subject_id: str,
    data_type: str = "ICA-FIX",
    credentials: Optional[Dict[str, str]] = None,
    output_dir: Optional[Path] = None
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Fetch data for a specific subject.
    
    Args:
        subject_id: The HCP subject ID.
        data_type: Type of data to fetch ('ICA-FIX' or 'raw').
        credentials: HCP API credentials.
        output_dir: Directory to save downloaded files.
        
    Returns:
        Tuple of (Path to downloaded file, Error message if any).
    """
    if not credentials:
        credentials = get_hcp_credentials()
        
    if not output_dir:
        config = get_config()
        output_dir = Path(config.get('OUTPUT_DIR', 'data/processed'))
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = f"https://api.humanconnectome.org/{HCP_API_VERSION}"
    auth = (credentials.get('username', ''), credentials.get('password', ''))
    
    # Determine the specific URL based on data type
    # This logic is simplified; real implementation would map data_type to specific HCP paths
    if data_type == "ICA-FIX":
        url = f"{base_url}/subjects/{subject_id}/fMRIs/MNINonLinear/RFMRI/RFMRI_REST1_LR"
    else:
        url = f"{base_url}/subjects/{subject_id}/fMRIs/RFMRI/RFMRI_REST1_LR"
        
    try:
        response = requests.get(url, auth=auth, stream=True, timeout=300)
        
        if response.status_code == 200:
            filename = f"{subject_id}_{data_type}.nii.gz"
            file_path = output_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded {filename} for subject {subject_id}")
            return file_path, None
        else:
            logger.error(f"Failed to download data for {subject_id}: {response.status_code}")
            return None, f"API error {response.status_code}"
            
    except requests.RequestException as e:
        logger.error(f"Network error downloading {subject_id}: {str(e)}")
        return None, str(e)

def download_pipeline(
    subject_ids: List[str],
    data_type: str = "ICA-FIX",
    credentials: Optional[Dict[str, str]] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Download data for a list of subjects, excluding those without behavioral data.
    
    This function integrates the subject exclusion logic (T016) with the data fetching logic.
    It first filters subjects based on behavioral data availability, then downloads
    data for the remaining subjects.
    
    Args:
        subject_ids: List of all available subject IDs.
        data_type: Type of data to fetch ('ICA-FIX' or 'raw').
        credentials: HCP API credentials.
        output_dir: Directory to save downloaded files.
        
    Returns:
        Dictionary mapping subject_id to status ('downloaded', 'excluded', 'error').
    """
    if not credentials:
        credentials = get_hcp_credentials()
        
    results = {}
    
    # Step 1: Filter subjects with behavioral data (T016 logic)
    valid_subjects = get_subject_list_with_behavioral_data(
        subject_ids, 
        credentials
    )
    
    # Mark excluded subjects
    excluded_set = set(subject_ids) - set(valid_subjects)
    for subj in excluded_set:
        results[subj] = "excluded"
        
    # Step 2: Download data for valid subjects
    for subject_id in valid_subjects:
        file_path, error = fetch_subject_data(
            subject_id, 
            data_type, 
            credentials, 
            output_dir
        )
        
        if file_path:
            results[subject_id] = "downloaded"
        else:
            results[subject_id] = f"error: {error}"
            
    return results