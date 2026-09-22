"""
Task T016c: Verify Validation Report Generation.

This script creates the necessary mock input files (.ingestion_status.json and validation_metrics.yaml)
and runs the generate_validation_report.py script to ensure it executes without errors
and produces a valid YAML output.
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths relative to project root
PROCESSED_DIR = project_root / "data" / "processed"
INGESTION_STATUS_PATH = PROCESSED_DIR / ".ingestion_status.json"
VALIDATION_METRICS_PATH = PROCESSED_DIR / "validation_metrics.yaml"
VALIDATION_REPORT_PATH = PROCESSED_DIR / "validation_report.yaml"
GENERATE_SCRIPT = project_root / "code" / "ingestion" / "generate_validation_report.py"

def setup_mock_inputs():
    """Create mock input files required for T016c verification."""
    logger.info("Setting up mock input files...")
    
    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mock .ingestion_status.json content
    mock_status = {
        "threshold_status": "50<=N<100",
        "exact_N": 78,
        "excluded_count": 12,
        "power_limitation_warning": "N < 100: Statistical power may be limited."
    }
    
    # Mock validation_metrics.yaml content
    mock_metrics = {
        "total_raw_records": 90,
        "passed_threshold_count": 78,
        "failed_threshold_count": 12,
        "pass_rate_percentage": 86.67
    }
    
    # Write mock status
    with open(INGESTION_STATUS_PATH, 'w') as f:
        json.dump(mock_status, f, indent=2)
    logger.info(f"Created mock status file: {INGESTION_STATUS_PATH}")
    
    # Write mock metrics
    with open(VALIDATION_METRICS_PATH, 'w') as f:
        yaml.dump(mock_metrics, f, default_flow_style=False)
    logger.info(f"Created mock metrics file: {VALIDATION_METRICS_PATH}")

def run_generation_script():
    """Execute the generate_validation_report.py script."""
    logger.info("Running generate_validation_report.py...")
    
    if not GENERATE_SCRIPT.exists():
        logger.error(f"Script not found: {GENERATE_SCRIPT}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(GENERATE_SCRIPT)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Script execution failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info("Script execution successful.")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False

def verify_output():
    """Verify that the validation report was created and contains valid YAML."""
    logger.info("Verifying output...")
    
    if not VALIDATION_REPORT_PATH.exists():
        logger.error(f"Output file not found: {VALIDATION_REPORT_PATH}")
        return False
    
    try:
        with open(VALIDATION_REPORT_PATH, 'r') as f:
            report = yaml.safe_load(f)
        
        if not isinstance(report, dict):
            logger.error("Output is not a valid YAML dictionary.")
            return False
        
        # Check required keys
        required_keys = ["status", "count", "excluded_count", "pass_rate_percentage"]
        missing_keys = [k for k in required_keys if k not in report]
        
        if missing_keys:
            logger.error(f"Missing required keys in report: {missing_keys}")
            return False
        
        logger.info(f"Validation report created successfully at {VALIDATION_REPORT_PATH}")
        logger.info(f"Report content: {report}")
        return True
        
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in output file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading output file: {e}")
        return False

def cleanup_mock_inputs():
    """Remove mock input files after verification."""
    logger.info("Cleaning up mock input files...")
    if INGESTION_STATUS_PATH.exists():
        INGESTION_STATUS_PATH.unlink()
    if VALIDATION_METRICS_PATH.exists():
        VALIDATION_METRICS_PATH.unlink()
    # Note: We keep the output file as the artifact of the task

def main():
    """Main entry point for T016c verification."""
    logger.info("Starting T016c: Verify Validation Report Generation")
    
    success = True
    
    try:
        # 1. Setup mock inputs
        setup_mock_inputs()
        
        # 2. Run the generation script
        if not run_generation_script():
            success = False
            logger.error("Script execution failed.")
        
        # 3. Verify output
        elif not verify_output():
            success = False
            logger.error("Output verification failed.")
        
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        success = False
        
    finally:
        # 4. Cleanup (optional, but good practice for test scripts)
        # We comment this out if we want to leave the artifacts for inspection,
        # but for a pure test run, we clean up inputs.
        # cleanup_mock_inputs() 
        pass
    
    if success:
        logger.info("T016c Verification PASSED.")
        sys.exit(0)
    else:
        logger.error("T016c Verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
