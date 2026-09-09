"""
fMRIPrep Docker Runner

Executes the fMRIPrep container with configuration derived from project settings.
Handles thread/memory constraints and output directory mapping.
"""
import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config.env import get_data_dir, get_config

logger = logging.getLogger(__name__)


class FMRIPrepRunnerError(Exception):
    """Custom exception for fMRIPrep runner failures."""
    pass


def get_fmriprep_config() -> Dict[str, Any]:
    """
    Retrieve fMRIPrep specific configuration from the global settings.
    
    Returns:
        Dict containing thread_count, memory_gb, and other relevant params.
    """
    config = get_config()
    
    # Default to safe values for CI/runner environments if not specified
    # but ensure they align with the project's preprocessing_params if available
    base_config = config.get('preprocessing_params', {})
    
    return {
        'thread_count': base_config.get('thread_count', 4),
        'memory_gb': base_config.get('memory_gb', 8),
        'fmriprep_version': base_config.get('fmriprep_version', '23.1.0'),
        'participant_label': base_config.get('participant_label', None),
        'nprocs': base_config.get('nprocs', 4),
        'omp_nthreads': base_config.get('omp_nthreads', 4),
    }


def build_fmriprep_command(
    dataset_path: Path,
    output_dir: Path,
    analysis_level: str = 'participant',
    participant_label: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Construct the docker run command for fMRIPrep.
    
    Args:
        dataset_path: Path to the BIDS dataset root.
        output_dir: Path to the output directory.
        analysis_level: 'participant', 'group', or 'report'.
        participant_label: Optional list of subject labels to process.
        config: Optional config dict overriding defaults.
    
    Returns:
        List of command line arguments.
    """
    if config is None:
        config = get_fmriprep_config()
    
    thread_count = config['thread_count']
    memory_gb = config['memory_gb']
    fmriprep_version = config['fmriprep_version']
    
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{dataset_path}:{dataset_path}:ro',
        '-v', f'{output_dir}:{output_dir}',
        '-v', '/tmp:/tmp',  # For temporary files
        '--env', 'OMP_NUM_THREADS={}'.format(config['omp_nthreads']),
        '--env', 'OPENBLAS_NUM_THREADS={}'.format(config['nprocs']),
        '--env', 'MKL_NUM_THREADS={}'.format(config['nprocs']),
        '--env', 'VECLIB_MAXIMUM_THREADS={}'.format(config['nprocs']),
        '--env', 'NUMEXPR_NUM_THREADS={}'.format(config['nprocs']),
        '-u', '{}:{}'.format(os.getuid(), os.getgid()),
        '--name', 'fmriprep_{}'.format(os.getpid()),
        'nipreps/fmriprep:{}'.format(fmriprep_version),
        str(dataset_path),
        'participant',
        '--output-spaces', 'MNI152NLin2009cAsym',
        '--fs-no-reconall',
        '--nprocs', str(config['nprocs']),
        '--omp-nthreads', str(config['omp_nthreads']),
        '--mem', '{}MB'.format(int(memory_gb * 1024)),
        '--use-aroma',
        '--md-only-boilerplate',
    ]
    
    if participant_label:
        for label in participant_label:
            cmd.extend(['--participant-label', label])
    
    cmd.append('--level')
    cmd.append(analysis_level)
    
    return cmd


def run_fmriprep(
    dataset_id: str,
    participant_labels: Optional[List[str]] = None,
    analysis_level: str = 'participant'
) -> subprocess.CompletedProcess:
    """
    Execute the fMRIPrep pipeline for a given dataset.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001').
        participant_labels: Specific subjects to process.
        analysis_level: 'participant', 'group', or 'report'.
    
    Returns:
        CompletedProcess instance with returncode and output.
    
    Raises:
        FMRIPrepRunnerError: If Docker is not found or the command fails.
    """
    data_dir = get_data_dir()
    dataset_root = Path(data_dir) / 'raw' / dataset_id
    output_root = Path(data_dir) / 'processed' / dataset_id
    
    if not dataset_root.exists():
        raise FMRIPrepRunnerError(
            f"Dataset path not found: {dataset_root}. "
            "Ensure datasets are downloaded first."
        )
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    config = get_fmriprep_config()
    cmd = build_fmriprep_command(
        dataset_path=dataset_root,
        output_dir=output_root,
        analysis_level=analysis_level,
        participant_label=participant_labels,
        config=config
    )
    
    logger.info(f"Executing fMRIPrep for {dataset_id}...")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # We handle errors manually to log them
        )
        
        if result.returncode != 0:
            logger.error(f"fMRIPrep failed for {dataset_id}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise FMRIPrepRunnerError(
                f"fMRIPrep failed with code {result.returncode}. "
                "Check logs for details."
            )
        
        logger.info(f"fMRIPrep completed successfully for {dataset_id}")
        return result
        
    except FileNotFoundError:
        raise FMRIPrepRunnerError(
            "Docker executable not found. Please ensure Docker is installed "
            "and running on this system."
        )
    except Exception as e:
        raise FMRIPrepRunnerError(f"Unexpected error running fMRIPrep: {e}")


def main():
    """
    CLI entry point for running fMRIPrep.
    Expects a dataset ID as the first argument.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.preprocessing.fmriprep_runner <dataset_id> [subject_id]")
        sys.exit(1)
    
    dataset_id = sys.argv[1]
    subjects = sys.argv[2:] if len(sys.argv) > 2 else None
    
    try:
        run_fmriprep(
            dataset_id=dataset_id,
            participant_labels=subjects,
            analysis_level='participant'
        )
        print(f"Successfully processed {dataset_id}")
    except FMRIPrepRunnerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
