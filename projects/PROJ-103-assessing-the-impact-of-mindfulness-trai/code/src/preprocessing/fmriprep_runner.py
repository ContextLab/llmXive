import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config.env import get_data_dir
from src.config.settings import get_config

logger = logging.getLogger(__name__)

class FMRIPrepRunnerError(Exception):
    """Custom exception for fMRIPrep runner errors."""
    pass

def get_fmriprep_config() -> Dict[str, Any]:
    """
    Retrieve fMRIPrep-specific configuration from the global settings.
    
    Returns:
        Dict containing thread and memory configuration settings.
    """
    config = get_config()
    
    # Extract preprocessing parameters which should contain resource constraints
    preprocessing_params = config.get('preprocessing_params', {})
    
    # Default resource constraints if not specified
    # These are CPU-limited settings suitable for CI/CD environments
    return {
        'omp_num_threads': preprocessing_params.get('omp_num_threads', 2),
        'mem_mb': preprocessing_params.get('mem_mb', 2048),
        'nprocs': preprocessing_params.get('nprocs', 2),
        'use_plugin': preprocessing_params.get('use_plugin', 'single'),
        'plugin_args': preprocessing_params.get('plugin_args', {})
    }

def build_fmriprep_command(
    dataset_path: Path,
    output_dir: Path,
    participant_label: Optional[str] = None,
    skip_bids_validation: bool = False
) -> List[str]:
    """
    Build the fMRIPrep Docker command with appropriate thread and memory settings.
    
    Args:
        dataset_path: Path to the BIDS dataset directory
        output_dir: Path to the output directory
        participant_label: Optional single participant label to process
        skip_bids_validation: Whether to skip BIDS validation
        
    Returns:
        List of command arguments for subprocess
    """
    if not dataset_path.exists():
        raise FMRIPrepRunnerError(f"Dataset path does not exist: {dataset_path}")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = get_fmriprep_config()
    
    # Build the command list
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{dataset_path}:/data:ro",
        "-v", f"{output_dir}:/output",
        "-v", "/tmp:/tmp",
        "-e", f"OMP_NUM_THREADS={config['omp_num_threads']}",
        "-e", f"MEM_MB={config['mem_mb']}",
        "--ulimit", f"memlock={config['mem_mb']}M",
        "--ulimit", f"as={config['mem_mb']}M",
        "--workdir", "/tmp",
        "nipreps/fmriprep:23.1.3",
        "/data",
        "/output",
        "participant",
        f"--participant-label={participant_label}" if participant_label else "",
        "--nthreads", str(config['omp_num_threads']),
        "--mem-mb", str(config['mem_mb']),
        "--omp-nthreads", str(config['omp_num_threads']),
        "-w", "/tmp/work",
        "--fs-no-reconall",
        "--use-syn-sdc",
        "--ignore", "fieldmaps"
    ]
    
    if skip_bids_validation:
        cmd.append("--skip-bids-validation")
        
    # Filter out empty strings
    cmd = [arg for arg in cmd if arg]
    
    logger.info(f"Built fMRIPrep command: {' '.join(cmd[:5])} ...")
    return cmd

def run_fmriprep(
    dataset_id: str,
    participant_label: Optional[str] = None,
    skip_bids_validation: bool = False
) -> subprocess.CompletedProcess:
    """
    Execute fMRIPrep preprocessing for a dataset using Docker.
    
    This function:
    1. Resolves dataset paths from environment configuration
    2. Builds the Docker command with CPU-limited settings
    3. Executes the preprocessing pipeline
    4. Logs progress and handles errors
    
    Args:
        dataset_id: The OpenNeuro dataset identifier (e.g., 'ds000001')
        participant_label: Optional single participant to process
        skip_bids_validation: Whether to skip BIDS validation checks
        
    Returns:
        CompletedProcess instance with return code and output
        
    Raises:
        FMRIPrepRunnerError: If Docker is not available or command fails
    """
    data_dir = get_data_dir()
    raw_dir = Path(data_dir) / "raw"
    processed_dir = Path(data_dir) / "processed"
    
    dataset_path = raw_dir / dataset_id
    output_dir = processed_dir / dataset_id / "fmriprep"
    
    if not dataset_path.exists():
        raise FMRIPrepRunnerError(
            f"Dataset not found at {dataset_path}. "
            f"Please run download_datasets.py first."
        )
        
    try:
        cmd = build_fmriprep_command(
            dataset_path=dataset_path,
            output_dir=output_dir,
            participant_label=participant_label,
            skip_bids_validation=skip_bids_validation
        )
        
        logger.info(f"Starting fMRIPrep for {dataset_id}...")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout for CI environments
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"fMRIPrep failed for {dataset_id}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise FMRIPrepRunnerError(
                f"fMRIPrep failed with return code {result.returncode}. "
                f"Check logs for details."
            )
            
        logger.info(f"fMRIPrep completed successfully for {dataset_id}")
        return result
        
    except FileNotFoundError:
        raise FMRIPrepRunnerError(
            "Docker executable not found. Please ensure Docker is installed and running."
        )
    except subprocess.TimeoutExpired:
        raise FMRIPrepRunnerError(
            f"fMRIPrep timed out after 2 hours for {dataset_id}. "
            "Consider increasing timeout or reducing dataset size."
        )

def main():
    """
    Main entry point for running fMRIPrep preprocessing.
    
    Expects dataset_id as a command-line argument.
    If no argument is provided, processes all downloaded datasets.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        logger.info("Usage: python fmriprep_runner.py <dataset_id> [participant_label]")
        logger.info("Example: python fmriprep_runner.py ds000001 sub-01")
        sys.exit(1)
        
    dataset_id = sys.argv[1]
    participant_label = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        run_fmriprep(
            dataset_id=dataset_id,
            participant_label=participant_label,
            skip_bids_validation=False
        )
        logger.info("Preprocessing pipeline completed successfully.")
    except FMRIPrepRunnerError as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
