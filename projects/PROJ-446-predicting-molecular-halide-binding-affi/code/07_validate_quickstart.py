"""
Task T038: Validate quickstart.md reproducibility.

This script executes the steps outlined in docs/quickstart.md to ensure
the project setup and pipeline are reproducible. It verifies:
1. Directory structure exists.
2. Python environment and dependencies are valid.
3. The data pipeline (T012-T017) can run (producing data/processed/halide_binding_data.csv).
4. The model training (T018-T022) can run (producing data/processed/model_runs.json).
5. The feature analysis (T023-T027) can run (producing data/processed/feature_analysis.json).
6. The statistical reporting (T028-T032) can run (producing docs/paper/report.md).

If any step fails, it logs the error and exits with a non-zero status.
"""

import os
import sys
import subprocess
import logging
import json
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'docs' / 'quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_directory_structure():
    """Verify required directories exist."""
    logger.info("Checking directory structure...")
    required_dirs = [
        "code", "code/utils",
        "data", "data/raw", "data/processed", "data/simulated",
        "docs", "docs/paper", "docs/paper/figures"
    ]
    missing = []
    for d in required_dirs:
        if not (project_root / d).exists():
            missing.append(d)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("Directory structure verified.")
    return True

def check_dependencies():
    """Verify Python environment and dependencies."""
    logger.info("Checking dependencies...")
    try:
        # Check for requirements.txt
        req_file = project_root / "code" / "requirements.txt"
        if not req_file.exists():
            logger.error("requirements.txt not found at code/requirements.txt")
            return False

        # Attempt to import key libraries
        libs = ['pandas', 'numpy', 'sklearn', 'rdkit', 'requests', 'bs4', 'yaml']
        for lib in libs:
            try:
                __import__(lib)
            except ImportError:
                logger.error(f"Missing dependency: {lib}")
                return False
        
        logger.info("Dependencies verified.")
        return True
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        return False

def run_script(script_name, description):
    """Execute a specific script module and verify it completes."""
    logger.info(f"Running {description} ({script_name})...")
    start_time = time.time()
    try:
        # Import the module's main function if it exists
        module_name = script_name.replace('.py', '')
        # Adjust path for import
        if module_name.startswith('0'):
            full_module_path = f"code.{module_name}"
        else:
            full_module_path = f"code.utils.{module_name}"
        
        try:
            module = __import__(full_module_path, fromlist=['main'])
        except ImportError:
            # Fallback: try direct import if path structure is different
            try:
                module = __import__(f"code.{module_name}", fromlist=['main'])
            except ImportError:
                logger.error(f"Could not import module: {module_name}")
                return False

        if not hasattr(module, 'main'):
            logger.warning(f"Module {module_name} has no 'main' function, attempting direct execution logic if available.")
            # If no main, we might need to just run the file as a script
            # But for reproducibility, we expect a main function or a clear entry point
            # For this validation, we assume the script can be run via python -m or similar
            # Let's try running it as a subprocess to be safe
            result = subprocess.run(
                [sys.executable, str(project_root / "code" / script_name)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"Script {script_name} failed:\n{result.stderr}")
                return False
        else:
            # Run the main function
            try:
                module.main()
            except SystemExit as e:
                if e.code != 0:
                    logger.error(f"Script {script_name} exited with code {e.code}")
                    return False
            except Exception as e:
                logger.error(f"Script {script_name} raised exception: {e}")
                return False

        duration = time.time() - start_time
        logger.info(f"{description} completed in {duration:.2f}s.")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"{description} timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False

def verify_outputs():
    """Verify that expected output files were created."""
    logger.info("Verifying output artifacts...")
    expected_files = [
        "data/processed/halide_binding_data.csv",
        "data/processed/model_runs.json",
        "data/processed/feature_analysis.json",
        "docs/paper/report.md"
    ]
    
    missing = []
    for f in expected_files:
        if not (project_root / f).exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Missing expected outputs: {missing}")
        return False
    
    logger.info("All expected outputs found.")
    return True

def main():
    logger.info("Starting Quickstart Validation (T038)...")
    
    # Step 1: Check structure
    if not check_directory_structure():
        return False

    # Step 2: Check dependencies
    if not check_dependencies():
        return False

    # Step 3: Run Data Pipeline (T012-T017)
    # Assuming 01_data_ingestion.py and 02_save_processed_data.py handle this
    if not run_script("01_data_ingestion.py", "Data Ingestion Pipeline"):
        return False
    if not run_script("02_save_processed_data.py", "Save Processed Data"):
        return False

    # Step 4: Run Model Training (T018-T022)
    if not run_script("03_model_training.py", "Model Training"):
        return False

    # Step 5: Run Feature Analysis (T023-T027)
    if not run_script("04_feature_analysis.py", "Feature Analysis"):
        return False
    if not run_script("05_feature_summary.py", "Feature Summary"):
        return False
    if not run_script("06_save_feature_outputs.py", "Save Feature Outputs"):
        return False

    # Step 6: Run Statistical Reporting (T028-T032)
    if not run_script("05_statistical_reporting.py", "Statistical Reporting"):
        return False
    if not run_script("06_generate_final_report.py", "Generate Final Report"):
        return False

    # Step 7: Verify Outputs
    if not verify_outputs():
        return False

    logger.info("Quickstart validation PASSED. Project is reproducible.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)