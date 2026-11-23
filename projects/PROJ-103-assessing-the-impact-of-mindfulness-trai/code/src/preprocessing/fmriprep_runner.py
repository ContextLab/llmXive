"""
fMRIPrep Docker runner script.

This module provides functionality to configure and run fMRIPrep
via Docker with appropriate thread and memory constraints.
"""

import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config.env import get_data_dir
from src.config.settings import get_preprocessing_params

logger = logging.getLogger(__name__)


class FMRIPrepRunnerError(Exception):
    """Custom exception for fMRIPrep runner errors."""
    pass


def get_fmriprep_config() -> Dict[str, Any]:
    """
    Retrieve fMRIPrep configuration from project settings.

    Returns:
        Dict containing:
            - docker_image: str
            - memory_gb: int
            - threads: int
            - output_format: str (default 'mni')
            - ignore_fields: List[str]
            - force_bids: bool
    """
    data_dir = get_data_dir()
    if not data_dir:
        raise FMRIPrepRunnerError("DATA_DIR environment variable is not set.")

    # Get preprocessing params from settings
    params = get_preprocessing_params()

    # Configure resource limits based on GitHub Actions constraints
    # Using conservative limits: 2 threads, 4GB memory for CI compatibility
    config = {
        "docker_image": "nipreps/fmriprep:23.1.3",
        "memory_gb": 4,
        "threads": 2,
        "output_format": "mni",
        "ignore_fields": ["fieldmap", "fmap"],  # Skip fieldmap processing if not available
        "force_bids": True,
        "clean_workdir": True,
    }

    # Override with settings if available
    if "smoothing_mm" in params:
        # Smoothing is handled in post-processing, not fMRIPrep
        pass

    return config


def build_fmriprep_command(
    dataset_path: str,
    output_dir: str,
    participant_label: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Build the Docker command to run fMRIPrep.

    Args:
        dataset_path: Path to the BIDS dataset directory
        output_dir: Path to the output directory
        participant_label: Specific participant label (e.g., 'sub-01') or 'all'
        config: Configuration dictionary from get_fmriprep_config()

    Returns:
        List of command arguments ready for subprocess.run()
    """
    if config is None:
        config = get_fmriprep_config()

    docker_image = config["docker_image"]
    memory_gb = config["memory_gb"]
    threads = config["threads"]

    # Ensure paths are absolute
    dataset_path = str(Path(dataset_path).resolve())
    output_dir = str(Path(output_dir).resolve())

    # Create output directory structure
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{dataset_path}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", "/tmp:/tmp",  # Allow temp files
        "-e", "OMP_NUM_THREADS=1",  # Limit OpenMP threads
        "--memory", f"{memory_gb}g",
        "--memory-swap", f"{memory_gb}g",
        "--cpus", str(threads),
        "--user", "root",  # fMRIPrep often needs root for file permissions
        docker_image,
        "/data", "/out", "participant",
        "--participant-label", participant_label if participant_label else "all",
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-license-file", "/opt/freesurfer/license.txt",
        "--ignore", ",".join(config.get("ignore_fields", [])),
        "--nthreads", str(threads),
        "--omp-nthreads", "1",
        "--mem", f"{memory_gb * 1024}MB",
        "--skull-strip-template", "MNI152NLin2009cAsym",
    ]

    # Add force BIDS flag if configured
    if config.get("force_bids", False):
        cmd.append("--bids-filter-file")
        cmd.append("/data/bids_dataset_description.json")

    # Add clean workdir flag
    if config.get("clean_workdir", False):
        cmd.append("--clean-workdir")

    return cmd


def run_fmriprep(
    dataset_path: str,
    output_dir: str,
    participant_label: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> subprocess.CompletedProcess:
    """
    Run fMRIPrep via Docker.

    Args:
        dataset_path: Path to the BIDS dataset directory
        output_dir: Path to the output directory
        participant_label: Specific participant label or 'all'
        config: Configuration dictionary
        dry_run: If True, only print the command without executing

    Returns:
        subprocess.CompletedProcess instance

    Raises:
        FMRIPrepRunnerError: If Docker is not available or command fails
    """
    if config is None:
        config = get_fmriprep_config()

    cmd = build_fmriprep_command(
        dataset_path, output_dir, participant_label, config
    )

    logger.info(f"Running fMRIPrep on {dataset_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Participant: {participant_label or 'all'}")
    logger.info(f"Docker image: {config['docker_image']}")
    logger.info(f"Resources: {config['memory_gb']}GB RAM, {config['threads']} threads")

    if dry_run:
        logger.info("DRY RUN - Command to be executed:")
        logger.info(" ".join(cmd))
        raise FMRIPrepRunnerError("Dry run mode - command not executed")

    # Check if Docker is available
    try:
        subprocess.run(
            ["docker", "--version"],
            check=True,
            capture_output=True,
            timeout=10
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise FMRIPrepRunnerError(
            f"Docker is not available or not properly configured: {e}"
        )

    # Run the command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=None  # No timeout for long-running fMRIPrep
        )

        if result.returncode != 0:
            logger.error(f"fMRIPrep failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise FMRIPrepRunnerError(
                f"fMRIPrep failed: {result.stderr[:500]}..."
            )

        logger.info("fMRIPrep completed successfully")
        return result

    except subprocess.TimeoutExpired as e:
        raise FMRIPrepRunnerError(f"fMRIPrep timed out: {e}")
    except FileNotFoundError as e:
        raise FMRIPrepRunnerError(f"Docker command not found: {e}")


def main():
    """
    Main entry point for fMRIPrep runner script.

    Usage:
        python -m src.preprocessing.fmriprep_runner --dataset <path> --output <path> [--participant <label>]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run fMRIPrep preprocessing on BIDS dataset"
    )
    parser.add_argument(
        "--dataset", "-d",
        required=True,
        help="Path to BIDS dataset directory"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output directory"
    )
    parser.add_argument(
        "--participant", "-p",
        default=None,
        help="Specific participant label (e.g., 'sub-01') or 'all'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command without executing"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        run_fmriprep(
            dataset_path=args.dataset,
            output_dir=args.output,
            participant_label=args.participant,
            dry_run=args.dry_run
        )
        print("fMRIPrep completed successfully")
        return 0
    except FMRIPrepRunnerError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())