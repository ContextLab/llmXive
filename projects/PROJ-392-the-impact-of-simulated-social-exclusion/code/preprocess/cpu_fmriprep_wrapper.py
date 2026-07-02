"""
CPU-only fMRIPrep wrapper script.

This script invokes the fMRIPrep Docker container with configuration
optimized for CPU-only execution (no GPU flags, appropriate thread limits).
It does not require fMRIPrep to be installed via pip; it relies on Docker.
"""
import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FMRIPREP_IMAGE = "nipreps/fmriprep:latest"

def build_fmriprep_command(
    input_dir: Path,
    output_dir: Path,
    participant_label: Optional[List[str]] = None,
    n_threads: int = 4,
    mem_mb: int = 4000,
    ignore_fields: Optional[List[str]] = None,
    output_spaces: Optional[List[str]] = None,
    force_b0field: bool = False,
    verbose: bool = False
) -> List[str]:
    """
    Construct the docker run command for fMRIPrep.

    Args:
        input_dir: Path to the BIDS dataset root.
        output_dir: Path for fMRIPrep outputs.
        participant_label: List of participant IDs to process (e.g., ['sub-01']).
        n_threads: Number of CPU threads to allocate.
        mem_mb: Memory limit in megabytes.
        ignore_fields: List of processing steps to ignore (e.g., ['slicetiming']).
        output_spaces: List of output spaces (e.g., ['MNI152NLin2009cAsym']).
        force_b0field: If True, forces B0 field map estimation.
        verbose: If True, enable fMRIPrep verbose output.

    Returns:
        List of command arguments for subprocess.run.
    """
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_dir.resolve()}:/input:ro",
        "-v", f"{output_dir.resolve()}:/output",
        "-v", f"{output_dir.resolve()}/work:/work",
        "-e", f"OMP_NUM_THREADS={n_threads}",
        "-e", f"OPENBLAS_NUM_THREADS={n_threads}",
        "-e", f"MKL_NUM_THREADS={n_threads}",
        "-e", f"VECLIB_MAXIMUM_THREADS={n_threads}",
        "-e", f"NUMEXPR_NUM_THREADS={n_threads}",
        "--user", str(os.getuid()),
        "--cpus", str(n_threads),
        "--memory", f"{mem_mb}m",
        FMRIPREP_IMAGE,
        "/input", "/output", "participant"
    ]

    # Add participant label if specified
    if participant_label:
        for label in participant_label:
            cmd.extend(["--participant-label", label])

    # Resource constraints
    cmd.extend(["--nthreads", str(n_threads)])
    cmd.extend(["--mem-mb", str(mem_mb)])

    # Ignore specific fields if requested
    if ignore_fields:
        for field in ignore_fields:
            cmd.extend(["--ignore", field])

    # Output spaces
    if output_spaces:
        for space in output_spaces:
            cmd.extend(["--output-spaces", space])

    # B0 field map enforcement
    if force_b0field:
        cmd.append("--force-b0field")

    # Verbose mode
    if verbose:
        cmd.append("--verbose")

    return cmd

def run_fmriprep(
    input_dir: Path,
    output_dir: Path,
    participant_label: Optional[List[str]] = None,
    n_threads: int = 4,
    mem_mb: int = 4000,
    ignore_fields: Optional[List[str]] = None,
    output_spaces: Optional[List[str]] = None,
    force_b0field: bool = False,
    verbose: bool = False
) -> int:
    """
    Execute the fMRIPrep Docker container.

    Args:
        input_dir: Path to the BIDS dataset root.
        output_dir: Path for fMRIPrep outputs.
        participant_label: List of participant IDs to process.
        n_threads: Number of CPU threads.
        mem_mb: Memory limit in MB.
        ignore_fields: List of steps to ignore.
        output_spaces: List of output spaces.
        force_b0field: Force B0 field map.
        verbose: Enable verbose output.

    Returns:
        Exit code from the subprocess (0 for success).
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input BIDS directory not found: {input_dir}")

    if not output_dir.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_fmriprep_command(
        input_dir=input_dir,
        output_dir=output_dir,
        participant_label=participant_label,
        n_threads=n_threads,
        mem_mb=mem_mb,
        ignore_fields=ignore_fields,
        output_spaces=output_spaces,
        force_b0field=force_b0field,
        verbose=verbose
    )

    logger.info(f"Executing fMRIPrep command:\n{' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"fMRIPrep execution failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        logger.error("Docker is not installed or not found in PATH. "
                     "Please install Docker and ensure it is running.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during fMRIPrep execution: {e}")
        return 1

def main():
    """
    CLI entry point for the CPU fMRIPrep wrapper.
    """
    parser = argparse.ArgumentParser(
        description="CPU-only wrapper for fMRIPrep using Docker."
    )
    parser.add_argument(
        "bids_dir",
        type=Path,
        help="Path to the BIDS dataset root directory."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Path to the directory where outputs will be written."
    )
    parser.add_argument(
        "--participant-label",
        nargs="+",
        help="List of participant IDs to process (e.g., sub-01)."
    )
    parser.add_argument(
        "--n-threads",
        type=int,
        default=4,
        help="Number of CPU threads to use (default: 4)."
    )
    parser.add_argument(
        "--mem-mb",
        type=int,
        default=4000,
        help="Memory limit in megabytes (default: 4000)."
    )
    parser.add_argument(
        "--ignore",
        nargs="+",
        help="List of processing steps to ignore (e.g., slicetiming)."
    )
    parser.add_argument(
        "--output-spaces",
        nargs="+",
        default=["MNI152NLin2009cAsym"],
        help="List of output spaces (default: MNI152NLin2009cAsym)."
    )
    parser.add_argument(
        "--force-b0field",
        action="store_true",
        help="Force B0 field map estimation."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from fMRIPrep."
    )

    args = parser.parse_args()

    exit_code = run_fmriprep(
        input_dir=args.bids_dir,
        output_dir=args.output_dir,
        participant_label=args.participant_label,
        n_threads=args.n_threads,
        mem_mb=args.mem_mb,
        ignore_fields=args.ignore,
        output_spaces=args.output_spaces,
        force_b0field=args.force_b0field,
        verbose=args.verbose
    )

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
