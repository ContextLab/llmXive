import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['prefrontal_centrality', 'hippocampal_centrality']
FEATURES_FILE = 'data/processed/features.csv'
VERIFICATION_LOG = 'data/metadata/feature_verification_log.txt'

def check_regional_centrality_preservation(features_path: str = FEATURES_FILE) -> bool:
    """
    Verify that the features file contains the required regional centrality columns.
    
    Args:
        features_path: Path to the features CSV file.
        
    Returns:
        bool: True if all required columns are present, False otherwise.
        
    Raises:
        FileNotFoundError: If the features file does not exist.
    """
    features_file = Path(features_path)
    
    if not features_file.exists():
        error_msg = f"ERROR: Features file not found at {features_path}"
        logger.error(error_msg)
        log_error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_csv(features_file)
    except Exception as e:
        error_msg = f"ERROR: Failed to read features file {features_path}: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        raise RuntimeError(error_msg)
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_cols:
        error_msg = f"ERROR: Missing regional centrality columns: {missing_cols}"
        logger.error(error_msg)
        log_error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Verification successful. All required columns present: {REQUIRED_COLUMNS}")
    log_success(f"Verification successful. All required columns present: {REQUIRED_COLUMNS}")
    return True

def log_error(message: str, log_path: str = VERIFICATION_LOG):
    """Log an error message to the verification log file."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"[ERROR] {message}\n")
    
    logger.error(f"Logged to {log_path}: {message}")

def log_success(message: str, log_path: str = VERIFICATION_LOG):
    """Log a success message to the verification log file."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"[SUCCESS] {message}\n")
    
    logger.info(f"Logged to {log_path}: {message}")

def run_verification_pipeline(features_path: str = FEATURES_FILE) -> bool:
    """
    Run the full verification pipeline for regional centrality preservation.
    
    Args:
        features_path: Path to the features CSV file.
        
    Returns:
        bool: True if verification passes, False otherwise.
    """
    try:
        result = check_regional_centrality_preservation(features_path)
        return result
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Verification pipeline failed: {str(e)}")
        return False

def main():
    """Main entry point for the verification script."""
    logger.info("Starting regional centrality preservation verification...")
    
    try:
        success = run_verification_pipeline()
        if success:
            logger.info("Verification PASSED.")
            sys.exit(0)
        else:
            logger.error("Verification FAILED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()