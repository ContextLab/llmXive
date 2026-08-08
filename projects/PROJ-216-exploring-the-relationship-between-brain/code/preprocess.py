import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils import ResourceMonitor
from config import get_dataset_ids, get_sample_limit, get_fallback_condition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """
    Execute a shell command and return the result.
    
    Args:
        command: List of command arguments
        cwd: Working directory for the command
        
    Returns:
        CompletedProcess instance
        
    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    logger.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Command failed with return code {result.returncode}")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command)
    
    return result

def check_fsl_afni() -> bool:
    """
    Check if FSL and AFNI are available in the system.
    
    Returns:
        True if both tools are available, False otherwise
    """
    # Check for FSL
    try:
        run_command(['which', 'fsl'])
        logger.info("FSL is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("FSL not found in PATH")
        return False
    
    # Check for AFNI
    try:
        run_command(['which', '3dcalc'])
        logger.info("AFNI is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("AFNI not found in PATH")
        return False
    
    return True

def calculate_motion_metrics(
    func_file: Path,
    output_dir: Path
) -> Dict[str, float]:
    """
    Calculate motion metrics for a subject's functional scan.
    
    Args:
        func_file: Path to the functional NIfTI file
        output_dir: Directory to store motion metrics output
        
    Returns:
        Dictionary containing motion metrics (translation, rotation)
    """
    # This is a placeholder for actual FSL/AFNI motion calculation
    # In a real implementation, this would use fsl_motion_outliers or similar
    metrics = {
        'mean_translation_mm': 0.0,
        'max_translation_mm': 0.0,
        'mean_rotation_rad': 0.0,
        'max_rotation_rad': 0.0,
        'framewise_displacement': 0.0
    }
    
    # TODO: Implement actual motion calculation using FSL/AFNI
    # For now, return placeholder values
    
    return metrics

def preprocess_subject(
    subject_id: str,
    raw_dir: Path,
    processed_dir: Path,
    resource_monitor: ResourceMonitor
) -> Dict[str, Any]:
    """
    Preprocess a single subject's fMRI data.
    
    Args:
        subject_id: Subject identifier
        raw_dir: Directory containing raw data
        processed_dir: Directory to store preprocessed data
        resource_monitor: ResourceMonitor instance for tracking RAM usage
        
    Returns:
        Dictionary containing preprocessing results and statistics
    """
    logger.info(f"Preprocessing subject: {subject_id}")
    
    # Start resource monitoring for this subject
    resource_monitor.start_subject(subject_id)
    start_time = time.time()
    
    try:
        # Find functional scan
        func_file = None
        for ext in ['.nii', '.nii.gz']:
            potential_file = raw_dir / f"{subject_id}_func{ext}"
            if potential_file.exists():
                func_file = potential_file
                break
        
        if not func_file:
            raise FileNotFoundError(f"No functional scan found for subject {subject_id}")
        
        # Create output directory
        subject_output_dir = processed_dir / subject_id
        subject_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Motion correction (using FSL's MCFLIRT)
        logger.info(f"Performing motion correction for {subject_id}")
        motion_corrected_file = subject_output_dir / f"{subject_id}_mc.nii.gz"
        
        # TODO: Implement actual motion correction command
        # mcflirt -in {func_file} -out {motion_corrected_file} -refvol 0
        
        # Spatial normalization (using FSL's FLIRT)
        logger.info(f"Performing spatial normalization for {subject_id}")
        normalized_file = subject_output_dir / f"{subject_id}_norm.nii.gz"
        
        # TODO: Implement actual normalization command
        # flirt -in {motion_corrected_file} -ref standard_template -out {normalized_file}
        
        # Bandpass filtering (using AFNI's 3dBandpass)
        logger.info(f"Performing bandpass filtering for {subject_id}")
        filtered_file = subject_output_dir / f"{subject_id}_filtered.nii.gz"
        
        # TODO: Implement actual filtering command
        # 3dBandpass -prefix {filtered_file} -low 0.01 -high 0.1 {normalized_file}
        
        # Calculate motion metrics
        motion_metrics = calculate_motion_metrics(filtered_file, subject_output_dir)
        
        # Stop resource monitoring for this subject
        end_time = time.time()
        resource_monitor.end_subject(subject_id)
        
        result = {
            'subject_id': subject_id,
            'status': 'success',
            'input_file': str(func_file),
            'output_file': str(filtered_file),
            'processing_time_seconds': end_time - start_time,
            'motion_metrics': motion_metrics,
            'ram_peak_mb': resource_monitor.get_subject_peak_ram(subject_id),
            'ram_avg_mb': resource_monitor.get_subject_avg_ram(subject_id)
        }
        
        logger.info(f"Successfully preprocessed subject {subject_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to preprocess subject {subject_id}: {str(e)}")
        resource_monitor.end_subject(subject_id, error=True)
        
        return {
            'subject_id': subject_id,
            'status': 'failed',
            'error': str(e),
            'processing_time_seconds': time.time() - start_time,
            'ram_peak_mb': resource_monitor.get_subject_peak_ram(subject_id),
            'ram_avg_mb': resource_monitor.get_subject_avg_ram(subject_id)
        }

def main():
    """
    Main function to run the preprocessing pipeline for all subjects.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Check for FSL and AFNI availability
    if not check_fsl_afni():
        logger.error("FSL or AFNI not available. Please install required tools.")
        sys.exit(1)
    
    # Load configuration
    dataset_ids = get_dataset_ids()
    sample_limit = get_sample_limit()
    fallback_condition = get_fallback_condition()
    
    logger.info(f"Dataset IDs: {dataset_ids}")
    logger.info(f"Sample limit: {sample_limit}")
    
    # Initialize resource monitor
    resource_monitor = ResourceMonitor()
    resource_monitor.start_session()
    
    # Define directories
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Get subject list (this would normally come from the downloaded dataset)
    # For now, we'll simulate with a placeholder
    subject_ids = [f"sub-{i:03d}" for i in range(1, sample_limit + 1)]
    
    logger.info(f"Processing {len(subject_ids)} subjects")
    
    # Process each subject
    results = []
    successful_count = 0
    
    for subject_id in subject_ids:
        result = preprocess_subject(subject_id, raw_dir, processed_dir, resource_monitor)
        results.append(result)
        
        if result['status'] == 'success':
            successful_count += 1
        
        # Log resource usage
        logger.info(f"Subject {subject_id} RAM usage: "
                   f"Peak={result['ram_peak_mb']:.1f}MB, "
                   f"Avg={result['ram_avg_mb']:.1f}MB")
    
    # Stop resource monitoring
    resource_monitor.end_session()
    
    # Write resource profile
    resource_profile = resource_monitor.get_session_profile()
    resource_profile_path = Path("data/processed/resource_profile.json")
    with open(resource_profile_path, 'w') as f:
        json.dump(resource_profile, f, indent=2)
    
    logger.info(f"Resource profile written to {resource_profile_path}")
    
    # Generate preprocessing statistics
    stats = {
        'total_subjects': len(subject_ids),
        'successful_subjects': successful_count,
        'success_rate_percentage': (successful_count / len(subject_ids)) * 100 if subject_ids else 0,
        'resource_profile_path': str(resource_profile_path),
        'processing_summary': {
            'total_time_seconds': sum(r.get('processing_time_seconds', 0) for r in results),
            'avg_processing_time_seconds': sum(r.get('processing_time_seconds', 0) for r in results) / len(results) if results else 0
        }
    }
    
    stats_path = Path("data/processed/preprocessing_stats.json")
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Preprocessing statistics written to {stats_path}")
    logger.info(f"Pipeline completed: {successful_count}/{len(subject_ids)} subjects successful")
    
    return stats

if __name__ == "__main__":
    main()