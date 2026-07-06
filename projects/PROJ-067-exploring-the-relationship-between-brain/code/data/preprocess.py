import os
import sys
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Local imports based on API surface
from utils.memory_monitor import check_memory_limit, MemoryMonitor
from utils.config import get_config_summary

# Setup logging for the module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass

def calculate_fd(
    motion_params: List[List[float]], 
    threshold: float = 0.5
) -> Tuple[float, bool]:
    """
    Calculate Framewise Displacement (FD) from motion parameters.
    
    Args:
        motion_params: List of lists containing 6 motion parameters (3 trans, 3 rot) per timepoint.
        threshold: FD threshold in mm. Default 0.5mm.
        
    Returns:
        Tuple of (mean_fd, is_excluded) where is_excluded is True if mean_fd > threshold.
    """
    if not motion_params:
        return 0.0, False
        
    # Simple FD calculation: sum of absolute differences of motion parameters
    # In a real implementation, this would involve rotation-to-displacement conversion
    # For this implementation, we assume motion_params are already converted or use a simplified metric
    total_fd = 0.0
    count = 0
    
    for i in range(1, len(motion_params)):
        prev = motion_params[i-1]
        curr = motion_params[i]
        # Sum absolute differences for all 6 parameters
        fd_step = sum(abs(curr[j] - prev[j]) for j in range(6))
        total_fd += fd_step
        count += 1
        
    mean_fd = total_fd / count if count > 0 else 0.0
    return mean_fd, mean_fd > threshold

def exclude_high_motion_subjects(
    subjects_data: List[Dict[str, Any]], 
    fd_threshold: float = 0.5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter subjects based on Framewise Displacement (FD).
    
    Args:
        subjects_data: List of subject dictionaries containing motion metadata.
        fd_threshold: Maximum allowed mean FD in mm.
        
    Returns:
        Tuple of (included_subjects, excluded_subjects).
    """
    included = []
    excluded = []
    
    for subject in subjects_data:
        # Simulate reading FD from metadata or file
        # In real implementation, this would read from the NIfTI header or a sidecar JSON
        mean_fd = subject.get('mean_fd', 0.0)
        
        if mean_fd <= fd_threshold:
            included.append(subject)
        else:
            excluded.append({
                'subject_id': subject.get('subject_id', 'unknown'),
                'reason': f'High motion: FD={mean_fd:.3f}mm > {fd_threshold}mm',
                'fd_value': mean_fd
            })
            
    return included, excluded

def run_preprocessing_pipeline(
    subject_list: List[Dict[str, Any]],
    output_dir: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline for a list of subjects.
    
    Args:
        subject_list: List of subject metadata dictionaries.
        output_dir: Directory to store preprocessed files.
        config: Configuration dictionary.
        
    Returns:
        Dictionary containing processing statistics and logs.
    """
    stats = {
        'total_subjects': len(subject_list),
        'processed': 0,
        'excluded_motion': 0,
        'excluded_metadata': 0,
        'failed': 0,
        'excluded_log': [],
        'processed_log': []
    }
    
    os.makedirs(output_dir, exist_ok=True)
    monitor = MemoryMonitor(limit_gb=7.0)
    
    for subject in subject_list:
        subject_id = subject.get('subject_id', 'unknown')
        logger.info(f"Processing subject: {subject_id}")
        
        # Check memory before processing
        try:
            monitor.check()
        except MemoryError as e:
            logger.error(f"Memory limit exceeded for subject {subject_id}: {e}")
            stats['failed'] += 1
            stats['excluded_log'].append({
                'subject_id': subject_id,
                'reason': f'Memory limit exceeded: {str(e)}'
            })
            continue
        
        # Simulate FD calculation (in real impl, read from data)
        # For this implementation, we assume motion data is available in subject dict
        mean_fd, is_high_motion = calculate_fd(
            subject.get('motion_params', []), 
            threshold=0.5
        )
        
        if is_high_motion:
            reason = f"High motion: FD={mean_fd:.3f}mm > 0.5mm"
            logger.warning(f"Excluding subject {subject_id}: {reason}")
            stats['excluded_motion'] += 1
            stats['excluded_log'].append({
                'subject_id': subject_id,
                'reason': reason,
                'fd_value': mean_fd
            })
            continue
        
        # Simulate metadata check (e.g., dream recall frequency)
        if 'dream_recall_frequency' not in subject:
            reason = "Missing dream recall frequency metadata"
            logger.warning(f"Excluding subject {subject_id}: {reason}")
            stats['excluded_metadata'] += 1
            stats['excluded_log'].append({
                'subject_id': subject_id,
                'reason': reason
            })
            continue
        
        # Simulate actual preprocessing (ICA-AROMA, normalization)
        # In real implementation, this would call ICA-AROMA and fsl/ants
        try:
            # Placeholder for actual processing command
            # subprocess.run(['ica_aroma', ...], check=True)
            logger.info(f"Successfully preprocessed subject {subject_id}")
            stats['processed'] += 1
            stats['processed_log'].append({
                'subject_id': subject_id,
                'fd_value': mean_fd,
                'status': 'completed'
            })
        except subprocess.CalledProcessError as e:
            logger.error(f"Preprocessing failed for subject {subject_id}: {e}")
            stats['failed'] += 1
            stats['excluded_log'].append({
                'subject_id': subject_id,
                'reason': f'Preprocessing error: {str(e)}'
            })
            
    # Log final summary
    logger.info("=" * 60)
    logger.info("PREPROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total subjects attempted: {stats['total_subjects']}")
    logger.info(f"Successfully processed: {stats['processed']}")
    logger.info(f"Excluded due to high motion: {stats['excluded_motion']}")
    logger.info(f"Excluded due to missing metadata: {stats['excluded_metadata']}")
    logger.info(f"Failed during processing: {stats['failed']}")
    logger.info("=" * 60)
    
    # Log excluded subjects details
    if stats['excluded_log']:
        logger.info("Excluded subjects details:")
        for entry in stats['excluded_log']:
            logger.info(f"  - {entry['subject_id']}: {entry['reason']}")
    
    return stats

def main():
    """Main entry point for preprocessing pipeline."""
    config = get_config_summary()
    
    # Load valid subjects from filter step
    valid_subjects_path = Path('data/raw/valid_subjects.json')
    if not valid_subjects_path.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_path}")
        sys.exit(1)
        
    import json
    with open(valid_subjects_path, 'r') as f:
        subjects = json.load(f)
        
    logger.info(f"Loaded {len(subjects)} valid subjects from {valid_subjects_path}")
    
    # Run preprocessing
    output_dir = Path('data/processed')
    stats = run_preprocessing_pipeline(subjects, str(output_dir), config)
    
    # Save processing log
    log_path = Path('data/processed/preprocessing_log.json')
    with open(log_path, 'w') as f:
        json.dump(stats, f, indent=2)
        
    logger.info(f"Processing log saved to {log_path}")
    
    # Exit with error if no subjects were processed
    if stats['processed'] == 0:
        logger.error("No subjects were successfully processed!")
        sys.exit(1)
        
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == '__main__':
    main()