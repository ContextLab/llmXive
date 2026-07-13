import os
import time
import json
import hashlib
import requests
import logging
from pathlib import Path
from nilearn import datasets
from config import get_config, get_hcp_credentials
from logging_config import get_logger

logger = get_logger(__name__)

class DataAvailabilitySwitch:
    """
    Logic to detect ICA-FIX availability and switch data source accordingly.
    """
    def __init__(self):
        self.config = get_config()
        self.ica_fix_available = False
    
    def check_ica_fix_availability(self, subject_id):
        """
        Check if ICA-FIX derived data is available for a subject.
        Returns True if available, False otherwise.
        """
        # In a real implementation, this would check the HCP API
        # For now, we simulate based on subject_id pattern
        # This is a placeholder - real implementation would query HCP
        logger.info(f"Checking ICA-FIX availability for {subject_id}")
        return False  # Default to raw data if not explicitly available
    
    def get_data_url(self, subject_id, data_type='ica_fix'):
        """
        Get the appropriate data URL based on availability.
        """
        if data_type == 'ica_fix' and self.check_ica_fix_availability(subject_id):
            # ICA-FIX URL
            return f"https://hcp.openfmri.org/{subject_id}/ica_fix"
        else:
            # Raw data URL
            return f"https://hcp.openfmri.org/{subject_id}/raw"

def get_fsl_tool_path():
    """
    Get the path to FSL tools.
    """
    fsl_path = os.getenv('FSLDIR')
    if not fsl_path:
        logger.warning("FSLDIR not set. FSL tools may not be available.")
        return None
    return fsl_path

def get_afni_tool_path():
    """
    Get the path to AFNI tools.
    """
    afni_path = os.getenv('AFNI_HOME')
    if not afni_path:
        logger.warning("AFNI_HOME not set. AFNI tools may not be available.")
        return None
    return afni_path

def get_subject_list_with_behavioral_data():
    """
    Get list of subjects that have both fMRI and behavioral data.
    Uses nilearn's ADHD dataset as a verified real data source.
    """
    try:
        # Fetch ADHD dataset from nilearn (verified real source)
        logger.info("Fetching ADHD dataset from nilearn...")
        bunch = datasets.fetch_adhd(
            data_dir=os.path.join(os.getenv("HOME", "/tmp"), "nilearn_data"),
            verbose=0,
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(bunch.phenotypic)
        
        # Filter for subjects with valid behavioral data
        # Assuming 'full_2_iq' or similar behavioral metric exists
        valid_subjects = df[df['full_2_iq'].notna()]
        
        logger.info(f"Found {len(valid_subjects)} subjects with behavioral data")
        return valid_subjects['Subject'].tolist()
    except Exception as e:
        logger.error(f"Failed to fetch subject list: {e}", exc_info=True)
        return []

def fetch_subject_data(subject_id, data_type='raw'):
    """
    Fetch data for a specific subject.
    """
    # In a real implementation, this would download from HCP
    # For now, we use nilearn's ADHD dataset as a fallback
    logger.info(f"Fetching data for subject {subject_id}")
    return None

def download_pipeline(subject_ids, data_dir="data/raw"):
    """
    Download and preprocess data for a list of subjects.
    """
    data_dir_path = Path(data_dir)
    data_dir_path.mkdir(parents=True, exist_ok=True)
    
    for subject_id in subject_ids:
        try:
            logger.info(f"Processing subject {subject_id}")
            # Placeholder for actual download logic
            # In real implementation, this would download and preprocess
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}", exc_info=True)
            continue

def main():
    """
    Main entry point for data download.
    """
    try:
        # Get subject list
        subjects = get_subject_list_with_behavioral_data()
        if not subjects:
            logger.warning("No subjects found with behavioral data")
            return False
        
        # Download pipeline
        download_pipeline(subjects[:10])  # Limit to 10 for testing
        return True
    except Exception as e:
        logger.error(f"Download pipeline failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
