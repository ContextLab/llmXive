import os
import sys
import json
import logging
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import gzip
import shutil

# Import from sibling modules as per API surface
import src.config
from src.data.quality_check import run_quality_check, save_manifest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Global state for checkpointing
checkpoint_file = Path("pipeline_checkpoint.json")
run_state: Dict[str, Any] = {
    "subjects_processed": [],
    "current_stage": "init",
    "start_time": None,
    "disk_usage_snapshot": 0
}

# Disk quota constants (in bytes)
# Default: 50GB limit, but configurable via config
DEFAULT_QUOTA_BYTES = 50 * 1024**3 
INTERMEDIATE_COMPRESSION_THRESHOLD = 100 * 1024**2  # 100MB

def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    logger.warning(f"Received signal {signum}. Saving checkpoint before exit...")
    save_checkpoint()
    sys.exit(0)

def save_checkpoint():
    """Save current run state to disk."""
    run_state["disk_usage_snapshot"] = get_current_disk_usage()
    run_state["timestamp"] = time.time()
    with open(checkpoint_file, 'w') as f:
        json.dump(run_state, f, indent=2)
    logger.info(f"Checkpoint saved: {len(run_state['subjects_processed'])} subjects processed.")

def load_checkpoint() -> bool:
    """Load previous run state if exists. Returns True if loaded."""
    if not checkpoint_file.exists():
        return False
    try:
        with open(checkpoint_file, 'r') as f:
            loaded_state = json.load(f)
        run_state.update(loaded_state)
        logger.info(f"Checkpoint loaded. Resuming from stage: {run_state['current_stage']}")
        return True
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return False

def get_current_disk_usage() -> int:
    """Calculate total disk usage of data and results directories."""
    total_size = 0
    data_dirs = [
        Path(src.config.DATA_DIR),
        Path(src.config.RESULTS_DIR),
        Path(src.config.INTERMEDIATE_DIR)
    ]
    
    for directory in data_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
    return total_size

def check_disk_quota() -> bool:
    """
    Check if current disk usage exceeds the quota.
    Returns True if quota is exceeded (action needed), False otherwise.
    """
    current_usage = get_current_disk_usage()
    quota = getattr(src.config, 'DISK_QUOTA_BYTES', DEFAULT_QUOTA_BYTES)
    
    logger.info(f"Current disk usage: {current_usage / (1024**3):.2f} GB / {quota / (1024**3):.2f} GB")
    
    if current_usage > quota:
        logger.warning(f"Disk quota exceeded! ({current_usage} > {quota})")
        return True
    return False

def compress_intermediates() -> int:
    """
    Compress large intermediate files to save space.
    Preserves raw NIfTI files as per reproducibility requirements.
    Returns the amount of space freed (bytes).
    """
    space_freed = 0
    intermediate_dir = Path(src.config.INTERMEDIATE_DIR)
    
    if not intermediate_dir.exists():
        return 0

    # Find large intermediate files (excluding raw NIfTI)
    for file_path in intermediate_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Skip raw NIfTI files (reproducibility requirement)
        if file_path.suffix.lower() in ['.nii', '.nii.gz']:
            # Check if it's in a 'raw' subdirectory or named as raw
            if 'raw' in file_path.parts:
                continue
        
        # Compress large files (> 100MB)
        if file_path.stat().st_size > INTERMEDIATE_COMPRESSION_THRESHOLD:
            compressed_path = Path(str(file_path) + '.gz')
            try:
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                original_size = file_path.stat().st_size
                compressed_size = compressed_path.stat().st_size
                freed = original_size - compressed_size
                
                if freed > 0:
                    file_path.unlink()
                    space_freed += freed
                    logger.info(f"Compressed: {file_path.name} (saved {freed / (1024**2):.2f} MB)")
            except Exception as e:
                logger.error(f"Failed to compress {file_path}: {e}")
    
    return space_freed

def get_subject_list() -> List[str]:
    """
    Get list of subjects to process, excluding already processed ones.
    Uses quality check manifest to filter high-motion subjects.
    """
    # Load quality check results to get valid subjects
    try:
        valid_subjects, _ = run_quality_check()
    except Exception as e:
        logger.error(f"Failed to load quality check results: {e}")
        return []

    # Filter out already processed subjects
    processed = set(run_state.get("subjects_processed", []))
    remaining = [s for s in valid_subjects if s not in processed]
    
    logger.info(f"Found {len(remaining)} subjects to process (already processed: {len(processed)})")
    return remaining

def process_subject(subject_id: str) -> bool:
    """
    Process a single subject through the pipeline.
    Includes disk quota checks and checkpointing.
    Returns True if successful.
    """
    logger.info(f"Processing subject: {subject_id}")
    run_state["current_stage"] = f"processing_{subject_id}"
    
    try:
        # Simulate processing stages
        # In real implementation, this would call download, preprocess, analysis modules
        
        # Stage 1: Download (if not already downloaded)
        run_state["current_stage"] = f"download_{subject_id}"
        # download_subject(subject_id) # Placeholder for actual implementation
        
        # Check disk quota after download
        if check_disk_quota():
            logger.warning("Disk quota exceeded after download. Attempting compression...")
            freed = compress_intermediates()
            if freed == 0:
                logger.error("Could not free enough space. Stopping.")
                return False
        
        # Stage 2: Preprocess
        run_state["current_stage"] = f"preprocess_{subject_id}"
        # preprocess_subject(subject_id) # Placeholder for actual implementation
        
        # Stage 3: Analysis
        run_state["current_stage"] = f"analysis_{subject_id}"
        # analyze_subject(subject_id) # Placeholder for actual implementation
        
        # Mark as complete
        run_state["subjects_processed"].append(subject_id)
        save_checkpoint()
        
        logger.info(f"Successfully processed subject: {subject_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process subject {subject_id}: {e}")
        save_checkpoint()
        return False

def run_full_pipeline():
    """Execute the full pipeline with checkpointing and disk management."""
    logger.info("Starting full pipeline execution")
    run_state["start_time"] = time.time()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Try to resume from checkpoint
    if load_checkpoint():
        logger.info("Resuming from checkpoint")
    else:
        logger.info("Starting fresh run")
    
    # Get subjects to process
    subjects = get_subject_list()
    if not subjects:
        logger.info("No subjects to process. Exiting.")
        return True
    
    # Process each subject
    success_count = 0
    for subject in subjects:
        if check_disk_quota():
            logger.warning("Disk quota exceeded. Attempting to free space...")
            freed = compress_intermediates()
            if freed == 0:
                logger.error("Cannot free enough space. Aborting pipeline.")
                break
        
        if process_subject(subject):
            success_count += 1
        else:
            logger.error(f"Pipeline failed for subject {subject}. Stopping.")
            break
    
    # Final checkpoint
    run_state["current_stage"] = "completed"
    run_state["end_time"] = time.time()
    run_state["total_duration"] = run_state["end_time"] - run_state["start_time"]
    save_checkpoint()
    
    logger.info(f"Pipeline completed. Processed {success_count}/{len(subjects)} subjects.")
    return success_count == len(subjects)

def main():
    """Entry point for the pipeline."""
    logger.info("Initializing pipeline...")
    
    # Ensure directories exist
    Path(src.config.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(src.config.RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(src.config.INTERMEDIATE_DIR).mkdir(parents=True, exist_ok=True)
    
    # Run the pipeline
    success = run_full_pipeline()
    
    if success:
        logger.info("Pipeline finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline finished with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()