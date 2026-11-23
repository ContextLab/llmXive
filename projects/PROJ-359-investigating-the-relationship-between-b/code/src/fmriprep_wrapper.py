"""
fMRIPrep Docker Execution Wrapper.

This module provides a wrapper to execute fMRIPrep via Docker with strict
resource constraints to fit CI environments (CPU-only, limited RAM).

Constraints (FR-002):
- Memory: 5g (--memory 5g, --mem_mb 4500)
- Processors: 1 (--nprocs 1)
- Docker Image: poldracklab/fmriprep:23.1.3 (pinned in requirements)
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Import shared utilities from existing API
from src.utils import log_event, setup_logging, get_log_path, write_json_log

# fMRIPrep Docker configuration constants
FMRIPREP_IMAGE = "poldracklab/fmriprep:23.1.3"
DOCKER_MEMORY_LIMIT = "5g"
DOCKER_MEM_MB = 4500
DOCKER_NPROCS = 1

# Required Docker flags for CI stability
DOCKER_FLAGS = [
    "--rm",  # Remove container after exit
    "--memory", DOCKER_MEMORY_LIMIT,
    "--mem_mb", str(DOCKER_MEM_MB),
    "--nprocs", str(DOCKER_NPROCS),
    "--userns=host",  # Required for fMRIPrep on some hosts
]

def build_fmriprep_command(
    subject_id: str,
    input_dir: Path,
    output_dir: Path,
    analysis_level: str = "participant",
    ignore_fields: Optional[list] = None,
    fd_thresh: float = 3.0,
) -> list:
    """
    Construct the full fMRIPrep Docker command.

    Args:
        subject_id: The participant ID (e.g., 'sub-01').
        input_dir: Path to the BIDS dataset root.
        output_dir: Path to the output directory.
        analysis_level: 'participant' or 'group'.
        ignore_fields: List of fields to ignore (e.g., 'fieldmaps').
        fd_thresh: Framewise Displacement threshold for exclusion logging.

    Returns:
        A list of command arguments suitable for subprocess.run.
    """
    cmd = ["docker", "run"]
    cmd.extend(DOCKER_FLAGS)

    # Bind mounts
    cmd.extend(["-v", f"{input_dir}:/data:ro"])
    cmd.extend(["-v", f"{output_dir}:/out"])

    # fMRIPrep arguments
    cmd.append(FMRIPREP_IMAGE)
    cmd.append("/data")
    cmd.append("/out")
    cmd.append(analysis_level)

    # Subject-specific flag
    cmd.extend(["--participant-label", subject_id])

    # Standard fMRIPrep flags for this pipeline
    cmd.extend(["--skip-bids-validation"])
    cmd.extend(["--output-spaces", "MNI"])
    cmd.extend(["--fs-license-file", "/opt/freesurfer/license.txt"])

    # Motion control (logging only, filtering happens in preprocess.py)
    cmd.extend(["--fd-spike-threshold", str(fd_thresh)])

    if ignore_fields:
        for field in ignore_fields:
            cmd.extend(["--ignore", field])

    return cmd

def execute_fmriprep(
    subject_id: str,
    input_dir: Path,
    output_dir: Path,
    log_dir: Path,
) -> Dict[str, Any]:
    """
    Execute fMRIPrep for a single subject via Docker.

    This function runs the Docker container with strict memory limits.
    It captures stdout/stderr and logs the result.

    Args:
        subject_id: Participant ID (e.g., 'sub-01').
        input_dir: Path to BIDS dataset.
        output_dir: Path for fMRIPrep outputs.
        log_dir: Directory to write execution logs.

    Returns:
        Dictionary containing execution status and metadata.
    """
    setup_logging()
    log_path = get_log_path("fmriprep_execution.json")
    
    # Ensure output directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = build_fmriprep_command(
        subject_id=subject_id,
        input_dir=input_dir,
        output_dir=output_dir,
    )

    log_event(f"Executing fMRIPrep for {subject_id}", level="INFO")
    log_event(f"Command: {' '.join(cmd)}", level="DEBUG")

    result = {
        "subject_id": subject_id,
        "status": "pending",
        "return_code": None,
        "command": " ".join(cmd),
        "memory_limit": DOCKER_MEMORY_LIMIT,
        "nprocs": DOCKER_NPROCS,
    }

    try:
        # Execute the command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=7200,  # 2 hour timeout per subject
        )

        result["return_code"] = process.returncode
        
        if process.returncode == 0:
            result["status"] = "success"
            log_event(f"fMRIPrep completed successfully for {subject_id}", level="INFO")
        else:
            result["status"] = "failed"
            log_event(f"fMRIPrep failed for {subject_id} with code {process.returncode}", level="ERROR")
            # Log error output for debugging
            if process.stderr:
                log_event(f"Stderr: {process.stderr[:500]}...", level="ERROR")

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["return_code"] = -1
        log_event(f"fMRIPrep timed out for {subject_id}", level="ERROR")
    except FileNotFoundError:
        result["status"] = "docker_not_found"
        result["return_code"] = -2
        log_event("Docker executable not found. Ensure Docker is installed and in PATH.", level="FATAL")
    except Exception as e:
        result["status"] = "error"
        result["error_message"] = str(e)
        log_event(f"Unexpected error during fMRIPrep execution: {e}", level="FATAL")

    # Write result to log
    write_json_log(log_path, result)
    
    return result

def main():
    """
    Main entry point for CLI execution.
    Expects environment variables or arguments for paths.
    """
    # Default paths (can be overridden by env vars or args in a full CLI)
    bids_root = Path(os.getenv("BIDS_ROOT", "data/raw/ds000278"))
    output_root = Path(os.getenv("FMRIPREP_OUTPUT", "data/preprocessed/fmriprep"))
    log_root = Path("data/logs")

    # Check for Docker availability
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Docker is not installed or not in PATH.")
        sys.exit(1)

    # Example: Run for a specific subject if provided, else list subjects
    # This is a simplified entry point; full pipeline integration happens in preprocess.py
    subject_label = os.getenv("PARTICIPANT_LABEL")
    
    if subject_label:
        print(f"Running fMRIPrep for {subject_label}...")
        result = execute_fmriprep(
            subject_id=subject_label,
            input_dir=bids_root,
            output_dir=output_root,
            log_dir=log_root,
        )
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "success" else 1)
    else:
        print("Usage: Set PARTICIPANT_LABEL env var or implement full subject loop.")
        print(f"Example: PARTICIPANT_LABEL=sub-01 python -m src.fmriprep_wrapper")
        sys.exit(0)

if __name__ == "__main__":
    main()
