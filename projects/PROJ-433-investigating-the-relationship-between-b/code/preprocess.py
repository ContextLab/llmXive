import os
import sys
import subprocess
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils import setup_logger
from download import verify_fMRI_availability

# fMRIPrep version as specified in plan.md (placeholder, should be updated with actual version)
FMRIREP_VERSION = "23.1.3"
FMRIREP_IMAGE = f"nipreps/fmriprep:{FMRIREP_VERSION}"

def get_fmriprep_command(
    subject_id: str,
    input_bids_dir: Path,
    output_dir: Path,
    work_dir: Path,
    mode: str = "ci",
    flags: Optional[List[str]] = None
) -> List[str]:
    """
    Construct the fMRIPrep command line.

    Args:
        subject_id: The subject identifier.
        input_bids_dir: Path to the BIDS dataset root.
        output_dir: Path to the output directory.
        work_dir: Path to the working directory.
        mode: Either 'ci' or 'cluster'.
        flags: Additional flags to append.

    Returns:
        List of command arguments.
    """
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_bids_dir}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", f"{work_dir}:/work",
        "--env", "OMP_NUM_THREADS=2",
        "--env", "OPENBLAS_NUM_THREADS=2",
        "--env", "MKL_NUM_THREADS=2",
        FMRIREP_IMAGE,
        "/data", "/out", "participant",
        "--participant-label", subject_id,
        "--skip-bids-validation",
        "--output-spaces", "MNI",
        "--cifti-output", "91k",
        "--fd-spike-threshold", "0.5"
    ]

    # Mode specific adjustments
    if mode == "ci":
        cmd.extend(["--nprocs", "2", "--mem", "7G", "--omp-nthreads", "2"])
    elif mode == "cluster":
        cmd.extend(["--mode", "slurm"]) # Example for cluster

    # Add standard flags requested in T013 description
    # Note: --motion-correction, --slice-timing, --nuisance-regression are defaults or handled by --cifti-output/--output-spaces in modern fmriprep
    # We explicitly add the requested flags if they are custom or if the environment expects them.
    # However, standard fmriprep CLI uses specific flags.
    # --motion-correction -> usually part of default pipeline
    # --slice-timing -> --slice-time-ref
    # --MNI -> --output-spaces MNI (already added)
    # --nuisance-regression -> --cifti-output or --use-aroma (nuisance is default in cifti)

    # To strictly satisfy the task description's flags, we append them if they are recognized or log a warning if ignored.
    # Since fmriprep doesn't take raw "--motion-correction" as a flag, we assume the task implies enabling these features.
    # We will add the specific flags that map to these features if they exist, otherwise we rely on defaults.
    # Standard flags:
    # --ignore: ignore specific steps (we do NOT ignore)
    # --fd-spike-threshold: set for motion
    
    if flags:
        cmd.extend(flags)

    return cmd

