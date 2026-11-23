"""
Main orchestration script for the molecular descriptor analysis pipeline.
Implements logging infrastructure to write to data_version.json.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import logging

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_project_root, get_data_processed_path, get_logs_path
from src.data.schema import (
    DataVersion,
    save_data_version_to_file,
    load_data_version_from_file,
    create_empty_data_version
)

# Configure logging
def setup_logging():
    """Configure logging to write to a file in the logs directory."""
    logs_path = get_logs_path()
    logs_path.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_path / "pipeline.log"
    
    # Create logger
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_data_version_path():
    """Get the path to the data_version.json file."""
    processed_path = get_data_processed_path()
    processed_path.mkdir(parents=True, exist_ok=True)
    return processed_path / "data_version.json"

def load_data_version():
    """Load existing data version from file, or return empty version if not exists."""
    version_path = get_data_version_path()
    if version_path.exists():
        return load_data_version_from_file(version_path)
    return create_empty_data_version()

def save_data_version(version: DataVersion):
    """Save data version to file."""
    version_path = get_data_version_path()
    save_data_version_to_file(version, version_path)

def log_data_version(source_url: str, checksum_sha256: str, logger: logging.Logger):
    """
    Log a new data version entry to data_version.json.
    
    Args:
        source_url: URL of the data source
        checksum_sha256: SHA256 checksum of the downloaded file
        logger: Logger instance to use for logging
    """
    version = load_data_version()
    
    # Create new entry
    from datetime import datetime
    new_entry = {
        "source_url": source_url,
        "checksum_sha256": checksum_sha256,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Append to versions list
    if "versions" not in version:
        version["versions"] = []
    version["versions"].append(new_entry)
    
    # Save back to file
    save_data_version(version)
    logger.info(f"Logged data version: {source_url} -> {checksum_sha256[:16]}...")

def log_pipeline_start(logger: logging.Logger, pipeline_name: str = "main"):
    """Log the start of a pipeline execution."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"Pipeline '{pipeline_name}' started at {timestamp}")
    return timestamp

def log_pipeline_end(logger: logging.Logger, pipeline_name: str = "main", start_time: float = None):
    """Log the end of a pipeline execution."""
    timestamp = datetime.now(timezone.utc).isoformat()
    duration = None
    if start_time:
        duration = time.time() - start_time
        logger.info(f"Pipeline '{pipeline_name}' completed at {timestamp} (duration: {duration:.2f}s)")
    else:
        logger.info(f"Pipeline '{pipeline_name}' completed at {timestamp}")

def ensure_data_directory():
    """Ensure all required data directories exist."""
    processed_path = get_data_processed_path()
    processed_path.mkdir(parents=True, exist_ok=True)
    
    raw_path = Path(get_project_root()) / "data" / "raw"
    raw_path.mkdir(parents=True, exist_ok=True)
    
    logs_path = get_logs_path()
    logs_path.mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for the pipeline."""
    # Setup logging
    logger = setup_logging()
    
    # Ensure directories exist
    ensure_data_directory()
    
    logger.info("Molecular Descriptor Analysis Pipeline")
    logger.info("=" * 50)
    
    # Log pipeline start
    start_time = time.time()
    log_pipeline_start(logger)
    
    try:
        # Placeholder for actual pipeline steps
        # These would be implemented in subsequent tasks
        logger.info("Pipeline steps to be implemented:")
        logger.info("  1. Data acquisition (T013)")
        logger.info("  2. Descriptor computation (T014)")
        logger.info("  3. Data merging (T015)")
        logger.info("  4. Dimensionality reduction (T022)")
        logger.info("  5. Clustering and enrichment (T024-T028)")
        logger.info("  6. Statistical analysis (T034-T040)")
        
        # Log pipeline end
        log_pipeline_end(logger, start_time=start_time)
        
        logger.info("Pipeline execution complete.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())