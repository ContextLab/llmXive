"""
Batch processing optimization module for the mTBI study pipeline.

Implements parallel processing, memory-aware batching, and runtime monitoring
to ensure the full pipeline completes within the 5-hour runtime limit (SC-004).
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import signal

# Import existing project utilities
from config import get_config, get_memory_limit_gb, get_runtime_limit_hours
from memory_monitor import get_current_ram_gb, is_limit_exceeded, check_and_warn
from time_monitor import initialize_runtime_monitor, check_runtime_status, get_elapsed_time_hours
from logging_config import get_logger, log_memory_warning
from data_ingestion import generate_manifest
from preprocessing import run_preprocessing_pipeline
from graph_metrics import process_connectivity_matrices
from statistical_model import run_statistical_analysis
from robustness import run_robustness_analysis
from analysis_report import generate_report

# Constants
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 1)  # Leave one core for OS
MEMORY_CHECK_INTERVAL = 60  # seconds
BATCH_SIZE = 5  # Subjects per batch to balance memory and throughput

logger = get_logger(__name__)

def initialize_batch_processing():
    """Initialize the batch processing environment."""
    logger.info("Initializing batch processing environment")
    
    # Initialize runtime monitoring
    initialize_runtime_monitor()
    
    # Check initial memory state
    current_ram = get_current_ram_gb()
    logger.info(f"Initial RAM usage: {current_ram:.2f} GB")
    
    # Check runtime limits
    runtime_ok = check_runtime_status()
    if not runtime_ok:
        logger.warning("Runtime limit approaching or exceeded")
        return False
    
    return True

def process_subject_batch(
    subject_ids: List[str],
    data_dir: Path,
    results_dir: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a batch of subjects with memory and runtime monitoring.
    
    Args:
        subject_ids: List of subject identifiers to process
        data_dir: Path to the raw data directory
        results_dir: Path to the results output directory
        config: Configuration dictionary
    
    Returns:
        Dictionary containing processing results and status
    """
    start_time = time.time()
    results = {
        'subjects_processed': [],
        'subjects_failed': [],
        'errors': [],
        'memory_peak_gb': 0.0,
        'runtime_seconds': 0.0,
        'status': 'success'
    }
    
    memory_limit = get_memory_limit_gb()
    
    for subject_id in subject_ids:
        # Check runtime limit before processing each subject
        if not check_runtime_status():
            logger.warning(f"Runtime limit exceeded, stopping batch processing")
            results['status'] = 'runtime_limit_exceeded'
            break
        
        # Check memory limit
        current_ram = get_current_ram_gb()
        if current_ram > memory_limit * 0.9:
            logger.warning(f"Memory usage high ({current_ram:.2f} GB), skipping subject {subject_id}")
            results['subjects_failed'].append(subject_id)
            results['errors'].append(f"Memory limit warning for subject {subject_id}")
            continue
        
        try:
            # Process individual subject
            logger.info(f"Processing subject: {subject_id}")
            
            # Run preprocessing
            preproc_result = run_preprocessing_pipeline(
                subject_id=subject_id,
                data_dir=data_dir,
                results_dir=results_dir,
                config=config
            )
            
            if not preproc_result.get('success', False):
                raise RuntimeError(f"Preprocessing failed for {subject_id}")
            
            # Compute graph metrics
            metrics_result = process_connectivity_matrices(
                subject_id=subject_id,
                results_dir=results_dir,
                config=config
            )
            
            if not metrics_result.get('success', False):
                raise RuntimeError(f"Graph metrics computation failed for {subject_id}")
            
            results['subjects_processed'].append(subject_id)
            
            # Update memory tracking
            current_ram = get_current_ram_gb()
            if current_ram > results['memory_peak_gb']:
                results['memory_peak_gb'] = current_ram
            
        except Exception as e:
            error_msg = f"Error processing {subject_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            results['subjects_failed'].append(subject_id)
            results['errors'].append(error_msg)
            results['status'] = 'partial_failure'
    
    results['runtime_seconds'] = time.time() - start_time
    return results

