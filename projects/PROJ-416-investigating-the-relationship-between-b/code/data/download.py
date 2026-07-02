import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import logging utilities from the project's utils module
from utils.logging import setup_logging, log_provenance

# Import Config to access environment variables
from config import Config

# Configure the logger
logger = logging.getLogger(__name__)

def validate_source_id(source_id: Optional[str]) -> bool:
    """
    Explicitly check for a verified OpenNeuro ID.
    
    If the source_id is missing, None, or empty, this function halts execution
    with a fatal error and logs "Missing verified dataset source" to align with
    Plan Summary "STATUS: BLOCKED" and FR-011.
    
    Args:
        source_id: The OpenNeuro dataset ID (e.g., 'ds000001').
        
    Returns:
        True if the ID is present and valid.
        
    Raises:
        SystemExit: If the ID is missing, halting the pipeline immediately.
    """
    if not source_id or not isinstance(source_id, str) or source_id.strip() == "":
        logger.critical("Missing verified dataset source")
        logger.critical("Pipeline halted due to missing OpenNeuro ID. "
                        "Please set OPENNEURO_DATASET_ID in environment or .env file.")
        # Halt execution immediately as per FR-011 and Plan constraints
        sys.exit(1)
    
    # Basic format validation (OpenNeuro IDs usually start with 'ds')
    if not source_id.startswith("ds"):
        logger.warning(f"Source ID '{source_id}' does not start with 'ds'. "
                       "Proceeding, but validation may fail later.")
    
    logger.info(f"Verified dataset source ID: {source_id}")
    return True

def get_dataset_metadata(source_id: str) -> Dict[str, Any]:
    """
    Fetches metadata for the given dataset ID.
    In a full implementation, this would query the OpenNeuro API.
    For now, it validates the ID and returns a placeholder structure 
    to ensure the pipeline can proceed to the next validation steps 
    once a real source is provided.
    
    Args:
        source_id: The OpenNeuro dataset ID.
        
    Returns:
        A dictionary containing dataset metadata.
    """
    # Ensure the ID is valid before attempting any fetch
    validate_source_id(source_id)
    
    logger.info(f"Fetching metadata for dataset: {source_id}")
    
    # Placeholder for actual API call:
    # response = requests.get(f"https://api.openneuro.org/datasets/{source_id}")
    # if response.status_code != 200:
    #     raise RuntimeError(f"Failed to fetch metadata: {response.text}")
    # return response.json()
    
    # Since we cannot fetch real data without a valid ID in this specific 
    # validation step, we return a minimal structure assuming validation passed.
    # The actual download logic (T012) will handle the real fetch.
    return {
        "id": source_id,
        "name": f"Dataset {source_id}",
        "status": "pending_download"
    }

def download_dataset_files(source_id: str, output_dir: Path) -> List[Path]:
    """
    Downloads dataset files from OpenNeuro.
    
    Args:
        source_id: The OpenNeuro dataset ID.
        output_dir: The local directory to save files.
        
    Returns:
        A list of paths to downloaded files.
    """
    validate_source_id(source_id)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Starting download for {source_id} to {output_dir}")
    
    # Implementation of actual download logic would go here.
    # For T012a, we focus on the validation halt.
    
    return []

def run_download(config: Config) -> bool:
    """
    Orchestrates the download process.
    
    Args:
        config: The project configuration object.
        
    Returns:
        True if successful, False otherwise.
    """
    source_id = config.OPENNEURO_DATASET_ID
    
    # The critical check happens here. If missing, the function will exit.
    validate_source_id(source_id)
    
    metadata = get_dataset_metadata(source_id)
    
    # Proceed with download logic
    output_path = config.DATA_RAW_DIR / source_id
    files = download_dataset_files(source_id, output_path)
    
    return len(files) > 0

def main():
    """
    Entry point for the download script.
    """
    # Setup logging
    log_path = Path("logs/download.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_path=log_path, level=logging.INFO)
    
    log_provenance(logger, "download.py", "T012a")
    
    try:
        # Load config
        config = Config()
        
        # Run the download pipeline
        success = run_download(config)
        
        if success:
            logger.info("Download completed successfully.")
        else:
            logger.warning("Download completed with no files (check source).")
            
    except SystemExit:
        # Re-raise SystemExit to ensure the pipeline halts as intended
        raise
    except Exception as e:
        logger.error(f"Download failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()