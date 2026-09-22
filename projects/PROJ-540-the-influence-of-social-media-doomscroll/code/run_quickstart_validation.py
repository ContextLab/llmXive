import os
import sys
import logging
import json
from pathlib import Path
from config import load_config, ensure_directories, set_seed, log_seed_status

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"VAL: {message}")

def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    exists = file_path.exists()
    _log_step(f"Checking if {file_path} exists: {exists}")
    return exists

def check_file_not_empty(file_path: Path) -> bool:
    """Check if a file is not empty."""
    if not file_path.exists():
        return False
    size = file_path.stat().st_size
    _log_step(f"Checking if {file_path} is not empty: size={size}")
    return size > 0

def run_validation() -> bool:
    """Run validation checks on generated outputs."""
    _log_step("Running quickstart validation")
    
    files_to_check = [
        Path("outputs/regression_results.json"),
        Path("outputs/correlation_results.json"),
        Path("outputs/robustness_results.json"),
        Path("outputs/final_report.md"),
        Path("outputs/plot.png"),
        Path("outputs/robustness_comparison.png")
    ]
    
    all_pass = True
    for file_path in files_to_check:
        if not check_file_exists(file_path):
            logger.error(f"Validation failed: {file_path} does not exist")
            all_pass = False
        elif not check_file_not_empty(file_path):
            logger.error(f"Validation failed: {file_path} is empty")
            all_pass = False
        else:
            logger.info(f"Validation passed: {file_path}")
    
    return all_pass

def main() -> None:
    """Main entry point for quickstart validation script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    # Set seed
    seed = config.get("seed", 42)
    set_seed(seed)
    log_seed_status(seed)
    
    success = run_validation()
    if success:
        logger.info("Quickstart validation completed successfully")
    else:
        logger.error("Quickstart validation failed")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
