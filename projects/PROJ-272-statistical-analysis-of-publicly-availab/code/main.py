import logging
import sys
import time
import tracemalloc
from pathlib import Path
import json

from config import get_path, ensure_dirs
from utils import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

def run_command(command: str, description: str = "") -> bool:
    """
    Run a shell command and log its execution.
    
    Args:
        command: The shell command to execute.
        description: Optional description of what the command does.
        
    Returns:
        True if command succeeded, False otherwise.
    """
    if description:
        logger.info(f"Executing: {description}")
    logger.info(f"Command: {command}")
    
    try:
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command completed successfully (return code: {result.returncode})")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return False

def measure_runtime_and_memory(commands: list) -> dict:
    """
    Measure total runtime and peak memory usage for a sequence of commands.
    
    Args:
        commands: List of command dictionaries with 'cmd' and 'description' keys.
        
    Returns:
        Dictionary with runtime and memory metrics.
    """
    tracemalloc.start()
    start_time = time.time()
    
    success = True
    for cmd_info in commands:
        cmd = cmd_info.get('cmd', '')
        desc = cmd_info.get('description', '')
        if not run_command(cmd, desc):
            success = False
            break
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        'total_seconds': end_time - start_time,
        'peak_rss_gb': peak / (1024 * 1024 * 1024),
        'success': success
    }

def save_runtime_metrics(metrics: dict, output_path: str) -> None:
    """
    Save runtime metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing runtime and memory metrics.
        output_path: Path to the output JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved runtime metrics to {output_path}")

def main():
    """
    Main entry point for the pipeline execution.
    
    This function orchestrates the full pipeline:
    1. Data ingestion and preprocessing
    2. Feature extraction
    3. Statistical analysis
    4. Model training and validation
    5. Runtime and memory measurement
    """
    # Setup logging
    setup_logging()
    
    logger.info("Starting the statistical analysis pipeline")
    
    # Define the pipeline commands
    pipeline_commands = [
        {
            'cmd': 'python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv',
            'description': 'Download and preprocess ADReSS dataset'
        },
        {
            'cmd': 'python code/t016_create_cleaned_dataset.py',
            'description': 'Create cleaned dataset file'
        },
        {
            'cmd': 'python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv',
            'description': 'Extract linguistic and semantic features'
        },
        {
            'cmd': 'python code/t024c_checksum.py',
            'description': 'Compute checksum for embeddings'
        },
        {
            'cmd': 'python code/t025_save_features.py',
            'description': 'Save final feature matrix'
        },
        {
            'cmd': 'python code/stats.py --input data/processed/features.csv --output data/results/statistical_metrics.json',
            'description': 'Run statistical analysis with Bonferroni correction'
        },
        {
            'cmd': 'python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json',
            'description': 'Train and validate predictive models'
        },
        {
            'cmd': 'python code/t012f_checksum_record.py',
            'description': 'Record raw data checksums'
        },
        {
            'cmd': 'python code/t012h_success_criterion.py',
            'description': 'Calculate success criterion SC-001'
        }
    ]
    
    # Measure runtime and memory
    metrics = measure_runtime_and_memory(pipeline_commands)
    
    # Save metrics
    runtime_log_path = get_path('results', 'runtime_log.json')
    memory_profile_path = get_path('results', 'memory_profile.json')
    
    save_runtime_metrics(
        {'total_seconds': metrics['total_seconds'], 'success': metrics['success']},
        runtime_log_path
    )
    
    save_runtime_metrics(
        {'peak_rss_gb': metrics['peak_rss_gb'], 'success': metrics['success']},
        memory_profile_path
    )
    
    if metrics['success']:
        logger.info("Pipeline completed successfully")
        logger.info(f"Total runtime: {metrics['total_seconds']:.2f} seconds")
        logger.info(f"Peak memory usage: {metrics['peak_rss_gb']:.2f} GB")
    else:
        logger.error("Pipeline failed during execution")
        sys.exit(1)

if __name__ == '__main__':
    main()
