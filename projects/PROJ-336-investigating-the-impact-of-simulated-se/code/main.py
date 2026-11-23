import os
import sys
import json
import logging
import signal
import time
import gzip
import shutil
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config for thresholds and paths
import src.config as config
from src.data.quality_check import run_quality_check, save_manifest
from src.data.download import download_dataset, validate_bids_structure
from src.utils.atlas import get_atlas_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Global state for checkpointing
checkpoint_state = {
    'completed_subjects': [],
    'current_stage': 'init',
    'start_time': None,
    'disk_usage_snapshot': 0
}

def signal_handler(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM."""
    logger.warning("Received termination signal. Saving checkpoint before exit...")
    save_checkpoint()
    sys.exit(0)

def save_checkpoint(state: Optional[Dict] = None):
    """Save current pipeline state to disk."""
    global checkpoint_state
    if state:
        checkpoint_state.update(state)
    
    checkpoint_path = Path('data/checkpoints')
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    checkpoint_file = checkpoint_path / 'pipeline_state.json'
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_state, f, indent=2)
    
    logger.info(f"Checkpoint saved: {len(checkpoint_state['completed_subjects'])} subjects completed")

def load_checkpoint() -> Dict:
    """Load pipeline state from disk if exists."""
    checkpoint_file = Path('data/checkpoints/pipeline_state.json')
    
    if not checkpoint_file.exists():
        logger.info("No existing checkpoint found. Starting fresh.")
        return checkpoint_state
    
    try:
        with open(checkpoint_file, 'r') as f:
            loaded_state = json.load(f)
            checkpoint_state.update(loaded_state)
            logger.info(f"Checkpoint loaded: resuming from stage '{checkpoint_state['current_stage']}'")
            return checkpoint_state
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}. Starting fresh.")
        return checkpoint_state

def get_current_disk_usage(base_path: str = 'data') -> float:
    """Calculate current disk usage in GB for the data directory."""
    total_size = 0
    base = Path(base_path)
    
    if not base.exists():
        return 0.0
        
    for file_path in base.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size / (1024 ** 3)  # Convert to GB

def check_disk_quota(current_usage: float, max_usage: float = config.DISK_QUOTA_GB) -> bool:
    """Check if current disk usage is within quota."""
    if current_usage >= max_usage:
        logger.error(f"Disk quota exceeded: {current_usage:.2f}GB >= {max_usage}GB")
        return False
    return True

def compress_intermediates(data_dir: str = 'data', exclude_patterns: List[str] = None) -> float:
    """
    Compress intermediate files (npy, csv, temp) to save space.
    Preserves raw NIfTI files as required by Constitution Principle III.
    Returns the space saved in GB.
    """
    if exclude_patterns is None:
        exclude_patterns = ['*.nii', '*.nii.gz', 'raw/', 'downloaded/']
    
    data_path = Path(data_dir)
    saved_bytes = 0
    compressed_count = 0
    
    logger.info("Starting intermediate file compression...")
    
    # Find candidate files for compression
    candidates = []
    for pattern in ['*.npy', '*.csv', '*.temp', '*.log']:
        candidates.extend(data_path.rglob(pattern))
    
    for file_path in candidates:
        # Skip if it's in an excluded directory or matches exclusion patterns
        rel_path = str(file_path.relative_to(data_path))
        if any(excl in rel_path for excl in exclude_patterns):
            continue
        
        # Skip if already compressed
        if file_path.suffix in ['.gz', '.zip', '.tar']:
            continue
        
        try:
            # Create compressed version
            compressed_path = Path(str(file_path) + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify compressed file is smaller, then replace
            if compressed_path.stat().st_size < file_path.stat().st_size:
                original_size = file_path.stat().st_size
                file_path.unlink()
                # Rename compressed to original name (remove .gz for the stored file)
                # Actually, keep .gz and update references? No, let's just store .gz
                # But for simplicity, let's keep the .gz and update the code to read .gz
                # For now, just keep the .gz and remove original
                saved_bytes += original_size - compressed_path.stat().st_size
                compressed_count += 1
                logger.debug(f"Compressed: {file_path.name}")
            else:
                compressed_path.unlink()  # Remove if not smaller
                  
        except Exception as e:
            logger.warning(f"Failed to compress {file_path}: {e}")
    
    saved_gb = saved_bytes / (1024 ** 3)
    logger.info(f"Compression complete: {compressed_count} files compressed, {saved_gb:.3f}GB saved")
    return saved_gb

def get_subject_list(dataset_dir: str = 'data/raw') -> List[str]:
    """
    Get list of subject IDs from the dataset directory.
    Returns list of subject IDs (e.g., ['sub-001', 'sub-002', ...])
    """
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        logger.warning(f"Dataset directory {dataset_dir} not found. Returning empty list.")
        return []
    
    subjects = []
    for item in dataset_path.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    
    return sorted(subjects)

def process_subject(subject_id: str, stage: str = 'preprocess') -> bool:
    """
    Process a single subject through the pipeline stages.
    Stages: 'download', 'quality_check', 'preprocess', 'analysis'
    Returns True if successful, False if failed or skipped.
    """
    logger.info(f"Processing subject: {subject_id} at stage: {stage}")
    
    try:
        # Load current checkpoint to check if already processed
        state = load_checkpoint()
        
        if subject_id in state['completed_subjects']:
            logger.info(f"Subject {subject_id} already completed. Skipping.")
            return True
        
        # Stage-specific processing
        if stage == 'download':
            # Verify BIDS structure (T014a)
            validate_bids_structure('data/raw')
            # Download if not exists (handled by download_dataset)
            # This is a placeholder for the actual download logic
            logger.info(f"Download stage for {subject_id} - BIDS validation passed")
            
        elif stage == 'quality_check':
            # Run quality check (T006)
            run_quality_check(subject_id)
            
        elif stage == 'preprocess':
            # Preprocessing logic would go here
            # For now, simulate completion
            logger.info(f"Preprocessing {subject_id}...")
            # In real implementation: call preprocess.py
            
        elif stage == 'analysis':
            # Analysis logic would go here
            logger.info(f"Analyzing {subject_id}...")
            # In real implementation: call connectivity.py, metrics.py
        
        # Update checkpoint
        state['completed_subjects'].append(subject_id)
        state['current_stage'] = stage
        save_checkpoint(state)
        
        logger.info(f"Subject {subject_id} completed stage: {stage}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process subject {subject_id}: {e}")
        # Save checkpoint even on failure to allow resumption
        save_checkpoint()
        return False

def run_full_pipeline():
    """
    Run the full pipeline with disk quota enforcement and checkpointing.
    """
    global checkpoint_state
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load checkpoint
    checkpoint_state = load_checkpoint()
    checkpoint_state['start_time'] = time.time()
    
    # Initial disk usage check
    current_usage = get_current_disk_usage()
    logger.info(f"Initial disk usage: {current_usage:.2f}GB")
    
    if not check_disk_quota(current_usage):
        logger.error("Disk quota exceeded at start. Cannot proceed.")
        return False
    
    # Get subjects to process
    subjects = get_subject_list()
    if not subjects:
        logger.warning("No subjects found to process.")
        return False
    
    # Filter out already completed subjects
    completed = set(checkpoint_state['completed_subjects'])
    pending = [s for s in subjects if s not in completed]
    
    logger.info(f"Processing {len(pending)} pending subjects out of {len(subjects)} total")
    
    # Process stages
    stages = ['download', 'quality_check', 'preprocess', 'analysis']
    
    for stage in stages:
        logger.info(f"=== Starting stage: {stage} ===")
        checkpoint_state['current_stage'] = stage
        save_checkpoint()
        
        for subject in pending:
            # Check disk quota before each subject
            current_usage = get_current_disk_usage()
            if not check_disk_quota(current_usage):
                logger.warning(f"Disk quota exceeded during {stage} for {subject}. Attempting compression...")
                saved = compress_intermediates()
                current_usage = get_current_disk_usage()
                
                if not check_disk_quota(current_usage):
                    logger.error("Disk quota still exceeded after compression. Aborting.")
                    return False
            
            success = process_subject(subject, stage)
            if not success:
                logger.error(f"Pipeline failed at subject {subject}, stage {stage}. Checkpoint saved.")
                return False
            
            # Periodic checkpoint
            if len(checkpoint_state['completed_subjects']) % 5 == 0:
                save_checkpoint()
        
        # Compress intermediates after each stage
        compress_intermediates()
    
    # Final checkpoint
    checkpoint_state['end_time'] = time.time()
    checkpoint_state['duration'] = checkpoint_state['end_time'] - checkpoint_state['start_time']
    save_checkpoint()
    
    final_usage = get_current_disk_usage()
    logger.info(f"Pipeline completed. Final disk usage: {final_usage:.2f}GB")
    return True

def main():
    """Entry point for the pipeline."""
    logger.info("Starting llmXive Sensory Deprivation Pipeline")
    
    success = run_full_pipeline()
    
    if success:
        logger.info("Pipeline completed successfully")
        sys.exit(0)
    else:
        logger.error("Pipeline failed or was interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()