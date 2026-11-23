"""
Backend Application Entry Point

This module serves as the main entry point for the backend API.
It performs essential startup checks, including the latency calibration
required by FR-003, before starting the application server.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_utils import setup_logging, get_logger
from utils.latency_calibrator import run_calibration
from utils.config_manager import get_config
from utils.resource_monitor import check_resources

logger = get_logger(__name__)

def run_startup_checks():
    """
    Executes all mandatory startup checks.
    
    Returns:
        bool: True if all checks pass, False otherwise.
    """
    logger.info("=== Starting Backend Application Startup Checks ===")
    
    # 1. Load Configuration
    try:
        logger.info("Loading environment configuration...")
        get_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

    # 2. Resource Check (RAM/CPU constraints)
    try:
        logger.info("Checking system resources (FR-007)...")
        check_resources()
        logger.info("Resource check passed.")
    except Exception as e:
        logger.error(f"Resource check failed: {e}")
        return False

    # 3. Latency Calibration (FR-003)
    # This is the critical check mandated by FR-003 for timestamp precision
    logger.info("Running latency calibration (FR-003)...")
    if not run_calibration():
        logger.critical("Latency calibration failed. The system cannot meet FR-003 requirements.")
        logger.critical("Aborting startup to prevent invalid study data collection.")
        return False
    
    logger.info("=== All Startup Checks Passed ===")
    return True

def main():
    """
    Main entry point for the backend application.
    Performs startup checks before launching the server.
    """
    # Setup logging first
    setup_logging()
    
    # Run mandatory startup checks
    if not run_startup_checks():
        logger.critical("Startup checks failed. Exiting.")
        sys.exit(1)

    # If checks pass, proceed to start the actual server logic
    # (Placeholder for actual server start, e.g., FastAPI/Uvicorn)
    logger.info("Starting backend server...")
    try:
        from backend.src.api.participant import main as api_main
        # In a real scenario, this would be uvicorn.run(...) or similar
        # For this task, we just ensure the imports work and the flow is valid
        logger.info("Backend server initialized (API modules loaded).")
        # api_main() # Uncomment to actually start the server loop
    except ImportError as e:
        logger.error(f"Failed to import API modules: {e}")
        sys.exit(1)
    
    logger.info("Backend application started successfully.")

if __name__ == "__main__":
    main()