import os
import sys
import logging
import argparse
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_dirs, DataConfig, TrainingConfig, AnalysisConfig
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

# Pipeline stages
STAGES = {
    'schema_check': 'code/data/schema_check.py',
    'download': 'code/data/download.py',
    'mapping': 'code/data/mapping.py',
    'clean': 'code/data/clean.py',
    'descriptors': 'code/data/descriptors.py',
    'exclusion_report': 'code/data/exclusion_report.py',
    'finalize': 'code/data/finalize_dataset.py',
    'split': 'code/data/split.py',
    'train': 'code/models/train.py',
    'evaluate': 'code/models/evaluate.py',
    'interpret': 'code/analysis/interpret.py',
    'sensitivity': 'code/analysis/sensitivity_runner.py',
    'collinearity': 'code/analysis/collinearity.py',
    'consistency': 'code/analysis/consistency.py',
    'hyperparameter_sensitivity': 'code/analysis/hyperparameter_sensitivity.py',
    'final_report': 'code/analysis/final_report.py',
}

def run_command(cmd, stage_name, timeout=None):
    """Run a shell command with optional timeout."""
    logger.info(f"Running stage: {stage_name}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        end_time = time.time()
        duration = end_time - start_time
        
        if result.stdout:
            logger.info(f"Output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Stderr:\n{result.stderr}")
        
        logger.info(f"Stage {stage_name} completed in {duration:.2f}s")
        return True, duration, None
        
    except subprocess.TimeoutExpired:
        logger.error(f"Stage {stage_name} timed out after {timeout}s")
        return False, timeout, "timeout"
    except subprocess.CalledProcessError as e:
        logger.error(f"Stage {stage_name} failed with return code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False, e.returncode, str(e)

def run_stage(stage_name, args):
    """Run a single pipeline stage."""
    if stage_name not in STAGES:
        logger.error(f"Unknown stage: {stage_name}")
        return False, 0, "unknown_stage"
    
    script_path = STAGES[stage_name]
    cmd = [sys.executable, script_path]
    
    # Add specific arguments based on stage
    if stage_name == 'train' and args.max_configs:
        cmd.extend(['--max-configs', str(args.max_configs)])
    
    return run_command(cmd, stage_name, args.timeout)

def count_rows(file_path):
    """Count rows in a CSV file."""
    try:
        with open(file_path, 'r') as f:
            # Count lines minus header
            return sum(1 for _ in f) - 1
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return 0

def run_full_pipeline(args):
    """Run the full pipeline with dynamic budgeting and timeout."""
    start_time = time.time()
    results = {
        'start_time': datetime.now().isoformat(),
        'stages': {},
        'success': False,
        'error': None
    }
    
    # Dynamic Budgeting: Check dataset size
    cleaned_data_path = "data/processed/cleaned_sn1.csv"
    if os.path.exists(cleaned_data_path):
        n_rows = count_rows(cleaned_data_path)
        logger.info(f"Dataset size: {n_rows} rows")
        
        if n_rows >= 2000:
            logger.info("Dataset size >= 2000, reducing hyperparameter search to 20 configurations")
            args.max_configs = 20
        else:
            args.max_configs = 50
    else:
        logger.warning(f"Cleaned data file not found: {cleaned_data_path}. Using default configs.")
        args.max_configs = 50
    
    # Run stages
    failed_stages = []
    for stage_name in STAGES.keys():
        success, duration, error = run_stage(stage_name, args)
        results['stages'][stage_name] = {
            'success': success,
            'duration': duration,
            'error': error
        }
        
        if not success:
            failed_stages.append(stage_name)
            if error == "timeout":
                logger.error(f"Pipeline aborted due to timeout at stage: {stage_name}")
                break
            # Continue to next stage unless critical failure
            # For now, we continue but mark pipeline as failed
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    results['end_time'] = datetime.now().isoformat()
    results['total_duration'] = total_duration
    results['success'] = len(failed_stages) == 0
    
    if not results['success']:
        results['error'] = f"Failed stages: {', '.join(failed_stages)}"
        logger.error(f"Pipeline failed. Failed stages: {', '.join(failed_stages)}")
    else:
        logger.info("Pipeline completed successfully")
    
    return results

def setup_logging_pipeline(log_file=None):
    """Setup logging for the pipeline."""
    if log_file is None:
        log_file = "artifacts/pipeline.log"
    
    ensure_dirs()
    return setup_logging(log_file)

def main():
    parser = argparse.ArgumentParser(description="Run the full SN1 rate constant prediction pipeline")
    parser.add_argument("--timeout", type=int, default=21600, help="Timeout in seconds (default: 6 hours)")
    parser.add_argument("--max-configs", type=int, default=None, help="Maximum hyperparameter configurations (dynamic budgeting)")
    parser.add_argument("--stage", type=str, choices=list(STAGES.keys()), help="Run a specific stage")
    parser.add_argument("--log-file", type=str, default="artifacts/pipeline.log", help="Log file path")
    args = parser.parse_args()

    setup_logging_pipeline(args.log_file)
    ensure_dirs()
    
    if args.stage:
        # Run single stage
        success, duration, error = run_stage(args.stage, args)
        if not success:
            sys.exit(1)
    else:
        # Run full pipeline
        results = run_full_pipeline(args)
        
        # Save feasibility test log
        log_path = "artifacts/feasibility_test_log.json"
        with open(log_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Feasibility test log saved to {log_path}")
        
        if not results['success']:
            logger.error("Pipeline execution failed")
            sys.exit(1)
        else:
            logger.info("Pipeline execution completed successfully")

if __name__ == "__main__":
    main()
