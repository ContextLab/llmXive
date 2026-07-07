"""
Main orchestration script for the Sensory Deprivation Network Dynamics pipeline.

Implements checkpointing logic to save state at each subject completion and
supports resumption from the last completed stage on timeout, disk overflow,
or interruption.

This script coordinates:
1. Data download (T011)
2. Quality Check (T006)
3. Preprocessing (T012)
4. Connectivity & Metrics (T018-T020)
5. Statistical Analysis (T026-T028)
"""
import os
import sys
import json
import logging
import signal
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import project configuration and utilities
import src.config as config
from src.data.quality_check import run_quality_check, save_manifest
from src.utils.atlas import get_atlas_path
from src.data.download import download_dataset
from src.data.preprocess import preprocess_subject
from src.analysis.connectivity import compute_connectivity_matrix
from src.analysis.metrics import compute_network_metrics
from src.analysis.aggregate import aggregate_metrics
from src.analysis.stats import run_statistical_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_PATH / 'pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global state for checkpointing
CHECKPOINT_FILE = config.RESULTS_PATH / 'pipeline_checkpoint.json'
CHECKPOINT_INTERVAL_SECONDS = 300  # Force checkpoint every 5 mins if running long

# State tracking
pipeline_state = {
    "start_time": None,
    "last_checkpoint": None,
    "subjects_completed": [],
    "subjects_failed": [],
    "current_stage": None,
    "current_subject": None,
    "config_snapshot": {}
}

def signal_handler(signum, frame):
    """Handle timeout/interrupt signals by saving checkpoint and exiting gracefully."""
    logger.warning(f"Received signal {signum}. Saving checkpoint and exiting...")
    save_checkpoint()
    sys.exit(1)

def save_checkpoint():
    """Save current pipeline state to disk for resumption."""
    pipeline_state["last_checkpoint"] = datetime.now().isoformat()
    pipeline_state["config_snapshot"] = {
        "dataset_ids": config.DATASET_IDS,
        "fd_threshold": config.FD_THRESHOLD,
        "min_sample_size": config.MIN_SAMPLE_SIZE
    }
    
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(pipeline_state, f, indent=2)
        logger.info(f"Checkpoint saved: {pipeline_state['current_subject']} completed.")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        raise

def load_checkpoint() -> Dict[str, Any]:
    """Load previous checkpoint if exists, returns empty state if not."""
    if not CHECKPOINT_FILE.exists():
        return {}
    
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load checkpoint: {e}")
        return {}

def check_disk_quota():
    """Check if disk usage is within limits. Raises error if exceeded."""
    if not config.DISK_QUOTA_MB:
        return
    
    total_size = 0
    for path in config.DATA_PATH.glob('**/*'):
        if path.is_file():
            total_size += path.stat().st_size
    
    total_mb = total_size / (1024 * 1024)
    if total_mb > config.DISK_QUOTA_MB:
        logger.error(f"Disk quota exceeded: {total_mb:.2f}MB > {config.DISK_QUOTA_MB}MB")
        raise RuntimeError("Disk quota exceeded. Please free space and resume.")

def get_subject_list() -> List[str]:
    """Get list of subjects to process, filtering out already completed ones."""
    checkpoint = load_checkpoint()
    completed = set(checkpoint.get("subjects_completed", []))
    
    # In a real implementation, this would scan the dataset for subjects
    # For now, we simulate based on config or download manifest
    # Placeholder: In real code, this would come from download.py manifest
    all_subjects = config.SAMPLE_SUBJECT_IDS or []
    
    return [s for s in all_subjects if s not in completed]

def process_subject(subject_id: str):
    """Process a single subject through the full pipeline."""
    logger.info(f"Processing subject: {subject_id}")
    pipeline_state["current_subject"] = subject_id
    pipeline_state["current_stage"] = "download"
    
    try:
        # 1. Download (if not already present)
        logger.info(f"Step 1: Downloading data for {subject_id}")
        # download_dataset(subject_id) # Uncomment when T011 is integrated
        
        # 2. Quality Check
        pipeline_state["current_stage"] = "quality_check"
        logger.info(f"Step 2: Running quality check for {subject_id}")
        # run_quality_check(subject_id) # Uncomment when T006 is fully integrated
        
        # 3. Preprocessing
        pipeline_state["current_stage"] = "preprocess"
        logger.info(f"Step 3: Preprocessing {subject_id}")
        # preprocess_subject(subject_id) # Uncomment when T012 is integrated
        
        # 4. Connectivity
        pipeline_state["current_stage"] = "connectivity"
        logger.info(f"Step 4: Computing connectivity for {subject_id}")
        # compute_connectivity_matrix(subject_id) # Uncomment when T018 is integrated
        
        # 5. Metrics
        pipeline_state["current_stage"] = "metrics"
        logger.info(f"Step 5: Computing network metrics for {subject_id}")
        # compute_network_metrics(subject_id) # Uncomment when T019/020 is integrated
        
        # Mark as completed
        pipeline_state["subjects_completed"].append(subject_id)
        save_checkpoint()
        
    except Exception as e:
        logger.error(f"Failed to process {subject_id}: {e}")
        pipeline_state["subjects_failed"].append({"id": subject_id, "error": str(e)})
        save_checkpoint()
        raise

def run_full_pipeline():
    """Execute the full pipeline with checkpointing."""
    logger.info("Starting Sensory Deprivation Network Dynamics Pipeline")
    pipeline_state["start_time"] = datetime.now().isoformat()
    
    # Setup signal handlers for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Check disk quota before starting
        check_disk_quota()
        
        # Get subjects to process
        subjects = get_subject_list()
        if not subjects:
            logger.info("No subjects to process. Pipeline complete.")
            return
        
        logger.info(f"Processing {len(subjects)} subjects...")
        
        for subject_id in subjects:
            check_disk_quota() # Check before each subject
            process_subject(subject_id)
            
            # Periodic checkpoint
            if len(pipeline_state["subjects_completed"]) % 5 == 0:
                save_checkpoint()
        
        # Final aggregation
        logger.info("Running final aggregation...")
        pipeline_state["current_stage"] = "aggregation"
        aggregate_metrics()
        run_statistical_analysis()
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        save_checkpoint()
        raise
    finally:
        pipeline_state["end_time"] = datetime.now().isoformat()
        save_checkpoint()

def main():
    """Entry point."""
    run_full_pipeline()

if __name__ == "__main__":
    main()