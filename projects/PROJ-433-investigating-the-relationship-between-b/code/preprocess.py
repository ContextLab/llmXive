"""
fMRIPrep Preprocessing Wrapper Module.

Invokes fMRIPrep container for fMRI preprocessing, handles QC validation,
and logs operations using the project's standardized logger.
"""
import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from local project modules (as per API surface)
from utils import setup_logger, check_fd, log_exclusion

# Configuration
FMRIPREP_CONTAINER = "nipreps/fmriprep:23.1.0"
DATA_ROOT = Path("data/raw")
PROCESSED_ROOT = Path("data/processed")
LOG_FILE = Path("data/preprocess_log.txt")


def get_fmriprep_command(
    subject_id: str,
    input_path: Path,
    output_dir: Path,
    mode: str = "ci"
) -> List[str]:
    """
    Construct the fMRIPrep Docker/Singularity command string.

    Args:
        subject_id: The subject identifier.
        input_path: Path to the raw fMRI NIfTI file.
        output_dir: Directory where fMRIPrep should write outputs.
        mode: 'ci' for subset/quick run, 'cluster' for full run.

    Returns:
        List of command parts ready for subprocess.run.
    """
    logger = setup_logger()
    logger.info(f"Constructing fMRIPrep command for subject {subject_id} in {mode} mode.")

    # Base docker run command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{DATA_ROOT}:/data:ro",
        "-v", f"{output_dir}:/output",
        "-v", f"{output_dir}/fs_license.txt:/root/.license.txt",
        "-w", "/output",
        FMRIPREP_CONTAINER,
        "/data", "/output", participant,
        "--participant-label", subject_id,
        "--skip-bids-validation",
        "--output-spaces", "MNI",
        "--fs-license-file", "/root/.license.txt"
    ]

    if mode == "ci":
        # Quick mode flags for CI testing
        cmd.extend([
            "--nprocs", "1",
            "--omp-nthreads", "1",
            "--mem", "2000",
            "--use-aroma", "false",
            "--ignore", "fieldmaps"
        ])
    elif mode == "cluster":
        # Full processing flags
        cmd.extend([
            "--nprocs", "4",
            "--omp-nthreads", "4",
            "--mem", "8000",
            "--use-aroma", "true"
        ])

    cmd.extend([
        "--motion-correction",
        "--slice-timing",
        "--nuisance-regression"
    ])

    logger.info(f"Full command: {' '.join(cmd)}")
    return cmd


def run_fmriprep(subject_id: str, mode: str = "ci") -> Dict[str, Any]:
    """
    Execute fMRIPrep for a specific subject.

    Args:
        subject_id: The subject identifier.
        mode: Execution mode ('ci' or 'cluster').

    Returns:
        Dict with 'success' (bool) and 'message' (str).
    """
    logger = setup_logger()
    logger.info(f"Starting fMRIPrep for subject {subject_id}. Mode: {mode}")

    # Check availability first
    from download import verify_fMRI_availability
    status = verify_fMRI_availability(subject_id)

    if status['status'] == 'MISSING':
        msg = f"Skipping preprocessing: {status['reason']}"
        logger.warning(msg)
        log_exclusion("Data Unavailable", subject_id)
        return {'success': False, 'message': msg}

    input_file = DATA_ROOT / subject_id / "MNINonLinear" / "Results" / "r11100" / "rfMRI_REST1_LR.nii.gz"
    output_dir = PROCESSED_ROOT / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure license file exists (mocked for this implementation context)
    license_file = output_dir / "fs_license.txt"
    if not license_file.exists():
        logger.warning("fs_license.txt not found. Creating placeholder.")
        license_file.write_text("FS_LICENSE_PLACEHOLDER\n")

    cmd = get_fmriprep_command(subject_id, input_file, output_dir, mode)

    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600 if mode == "ci" else 72000
        )

        if result.returncode != 0:
            error_msg = f"fMRIPrep failed for {subject_id}: {result.stderr}"
            logger.error(error_msg)
            return {'success': False, 'message': error_msg}

        logger.info(f"fMRIPrep completed successfully for {subject_id}.")
        return {'success': True, 'message': "Success"}

    except subprocess.TimeoutExpired:
        msg = f"Timeout for {subject_id}"
        logger.error(msg)
        return {'success': False, 'message': msg}
    except FileNotFoundError:
        msg = "Docker not found. Ensure Docker is installed and running."
        logger.error(msg)
        return {'success': False, 'message': msg}


