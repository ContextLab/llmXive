import os
import sys
import logging
import json
from pathlib import Path
from config import load_config, ensure_directories, set_seed, log_seed_status

# Configure logging for the validation run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('outputs/validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists at the given path."""
    exists = filepath.exists()
    if exists:
        logger.info(f"CHECK: File exists: {filepath}")
    else:
        logger.error(f"CHECK FAILED: File missing: {filepath}")
    return exists

def check_file_not_empty(filepath: Path) -> bool:
    """Check if a file exists and is not empty."""
    if not filepath.exists():
        logger.error(f"CHECK FAILED: File missing (cannot check size): {filepath}")
        return False
    
    size = filepath.stat().st_size
    is_not_empty = size > 0
    if is_not_empty:
        logger.info(f"CHECK: File not empty ({size} bytes): {filepath}")
    else:
        logger.error(f"CHECK FAILED: File is empty: {filepath}")
    return is_not_empty

def run_validation(config: dict) -> dict:
    """
    Run the quickstart validation checks as defined in the project plan.
    Validates that all expected output artifacts from the pipeline exist and are non-empty.
    """
    logger.info("Starting Quickstart Validation Run...")
    
    # Load seed and ensure directories
    set_seed(config.get('seed'))
    log_seed_status()
    ensure_directories()

    results = {
        "status": "passed",
        "checks": [],
        "errors": []
    }

    # Define expected output artifacts based on tasks T013, T021, T022, T027, T029, T030, T022b, T029b
    expected_files = [
        ("data/processed/analysis_data.csv", "Cleaned dataset (T013)"),
        ("outputs/regression_results.json", "Regression results (T021)"),
        ("outputs/correlation_results.json", "Correlation results (T022)"),
        ("outputs/robustness_results.json", "Robustness results (T027)"),
        ("outputs/plot.png", "Main scatter plot (T029)"),
        ("outputs/final_report.md", "Final report (T030)"),
        ("outputs/diagnostics_residuals.png", "Residuals plot (T022b)"),
        ("outputs/diagnostics_qq.png", "Q-Q plot (T022b)"),
        ("outputs/robustness_comparison.png", "Robustness comparison plot (T029b)")
    ]

    all_passed = True

    for filepath_str, description in expected_files:
        filepath = Path(filepath_str)
        exists = check_file_exists(filepath)
        not_empty = check_file_not_empty(filepath) if exists else False
        
        check_result = {
            "file": str(filepath),
            "description": description,
            "exists": exists,
            "not_empty": not_empty,
            "status": "passed" if (exists and not_empty) else "failed"
        }
        
        results["checks"].append(check_result)
        
        if not (exists and not_empty):
            all_passed = False
            error_msg = f"Validation failed for {description}: {filepath}"
            if not exists:
                error_msg += " (File missing)"
            else:
                error_msg += " (File empty)"
            results["errors"].append(error_msg)
            logger.error(error_msg)

    results["status"] = "passed" if all_passed else "failed"
    
    # Save validation report
    report_path = Path("outputs/validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation Report saved to {report_path}")
    logger.info(f"Overall Status: {results['status'].upper()}")
    
    return results

def main():
    """Main entry point for the quickstart validation."""
    try:
        config = load_config()
        results = run_validation(config)
        
        if results["status"] == "failed":
            logger.error("Quickstart validation FAILED. See logs for details.")
            sys.exit(1)
        else:
            logger.info("Quickstart validation PASSED.")
            sys.exit(0)
    except Exception as e:
        logger.exception(f"Validation run crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
