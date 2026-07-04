import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from code.data_loader import calculate_md5, verify_checksum, download_hcp_fmri_data, download_phenotype_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_phenotype_file(path: str) -> bool:
    """Validate existence and format of phenotype file."""
    if not os.path.exists(path):
        logger.error(f"Phenotype file not found: {path}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(path)
        required_cols = ['subject_id', 'creative_score']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Phenotype file missing required columns: {required_cols}")
            return False
        logger.info(f"Phenotype file validated: {path} ({len(df)} records)")
        return True
    except Exception as e:
        logger.error(f"Failed to validate phenotype file: {e}")
        return False

def validate_fmri_data(subject_id: str, data_dir: str) -> bool:
    """Validate existence of fMRI data for a subject."""
    expected_path = Path(data_dir) / subject_id / "fMRI"
    if not expected_path.exists():
        logger.warning(f"fMRI data not found for subject {subject_id}")
        return False
    logger.info(f"fMRI data validated for subject {subject_id}")
    return True

def validate_data_integrity(data_dir: str, phenotype_path: str) -> Tuple[bool, List[str]]:
    """
    Validate overall data integrity before processing.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check phenotype file
    if not validate_phenotype_file(phenotype_path):
        errors.append("Phenotype file validation failed")
    
    # Check data directory
    if not os.path.exists(data_dir):
        errors.append(f"Data directory not found: {data_dir}")
    
    return len(errors) == 0, errors

def main():
    """Main entry point for the research pipeline."""
    logger.info("Starting llmXive research pipeline...")
    
    # Configuration
    data_dir = "data/raw"
    processed_dir = "data/processed"
    phenotype_path = "data/raw/Creative_Problem_Solving.csv"
    
    # Ensure directories exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Validate data
    is_valid, errors = validate_data_integrity(data_dir, phenotype_path)
    if not is_valid:
        logger.critical("Data validation failed. Cannot proceed.")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    
    logger.info("Data validation passed. Proceeding with analysis...")
    
    # Placeholder for main analysis pipeline
    # In a full implementation, this would call entropy.py, modeling.py, etc.
    logger.info("Pipeline execution complete (placeholder).")

if __name__ == "__main__":
    main()
