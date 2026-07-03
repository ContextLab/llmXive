"""
Quickstart Validation Script for PROJ-117.

This script validates the project setup and pipeline execution by:
1. Checking required files and directories exist.
2. Verifying dependencies are installed.
3. Running the full pipeline (download -> preprocess -> train -> validate -> interpret).
4. Checking that expected output artifacts are generated.

Usage:
    python code/validate_quickstart.py
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
EXPECTED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "models",
    "artifacts/reports",
    "artifacts/figures",
    "tests",
    "specs"
]

EXPECTED_FILES = [
    "requirements.txt",
    "README.md",
    "quickstart.md",
    "data/metadata.yaml",
    ".env.example"
]

PIPELINE_SCRIPTS = [
    "code/download.py",
    "code/geometry_parser.py",
    "code/preprocess.py",
    "code/diagnostics.py",
    "code/train.py",
    "code/validate.py",
    "code/interpret.py"
]

EXPECTED_OUTPUTS = [
    "data/processed/parsed_geometry.parquet",
    "data/processed/cleaned_dataset.parquet",
    "models/best_model.json",
    "artifacts/reports/training_metrics.json",
    "artifacts/reports/validation_report.json",
    "artifacts/reports/collinearity_diagnostic.json",
    "artifacts/figures/shap_summary.png",
    "artifacts/reports/threshold-variation-table.csv"
]

def check_directory_structure() -> Tuple[bool, List[str]]:
    """Check if all required directories exist."""
    missing_dirs = []
    for dir_path in EXPECTED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.error(f"Missing directories: {missing_dirs}")
        return False, missing_dirs
    
    logger.info("✓ All required directories exist")
    return True, []

def check_required_files() -> Tuple[bool, List[str]]:
    """Check if all required files exist."""
    missing_files = []
    for file_path in EXPECTED_FILES:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing files: {missing_files}")
        return False, missing_files
    
    logger.info("✓ All required files exist")
    return True, []

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required dependencies are installed."""
    try:
        import pandas
        import numpy
        import sklearn
        import xgboost
        import shap
        import matplotlib
        import requests
        import pymatgen
        import pyarrow
        import python_dotenv
        logger.info("✓ All required dependencies are installed")
        return True, []
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False, [str(e)]

def check_pipeline_scripts() -> Tuple[bool, List[str]]:
    """Check if all pipeline scripts exist and are syntactically valid."""
    invalid_scripts = []
    
    for script_path in PIPELINE_SCRIPTS:
        full_path = PROJECT_ROOT / script_path
        if not full_path.exists():
            invalid_scripts.append(script_path)
            continue
        
        # Check syntax
        try:
            with open(full_path, 'r') as f:
                compile(f.read(), full_path, 'exec')
        except SyntaxError as e:
            invalid_scripts.append(f"{script_path} (Syntax Error: {e})")
    
    if invalid_scripts:
        logger.error(f"Invalid or missing scripts: {invalid_scripts}")
        return False, invalid_scripts
    
    logger.info("✓ All pipeline scripts exist and are syntactically valid")
    return True, []

