import os
import sys
import json
import logging
import signal
import time
import shutil
import gzip
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import configuration and utilities from existing project structure
import src.config
from src.data.quality_check import run_quality_check, save_manifest
from src.utils.atlas import get_atlas_path
from src.data.download import download_dataset
from src.data.preprocess import preprocess_subject
from src.analysis.connectivity import compute_connectivity
from src.analysis.metrics import compute_network_metrics
from src.analysis.aggregate import aggregate_metrics
from src.analysis.stats import run_statistical_analysis
from src.viz.plot_networks import generate_network_plots
from src.viz.plot_metrics import generate_metric_plots

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global state for checkpointing
checkpoint_file = Path('data/checkpoints/pipeline_state.json')
interrupt_flag = False

def signal_handler(signum, frame):
    """Handle interruption signals gracefully."""
    global interrupt_flag
    logger.warning(f"Received signal {signum}. Initiating graceful shutdown...")
    interrupt_flag = True

def save_checkpoint(state: Dict[str, Any], checkpoint_path: Optional[Path] = None):
    """Save the current pipeline state to a JSON file."""
    if checkpoint_path is None:
        checkpoint_path = checkpoint_file
    
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checkpoint_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Checkpoint saved to {checkpoint_path}")

def load_checkpoint(checkpoint_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the last saved pipeline state, if it exists."""
    if checkpoint_path is None:
        checkpoint_path = checkpoint_file
    
    if not checkpoint_path.exists():
        logger.info("No existing checkpoint found.")
        return None
    
    try:
        with open(checkpoint_path, 'r') as f:
            state = json.load(f)
        logger.info(f"Loaded checkpoint from {checkpoint_path}")
        return state
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return None

def get_current_disk_usage(base_path: Optional[Path] = None) -> float:
    """Get current disk usage in GB for the project data directory."""
    if base_path is None:
        base_path = Path('data')
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(base_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except FileNotFoundError:
                continue
    
    return total_size / (1024 ** 3)  # Convert to GB

def check_disk_quota(usage_gb: float, max_gb: float = 100.0) -> bool:
    """Check if current disk usage is within quota."""
    if usage_gb >= max_gb:
        logger.error(f"Disk quota exceeded: {usage_gb:.2f}GB >= {max_gb}GB")
        return False
    return True

def compress_intermediates(data_dir: Path, preserve_raw: bool = True):
    """
    Compress intermediate files to save disk space while preserving raw data.
    
    Args:
        data_dir: Base data directory
        preserve_raw: If True, never compress raw NIfTI files
    """
    logger.info("Starting compression of intermediate files...")
    
    # Define patterns for files to compress (excluding raw data)
    compress_patterns = [
        'processed/',
        'intermediate/',
        'temp/',
        '*.nii.gz'  # Compress already gzipped files if they are not raw
    ]
    
    raw_extensions = ['.nii', '.nii.gz']
    raw_dirs = ['raw', 'downloads', 'bids']
    
    compressed_count = 0
    
    for root, dirs, files in os.walk(data_dir):
        # Skip raw data directories if preserve_raw is True
        if preserve_raw:
            if any(raw_dir in Path(root).parts for raw_dir in raw_dirs):
                continue
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip if already compressed or if it's raw data
            if file.endswith('.tar.gz') or file.endswith('.zip'):
                continue
            
            if preserve_raw and any(file.endswith(ext) for ext in raw_extensions):
                # Check if this is in a raw data directory
                if any(raw_dir in file_path.parts for raw_dir in raw_dirs):
                    continue
            
            try:
                # Create compressed version
                compressed_path = str(file_path) + '.gz'
                
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original if compression successful
                file_path.unlink()
                compressed_count += 1
                logger.debug(f"Compressed: {file_path} -> {compressed_path}")
                
            except Exception as e:
                logger.warning(f"Failed to compress {file_path}: {e}")
    
    logger.info(f"Compression complete. Compressed {compressed_count} files.")

def get_subject_list(state: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get list of subjects to process, optionally resuming from checkpoint."""
    if state and 'subjects_processed' in state:
        # Resume from checkpoint
        processed = set(state['subjects_processed'])
        all_subjects = state.get('all_subjects', [])
        return [s for s in all_subjects if s not in processed]
    
    # Default: get subjects from data directory or config
    # This would typically scan the BIDS dataset
    # For now, return an empty list or read from config
    return src.config.get_subject_list()

def process_subject(subject_id: str, state: Dict[str, Any]) -> bool:
    """
    Process a single subject through the full pipeline.
    
    Args:
        subject_id: Subject identifier
        state: Current pipeline state
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing subject: {subject_id}")
    
    try:
        # Step 1: Download (if not already done)
        # This is handled by the main pipeline flow
        
        # Step 2: Quality Check
        # Quality check is typically run once for all subjects
        
        # Step 3: Preprocess
        preprocess_output = preprocess_subject(subject_id)
        if not preprocess_output:
            logger.error(f"Preprocessing failed for {subject_id}")
            return False
        
        # Step 4: Compute Connectivity
        connectivity_matrix = compute_connectivity(subject_id)
        if connectivity_matrix is None:
            logger.error(f"Connectivity computation failed for {subject_id}")
            return False
        
        # Step 5: Compute Network Metrics
        metrics = compute_network_metrics(subject_id, connectivity_matrix)
        if metrics is None:
            logger.error(f"Network metrics computation failed for {subject_id}")
            return False
        
        # Step 6: Save intermediate results
        results_dir = Path('results') / 'intermediate' / subject_id
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        metrics_path = results_dir / 'metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save connectivity matrix
        import numpy as np
        conn_path = results_dir / 'connectivity.npy'
        np.save(conn_path, connectivity_matrix)
        
        logger.info(f"Successfully processed subject {subject_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}", exc_info=True)
        return False

def run_full_pipeline():
    """Run the full analysis pipeline with checkpointing and disk quota enforcement."""
    global interrupt_flag
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting full pipeline execution...")
    
    # Load or initialize state
    state = load_checkpoint()
    if state is None:
        state = {
            'start_time': time.time(),
            'subjects_processed': [],
            'all_subjects': get_subject_list(),
            'stage': 'initialization',
            'errors': []
        }
        
        # Initial setup
        logger.info("Initializing pipeline...")
        
        # Ensure directories exist
        Path('logs').mkdir(exist_ok=True)
        Path('data/checkpoints').mkdir(parents=True, exist_ok=True)
        Path('results/intermediate').mkdir(parents=True, exist_ok=True)
        
        # Download datasets if needed
        if not state['all_subjects']:
            logger.info("Fetching subject list from datasets...")
            try:
                # Attempt to download and get subject list
                download_dataset(src.config.DATASET_IDS[0])
                state['all_subjects'] = get_subject_list()
            except Exception as e:
                logger.error(f"Failed to initialize dataset: {e}")
                state['errors'].append(str(e))
                save_checkpoint(state)
                return False
        
        # Run quality check once
        logger.info("Running quality check...")
        try:
            run_quality_check()
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            state['errors'].append(f"Quality check: {str(e)}")
            save_checkpoint(state)
            return False
    
    # Process subjects
    subjects = get_subject_list(state)
    logger.info(f"Processing {len(subjects)} subjects...")
    
    for subject_id in subjects:
        if interrupt_flag:
            logger.warning("Interrupt flag set. Saving checkpoint and exiting.")
            state['stage'] = 'interrupted'
            save_checkpoint(state)
            return False
        
        # Check disk quota before processing
        current_usage = get_current_disk_usage()
        if not check_disk_quota(current_usage, src.config.DISK_QUOTA_GB):
            logger.error("Disk quota exceeded. Attempting to compress intermediates...")
            compress_intermediates(Path('data'), preserve_raw=True)
            current_usage = get_current_disk_usage()
            if not check_disk_quota(current_usage, src.config.DISK_QUOTA_GB):
                logger.error("Still over quota after compression. Aborting.")
                state['stage'] = 'disk_quota_exceeded'
                save_checkpoint(state)
                return False
        
        # Process subject
        success = process_subject(subject_id, state)
        
        if success:
            state['subjects_processed'].append(subject_id)
            state['stage'] = f'processing_{subject_id}'
            save_checkpoint(state)
        else:
            state['errors'].append(f"Failed to process {subject_id}")
            # Continue with next subject or abort based on config
            if src.config.ABORT_ON_ERROR:
                logger.error("Aborting due to error.")
                save_checkpoint(state)
                return False
    
    # Final aggregation and analysis
    logger.info("Running final aggregation and statistical analysis...")
    try:
        aggregate_metrics()
        run_statistical_analysis()
        generate_network_plots()
        generate_metric_plots()
        
        state['stage'] = 'completed'
        state['end_time'] = time.time()
        state['duration'] = state['end_time'] - state['start_time']
        
        # Compress intermediates at the end
        logger.info("Compressing intermediate files...")
        compress_intermediates(Path('data'), preserve_raw=True)
        
    except Exception as e:
        logger.error(f"Final analysis failed: {e}")
        state['errors'].append(f"Final analysis: {str(e)}")
        state['stage'] = 'final_analysis_failed'
    
    save_checkpoint(state)
    logger.info("Pipeline execution complete.")
    return len(state['errors']) == 0

def main():
    """Entry point for the pipeline."""
    logger.info("llmXive Sensory Deprivation Pipeline v1.0")
    logger.info(f"Disk quota: {src.config.DISK_QUOTA_GB}GB")
    logger.info(f"Dataset IDs: {src.config.DATASET_IDS}")
    
    success = run_full_pipeline()
    
    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline completed with errors.")
        sys.exit(1)

if __name__ == '__main__':
    main()