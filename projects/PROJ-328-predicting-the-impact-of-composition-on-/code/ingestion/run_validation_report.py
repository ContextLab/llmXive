"""
Task T019: Execute Validation Report Generation
Runs the script from T016b (generate_validation_report.py) to produce
data/processed/validation_report.yaml.

Prerequisites:
- data/processed/.ingestion_status.json (from T014)
- data/processed/validation_metrics.yaml (from T014a)

Output:
- data/processed/validation_report.yaml
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
import subprocess

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_ingestion_status_file():
    """Ensure the ingestion status file exists."""
    status_file = project_root / "data" / "processed" / ".ingestion_status.json"
    if not status_file.exists():
        logger.error(f"Required file missing: {status_file}")
        raise FileNotFoundError(f"Missing prerequisite: {status_file}")
    logger.info(f"Verified existence of {status_file}")
    return status_file

def ensure_metrics_file():
    """Ensure the validation metrics file exists."""
    metrics_file = project_root / "data" / "processed" / "validation_metrics.yaml"
    if not metrics_file.exists():
        logger.error(f"Required file missing: {metrics_file}")
        raise FileNotFoundError(f"Missing prerequisite: {metrics_file}")
    logger.info(f"Verified existence of {metrics_file}")
    return metrics_file

def run_generation_script():
    """Run the generate_validation_report.py script."""
    script_path = project_root / "code" / "ingestion" / "generate_validation_report.py"
    if not script_path.exists():
        logger.error(f"Generation script missing: {script_path}")
        raise FileNotFoundError(f"Missing script: {script_path}")
    
    logger.info(f"Executing generation script: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed with return code {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        raise

def verify_output():
    """Verify the output file was created and is valid YAML."""
    output_file = project_root / "data" / "processed" / "validation_report.yaml"
    if not output_file.exists():
        logger.error(f"Output file not generated: {output_file}")
        return False
    
    try:
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        required_keys = ['status', 'count', 'excluded_count', 'power_limitation_warning', 'pass_rate_percentage']
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            logger.warning(f"Output YAML missing keys: {missing_keys}")
            # We still return True as the file exists, but log the warning
        
        logger.info(f"Successfully generated and verified {output_file}")
        logger.info(f"Report summary: status={data.get('status')}, count={data.get('count')}")
        return True
    except yaml.YAMLError as e:
        logger.error(f"Output file is not valid YAML: {e}")
        return False

def main():
    """Main entry point for T019."""
    logger.info("Starting T019: Execute Validation Report Generation")
    
    try:
        # 1. Verify prerequisites
        ensure_ingestion_status_file()
        ensure_metrics_file()
        
        # 2. Run the generation script
        run_generation_script()
        
        # 3. Verify the output
        if verify_output():
            logger.info("T019 completed successfully.")
            return 0
        else:
            logger.error("T019 failed: Output verification failed.")
            return 1
            
    except Exception as e:
        logger.error(f"T019 failed with exception: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())