def run_optimized_pipeline(
    data_dir: Optional[Path] = None,
    results_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full pipeline with optimizations for batch processing.
    
    This function:
    1. Initializes monitoring infrastructure
    2. Processes subjects in optimized batches
    3. Monitors memory and runtime continuously
    4. Aggregates results and generates final report
    
    Args:
        data_dir: Path to raw data directory
        results_dir: Path to results output directory
        manifest_path: Path to the manifest CSV file
    
    Returns:
        Final analysis report dictionary
    """
    logger.info("Starting optimized batch pipeline")
    
    # Initialize
    if not initialize_batch_processing():
        return {'status': 'failed', 'reason': 'Initialization failed'}
    
    # Set default paths
    if data_dir is None:
        data_dir = Path('data/raw')
    if results_dir is None:
        results_dir = Path('data/results')
    if manifest_path is None:
        manifest_path = results_dir / 'manifest.csv'
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return {'status': 'failed', 'reason': 'Manifest not found'}
    
    # Read manifest and group subjects into batches
    import pandas as pd
    manifest_df = pd.read_csv(manifest_path)
    subject_ids = manifest_df['subject_id'].unique().tolist()
    
    logger.info(f"Found {len(subject_ids)} subjects to process")
    
    # Create batches
    batches = [
        subject_ids[i:i + BATCH_SIZE]
        for i in range(0, len(subject_ids), BATCH_SIZE)
    ]
    
    logger.info(f"Processing {len(batches)} batches")
    
    # Process batches (sequential for memory safety, with monitoring)
    all_results = {
        'subjects_processed': [],
        'subjects_failed': [],
        'errors': [],
        'total_runtime_seconds': 0.0,
        'peak_memory_gb': 0.0,
        'batches_processed': 0
    }
    
    config = get_config()
    
    for batch_idx, batch in enumerate(batches):
        logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")
        
        # Check runtime before each batch
        if not check_runtime_status():
            logger.warning("Runtime limit exceeded, stopping pipeline")
            break
        
        # Process batch
        batch_result = process_subject_batch(
            subject_ids=batch,
            data_dir=data_dir,
            results_dir=results_dir,
            config=config
        )
        
        # Aggregate results
        all_results['subjects_processed'].extend(batch_result['subjects_processed'])
        all_results['subjects_failed'].extend(batch_result['subjects_failed'])
        all_results['errors'].extend(batch_result['errors'])
        all_results['total_runtime_seconds'] += batch_result['runtime_seconds']
        
        if batch_result['memory_peak_gb'] > all_results['peak_memory_gb']:
            all_results['peak_memory_gb'] = batch_result['memory_peak_gb']
        
        all_results['batches_processed'] += 1
        
        # Memory check between batches
        current_ram = get_current_ram_gb()
        if current_ram > get_memory_limit_gb() * 0.8:
            logger.warning(f"High memory usage between batches: {current_ram:.2f} GB")
    
    # Run statistical analysis on aggregated results
    logger.info("Running statistical analysis")
    try:
        stats_result = run_statistical_analysis(
            results_dir=results_dir,
            config=config
        )
        all_results['statistical_analysis'] = stats_result
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        all_results['statistical_analysis'] = {'status': 'failed', 'error': str(e)}
    
    # Run robustness analysis
    logger.info("Running robustness analysis")
    try:
        robustness_result = run_robustness_analysis(
            results_dir=results_dir,
            config=config
        )
        all_results['robustness_analysis'] = robustness_result
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}")
        all_results['robustness_analysis'] = {'status': 'failed', 'error': str(e)}
    
    # Generate final report
    logger.info("Generating final analysis report")
    report = generate_report(
        results_dir=results_dir,
        pipeline_results=all_results
    )
    
    # Save report
    report_path = results_dir / 'analysis_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Pipeline complete. Report saved to {report_path}")
    return report

def main():
    """Main entry point for batch processing."""
    logger.info("Starting batch processor")
    
    try:
        report = run_optimized_pipeline()
        
        if report.get('status') == 'success':
            logger.info("Batch processing completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Batch processing failed: {report.get('reason', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error in batch processing: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
