import os
import sys
from pathlib import Path
from typing import List
from config import INPUT_PATHS, DQS_REQUIRED, ensure_directories
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger(__name__)

def check_local_file_exists(file_path: str) -> bool:
    """
    Check if a specific local file exists.
    
    Args:
        file_path: Absolute or relative path to the file.
        
    Returns:
        True if the file exists and is a regular file, False otherwise.
    """
    path = Path(file_path)
    return path.is_file()

def verify_required_files() -> List[str]:
    """
    Verify that all required input files defined in INPUT_PATHS exist locally.
    
    Returns:
        A list of missing file paths.
    """
    missing_files = []
    
    # Ensure directories exist first
    ensure_directories()
    
    for category, paths in INPUT_PATHS.items():
        if isinstance(paths, str):
            # Single path
            if not check_local_file_exists(paths):
                missing_files.append(paths)
        elif isinstance(paths, dict):
            # Dictionary of paths (e.g., {'microbiome': 'path/to/file', 'cognitive': 'path/to/file'})
            for key, path in paths.items():
                if not check_local_file_exists(path):
                    missing_files.append(path)
    
    return missing_files

def verify_data_source_availability() -> bool:
    """
    Main verification function for T048a.
    
    Checks if the verified data source (local files in data/raw/) exists.
    If DQS_REQUIRED is True, it also checks for the specific dietary data columns
    by verifying the existence of the dietary data file.
    
    Raises:
        FileNotFoundError: If required files are missing and no fallback is available.
        
    Returns:
        True if all required data sources are available.
    """
    log_pipeline_start("verify_data_source")
    log_provenance("Starting data source availability verification for T048a")
    
    # 1. Check local files in data/raw/
    missing_files = verify_required_files()
    
    if missing_files:
        error_msg = (
            f"FATAL: Required data files are missing in {Path('data/raw')}.\n"
            f"Missing files: {missing_files}\n"
            f"Please ensure data is placed in {Path('data/raw')} as per README.md instructions.\n"
            f"See docs/data_source_resolution.md for data access details."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    log_provenance("All required local data files found.")
    
    # 2. If DQS is required, verify the dietary data file specifically
    if DQS_REQUIRED:
        dietary_path = INPUT_PATHS.get('dietary_data') or INPUT_PATHS.get('dietary', {}).get('raw')
        if dietary_path and not check_local_file_exists(dietary_path):
            error_msg = (
                f"FATAL: Dietary data file is missing but DQS_REQUIRED is True.\n"
                f"Expected file: {dietary_path}\n"
                f"Set DQS_REQUIRED=False in config.py to proceed without dietary data."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        log_provenance("DQS data file verified.")
    
    log_pipeline_end("verify_data_source", status="SUCCESS")
    return True

def main():
    """Entry point for script execution."""
    try:
        verify_data_source_availability()
        print("Data source verification PASSED.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Data source verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()