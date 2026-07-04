"""
T047: Quickstart validation script.
Executes the full pipeline end-to-end to ensure reproducibility.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Add project root to path if running from subdirectory
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_name: str, description: str) -> bool:
    """Execute a pipeline script and return success status."""
    logger.info(f"Running {description}: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, str(project_root / script_name)],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run {script_name}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Script not found: {script_name}")
        return False

def validate_outputs() -> bool:
    """Verify that all expected output files exist."""
    config = get_config()
    expected_files = [
        config['paths']['raw_data'],
        config['paths']['cleaned_data'],
        config['paths']['engineered_data'],
        config['paths']['model_results'],
        config['paths']['validity_metrics'],
        config['paths']['modeling_log'],
        config['paths']['report_pdf'],
        config['paths']['figures']['roc_plot']
    ]

    missing_files = []
    for file_path in expected_files:
        full_path = Path(project_root) / file_path
        if not full_path.exists():
            missing_files.append(str(full_path))
            logger.error(f"Missing output file: {full_path}")
        else:
            logger.info(f"Found output file: {full_path}")

    return len(missing_files) == 0

def main():
    logger.info("Starting Quickstart Validation (T047)")
    logger.info("=" * 50)

    config = get_config()
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Random Seed: {config['random_seed']}")

    # Step 1: Generate synthetic data (if real data not available)
    success = run_script(
        "00_generate_synthetic_data.py",
        "Data Generation"
    )
    if not success:
        logger.error("Data generation failed. Aborting validation.")
        return 1

    # Step 2: Download and clean data
    success = run_script(
        "01_download_data.py",
        "Data Download"
    )
    if not success:
        logger.error("Data download failed. Aborting validation.")
        return 1

    # Step 3: Clean data
    success = run_script(
        "02_clean_data.py",
        "Data Cleaning"
    )
    if not success:
        logger.error("Data cleaning failed. Aborting validation.")
        return 1

    # Step 4: Engineer features
    success = run_script(
        "03_engineer_features.py",
        "Feature Engineering"
    )
    if not success:
        logger.error("Feature engineering failed. Aborting validation.")
        return 1

    # Step 5: Model analysis
    success = run_script(
        "04_model_analysis.py",
        "Model Analysis"
    )
    if not success:
        logger.error("Model analysis failed. Aborting validation.")
        return 1

    # Step 6: Generate report
    success = run_script(
        "05_generate_report.py",
        "Report Generation"
    )
    if not success:
        logger.error("Report generation failed. Aborting validation.")
        return 1

    # Step 7: Finalize results
    success = run_script(
        "06_finalize_results.py",
        "Result Finalization"
    )
    if not success:
        logger.error("Result finalization failed. Aborting validation.")
        return 1

    # Validate all outputs exist
    logger.info("Validating output files...")
    if not validate_outputs():
        logger.error("Output validation failed. Some expected files are missing.")
        return 1

    logger.info("=" * 50)
    logger.info("Quickstart validation PASSED successfully!")
    logger.info("All pipeline steps executed and outputs generated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
