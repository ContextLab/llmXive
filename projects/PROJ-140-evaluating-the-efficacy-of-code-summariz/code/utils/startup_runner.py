"""
Startup Runner for Application Initialization and Checks.

This module orchestrates the execution of mandatory startup checks,
including the latency calibration required by FR-003.

It ensures that the system environment is valid before the main
application logic proceeds.
"""
import sys
import os
from pathlib import Path
from utils.config_manager import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.latency_calibrator import run_calibration

logger = get_logger(__name__)

def run_startup_checks() -> bool:
    """
    Executes all mandatory startup checks.

    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info("Starting application startup checks...")

    # 1. Load Configuration
    try:
        config = get_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

    # 2. Run Latency Calibration (FR-003 Mandate)
    # This must run at startup to verify timestamp precision <= 100ms
    logger.info("Running mandatory latency calibration (FR-003)...")
    calibration_success = run_calibration()

    if not calibration_success:
        logger.error("Startup aborted: Latency calibration failed.")
        logger.error("The system does not meet the timestamp precision requirements.")
        return False

    logger.info("All startup checks passed.")
    return True

def main():
    """Entry point for the startup runner."""
    # Ensure project root is in path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Setup logging first
    setup_logging()

    success = run_startup_checks()

    if not success:
        sys.exit(1)
    
    # If successful, the main application would continue here
    # For now, we exit 0 to indicate readiness
    sys.exit(0)

if __name__ == "__main__":
    main()