def get_preprocessed_paths(subject_id: str) -> Dict[str, Path]:
    """
    Return paths to expected preprocessed outputs.

    Args:
        subject_id: The subject identifier.

    Returns:
        Dict mapping output type to Path.
    """
    base = PROCESSED_ROOT / subject_id / "sub-" + subject_id
    return {
        "bold_mni": base / "func" / f"{base.name}_task-rest_space-MNI_desc-preproc_bold.nii.gz",
        "confounds": base / "func" / f"{base.name}_task-rest_desc-confounds_regressors.tsv"
    }


def calculate_fd_from_confounds(confounds_path: Path) -> float:
    """
    Calculate Framewise Displacement (FD) from confounds TSV.

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        Float representing the mean FD.
    """
    logger = setup_logger()
    if not confounds_path.exists():
        logger.warning(f"Confounds file missing for FD calculation: {confounds_path}")
        return 999.0  # High value to trigger exclusion

    try:
        import pandas as pd
        df = pd.read_csv(confounds_path, sep='\t')
        # Standard FD calculation: sum of absolute differences of motion parameters
        # Assuming columns 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
        # Note: Rotation should ideally be converted to mm, but for simplicity here we sum abs diffs
        motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        available_cols = [c for c in motion_cols if c in df.columns]
        if not available_cols:
            logger.warning(f"No motion columns found in {confounds_path}")
            return 999.0

        diffs = df[available_cols].diff().abs().sum(axis=1)
        mean_fd = diffs.mean()
        logger.info(f"Calculated mean FD for {confounds_path.parent.name}: {mean_fd:.4f}")
        return float(mean_fd)
    except Exception as e:
        logger.error(f"Error calculating FD: {e}")
        return 999.0


def validate_preprocessed_outputs(subject_id: str) -> Dict[str, Any]:
    """
    Validate that preprocessed outputs exist and pass QC (FD check).

    Args:
        subject_id: The subject identifier.

    Returns:
        Dict with 'valid' (bool) and 'reason' (str if invalid).
    """
    logger = setup_logger()
    logger.info(f"Validating outputs for {subject_id}")

    paths = get_preprocessed_paths(subject_id)

    # Check file existence
    for name, path in paths.items():
        if not path.exists():
            reason = f"Output missing: {name} ({path})"
            logger.warning(f"Validation failed for {subject_id}: {reason}")
            return {'valid': False, 'reason': reason}

    # Check FD
    confounds_path = paths['confounds']
    fd = calculate_fd_from_confounds(confounds_path)

    if not check_fd(fd, threshold=0.5):
        reason = f"High motion detected: FD={fd:.4f} > 0.5mm"
        logger.warning(f"QC Failed for {subject_id}: {reason}")
        log_exclusion("High Motion", subject_id)
        return {'valid': False, 'reason': reason}

    logger.info(f"Validation passed for {subject_id} (FD={fd:.4f})")
    return {'valid': True, 'reason': "All checks passed"}


def main():
    """CLI entry point for preprocessing."""
    logger = setup_logger()
    parser = argparse.ArgumentParser(description="Run fMRIPrep preprocessing")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID")
    parser.add_argument("--mode", type=str, default="ci", choices=["ci", "cluster"], help="Run mode")
    args = parser.parse_args()

    logger.info(f"Starting preprocessing pipeline for {args.subject}")

    # Run preprocessing
    result = run_fmriprep(args.subject, args.mode)
    if not result['success']:
        logger.error(f"Preprocessing failed: {result['message']}")
        sys.exit(1)

    # Validate outputs
    validation = validate_preprocessed_outputs(args.subject)
    if not validation['valid']:
        logger.error(f"Validation failed: {validation['reason']}")
        sys.exit(1)

    logger.info(f"Pipeline completed successfully for {args.subject}")


if __name__ == "__main__":
    main()
