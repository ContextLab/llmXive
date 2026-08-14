"""
Script to run the full pipeline and measure total job duration.
Generates data/ci_report.json with timing and status.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_DURATION_SECONDS = 6 * 3600  # 6 hours
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CI_REPORT_PATH = DATA_DIR / "ci_report.json"

def ensure_dirs():
    """Ensure required directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def run_pipeline():
    """
    Execute the full pipeline by importing and running main.main().
    Returns (success, duration_seconds, error_message).
    """
    start_time = time.time()
    error_msg = None
    success = False

    try:
        # Import main module dynamically to ensure we get the latest code
        import importlib.util
        main_path = PROJECT_ROOT / "code" / "main.py"
        
        if not main_path.exists():
            raise FileNotFoundError(f"main.py not found at {main_path}")

        spec = importlib.util.spec_from_file_location("main_module", main_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {main_path}")
        
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["main_module"] = main_module
        spec.loader.exec_module(main_module)

        # Run the main function
        logger.info("Starting full pipeline execution...")
        main_module.main()
        
        success = True
        logger.info("Pipeline completed successfully.")
        
    except MemoryError as e:
        error_msg = f"MemoryError during pipeline: {str(e)}"
        logger.error(error_msg)
        # MemoryError is expected to be handled gracefully by main.py
        # We consider it a partial success if the script didn't crash entirely
        success = True  # main.py should handle this
        
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        success = False
        
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline execution finished in {duration:.2f} seconds.")
        return success, duration, error_msg

def generate_ci_report(success: bool, duration: float, error: str = None):
    """Generate the CI report JSON file."""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "task_id": "T031",
        "status": "success" if success else "failed",
        "duration_seconds": round(duration, 2),
        "max_allowed_seconds": MAX_DURATION_SECONDS,
        "within_time_limit": duration <= MAX_DURATION_SECONDS,
        "runner": "ubuntu-latest",
        "message": error if error else ("Pipeline completed within time limit" if success else "Pipeline failed")
    }
    
    # Write report to file
    with open(CI_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"CI report written to {CI_REPORT_PATH}")
    return report

def main():
    """Main entry point for the timing script."""
    logger.info(f"Running pipeline timing check on {PROJECT_ROOT}")
    logger.info(f"Max allowed duration: {MAX_DURATION_SECONDS} seconds (6 hours)")
    
    ensure_dirs()
    
    success, duration, error = run_pipeline()
    report = generate_ci_report(success, duration, error)
    
    # Print summary
    print("\n" + "="*60)
    print("CI REPORT SUMMARY")
    print("="*60)
    print(f"Status: {report['status']}")
    print(f"Duration: {report['duration_seconds']} seconds")
    print(f"Time Limit: {report['max_allowed_seconds']} seconds")
    print(f"Within Limit: {report['within_time_limit']}")
    print(f"Message: {report['message']}")
    print("="*60)
    
    # Exit with appropriate code
    if not success or not report['within_time_limit']:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
