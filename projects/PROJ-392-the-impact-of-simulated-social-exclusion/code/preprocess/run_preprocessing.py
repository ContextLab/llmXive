"""
Preprocessing orchestration script for fMRI data.

Handles chunked processing of subjects (batches) to manage CPU/RAM constraints.
Invokes the cpu_fmriprep_wrapper for each subject and generates preprocessed NIfTI
images with slice-timing correction, realignment, normalization to MNI, and smoothing.
Includes failure logging and progress tracking.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules based on provided API surface
from utils.config_loader import load_config, get_dataset_by_id
from utils.provenance import generate_provenance_sidecar
from preprocess.cpu_fmriprep_wrapper import run_fmriprep, check_docker_installed

# Configure logging
LOG_DIR = Path("data/results")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"preprocessing_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_subjects_for_dataset(dataset_id: str) -> List[str]:
    """
    Retrieve list of subject IDs for a given dataset from the raw data directory.
    Assumes BIDS structure: data/raw-fmri/<dataset_id>/sub-<label>/
    """
    raw_base = Path("data/raw-fmri") / dataset_id
    if not raw_base.exists():
        logger.warning(f"Raw data directory not found for {dataset_id}: {raw_base}")
        return []
    
    subjects = []
    for item in raw_base.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subject_id = item.name.replace("sub-", "")
            subjects.append(subject_id)
    
    logger.info(f"Found {len(subjects)} subjects in {dataset_id}")
    return sorted(subjects)

def process_subject_batch(
    dataset_id: str,
    subject_ids: List[str],
    output_dir: Path,
    smoothing_fwhm: int = 6,
    n_threads: int = 4
) -> Dict[str, Any]:
    """
    Process a batch of subjects through the fMRIPrep wrapper.
    
    Args:
        dataset_id: OpenNeuro dataset ID (e.g., ds000246)
        subject_ids: List of subject labels to process
        output_dir: Directory to write preprocessed outputs
        smoothing_fwhm: Smoothing kernel in mm (default 6mm)
        n_threads: Number of CPU threads for fMRIPrep
    
    Returns:
        Dictionary with success/failure counts and details
    """
    results = {
        "total": len(subject_ids),
        "success": 0,
        "failed": 0,
        "details": []
    }
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for subject_id in subject_ids:
        start_time = time.time()
        try:
            logger.info(f"Processing {dataset_id}:sub-{subject_id}")
            
            # Run preprocessing via wrapper
            success, output_paths = run_fmriprep(
                dataset_id=dataset_id,
                subject_id=subject_id,
                output_dir=str(output_dir),
                smoothing_fwhm=smoothing_fwhm,
                n_threads=n_threads
            )
            
            elapsed = time.time() - start_time
            
            if success:
                results["success"] += 1
                # Generate provenance sidecar
                for path in output_paths:
                    if path.exists():
                        generate_provenance_sidecar(
                            input_path=path,
                            pipeline_name="fmriprep_cpu",
                            parameters={
                                "smoothing_fwhm": smoothing_fwhm,
                                "n_threads": n_threads,
                                "dataset_id": dataset_id,
                                "subject_id": subject_id
                            }
                        )
                logger.info(f"Completed {dataset_id}:sub-{subject_id} in {elapsed:.2f}s")
            else:
                results["failed"] += 1
                results["details"].append({
                    "subject_id": subject_id,
                    "status": "failed",
                    "error": "fmriprep_wrapper returned failure"
                })
                logger.error(f"Failed {dataset_id}:sub-{subject_id}")
                
        except Exception as e:
            results["failed"] += 1
            elapsed = time.time() - start_time
            results["details"].append({
                "subject_id": subject_id,
                "status": "exception",
                "error": str(e)
            })
            logger.exception(f"Exception processing {dataset_id}:sub-{subject_id}: {e}")
    
    return results

def run_preprocessing(
    dataset_ids: List[str],
    batch_size: int = 5,
    smoothing_fwhm: int = 6,
    n_threads: int = 4
) -> Dict[str, Any]:
    """
    Main entry point for chunked preprocessing across multiple datasets.
    
    Args:
        dataset_ids: List of dataset IDs to process
        batch_size: Number of subjects to process in parallel batches
        smoothing_fwhm: Smoothing kernel size in mm
        n_threads: CPU threads per fMRIPrep instance
    
    Returns:
        Aggregated results dictionary
    """
    if not check_docker_installed():
        logger.error("Docker is not installed or not running. Aborting.")
        return {"error": "Docker not available"}
    
    overall_results = {
        "datasets": {},
        "summary": {
            "total_subjects": 0,
            "total_success": 0,
            "total_failed": 0
        }
    }
    
    for dataset_id in dataset_ids:
        logger.info(f"Starting preprocessing for dataset: {dataset_id}")
        
        subjects = get_subjects_for_dataset(dataset_id)
        if not subjects:
            logger.warning(f"No subjects found for {dataset_id}, skipping.")
            continue
        
        # Chunk subjects into batches
        batches = [subjects[i:i + batch_size] for i in range(0, len(subjects), batch_size)]
        logger.info(f"Processing {len(subjects)} subjects in {len(batches)} batches")
        
        dataset_results = {
            "batches_processed": 0,
            "subject_results": []
        }
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} for {dataset_id}")
            
            output_subdir = Path("data/processed-fmri") / dataset_id
            batch_result = process_subject_batch(
                dataset_id=dataset_id,
                subject_ids=batch,
                output_dir=output_subdir,
                smoothing_fwhm=smoothing_fwhm,
                n_threads=n_threads
            )
            
            dataset_results["subject_results"].append(batch_result)
            dataset_results["batches_processed"] += 1
          
            overall_results["summary"]["total_subjects"] += batch_result["total"]
            overall_results["summary"]["total_success"] += batch_result["success"]
            overall_results["summary"]["total_failed"] += batch_result["failed"]
        
        overall_results["datasets"][dataset_id] = dataset_results
    
    return overall_results

def main():
    parser = argparse.ArgumentParser(
        description="Run fMRI preprocessing pipeline with chunked subject processing."
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["ds000246", "ds004738"],
        help="List of OpenNeuro dataset IDs to process (default: ds000246 ds004738)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of subjects to process in each batch (default: 5)"
    )
    parser.add_argument(
        "--smoothing-fwhm",
        type=int,
        default=6,
        help="Smoothing kernel size in mm (default: 6)"
    )
    parser.add_argument(
        "--n-threads",
        type=int,
        default=4,
        help="Number of CPU threads for fMRIPrep (default: 4)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed-fmri",
        help="Base output directory for preprocessed data"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting preprocessing pipeline with args: {vars(args)}")
    
    results = run_preprocessing(
        dataset_ids=args.datasets,
        batch_size=args.batch_size,
        smoothing_fwhm=args.smoothing_fwhm,
        n_threads=args.n_threads
    )
    
    # Write results summary to JSON
    summary_path = Path("data/results/preprocessing_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Preprocessing complete. Summary written to {summary_path}")
    
    # Print summary
    total = results["summary"]["total_subjects"]
    success = results["summary"]["total_success"]
    failed = results["summary"]["total_failed"]
    rate = (success / total * 100) if total > 0 else 0
    
    logger.info(f"Pipeline Summary: {success}/{total} subjects successful ({rate:.1f}%)")
    if failed > 0:
        logger.warning(f"{failed} subjects failed processing. Check logs for details.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())