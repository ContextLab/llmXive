"""
CPU-tractable fMRIPrep wrapper script.

Invokes the fMRIPrep Docker container with configuration optimized for
CPU-only execution (thread control, no GPU flags).
"""
import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

DOCKER_IMAGE = "nipreps/fmriprep:latest"

def check_docker_installed() -> bool:
    """Verify that Docker is installed and running."""
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Docker is not installed or not running. Please install Docker Desktop or Engine.")
        return False

def build_fmriprep_command(
    input_dir: Path,
    output_dir: Path,
    participant_label: Optional[List[str]] = None,
    nthreads: int = 4,
    mem_gb: int = 8,
    skip_bids_validation: bool = False,
    work_dir: Optional[Path] = None
) -> List[str]:
    """
    Construct the docker run command for fMRIPrep.

    Args:
        input_dir: Path to the BIDS dataset root.
        output_dir: Path to the output directory.
        participant_label: List of participant IDs to process (e.g., ['sub-01']).
        nthreads: Number of threads to allocate to fMRIPrep.
        mem_gb: Memory limit in GB.
        skip_bids_validation: If True, skip BIDS validation.
        work_dir: Optional working directory for intermediate files.

    Returns:
        List of command arguments.
    """
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_dir.resolve()}:/data:ro",
        "-v", f"{output_dir.resolve()}:/out",
        "--user", "$(id -u):$(id -g)",
        "--env", f"OMP_NUM_THREADS={nthreads}",
        "--env", f"OPENBLAS_NUM_THREADS={nthreads}",
        "--env", f"MKL_NUM_THREADS={nthreads}",
        "--env", f"VECLIB_MAXIMUM_THREADS={nthreads}",
        "--env", f"NUMEXPR_NUM_THREADS={nthreads}",
    ]

    if work_dir:
        cmd.extend(["-v", f"{work_dir.resolve()}:/work"])

    cmd.extend([
        DOCKER_IMAGE,
        "/data", "/out", "participant",
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-no-reconall",
        "--nthreads", str(nthreads),
        "--mem-mb", str(mem_gb * 1024),
    ])

    if skip_bids_validation:
        cmd.append("--skip-bids-validation")

    if work_dir:
        cmd.extend(["--work-dir", "/work"])

    if participant_label:
        for label in participant_label:
            cmd.extend(["--participant-label", label])

    return cmd

def run_fmriprep(
    input_dir: Path,
    output_dir: Path,
    participant_label: Optional[List[str]] = None,
    nthreads: int = 4,
    mem_gb: int = 8,
    skip_bids_validation: bool = False,
    work_dir: Optional[Path] = None
) -> int:
    """
    Execute the fMRIPrep Docker container.

    Args:
        input_dir: Path to the BIDS dataset root.
        output_dir: Path to the output directory.
        participant_label: List of participant IDs to process.
        nthreads: Number of threads.
        mem_gb: Memory limit in GB.
        skip_bids_validation: Skip BIDS validation flag.
        work_dir: Working directory for intermediates.

    Returns:
        Exit code from the subprocess.
    """
    if not check_docker_installed():
        return 1

    cmd = build_fmriprep_command(
        input_dir=input_dir,
        output_dir=output_dir,
        participant_label=participant_label,
        nthreads=nthreads,
        mem_gb=mem_gb,
        skip_bids_validation=skip_bids_validation,
        work_dir=work_dir
    )

    logger.info("Executing fMRIPrep with command:")
    logger.info(" ".join(cmd))

    try:
        result = subprocess.run(cmd)
        if result.returncode == 0:
            logger.info("fMRIPrep completed successfully.")
        else:
            logger.error(f"fMRIPrep failed with exit code {result.returncode}")
        return result.returncode
    except KeyboardInterrupt:
        logger.error("Process interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Error executing fMRIPrep: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="CPU-optimized wrapper for fMRIPrep via Docker."
    )
    parser.add_argument(
        "bids_dir",
        type=Path,
        help="Path to the BIDS dataset root directory."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Path to the output directory."
    )
    parser.add_argument(
        "--participants",
        type=str,
        nargs="+",
        default=None,
        help="List of participant labels (e.g., sub-01 sub-02)."
    )
    parser.add_argument(
        "--nthreads",
        type=int,
        default=4,
        help="Number of threads to use (default: 4)."
    )
    parser.add_argument(
        "--mem-gb",
        type=int,
        default=8,
        help="Memory limit in GB (default: 8)."
    )
    parser.add_argument(
        "--skip-bids-validation",
        action="store_true",
        help="Skip BIDS validation."
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Working directory for intermediate files."
    )

    args = parser.parse_args()

    if not args.bids_dir.exists():
        logger.error(f"BIDS directory not found: {args.bids_dir}")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)

    participant_labels = args.participants
    if participant_labels:
        # Ensure 'sub-' prefix if missing
        participant_labels = [
            p if p.startswith("sub-") else f"sub-{p}"
            for p in participant_labels
        ]

    exit_code = run_fmriprep(
        input_dir=args.bids_dir,
        output_dir=args.output_dir,
        participant_label=participant_labels,
        nthreads=args.nthreads,
        mem_gb=args.mem_gb,
        skip_bids_validation=args.skip_bids_validation,
        work_dir=args.work_dir
    )

    sys.exit(exit_code)

if __name__ == "__main__":
    main()