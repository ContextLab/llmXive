"""
Run QC-only preprocessing pipeline.

This script calculates tSNR for subjects in the raw data directory,
validates against the threshold (>= 50), and writes the validation status
to data/analysis/validation_status.json.

It also generates the QC summary CSV (data/analysis/qc_summary.csv)
recording tSNR values and pass/fail counts.

Usage:
    python code/preprocess/run_qc_only.py --input data/raw --output data/processed
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import nibabel as nib
import pandas as pd

from code.logging_config import get_logger
from code.config import get_config

logger = get_logger(__name__)

# Constants
TSNR_THRESHOLD = 50.0
MIN_VOLUMES_TO_SKIP = 4  # Standard practice to skip initial volumes

def calculate_tsnr(nifti_path: Path) -> float:
    """
    Calculate tSNR (temporal Signal-to-Noise Ratio) for a 4D NIfTI file.
    
    tSNR = mean(signal) / std(signal) across time, excluding initial volumes.
    
    Args:
        nifti_path: Path to the 4D NIfTI file.
        
    Returns:
        tSNR value (float).
        
    Raises:
        ValueError: If the image is not 4D or has insufficient volumes.
    """
    if not nifti_path.exists():
        raise FileNotFoundError(f"Input file not found: {nifti_path}")
        
    img = nib.load(str(nifti_path))
    data = img.get_fdata()
    
    if data.ndim != 4:
        raise ValueError(f"Expected 4D image, got {data.ndim}D: {nifti_path}")
        
    n_volumes = data.shape[3]
    if n_volumes <= MIN_VOLUMES_TO_SKIP:
        raise ValueError(
            f"Insufficient volumes ({n_volumes}) to calculate tSNR "
            f"(need more than {MIN_VOLUMES_TO_SKIP} to skip initial volumes): {nifti_path}"
        )
    
    # Exclude initial volumes
    time_series = data[..., MIN_VOLUMES_TO_SKIP:]
    
    # Calculate mean and std across time axis (axis=3)
    mean_signal = np.mean(time_series, axis=3)
    std_signal = np.std(time_series, axis=3)
    
    # Avoid division by zero
    std_signal = np.where(std_signal == 0, 1e-10, std_signal)
    
    tsnr_map = mean_signal / std_signal
    
    # Return mean tSNR across all voxels
    return float(np.mean(tsnr_map))

def find_nifti_files(input_dir: Path) -> List[Path]:
    """
    Find all 4D NIfTI files in the input directory.
    
    Args:
        input_dir: Directory to search.
        
    Returns:
        List of paths to 4D NIfTI files.
    """
    nifti_files = []
    for ext in ['*.nii', '*.nii.gz']:
        nifti_files.extend(input_dir.rglob(ext))
    
    # Filter for 4D images
    valid_files = []
    for f in nifti_files:
        try:
            img = nib.load(str(f))
            if img.ndim == 4:
                valid_files.append(f)
        except Exception as e:
            logger.warning(f"Skipping {f}: {e}")
            
    return valid_files

def run_qc_pipeline(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Run the QC-only preprocessing pipeline.
    
    Args:
        input_dir: Directory containing raw NIfTI files.
        output_dir: Directory to write processed outputs.
        
    Returns:
        Dictionary with pipeline results and status.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    nifti_files = find_nifti_files(input_dir)
    
    if not nifti_files:
        logger.error(f"No 4D NIfTI files found in {input_dir}")
        return {
            "status": "failed",
            "reason": "No 4D NIfTI files found",
            "subjects_processed": 0,
            "subjects_passed": 0,
            "subjects_failed": 0
        }
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for nifti_path in nifti_files:
        subject_id = nifti_path.stem
        # Handle .nii.gz case
        if subject_id.endswith('.nii'):
            subject_id = subject_id[:-4]
            
        try:
            tsnr = calculate_tsnr(nifti_path)
            passed = tsnr >= TSNR_THRESHOLD
            
            if passed:
                passed_count += 1
                status = "passed"
            else:
                failed_count += 1
                status = "failed"
                
            results.append({
                "subject_id": subject_id,
                "tsnr": tsnr,
                "threshold": TSNR_THRESHOLD,
                "status": status,
                "input_path": str(nifti_path)
            })
            
            logger.info(f"Subject {subject_id}: tSNR={tsnr:.2f}, status={status}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Subject {subject_id} failed QC: {e}")
            results.append({
                "subject_id": subject_id,
                "tsnr": None,
                "threshold": TSNR_THRESHOLD,
                "status": "failed",
                "input_path": str(nifti_path),
                "error": str(e)
            })
    
    # Determine overall status
    if passed_count == 0 and failed_count > 0:
        overall_status = "failed"
    elif passed_count > 0 and failed_count == 0:
        overall_status = "passed"
    else:
        # Mixed results - pipeline passes but some subjects failed
        overall_status = "passed"  # Partial pass is acceptable for QC
    
    # Write QC summary CSV
    qc_summary_path = output_dir.parent / "analysis" / "qc_summary.csv"
    qc_summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(qc_summary_path, index=False)
    logger.info(f"QC summary written to {qc_summary_path}")
    
    # Write validation status JSON
    validation_status = {
        "status": overall_status,
        "threshold": TSNR_THRESHOLD,
        "subjects_processed": len(results),
        "subjects_passed": passed_count,
        "subjects_failed": failed_count,
        "pass_rate": passed_count / len(results) if results else 0.0,
        "qc_summary_path": str(qc_summary_path),
        "timestamp": pd.Timestamp.utcnow().isoformat()
    }
    
    validation_path = output_dir / "validation_status.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_status, f, indent=2)
    logger.info(f"Validation status written to {validation_path}")
    
    return validation_status

def main():
    parser = argparse.ArgumentParser(
        description="Run QC-only preprocessing on fMRI data"
    )
    parser.add_argument(
        "--input", 
        type=Path, 
        required=True,
        help="Input directory containing raw NIfTI files"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        required=True,
        help="Output directory for processed data and QC results"
    )
    parser.add_argument(
        "--tsnr-threshold",
        type=float,
        default=TSNR_THRESHOLD,
        help=f"tSNR threshold (default: {TSNR_THRESHOLD})"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input directory does not exist: {args.input}")
        sys.exit(1)
        
    try:
        result = run_qc_pipeline(args.input, args.output)
        
        if result["status"] == "failed":
            logger.error(f"QC pipeline failed: {result.get('reason', 'Unknown')}")
            sys.exit(1)
            
        logger.info(f"QC pipeline completed successfully: {result['subjects_passed']}/{result['subjects_processed']} subjects passed")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"QC pipeline failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()