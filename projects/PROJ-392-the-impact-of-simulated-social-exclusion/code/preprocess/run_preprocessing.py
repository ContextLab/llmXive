"""
Preprocessing orchestration script for fMRI data.

This script handles chunked processing (batches of subjects) and generates
preprocessed NIfTI images using the CPU-compatible fMRIPrep wrapper.
It includes failure logging and progress tracking.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules
from config.loader import get_config, get_path, ensure_paths_exist
from preprocess.cpu_fmriprep_wrapper import run_fmriprep, build_fmriprep_command
from utils.provenance import generate_provenance_record, write_provenance_sidecar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/preprocessing_log.txt', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def get_subject_list(raw_data_dir: Path) -> List[str]:
    """
    Extract list of participant IDs from the raw BIDS dataset.
    
    Args:
        raw_data_dir: Path to the raw BIDS dataset directory.
        
    Returns:
        List of participant IDs (e.g., ['sub-01', 'sub-02']).
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Look for participant subdirectories
    subjects = []
    for item in raw_data_dir.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    
    if not subjects:
        logger.warning(f"No subject directories found in {raw_data_dir}")
    
    return sorted(subjects)

def process_subject_batch(
    subject_ids: List[str],
    raw_bids_dir: Path,
    processed_dir: Path,
    dataset_id: str,
    working_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process a batch of subjects through fMRIPrep.
    
    Args:
        subject_ids: List of subject IDs to process.
        raw_bids_dir: Path to raw BIDS dataset.
        processed_dir: Path to output processed data directory.
        dataset_id: Identifier for the dataset (e.g., 'ds000246').
        working_dir: Optional working directory for intermediate files.
        
    Returns:
        Dictionary with processing results and metrics.
    """
    results = {
        'processed': [],
        'failed': [],
        'skipped': [],
        'start_time': datetime.now().isoformat(),
        'end_time': None
    }
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    for subject_id in subject_ids:
        subject_start = time.time()
        logger.info(f"Processing {subject_id}...")
        
        try:
            # Determine input and output paths
            input_dir = raw_bids_dir / subject_id
            output_dir = processed_dir / dataset_id / subject_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if already processed (idempotency)
            nifti_files = list(output_dir.glob('func/*.nii.gz'))
            if nifti_files:
                logger.info(f"Skipping {subject_id} - already processed")
                results['skipped'].append({
                    'subject': subject_id,
                    'reason': 'already_processed',
                    'time_elapsed': time.time() - subject_start
                })
                continue
            
            # Run fMRIPrep
            success, message = run_fmriprep(
                input_bids=str(raw_bids_dir),
                output_dir=str(processed_dir),
                subject=subject_id,
                dataset_id=dataset_id,
                working_dir=str(working_dir) if working_dir else None
            )
            
            if success:
                # Verify output
                actual_output = processed_dir / dataset_id / subject_id / 'func'
                if actual_output.exists() and list(actual_output.glob('*.nii.gz')):
                    results['processed'].append({
                        'subject': subject_id,
                        'status': 'success',
                        'time_elapsed': time.time() - subject_start
                    })
                    
                    # Generate provenance sidecar
                    provenance = generate_provenance_record(
                        pipeline='fmriprep_cpu_wrapper',
                        version='1.0',
                        input_files=[str(input_dir)],
                        output_files=[str(actual_output)],
                        parameters={
                            'dataset_id': dataset_id,
                            'slice_timing': True,
                            'realign': True,
                            'normalize': 'MNI152NLin2009cAsym',
                            'smoothing': '6mm'
                        }
                    )
                    write_provenance_sidecar(
                        output_dir / 'provenance.json',
                        provenance
                    )
                    logger.info(f"Successfully processed {subject_id}")
                else:
                    raise RuntimeError("Output NIfTI files not found after fMRIPrep")
            else:
                raise RuntimeError(f"fMRIPrep failed: {message}")
                
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {str(e)}")
            results['failed'].append({
                'subject': subject_id,
                'error': str(e),
                'time_elapsed': time.time() - subject_start
            })
    
    results['end_time'] = datetime.now().isoformat()
    return results

def chunk_subjects(subject_ids: List[str], chunk_size: int = 4) -> List[List[str]]:
    """
    Split subject list into chunks for batch processing.
    
    Args:
        subject_ids: List of subject IDs.
        chunk_size: Number of subjects per batch.
        
    Returns:
        List of subject batches.
    """
    return [
        subject_ids[i:i + chunk_size] 
        for i in range(0, len(subject_ids), chunk_size)
    ]

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(
        description='Run fMRI preprocessing on BIDS datasets'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/project_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        help='Specific dataset ID to process (e.g., ds000246)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=4,
        help='Number of subjects per processing batch'
    )
    parser.add_argument(
        '--working-dir',
        type=str,
        default='data/working',
        help='Working directory for intermediate files'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = get_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Ensure paths exist
    ensure_paths_exist(config)
    
    # Get paths
    raw_dir = Path(get_path(config, 'raw_fmri_dir'))
    processed_dir = Path(get_path(config, 'processed_fmri_dir'))
    working_dir = Path(args.working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine datasets to process
    datasets = []
    if args.dataset:
        datasets = [args.dataset]
    else:
        datasets = get_all_dataset_ids(config)
    
    logger.info(f"Processing datasets: {datasets}")
    
    overall_results = {
        'datasets': {},
        'summary': {
            'total_subjects': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0
        }
    }
    
    for dataset_id in datasets:
        logger.info(f"Processing dataset: {dataset_id}")
        
        # Get dataset-specific paths
        dataset_raw_dir = raw_dir / dataset_id
        
        if not dataset_raw_dir.exists():
            logger.warning(f"Dataset directory not found: {dataset_raw_dir}")
            continue
        
        # Get subjects
        subjects = get_subject_list(dataset_raw_dir)
        if not subjects:
            logger.warning(f"No subjects found in {dataset_raw_dir}")
            continue
        
        logger.info(f"Found {len(subjects)} subjects in {dataset_id}")
        
        # Chunk and process
        chunks = chunk_subjects(subjects, args.chunk_size)
        dataset_results = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} subjects)")
            result = process_subject_batch(
                subject_ids=chunk,
                raw_bids_dir=dataset_raw_dir,
                processed_dir=processed_dir,
                dataset_id=dataset_id,
                working_dir=working_dir
            )
            dataset_results.append(result)
        
        # Aggregate results for this dataset
        overall_results['datasets'][dataset_id] = {
            'batches': len(chunks),
            'results': dataset_results
        }
        
        # Update summary
        for res in dataset_results:
            overall_results['summary']['processed'] += len(res['processed'])
            overall_results['summary']['failed'] += len(res['failed'])
            overall_results['summary']['skipped'] += len(res['skipped'])
            overall_results['summary']['total_subjects'] += len(res['processed']) + len(res['failed']) + len(res['skipped'])
    
    # Write final metrics
    metrics_path = Path(get_path(config, 'results_dir')) / 'preprocessing_metrics.json'
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_path, 'w') as f:
        json.dump(overall_results, f, indent=2)
    
    logger.info(f"Preprocessing complete. Metrics saved to {metrics_path}")
    
    # Print summary
    summary = overall_results['summary']
    logger.info(f"Total subjects: {summary['total_subjects']}")
    logger.info(f"Processed: {summary['processed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Skipped: {summary['skipped']}")
    
    if summary['failed'] > 0:
        logger.warning(f"{summary['failed']} subjects failed processing")
        sys.exit(1)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
