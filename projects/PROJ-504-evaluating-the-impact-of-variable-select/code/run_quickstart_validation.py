"""
Task T048: Run quickstart.md validation.

This script validates the project state against the expected outputs
defined in the quickstart and task specifications. It verifies:
1. Directory structure exists (T001, T005)
2. Required configuration files exist (T002, T003, T007)
3. Simulation results integrity (T020, T054)
4. API surface imports (T008, T024-T026, T027-T030)

It exits with code 0 on success, 1 on failure.
"""
from __future__ import annotations

import sys
import os
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from quickstart_validator import (
    check_directories,
    check_files,
    check_simulation_results_integrity,
    check_imports,
    main as validator_main
)
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

def run_validation() -> bool:
    """
    Execute the full validation suite for the project.
    Returns True if all checks pass, False otherwise.
    """
    logger.info("Starting Quickstart Validation (T048)...")
    
    # 1. Check Directory Structure
    logger.info("Checking directory structure...")
    if not check_directories():
        logger.error("Directory structure check failed.")
        return False
    
    # 2. Check Required Files
    logger.info("Checking required files (config, requirements, etc.)...")
    if not check_files():
        logger.error("Required files check failed.")
        return False
    
    # 3. Check Simulation Results Integrity
    logger.info("Checking simulation results integrity...")
    if not check_simulation_results_integrity():
        logger.error("Simulation results integrity check failed.")
        return False
    
    # 4. Check API Surface Imports
    logger.info("Verifying API surface imports...")
    if not check_imports():
        logger.error("API surface import check failed.")
        return False
    
    logger.info("All validation checks passed successfully.")
    return True

def main():
    """Entry point for the validation script."""
    setup_logging(level=logging.INFO, log_file="results/validation.log")
    
    success = run_validation()
    
    if success:
        logger.info("Validation Complete: SUCCESS")
        sys.exit(0)
    else:
        logger.error("Validation Complete: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
