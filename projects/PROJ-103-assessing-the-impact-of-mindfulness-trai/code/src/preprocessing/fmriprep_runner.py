"""
fMRIPrep Docker Runner

Executes fMRIPrep preprocessing within a Docker container with CPU and memory constraints.
Reads configuration from src/config/settings.py and environment variables from src/config/env.py.
"""
import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config.settings import get_config
from src.config.env import get_data_dir

logger = logging.getLogger(__name__)

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
    preprocessing_params = config.get('preprocessing_params', {})
    
    # Extract thread/memory limits from config or defaults
    # These are expected to be set in the main config for resource management
    return {
        'omp_num_threads': int(os.getenv('OMP_NUM_THREADS', '4')),
        'nprocs': int(os.getenv('NPROCS', '4')),
        'mem_mb': int(os.getenv('MEM_MB', '4000')),
        'output_dir': str(get_data_dir() / 'processed' / 'fmriprep'),
        'work_dir': str(get_data_dir() / 'processed' / 'fmriprep' / 'work'),
        'participant_label': None,  # Can be overridden
    }

def build_fmriprep_command(
    dataset_dir: str,
    output_dir: str,
    work_dir: str,
    participant_label: Optional[List[str]] = None,
    skip_bids_validation: bool = False
) -> List[str]:
    """
    Construct the Docker run command for fMRIPrep.
    
    Args:
        dataset_dir: Path to the BIDS dataset directory.
        output_dir: Path to the output directory.
        work_dir: Path to the working directory.
        participant_label: Optional list of participant labels to process.
        skip_bids_validation: If True, skip BIDS validation.
        
    Returns:
        List of command arguments for subprocess.
    """
    config = get_fmriprep_config()
    
    cmd = [
        'docker', 'run', '--rm',
        '-e', f'OMP_NUM_THREADS={config["omp_num_threads"]}',
        '-e', f'NPROCS={config["nprocs"]}',
        '-e', f'MEM_MB={config["mem_mb"]}',
        '-v', f'{dataset_dir}:/data:ro',
        '-v', f'{output_dir}:/out',
        '-v', f'{work_dir}:/work',
        'nipreps/fmriprep:latest',
        '/data', '/out', 'participant',
        '--participant-label', ','.join(participant_label) if participant_label else '',
        '--output-spaces', 'MNI152NLin2009cAsym',
        '--fs-license-file', '/opt/freesurfer/license.txt',
    ]
    
    if config['omp_num_threads'] > 0:
        cmd.extend(['--nthreads', str(config['omp_num_threads'])])
    if config['mem_mb'] > 0:
        cmd.extend(['--mem-mb', str(config['mem_mb'])])
        
    if skip_bids_validation:
        cmd.append('--skip-bids-validation')
        
    # Remove empty participant label argument if not provided
    if '--participant-label' in cmd and cmd[cmd.index('--participant-label') + 1] == '':
        cmd.pop(cmd.index('--participant-label') + 1)
        cmd.pop(cmd.index('--participant-label'))
        
    return cmd

def run_fmriprep(
    dataset_dir: Optional[str] = None,
    participant_label: Optional[List[str]] = None,
    skip_bids_validation: bool = False
) -> subprocess.CompletedProcess:
    """
    Run fMRIPrep via Docker.
    
    Args:
        dataset_dir: Path to BIDS dataset. Defaults to data/raw/bids.
        participant_label: List of subject IDs to process.
        skip_bids_validation: Skip BIDS validation check.
        
    Returns:
        CompletedProcess instance with result details.
        
    Raises:
        FMRIPrepRunnerError: If Docker is not available or command fails.
    """
    if dataset_dir is None:
        data_root = get_data_dir()
        dataset_dir = str(data_root / 'raw' / 'bids')
        
    if not os.path.exists(dataset_dir):
        raise FMRIPrepRunnerError(f"Dataset directory not found: {dataset_dir}")
        
    config = get_fmriprep_config()
    output_dir = config['output_dir']
    work_dir = config['work_dir']
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    
    cmd = build_fmriprep_command(
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        work_dir=work_dir,
        participant_label=participant_label,
        skip_bids_validation=skip_bids_validation
    )
    
    logger.info(f"Running fMRIPrep with command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"fMRIPrep failed with return code {e.returncode}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        raise FMRIPrepRunnerError(f"fMRIPrep execution failed: {e.stderr}")
    except FileNotFoundError:
        raise FMRIPrepRunnerError("Docker executable not found. Please ensure Docker is installed and running.")

def main():
    """Entry point for running fMRIPrep from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run fMRIPrep preprocessing pipeline")
    parser.add_argument(
        '--dataset-dir',
        type=str,
        default=None,
        help="Path to BIDS dataset directory (default: data/raw/bids)"
    )
    parser.add_argument(
        '--participant-label',
        type=str,
        nargs='+',
        default=None,
        help="List of participant labels to process"
    )
    parser.add_argument(
        '--skip-bids-validation',
        action='store_true',
        help="Skip BIDS validation"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_fmriprep(
            dataset_dir=args.dataset_dir,
            participant_label=args.participant_label,
            skip_bids_validation=args.skip_bids_validation
        )
        logger.info("fMRIPrep completed successfully")
        print(result.stdout)
    except FMRIPrepRunnerError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()