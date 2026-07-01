"""
fMRIPrep Docker Runner

Executes fMRIPrep via Docker with CPU-limited thread and memory constraints
as defined in docker/fmriprep.Dockerfile and project configuration.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config.env import get_data_dir, get_config


class FMRIPrepRunnerError(Exception):
    """Custom exception for fMRIPrep runner errors."""
    pass


def get_fmriprep_config() -> Dict[str, Any]:
    """
    Retrieve fMRIPrep specific configuration from settings.
    
    Returns:
        Dict containing thread and memory constraints.
    """
    config = get_config()
    preprocessing_params = config.get("preprocessing_params", {})
    
    # Default constraints if not explicitly set in config
    # These align with docker/fmriprep.Dockerfile CPU-limited settings
    return {
        "nthreads": preprocessing_params.get("nthreads", 2),
        "mem_mb": preprocessing_params.get("mem_mb", 2048),
        "omp_nthreads": preprocessing_params.get("omp_nthreads", 2),
        "smoothing_fwhm": preprocessing_params.get("smoothing_mm", 6),
    }


def build_fmriprep_command(
    dataset_id: str,
    subject_id: str,
    output_dir: Path,
    config: Dict[str, Any]
) -> List[str]:
    """
    Build the fMRIPrep Docker command with resource constraints.
    
    Args:
        dataset_id: OpenNeuro dataset identifier (e.g., 'ds000001')
        subject_id: Subject identifier (e.g., 'sub-01')
        output_dir: Directory for fMRIPrep outputs
        config: Configuration dictionary with thread/memory settings
        
    Returns:
        List of command arguments for subprocess execution
    """
    data_dir = get_data_dir()
    raw_dir = Path(data_dir) / "raw"
    
    # Construct paths
    dataset_path = raw_dir / dataset_id
    if not dataset_path.exists():
        raise FMRIPrepRunnerError(
            f"Dataset path does not exist: {dataset_path}"
        )
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # fMRIPrep Docker command
    # Using --nthreads and --omp-nthreads for CPU limits
    # Using --mem-mb for memory limits
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{raw_dir}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", f"{output_dir}/work:/work",
        "--name", f"fmriprep_{dataset_id}_{subject_id}",
        "--gpus", "all",  # Optional: enable GPU if available
        "nipreps/fmriprep:latest",  # Using latest stable version
        "/data", "/out", "participant",
        "--participant-label", subject_id,
        "--skip-bids-validation",  # Assume validation passed earlier
        "--nthreads", str(config["nthreads"]),
        "--omp-nthreads", str(config["omp_nthreads"]),
        "--mem-mb", str(config["mem_mb"]),
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-license-file", "/opt/freesurfer/license.txt",  # If using FreeSurfer
        "--verbose",
    ]
    
    # Add smoothing if specified in config
    if config.get("smoothing_fwhm"):
        cmd.extend(["--smooth", str(config["smoothing_fwhm"])])
        
    return cmd


def run_fmriprep(
    dataset_id: str,
    subject_id: str,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Execute fMRIPrep for a specific subject in a dataset.
    
    Args:
        dataset_id: OpenNeuro dataset identifier
        subject_id: Subject identifier
        output_dir: Optional custom output directory
        
    Returns:
        Dict with execution status and output paths
        
    Raises:
        FMRIPrepRunnerError: If Docker is not available or execution fails
    """
    config = get_fmriprep_config()
    
    if output_dir is None:
        data_dir = get_data_dir()
        output_dir = Path(data_dir) / "processed" / dataset_id / subject_id
        
    try:
        cmd = build_fmriprep_command(
            dataset_id, subject_id, output_dir, config
        )
        
        # Execute the command
        print(f"Running fMRIPrep for {dataset_id}/{subject_id}...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verify output exists
        participant_dir = output_dir / "sub-" + subject_id
        if not participant_dir.exists():
            raise FMRIPrepRunnerError(
                f"fMRIPrep output not found: {participant_dir}"
            )
        
        return {
            "status": "success",
            "output_dir": str(output_dir),
            "dataset_id": dataset_id,
            "subject_id": subject_id,
            "command_executed": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.CalledProcessError as e:
        raise FMRIPrepRunnerError(
            f"fMRIPrep execution failed: {e.stderr}"
        ) from e
    except FileNotFoundError as e:
        raise FMRIPrepRunnerError(
            f"Docker not found. Please install Docker: {e}"
        ) from e
    except Exception as e:
        raise FMRIPrepRunnerError(
            f"Unexpected error during fMRIPrep execution: {str(e)}"
        ) from e


def main():
    """
    Main entry point for command-line execution.
    
    Usage:
        python -m src.preprocessing.fmriprep_runner --dataset ds000001 --subject sub-01
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run fMRIPrep preprocessing for a specific subject"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="OpenNeuro dataset ID (e.g., ds000001)"
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Subject ID (e.g., sub-01)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional custom output directory"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_fmriprep(
            dataset_id=args.dataset,
            subject_id=args.subject,
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        print(f"Success: {result['output_dir']}")
        sys.exit(0)
    except FMRIPrepRunnerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()