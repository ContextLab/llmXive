import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_dirs, DataConfig, TrainingConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def run_command(cmd: list, description: str = "") -> bool:
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def run_stage(stage_name: str, script_path: str, args: list = None) -> bool:
    """Run a specific stage script."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    return run_command(cmd, stage_name)

def count_rows(file_path: str) -> int:
    """Count rows in a CSV file."""
    if not os.path.exists(file_path):
        return 0
    with open(file_path, 'r') as f:
        return sum(1 for _ in f) - 1  # Exclude header

def run_full_pipeline(max_configs: int = None):
    """Execute the full pipeline from ingestion to final report."""
    ensure_dirs()
    
    stages = [
        ("Schema Check", "code/data/schema_check.py"),
        ("Schema Validation", "code/data/schema_validate.py"),
        ("Download Data", "code/data/download.py"),
        ("Initialize Exclusion Log", "code/data/init_exclusion_log.py"),
        ("Map Columns", "code/data/mapping.py"),
        ("Clean and Filter", "code/data/clean.py"),
        ("Compute Descriptors", "code/data/descriptors.py"),
        ("Validate Exclusion Schema", "code/data/validate_exclusion_schema.py"),
        ("Aggregate Exclusion Report", "code/data/exclusion_report.py"),
        ("Finalize Dataset", "code/data/finalize_dataset.py"),
        ("Split Dataset", "code/data/split.py"),
        ("Train Model", "code/models/train.py", []),
        ("Evaluate Model", "code/models/evaluate.py"),
        ("Interpret Results", "code/analysis/interpret.py"),
        ("Collinearity Analysis", "code/analysis/collinearity.py"),
        ("Sensitivity Analysis", "code/analysis/sensitivity_runner.py"),
        ("Hyperparameter Sensitivity", "code/analysis/hyperparameter_sensitivity.py"),
        ("Consistency Analysis", "code/analysis/consistency.py"),
        ("Generate Reports", "code/analysis/generate_reports.py"),
        ("Final Validation", "code/data/final_validation.py"),
        ("Generate Final Report", "code/analysis/final_report.py"),
    ]

    # Handle max_configs for training stage
    for i, stage in enumerate(stages):
        if stage[1] == "code/models/train.py":
            if max_configs:
                stages[i] = ("Train Model", "code/models/train.py", ["--max-configs", str(max_configs)])
            break

    success = True
    for stage_info in stages:
        stage_name = stage_info[0]
        script_path = stage_info[1]
        args = stage_info[2] if len(stage_info) > 2 else None

        if not run_stage(stage_name, script_path, args):
            logger.error(f"Stage failed: {stage_name}")
            success = False
            break

    if success:
        logger.info("Pipeline completed successfully")
    else:
        logger.error("Pipeline failed")

    return success

def setup_logging_pipeline():
    """Setup logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def main():
    parser = argparse.ArgumentParser(description="Run the full SN1 rate constant prediction pipeline")
    parser.add_argument("--max-configs", type=int, default=None,
                      help="Maximum number of hyperparameter configurations for training")
    args = parser.parse_args()

    log_file = setup_logging_pipeline()
    logger.info(f"Logging to: {log_file}")
    logger.info("Starting full pipeline execution")

    success = run_full_pipeline(args.max_configs)

    if success:
        logger.info("Full pipeline completed successfully")
        sys.exit(0)
    else:
        logger.error("Full pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
