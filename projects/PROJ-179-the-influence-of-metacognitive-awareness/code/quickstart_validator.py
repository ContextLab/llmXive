"""
T034: Quickstart Validation Script

Validates end-to-end reproducibility by executing the pipeline stages
defined in quickstart.md and verifying expected outputs are generated.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"

# Expected output artifacts from the pipeline
EXPECTED_ARTIFACTS = {
    "data/validation_report.json": ["status"],
    "data/derived/trial_data.csv": ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"],
    "data/results/bootstrap_config.json": ["bootstrap_count"],
    "data/results/primary_analysis.json": ["correlation_r", "p_value", "ci_lower", "ci_upper"],
    "data/results/regression_analysis.json": ["r_squared", "adjusted_r_squared", "f_change", "p_change"],
    "data/results/robustness_analysis.json": ["visual_correlation", "auditory_correlation"]
}

def check_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    if not path.exists():
        logger.error(f"Missing expected artifact: {path}")
        return False
    logger.info(f"Found artifact: {path}")
    return True

def validate_json_structure(path: Path, required_keys: List[str]) -> bool:
    """Validate that a JSON file contains required keys."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            logger.error(f"Missing keys in {path}: {missing}")
            return False
        logger.info(f"Validated JSON structure for {path}")
        return True
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return False

def validate_csv_columns(path: Path, required_columns: List[str]) -> bool:
    """Validate that a CSV file contains required columns."""
    try:
        import pandas as pd
        df = pd.read_csv(path)
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.error(f"Missing columns in {path}: {missing}")
            return False
        logger.info(f"Validated CSV structure for {path}")
        return True
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return False

def run_pipeline_stage(stage_name: str, script_path: Path) -> bool:
    """Run a specific pipeline stage."""
    logger.info(f"Running pipeline stage: {stage_name}")
    try:
        # Ensure we are in the project root
        os.chdir(PROJECT_ROOT)
        
        # Construct command
        cmd = [sys.executable, str(script_path)]
        
        # Run with timeout (6 hours in seconds)
        start_time = time.time()
        result = subprocess.run(
            cmd,
            timeout=21600,  # 6 hours
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"Stage {stage_name} failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info(f"Stage {stage_name} completed in {elapsed:.2f}s")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Stage {stage_name} timed out after 6 hours")
        return False
    except Exception as e:
        logger.error(f"Error running stage {stage_name}: {e}")
        return False

def run_validation() -> bool:
    """Run the full validation pipeline."""
    logger.info("Starting quickstart validation...")
    
    # Define pipeline stages in execution order
    pipeline_stages = [
        ("Data Availability Check", CODE_DIR / "data" / "validate_data_availability.py"),
        ("Data Download", CODE_DIR / "data" / "download.py"),
        ("Data Validation", CODE_DIR / "data" / "validate_data.py"),
        ("Preprocessing", CODE_DIR / "data" / "preprocess.py"),
        ("Correlation Analysis", CODE_DIR / "src" / "analysis" / "correlation.py"),
        ("Bootstrap Analysis", CODE_DIR / "src" / "analysis" / "bootstrap.py"),
        ("Regression Analysis", CODE_DIR / "src" / "analysis" / "regression.py"),
        ("Modality Filtering", CODE_DIR / "src" / "analysis" / "filter.py"),
        ("Robustness Analysis", CODE_DIR / "src" / "analysis" / "robustness.py"),
        ("Report Generation", CODE_DIR / "src" / "report" / "generate.py"),
        ("Disjoint Trials Validation", CODE_DIR / "data" / "validate_disjoint_trials.py")
    ]
    
    # Run each stage
    for stage_name, script_path in pipeline_stages:
        if not script_path.exists():
            logger.warning(f"Script not found: {script_path}, skipping stage {stage_name}")
            continue
        
        if not run_pipeline_stage(stage_name, script_path):
            logger.error(f"Pipeline failed at stage: {stage_name}")
            return False
    
    # Validate all expected artifacts
    logger.info("Validating output artifacts...")
    all_valid = True
    
    for artifact_path, required_keys in EXPECTED_ARTIFACTS.items():
        full_path = PROJECT_ROOT / artifact_path
        
        if not check_file_exists(full_path):
            all_valid = False
            continue
        
        if artifact_path.endswith('.json'):
            if not validate_json_structure(full_path, required_keys):
                all_valid = False
        elif artifact_path.endswith('.csv'):
            if not validate_csv_columns(full_path, required_keys):
                all_valid = False
    
    if all_valid:
        logger.info("Quickstart validation PASSED: All stages completed and artifacts validated.")
        return True
    else:
        logger.error("Quickstart validation FAILED: Some artifacts missing or invalid.")
        return False

def main():
    """Main entry point."""
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