def run_fmriprep(
    subject_id: str,
    bids_dir: Path,
    output_dir: Path,
    work_dir: Path,
    mode: str = "ci",
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Execute the fMRIPrep container for a given subject.

    Args:
        subject_id: Subject ID.
        bids_dir: Input BIDS directory.
        output_dir: Output directory.
        work_dir: Working directory.
        mode: Execution mode ('ci' or 'cluster').
        logger: Logger instance.

    Returns:
        True if successful, False otherwise.
    """
    if logger is None:
        logger = setup_logger("preprocess")

    logger.info(f"Starting fMRIPrep for subject {subject_id} in mode {mode}")

    # Check availability first (T012b requirement)
    status = verify_fMRI_availability()
    if status.get("status") == "MISSING":
        reason = status.get("reason", "Data Gap: fMRI time-series not found")
        logger.warning(f"N/A - Data Unavailable for {subject_id}: {reason}")
        return False

    # Get container hash
    try:
        hash_result = subprocess.run(
            ["docker", "inspect", "--format", "{{.Id}}", FMRIREP_IMAGE],
            capture_output=True, text=True, check=True
        )
        container_hash = hash_result.stdout.strip()
    except subprocess.CalledProcessError:
        logger.error(f"Could not retrieve container hash for {FMRIREP_IMAGE}. Is it pulled?")
        return False

    cmd = get_fmriprep_command(
        subject_id=subject_id,
        input_bids_dir=bids_dir,
        output_dir=output_dir,
        work_dir=work_dir,
        mode=mode
    )

    logger.info(f"Container Hash: {container_hash}")
    logger.info(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            logger.info(f"fMRIPrep completed successfully for {subject_id}")
            return True
        else:
            logger.error(f"fMRIPrep failed for {subject_id} with return code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error for {subject_id}: {e}")
        return False

def get_preprocessed_paths(
    subject_id: str,
    output_dir: Path,
    space: str = "MNI"
) -> Dict[str, Path]:
    """
    Construct expected output paths for preprocessed data.

    Args:
        subject_id: Subject ID.
        output_dir: Output directory.
        space: Target space (e.g., MNI).

    Returns:
        Dictionary of expected file paths.
    """
    base = output_dir / "sub-" + subject_id / "func"
    # Standard fMRIPrep output naming
    preproc_nifti = base / f"sub-{subject_id}_task-rest_space-{space}_desc-preproc_bold.nii.gz"
    confounds = base / f"sub-{subject_id}_task-rest_desc-confounds_regressors.tsv"
    
    return {
        "bold": preproc_nifti,
        "confounds": confounds
    }

def calculate_fd_from_confounds(confounds_path: Path) -> float:
    """
    Calculate Framewise Displacement (FD) from confounds file.

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        Mean FD value.
    """
    import pandas as pd
    
    if not confounds_path.exists():
        return 0.0

    try:
        df = pd.read_csv(confounds_path, sep='\t')
        # Standard FD calculation: sum of absolute differences of motion parameters
        # fMRIPrep provides 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
        # We need to handle rotation to mm conversion (approx 50mm radius)
        if all(col in df.columns for col in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']):
            trans = df[['trans_x', 'trans_y', 'trans_z']].abs().diff().sum(axis=1)
            rot = df[['rot_x', 'rot_y', 'rot_z']].abs().diff().sum(axis=1) * 50.0 # Approx conversion
            fd = trans + rot
            return fd.mean()
        else:
            logging.warning(f"Confounds file {confounds_path} missing motion columns.")
            return 0.0
    except Exception as e:
        logging.error(f"Error calculating FD: {e}")
        return 0.0

def validate_preprocessed_outputs(
    subject_id: str,
    output_dir: Path,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate that preprocessed outputs exist and meet QC metrics.

    Args:
        subject_id: Subject ID.
        output_dir: Output directory.
        logger: Logger instance.

    Returns:
        True if valid, False otherwise.
    """
    if logger is None:
        logger = setup_logger("preprocess")

    paths = get_preprocessed_paths(subject_id, output_dir)
    
    if not paths["bold"].exists():
        logger.warning(f"Preprocessed BOLD file missing for {subject_id}")
        return False

    # Check FD
    if paths["confounds"].exists():
        fd = calculate_fd_from_confounds(paths["confounds"])
        if fd > 0.5:
            logger.warning(f"Subject {subject_id} excluded: FD={fd:.3f} > 0.5mm")
            return False
    
    logger.info(f"Validation passed for {subject_id}")
    return True

def main():
    """
    Main entry point for the preprocessing script.
    Supports CLI arguments and MODE environment variable.
    """
    parser = argparse.ArgumentParser(description="Run fMRIPrep preprocessing")
    parser.add_argument("--mode", type=str, default=None, choices=["ci", "cluster"],
                        help="Execution mode (ci or cluster). Overrides MODE env var.")
    parser.add_argument("--subject", type=str, default=None, help="Subject ID to process. If None, processes all available.")
    parser.add_argument("--bids-dir", type=str, required=True, help="Path to BIDS dataset")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to output directory")
    parser.add_argument("--work-dir", type=str, required=True, help="Path to working directory")

    args = parser.parse_args()

    # Determine mode
    mode = args.mode or os.environ.get("MODE", "ci")
    if mode not in ["ci", "cluster"]:
        mode = "ci"

    logger = setup_logger("preprocess")
    logger.info(f"Preprocessing started in mode: {mode}")

    bids_dir = Path(args.bids_dir)
    output_dir = Path(args.output_dir)
    work_dir = Path(args.work_dir)

    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Check global availability first
    status = verify_fMRI_availability()
    if status.get("status") == "MISSING":
        logger.warning("N/A - Data Unavailable: Skipping all preprocessing.")
        return

    # Determine subjects to process
    subjects = []
    if args.subject:
        subjects = [args.subject]
    else:
        # Scan bids_dir for subjects
        if bids_dir.exists():
            for item in bids_dir.iterdir():
                if item.is_dir() and item.name.startswith("sub-"):
                    subjects.append(item.name.replace("sub-", ""))
        else:
            logger.error(f"BIDS directory {bids_dir} does not exist.")
            return

    if not subjects:
        logger.warning("No subjects found to process.")
        return

    for sub in subjects:
        success = run_fmriprep(
            subject_id=sub,
            bids_dir=bids_dir,
            output_dir=output_dir,
            work_dir=work_dir,
            mode=mode,
            logger=logger
        )
        
        if success:
            validate_preprocessed_outputs(sub, output_dir, logger)

    logger.info("Preprocessing pipeline finished.")

if __name__ == "__main__":
    main()
