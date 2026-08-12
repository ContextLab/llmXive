"""
Docker configuration generator for fmriprep.

This module provides functions to generate Docker run commands and configuration
for running fmriprep with appropriate memory and process limits for the
PROJ-195-examining-the-impact-of-auditory-feedback-motor-learning project.

It ensures efficient resource utilization on constrained compute environments.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any


# Default configuration for constrained environments (free-tier CPU)
DEFAULT_MEMORY_LIMIT = "4g"  # 4GB RAM limit
DEFAULT_PROCESS_LIMIT = 2    # 2 processes (threads)
DEFAULT_IMAGE_TAG = "23.1.0" # Stable fmriprep version
DEFAULT_WORK_DIR = "/tmp/fmriprep_work"


def get_docker_run_command(
    bids_dir: Path,
    output_dir: Path,
    participant_label: Optional[str] = None,
    memory_limit: str = DEFAULT_MEMORY_LIMIT,
    process_limit: int = DEFAULT_PROCESS_LIMIT,
    image_tag: str = DEFAULT_IMAGE_TAG,
    work_dir: Optional[Path] = None
) -> list:
    """
    Generate a Docker run command for fmriprep with resource limits.

    Args:
        bids_dir: Path to the BIDS dataset directory.
        output_dir: Path to the output directory for derivatives.
        participant_label: Optional single subject label to process.
        memory_limit: Docker memory limit (e.g., '4g', '2g').
        process_limit: Number of processes/threads for fmriprep.
        image_tag: fmriprep Docker image tag.
        work_dir: Working directory for temporary files.

    Returns:
        A list of command line arguments representing the docker run command.
    """
    if not bids_dir.exists():
        raise FileNotFoundError(f"BIDS directory not found: {bids_dir}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if work_dir is None:
        work_dir = Path(DEFAULT_WORK_DIR)
        work_dir.mkdir(parents=True, exist_ok=True)

    image_name = f"nipreps/fmriprep:{image_tag}"

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{bids_dir}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", f"{work_dir}:/work",
        "-e", "OMP_NUM_THREADS=1",  # Prevent OpenMP oversubscription
        "-e", "OPENBLAS_NUM_THREADS=1",
        "-e", "MKL_NUM_THREADS=1",
        "--memory", memory_limit,
        "--memory-swap", memory_limit,
        "--cpus", str(process_limit),
        "--env", f"FS_LICENSE={os.environ.get('FS_LICENSE', '')}" if os.environ.get('FS_LICENSE') else None,
        image_name,
        "/data", "/out", "participant",
        "--participant-label", participant_label if participant_label else "",
        "--skip-bids-validation",  # We validated manually in download.py
        "--nthreads", str(process_limit),
        "--omp-nthreads", "1",
        "--mem_mb", str(int(memory_limit.rstrip('g')) * 1024),
        "--clean-workdir",
        "--fs-no-reconall",  # Skip FreeSurfer recon-all for speed/memory
    ]

    # Filter out None values (e.g., if FS_LICENSE is not set)
    return [arg for arg in cmd if arg is not None]


def validate_docker_installation() -> bool:
    """
    Check if Docker is installed and running.

    Returns:
        True if Docker is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def pull_fmriprep_image(tag: str = DEFAULT_IMAGE_TAG) -> bool:
    """
    Pull the specified fmriprep Docker image.

    Args:
        tag: The image tag to pull.

    Returns:
        True if successful, False otherwise.
    """
    image_name = f"nipreps/fmriprep:{tag}"
    try:
        print(f"Pulling {image_name}...")
        result = subprocess.run(
            ["docker", "pull", image_name],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: Docker not found. Please install Docker.", file=sys.stderr)
        return False


def generate_config_file(
    output_path: Path,
    bids_dir: Path,
    output_dir: Path,
    memory_limit: str = DEFAULT_MEMORY_LIMIT,
    process_limit: int = DEFAULT_PROCESS_LIMIT,
    image_tag: str = DEFAULT_IMAGE_TAG
) -> Path:
    """
    Generate a shell script configuration for running fmriprep.

    Args:
        output_path: Path to write the configuration script.
        bids_dir: Path to the BIDS dataset.
        output_dir: Path for output derivatives.
        memory_limit: Memory limit string.
        process_limit: Process limit integer.
        image_tag: Docker image tag.

    Returns:
        Path to the generated configuration script.
    """
    cmd = get_docker_run_command(
        bids_dir=bids_dir,
        output_dir=output_dir,
        memory_limit=memory_limit,
        process_limit=process_limit,
        image_tag=image_tag
    )

    script_content = f"""#!/bin/bash
# fmriprep Docker Configuration Script
# Generated for PROJ-195-examining-the-impact-of-auditory-feedback-motor-learning
# Memory Limit: {memory_limit}
# Process Limit: {process_limit}
# Image: nipreps/fmriprep:{image_tag}

set -e

echo "Starting fmriprep with resource limits..."
echo "BIDS Dir: {bids_dir}"
echo "Output Dir: {output_dir}"

{" ".join(cmd)}

echo "fmriprep execution completed."
"""

    output_path.write_text(script_content)
    os.chmod(output_path, 0o755)
    return output_path


def main():
    """
    Main entry point for generating Docker configuration.

    Usage:
        python code/docker_fmriprep_config.py --bids data/raw --output data/derivatives
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Docker configuration for fmriprep"
    )
    parser.add_argument(
        "--bids", type=Path, required=True,
        help="Path to BIDS dataset directory"
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Path to output derivatives directory"
    )
    parser.add_argument(
        "--memory", type=str, default=DEFAULT_MEMORY_LIMIT,
        help=f"Memory limit (default: {DEFAULT_MEMORY_LIMIT})"
    )
    parser.add_argument(
        "--processes", type=int, default=DEFAULT_PROCESS_LIMIT,
        help=f"Number of processes (default: {DEFAULT_PROCESS_LIMIT})"
    )
    parser.add_argument(
        "--tag", type=str, default=DEFAULT_IMAGE_TAG,
        help=f"fmriprep image tag (default: {DEFAULT_IMAGE_TAG})"
    )
    parser.add_argument(
        "--config-out", type=Path, default=Path("run_fmriprep.sh"),
        help="Path to write the generated shell script"
    )

    args = parser.parse_args()

    # Validate Docker
    if not validate_docker_installation():
        print("ERROR: Docker is not installed or not running.", file=sys.stderr)
        sys.exit(1)

    # Pull image if not present
    try:
        subprocess.run(
            ["docker", "image", "inspect", f"nipreps/fmriprep:{args.tag}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        if not pull_fmriprep_image(args.tag):
            print("ERROR: Failed to pull fmriprep image.", file=sys.stderr)
            sys.exit(1)

    # Generate config
    config_path = generate_config_file(
        output_path=args.config_out,
        bids_dir=args.bids,
        output_dir=args.output,
        memory_limit=args.memory,
        process_limit=args.processes,
        image_tag=args.tag
    )

    print(f"Docker configuration generated: {config_path}")
    print("Run with: bash " + str(config_path))


if __name__ == "__main__":
    main()