"""
T042: Quickstart Validation Script

This script validates the project's quickstart functionality by:
1. Checking the existence of required files (README.md, quickstart.md, requirements.txt)
2. Verifying the project structure (code/, data/, tests/, contracts/)
3. Attempting to import core modules to ensure dependencies are met
4. Running a dry-run of the main pipeline with synthetic data
5. Validating output artifacts are generated correctly
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"✓ {description}: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def check_directory_exists(path: Path, description: str) -> bool:
    """Check if a directory exists and log the result."""
    if path.exists() and path.is_dir():
        logger.info(f"✓ {description}: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def validate_project_structure() -> bool:
    """Validate the project directory structure."""
    logger.info("Validating project structure...")
    root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        (root / "code", "code directory"),
        (root / "data", "data directory"),
        (root / "tests", "tests directory"),
        (root / "contracts", "contracts directory"),
        (root / "specs", "specs directory"),
    ]
    
    all_exist = True
    for dir_path, description in required_dirs:
        if not check_directory_exists(dir_path, description):
            all_exist = False
    
    return all_exist

def validate_required_files() -> bool:
    """Validate required project files exist."""
    logger.info("Validating required files...")
    root = Path(__file__).parent.parent.parent
    
    required_files = [
        (root / "README.md", "README.md"),
        (root / "quickstart.md", "quickstart.md"),
        (root / "requirements.txt", "requirements.txt"),
        (root / "tasks.md", "tasks.md"),
        (root / "plan.md", "plan.md"),
    ]
    
    all_exist = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def validate_dependencies() -> bool:
    """Validate that required dependencies can be imported."""
    logger.info("Validating dependencies...")
    
    required_imports = [
        ("rdkit", "RDKit"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("sklearn", "scikit-learn"),
        ("yaml", "PyYAML"),
        ("pytest", "pytest"),
    ]
    
    all_importable = True
    for module, description in required_imports:
        try:
            __import__(module)
            logger.info(f"✓ {description} importable")
        except ImportError as e:
            logger.error(f"✗ {description} import failed: {e}")
            all_importable = False
    
    return all_importable

def validate_core_modules() -> bool:
    """Validate that core modules can be imported."""
    logger.info("Validating core modules...")
    
    # Add code directory to path
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root))
    
    required_modules = [
        ("main", "main orchestrator"),
        ("data.descriptors", "descriptors module"),
        ("data.preprocess", "preprocess module"),
        ("data.download", "download module"),
        ("data.synthetic_gen", "synthetic_gen module"),
        ("models.train", "train module"),
        ("models.evaluate", "evaluate module"),
        ("interpret.shap_analysis", "shap_analysis module"),
    ]
    
    all_importable = True
    for module, description in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ {description} importable")
        except ImportError as e:
            logger.error(f"✗ {description} import failed: {e}")
            all_importable = False
    
    return all_importable

def run_synthetic_pipeline() -> bool:
    """Run the synthetic data pipeline as a quickstart validation."""
    logger.info("Running synthetic pipeline validation...")
    
    root = Path(__file__).parent.parent
    main_script = root / "main.py"
    
    if not main_script.exists():
        logger.error("main.py not found")
        return False
    
    try:
        # Run with synthetic mode
        result = subprocess.run(
            [sys.executable, str(main_script), "--mode", "synthetic"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ Synthetic pipeline completed successfully")
            return True
        else:
            logger.error(f"✗ Synthetic pipeline failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("✗ Synthetic pipeline timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Error running synthetic pipeline: {e}")
        return False

def validate_output_artifacts() -> bool:
    """Validate that expected output artifacts were generated."""
    logger.info("Validating output artifacts...")
    root = Path(__file__).parent.parent.parent
    
    required_artifacts = [
        (root / "data" / "raw" / "synthetic_data.csv", "Synthetic raw data"),
        (root / "data" / "processed" / "cleaned_data.csv", "Cleaned processed data"),
        (root / "data" / "processed" / "outliers.csv", "Outliers file"),
        (root / "data" / "models" / "best_model.pkl", "Best model"),
        (root / "data" / "evaluation" / "metrics.json", "Evaluation metrics"),
        (root / "data" / "validation" / "sc002_match_report.json", "SC-002 match report"),
        (root / "data" / "validation" / "sc003_r2_report.json", "SC-003 R² report"),
    ]
    
    all_exist = True
    for artifact_path, description in required_artifacts:
        if not check_file_exists(artifact_path, description):
            all_exist = False
    
    return all_exist

def main():
    """Main validation function."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T042)")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    validation_results = {
        "project_structure": validate_project_structure(),
        "required_files": validate_required_files(),
        "dependencies": validate_dependencies(),
        "core_modules": validate_core_modules(),
        "synthetic_pipeline": run_synthetic_pipeline(),
        "output_artifacts": validate_output_artifacts(),
    }
    
    logger.info("=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    
    all_passed = True
    for check, passed in validation_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{check}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ ALL VALIDATIONS PASSED")
        logger.info("Quickstart validation successful!")
        return 0
    else:
        logger.error("✗ SOME VALIDATIONS FAILED")
        logger.error("Please review the errors above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())