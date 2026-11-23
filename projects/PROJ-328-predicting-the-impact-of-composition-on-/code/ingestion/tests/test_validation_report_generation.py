"""
T016c: Verify Validation Report Generation (Integration Test).

This script runs the `code/ingestion/generate_validation_report.py` script
using the ACTUAL output files produced by T014 and T014a.

It does NOT use mock data. It expects:
- data/processed/.ingestion_status.json (from T014)
- data/processed/validation_metrics.yaml (from T014a)

If the script fails or produces invalid YAML, it will raise an error.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
import subprocess
import shutil
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
project_root = Path(__file__).resolve().parents[3]
processed_dir = project_root / "data" / "processed"
status_file = processed_dir / ".ingestion_status.json"
metrics_file = processed_dir / "validation_metrics.yaml"
report_file = processed_dir / "validation_report.yaml"
script_path = project_root / "code" / "ingestion" / "generate_validation_report.py"

def check_prerequisites():
    """Check if required input files exist."""
    logger.info("Checking prerequisites...")
    
    if not status_file.exists():
        logger.error(f"Required input file missing: {status_file}")
        logger.error("T014 (validator.py) must run successfully before this test.")
        return False
    
    if not metrics_file.exists():
        logger.error(f"Required input file missing: {metrics_file}")
        logger.error("T014a (validation_metrics.py) must run successfully before this test.")
        return False
    
    logger.info("Prerequisites met.")
    return True

def validate_ingestion_status():
    """Validate the structure of the ingestion status file."""
    logger.info("Validating ingestion status structure...")
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        required_keys = ["threshold_status", "exact_N", "excluded_count", "reduced_n_flag"]
        missing_keys = [k for k in required_keys if k not in status]
        
        if missing_keys:
            logger.error(f"Ingestion status missing required keys: {missing_keys}")
            return False
        
        # Validate types
        if not isinstance(status["exact_N"], int):
            logger.error(f"exact_N must be an integer, got {type(status['exact_N'])}")
            return False
        
        if not isinstance(status["threshold_status"], str):
            logger.error(f"threshold_status must be a string, got {type(status['threshold_status'])}")
            return False
        
        logger.info("Ingestion status structure is valid.")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ingestion status JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating ingestion status: {e}")
        return False

def validate_validation_metrics():
    """Validate the structure of the validation metrics file."""
    logger.info("Validating validation metrics structure...")
    try:
        with open(metrics_file, 'r') as f:
            metrics = yaml.safe_load(f)
        
        required_keys = ["total_raw_records", "passed_threshold_count", "failed_threshold_count", "pass_rate_percentage"]
        missing_keys = [k for k in required_keys if k not in metrics]
        
        if missing_keys:
            logger.error(f"Validation metrics missing required keys: {missing_keys}")
            return False
        
        # Validate types
        if not isinstance(metrics["total_raw_records"], int):
            logger.error(f"total_raw_records must be an integer, got {type(metrics['total_raw_records'])}")
            return False
        
        if not isinstance(metrics["pass_rate_percentage"], (int, float)):
            logger.error(f"pass_rate_percentage must be a number, got {type(metrics['pass_rate_percentage'])}")
            return False
        
        logger.info("Validation metrics structure is valid.")
        return True
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse validation metrics YAML: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating validation metrics: {e}")
        return False

def run_generation_script():
    """Run the generate_validation_report.py script."""
    logger.info(f"Running generation script: {script_path}")
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Script execution failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info("Script execution completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running script: {e}")
        return False

def validate_output_report():
    """Validate the generated validation report."""
    logger.info("Validating generated report...")
    
    if not report_file.exists():
        logger.error(f"Output report file not created: {report_file}")
        return False
    
    try:
        with open(report_file, 'r') as f:
            report = yaml.safe_load(f)
        
        required_keys = ["status", "count", "excluded_count", "pass_rate_percentage"]
        missing_keys = [k for k in required_keys if k not in report]
        
        if missing_keys:
            logger.error(f"Report missing required keys: {missing_keys}")
            return False
        
        # Validate consistency with inputs
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        if report["status"] != status["threshold_status"]:
            logger.error(f"Report status mismatch: {report['status']} != {status['threshold_status']}")
            return False
        
        if report["count"] != status["exact_N"]:
            logger.error(f"Report count mismatch: {report['count']} != {status['exact_N']}")
            return False
        
        if report["excluded_count"] != status["excluded_count"]:
            logger.error(f"Report excluded_count mismatch: {report['excluded_count']} != {status['excluded_count']}")
            return False
        
        with open(metrics_file, 'r') as f:
            metrics = yaml.safe_load(f)
        
        if abs(report["pass_rate_percentage"] - metrics["pass_rate_percentage"]) > 0.01:
            logger.error(f"Report pass_rate_percentage mismatch: {report['pass_rate_percentage']} != {metrics['pass_rate_percentage']}")
            return False
        
        logger.info("Report validation passed.")
        return True
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse generated report YAML: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating report: {e}")
        return False

def main():
    """Main entry point for T016c."""
    logger.info("Starting T016c: Verify Validation Report Generation (Integration Test)")
    
    success = True
    
    if not check_prerequisites():
        success = False
    elif not validate_ingestion_status():
        success = False
    elif not validate_validation_metrics():
        success = False
    elif not run_generation_script():
        success = False
    elif not validate_output_report():
        success = False
    
    if success:
        logger.info("T016c PASSED: Validation report generation verified successfully.")
        return 0
    else:
        logger.error("T016c FAILED: One or more verification steps failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())