"""
Startup Runner for Project Initialization and Validation.

This module orchestrates the startup sequence for the application,
ensuring all critical prerequisites are met before the main study
logic begins. It specifically integrates the Latency Calibrator
(FR-003) as mandated by T012a.

Execution Flow:
1. Load Configuration.
2. Run Latency Calibration (Critical Path).
3. Exit with failure if calibration fails.
"""

import sys
import os
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config_manager import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.latency_calibrator import run_calibration

logger = get_logger(__name__)

def run_startup_checks():
    """
    Executes all mandatory startup checks.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("Starting Application Initialization Sequence")
    logger.info("=" * 60)

    # 1. Configuration Validation
    try:
        logger.info("Step 1: Validating environment configuration...")
        config = get_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Configuration validation failed: {e}")
        return False

    # 2. Latency Calibration (FR-003)
    # This is the specific integration mandated by T012a.
    logger.info("Step 2: Running Latency Calibration (FR-003)...")
    logger.info("Verifying timestamp precision <= 100ms...")
    
    calibration_success = run_calibration()

    if not calibration_success:
        logger.error("CRITICAL: Latency calibration failed. "
                     "The system does not meet FR-003 requirements. "
                     "Startup aborted to prevent invalid data collection.")
        return False

    logger.info("Step 3: All startup checks passed.")
    logger.info("=" * 60)
    logger.info("System Ready. Proceeding to main application logic.")
    logger.info("=" * 60)
    
    return True

def main():
    """
    Entry point for the startup runner.
    Can be called by backend main.py, frontend app.jsx (via API), 
    or run directly as a script.
    """
    # Initialize logging first
    setup_logging()

    success = run_startup_checks()

    # Exit with code 1 if critical checks fail
    if not success:
        logger.critical("Startup sequence failed. Exiting.")
        sys.exit(1)
    
    logger.info("Startup sequence completed successfully.")
    return 0

if __name__ == "__main__":
    main()