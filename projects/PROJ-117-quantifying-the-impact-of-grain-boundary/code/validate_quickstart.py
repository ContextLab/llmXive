import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directory_structure():
    """Verify required project directories exist."""
    required_dirs = [
        'code',
        'data/raw',
        'data/processed',
        'models',
        'artifacts/reports',
        'artifacts/figures',
        'tests/unit',
        'tests/integration'
    ]
    missing = []
    for d in required_dirs:
        if not Path(d).exists():
            missing.append(d)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("Directory structure validated successfully.")
    return True

def check_required_files():
    """Verify required configuration and metadata files exist."""
    required_files = [
        'config.yaml',
        'data/metadata.yaml',
        'requirements.txt',
        '.env.example',
        'README.md',
        'tasks.md',
        'specs/001-grain-boundary-diffusivity/spec.md'
    ]
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Missing required files: {missing}")
        return False
    
    logger.info("Required files validated successfully.")
    return True

def check_dependencies():
    """Verify required Python packages are installed."""
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 'xgboost', 'shap', 
        'matplotlib', 'requests', 'pymatgen', 'python-dotenv',
        'ruff', 'black'
    ]
    missing = []
    
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"Missing Python packages: {missing}")
        return False
    
    logger.info("Dependencies validated successfully.")
    return True

def check_pipeline_scripts():
    """Verify all pipeline scripts exist and are syntactically valid."""
    scripts = [
        'code/download.py',
        'code/geometry_parser.py',
        'code/preprocess.py',
        'code/diagnostics.py',
        'code/train.py',
        'code/validate.py',
        'code/interpret.py'
    ]
    missing = []
    
    for script in scripts:
        path = Path(script)
        if not path.exists():
            missing.append(script)
            continue
        
        # Check syntax
        try:
            compile(path.read_text(), str(path), 'exec')
        except SyntaxError as e:
            logger.error(f"Syntax error in {script}: {e}")
            return False
    
    if missing:
        logger.error(f"Missing pipeline scripts: {missing}")
        return False
    
    logger.info("Pipeline scripts validated successfully.")
    return True

def run_pipeline_step(script_name, step_name):
    """Execute a specific pipeline step and verify it completes."""
    logger.info(f"Running {step_name}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"{step_name} failed with return code {result.returncode}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            return False
        
        logger.info(f"{step_name} completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"{step_name} timed out after 300 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running {step_name}: {e}")
        return False

def check_output_artifacts():
    """Verify that pipeline outputs were created."""
    # Check for model artifact
    model_path = Path('models/best_model.json')
    if not model_path.exists():
        logger.error("Model artifact not found: models/best_model.json")
        return False
    
    # Check for training metrics
    metrics_path = Path('artifacts/reports/training_metrics.json')
    if not metrics_path.exists():
        logger.error("Training metrics not found: artifacts/reports/training_metrics.json")
        return False
    
    # Check for validation report
    validation_path = Path('artifacts/reports/validation_report.json')
    if not validation_path.exists():
        logger.error("Validation report not found: artifacts/reports/validation_report.json")
        return False
    
    # Check for sensitivity table
    sensitivity_path = Path('artifacts/reports/threshold-sensitivity-table.csv')
    if not sensitivity_path.exists():
        logger.error("Sensitivity table not found: artifacts/reports/threshold-sensitivity-table.csv")
        return False
    
    logger.info("Output artifacts validated successfully.")
    return True

def validate_output_content():
    """Validate the content of key output artifacts."""
    # Validate training metrics
    metrics_path = Path('artifacts/reports/training_metrics.json')
    try:
        with open(metrics_path) as f:
            metrics = json.load(f)
        
        required_keys = ['r2', 'rmse', 'mape']
        missing_keys = [k for k in required_keys if k not in metrics]
        
        if missing_keys:
            logger.error(f"Missing keys in training metrics: {missing_keys}")
            return False
        
        if metrics['r2'] < 0.7:
            logger.warning(f"Model R² ({metrics['r2']}) is below threshold (0.7)")
        
    except Exception as e:
        logger.error(f"Error validating training metrics: {e}")
        return False
    
    # Validate validation report
    validation_path = Path('artifacts/reports/validation_report.json')
    try:
        with open(validation_path) as f:
            report = json.load(f)
        
        required_keys = ['cv_r2_mean', 'cv_r2_std', 'bias_test_results']
        missing_keys = [k for k in required_keys if k not in report]
        
        if missing_keys:
            logger.error(f"Missing keys in validation report: {missing_keys}")
            return False
        
        if report['cv_r2_std'] > 0.05:
            logger.warning(f"Cross-validation R² std ({report['cv_r2_std']}) exceeds threshold (0.05)")
        
    except Exception as e:
        logger.error(f"Error validating validation report: {e}")
        return False
    
    logger.info("Output content validated successfully.")
    return True

def main():
    """Main validation function for quickstart.md."""
    logger.info("Starting quickstart validation...")
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_required_files),
        ("Dependencies", check_dependencies),
        ("Pipeline Scripts", check_pipeline_scripts),
    ]
    
    for name, check_func in checks:
        if not check_func():
            logger.error(f"Validation FAILED at {name}")
            return 1
    
    # Check if we need to run the pipeline or just validate outputs
    model_exists = Path('models/best_model.json').exists()
    
    if not model_exists:
        logger.info("Model not found. Running full pipeline...")
        
        # Run download (may fail if no data available, which is expected)
        if not run_pipeline_step('code/download.py', "Download"):
            logger.warning("Download step failed (expected if no data available)")
        
        # Run geometry parsing
        if not run_pipeline_step('code/geometry_parser.py', "Geometry Parsing"):
            logger.error("Geometry parsing failed")
            return 1
        
        # Run preprocessing
        if not run_pipeline_step('code/preprocess.py', "Preprocessing"):
            logger.error("Preprocessing failed")
            return 1
        
        # Run diagnostics
        if not run_pipeline_step('code/diagnostics.py', "Diagnostics"):
            logger.error("Diagnostics failed")
            return 1
        
        # Run training
        if not run_pipeline_step('code/train.py', "Training"):
            logger.error("Training failed")
            return 1
        
        # Run validation
        if not run_pipeline_step('code/validate.py', "Validation"):
            logger.error("Validation failed")
            return 1
        
        # Run interpretability
        if not run_pipeline_step('code/interpret.py', "Interpretability"):
            logger.error("Interpretability failed")
            return 1
    else:
        logger.info("Model found. Skipping pipeline execution.")
    
    # Final artifact checks
    if not check_output_artifacts():
        logger.error("Output artifact validation FAILED")
        return 1
    
    if not validate_output_content():
        logger.error("Output content validation FAILED")
        return 1
    
    logger.info("Quickstart validation PASSED")
    return 0

if __name__ == '__main__':
    sys.exit(main())