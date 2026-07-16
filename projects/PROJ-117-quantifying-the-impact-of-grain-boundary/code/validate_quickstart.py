import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('artifacts/reports/quickstart_validation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Ensure logging is configured."""
    return logger

def check_directory_structure() -> bool:
    """Verify required directory structure exists."""
    required_dirs = [
        'code', 'data', 'data/raw', 'data/processed',
        'models', 'artifacts', 'artifacts/figures', 'artifacts/reports',
        'tests', 'tests/unit', 'tests/integration'
    ]
    missing = []
    for d in required_dirs:
        if not Path(d).exists():
            missing.append(d)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("Directory structure verified.")
    return True

def check_required_files() -> bool:
    """Verify required configuration and data files exist."""
    required_files = [
        'config.yaml', 'requirements.txt', 'metadata.yaml',
        'data/metadata.yaml', 'models/best_model.json',
        'data/processed/cleaned_dataset.parquet',
        'artifacts/reports/training_metrics.json',
        'artifacts/reports/validation_report.json'
    ]
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Missing required files: {missing}")
        return False
    
    logger.info("Required files verified.")
    return True

def check_dependencies() -> bool:
    """Verify critical dependencies are installed."""
    critical_packages = [
        'pandas', 'numpy', 'scikit-learn', 'xgboost', 
        'shap', 'matplotlib', 'pymatgen', 'psutil'
    ]
    missing = []
    for pkg in critical_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"Missing dependencies: {missing}")
        return False
    
    logger.info("Dependencies verified.")
    return True

def check_pipeline_scripts() -> bool:
    """Verify all pipeline scripts exist and are syntactically valid."""
    scripts = [
        'code/download.py', 'code/geometry_parser.py', 'code/preprocess.py',
        'code/diagnostics.py', 'code/train.py', 'code/validate.py',
        'code/interpret.py', 'code/data_streamer.py'
    ]
    missing_or_invalid = []
    
    for script in scripts:
        path = Path(script)
        if not path.exists():
            missing_or_invalid.append(f"{script} (missing)")
            continue
        
        # Check syntax
        try:
            with open(path, 'r') as f:
                compile(f.read(), path, 'exec')
        except SyntaxError as e:
            missing_or_invalid.append(f"{script} (syntax error: {e})")
    
    if missing_or_invalid:
        logger.error(f"Invalid pipeline scripts: {missing_or_invalid}")
        return False
    
    logger.info("Pipeline scripts verified.")
    return True

def run_pipeline_step(step_name: str, script_path: str) -> bool:
    """Run a specific pipeline step and check for success."""
    logger.info(f"Running pipeline step: {step_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per step
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            logger.info(f"Step {step_name} completed successfully.")
            return True
        else:
            logger.error(f"Step {step_name} failed with return code {result.returncode}")
            logger.error(f"Stdout: {result.stdout}")
            logger.error(f"Stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Step {step_name} timed out after 300 seconds")
        return False
    except Exception as e:
        logger.error(f"Step {step_name} raised exception: {str(e)}")
        return False

def check_output_artifacts() -> bool:
    """Verify that pipeline execution produced expected output artifacts."""
    expected_artifacts = [
        ('data/raw/', '.cif', 'CIF files'),
        ('data/processed/', '.parquet', 'Parquet files'),
        ('models/', '.json', 'Model files'),
        ('artifacts/reports/', '.json', 'Report files'),
        ('artifacts/figures/', '.png', 'Figure files')
    ]
    
    missing = []
    for base, ext, desc in expected_artifacts:
        base_path = Path(base)
        if not base_path.exists():
            missing.append(f"{base} (directory missing)")
            continue
        
        files = list(base_path.glob(f'*{ext}'))
        if not files:
            missing.append(f"{base} (no {desc} found)")
    
    if missing:
        logger.error(f"Missing output artifacts: {missing}")
        return False
    
    logger.info("Output artifacts verified.")
    return True

def validate_output_content() -> bool:
    """Validate content of key output files."""
    # Validate training metrics
    metrics_path = Path('artifacts/reports/training_metrics.json')
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            required_keys = ['r2', 'rmse', 'mape']
            missing_keys = [k for k in required_keys if k not in metrics]
            if missing_keys:
                logger.error(f"training_metrics.json missing keys: {missing_keys}")
                return False
            
            # Check R2 is within valid range
            r2 = metrics.get('r2')
            if r2 is not None and not (0 <= r2 <= 1):
                logger.warning(f"R2 value {r2} outside expected range [0, 1]")
            
            logger.info("Training metrics validated.")
        except Exception as e:
            logger.error(f"Error validating training_metrics.json: {str(e)}")
            return False
    else:
        logger.error("training_metrics.json not found")
        return False
    
    # Validate validation report
    val_path = Path('artifacts/reports/validation_report.json')
    if val_path.exists():
        try:
            with open(val_path, 'r') as f:
                val_report = json.load(f)
            
            required_keys = ['cv_r2_mean', 'cv_r2_std', 'bias_test_results']
            missing_keys = [k for k in required_keys if k not in val_report]
            if missing_keys:
                logger.error(f"validation_report.json missing keys: {missing_keys}")
                return False
            
            logger.info("Validation report validated.")
        except Exception as e:
            logger.error(f"Error validating validation_report.json: {str(e)}")
            return False
    else:
        logger.error("validation_report.json not found")
        return False
    
    return True

def main():
    """Run comprehensive quickstart validation."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)
    
    all_passed = True
    
    # Step 1: Directory structure
    if not check_directory_structure():
        all_passed = False
    
    # Step 2: Required files
    if not check_required_files():
        all_passed = False
    
    # Step 3: Dependencies
    if not check_dependencies():
        all_passed = False
    
    # Step 4: Pipeline scripts
    if not check_pipeline_scripts():
        all_passed = False
    
    # Step 5: Run pipeline steps (optional if artifacts exist)
    # Only run if we want to verify end-to-end execution
    # For validation, we check if artifacts exist and are valid
    
    # Step 6: Output artifacts
    if not check_output_artifacts():
        all_passed = False
    
    # Step 7: Content validation
    if not validate_output_content():
        all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("Quickstart validation PASSED")
        logger.info("All checks completed successfully.")
    else:
        logger.error("Quickstart validation FAILED")
        logger.error("One or more checks did not pass.")
    logger.info("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