def run_pipeline_step(step_name: str, script_path: str) -> Tuple[bool, str]:
    """Run a single pipeline step and return success status and output."""
    logger.info(f"Running {step_name}...")
    
    full_path = PROJECT_ROOT / script_path
    cmd = [sys.executable, str(full_path)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Failed with return code {result.returncode}\nStderr: {result.stderr}\nStdout: {result.stdout}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"✓ {step_name} completed successfully")
        return True, result.stdout
    
    except subprocess.TimeoutExpired:
        error_msg = f"{step_name} timed out after 1 hour"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Exception running {step_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def check_output_artifacts() -> Tuple[bool, List[str]]:
    """Check if all expected output artifacts were generated."""
    missing_outputs = []
    
    for output_path in EXPECTED_OUTPUTS:
        full_path = PROJECT_ROOT / output_path
        if not full_path.exists():
            missing_outputs.append(output_path)
    
    if missing_outputs:
        logger.error(f"Missing output artifacts: {missing_outputs}")
        return False, missing_outputs
    
    logger.info("✓ All expected output artifacts were generated")
    return True, []

def validate_output_content() -> Tuple[bool, str]:
    """Validate the content of key output artifacts."""
    validation_errors = []
    
    # Validate training metrics
    metrics_path = PROJECT_ROOT / "artifacts/reports/training_metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            required_keys = ['r2', 'rmse', 'mape']
            missing_keys = [k for k in required_keys if k not in metrics]
            
            if missing_keys:
                validation_errors.append(f"training_metrics.json missing keys: {missing_keys}")
            else:
                if metrics['r2'] < 0.7:
                    validation_errors.append(f"R² ({metrics['r2']}) is below threshold of 0.7")
        except Exception as e:
            validation_errors.append(f"Error validating training_metrics.json: {str(e)}")
    else:
        validation_errors.append("training_metrics.json not found")
    
    # Validate validation report
    val_report_path = PROJECT_ROOT / "artifacts/reports/validation_report.json"
    if val_report_path.exists():
        try:
            with open(val_report_path, 'r') as f:
                report = json.load(f)
            
            required_keys = ['cv_r2_mean', 'cv_r2_std', 'bias_test_intercept', 'bias_test_slope']
            missing_keys = [k for k in required_keys if k not in report]
            
            if missing_keys:
                validation_errors.append(f"validation_report.json missing keys: {missing_keys}")
            elif report['cv_r2_std'] > 0.05:
                validation_errors.append(f"CV R² std ({report['cv_r2_std']}) exceeds threshold of 0.05")
        except Exception as e:
            validation_errors.append(f"Error validating validation_report.json: {str(e)}")
    else:
        validation_errors.append("validation_report.json not found")
    
    if validation_errors:
        logger.error(f"Output content validation errors: {validation_errors}")
        return False, "; ".join(validation_errors)
    
    logger.info("✓ Output content validation passed")
    return True, "All validations passed"

def main() -> int:
    """Main validation function."""
    logger.info("Starting Quickstart Validation...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    
    all_checks_passed = True
    errors = []
    
    # Phase 1: Check project structure
    logger.info("\n--- Phase 1: Checking Project Structure ---")
    success, missing = check_directory_structure()
    if not success:
        all_checks_passed = False
        errors.extend(missing)
    
    success, missing = check_required_files()
    if not success:
        all_checks_passed = False
        errors.extend(missing)
    
    # Phase 2: Check dependencies
    logger.info("\n--- Phase 2: Checking Dependencies ---")
    success, missing = check_dependencies()
    if not success:
        all_checks_passed = False
        errors.extend(missing)
    
    # Phase 3: Check pipeline scripts
    logger.info("\n--- Phase 3: Checking Pipeline Scripts ---")
    success, invalid = check_pipeline_scripts()
    if not success:
        all_checks_passed = False
        errors.extend(invalid)
    
    if not all_checks_passed:
        logger.error("\n--- Validation FAILED (Pre-execution checks) ---")
        logger.error(f"Errors: {errors}")
        return 1
    
    # Phase 4: Run pipeline (if structure is valid)
    logger.info("\n--- Phase 4: Running Pipeline ---")
    pipeline_steps = [
        ("Data Download", "code/download.py"),
        ("Geometry Parsing", "code/geometry_parser.py"),
        ("Preprocessing", "code/preprocess.py"),
        ("Diagnostics", "code/diagnostics.py"),
        ("Training", "code/train.py"),
        ("Validation", "code/validate.py"),
        ("Interpretation", "code/interpret.py")
    ]
    
    for step_name, script_path in pipeline_steps:
        success, output = run_pipeline_step(step_name, script_path)
        if not success:
            all_checks_passed = False
            errors.append(f"{step_name} failed: {output}")
            # Continue with remaining steps to gather all errors
    
    if not all_checks_passed:
        logger.error("\n--- Validation FAILED (Pipeline execution errors) ---")
        logger.error(f"Errors: {errors}")
        return 1
    
    # Phase 5: Check output artifacts
    logger.info("\n--- Phase 5: Checking Output Artifacts ---")
    success, missing = check_output_artifacts()
    if not success:
        all_checks_passed = False
        errors.extend(missing)
    
    if not all_checks_passed:
        logger.error("\n--- Validation FAILED (Missing artifacts) ---")
        logger.error(f"Errors: {errors}")
        return 1
    
    # Phase 6: Validate output content
    logger.info("\n--- Phase 6: Validating Output Content ---")
    success, msg = validate_output_content()
    if not success:
        all_checks_passed = False
        errors.append(msg)
    
    if not all_checks_passed:
        logger.error("\n--- Validation FAILED (Content validation errors) ---")
        logger.error(f"Errors: {errors}")
        return 1
    
    logger.info("\n" + "="*50)
    logger.info("✓ QUICKSTART VALIDATION PASSED")
    logger.info("="*50)
    logger.info("All checks completed successfully:")
    logger.info("  - Project structure is correct")
    logger.info("  - All dependencies are installed")
    logger.info("  - All pipeline scripts are valid")
    logger.info("  - Pipeline executed successfully")
    logger.info("  - All output artifacts were generated")
    logger.info("  - Output content meets quality thresholds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())