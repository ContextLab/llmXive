import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import subprocess

def run_pytest_suite():
    """
    Runs the full pytest suite for the project and generates a summary report.
    Returns 0 if all tests pass, 1 otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "code" / "tests"
    output_log = project_root / "data" / "logs" / "pytest_results.log"
    
    # Ensure log directory exists
    output_log.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(output_log),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting pytest suite execution...")
    logger.info(f"Tests directory: {tests_dir}")
    logger.info(f"Output log: {output_log}")

    # Build pytest command
    # Using -v for verbose output, --tb=short for concise tracebacks
    # --junit-xml for machine-readable results (optional but good practice)
    junit_xml_path = project_root / "data" / "logs" / "pytest_junit.xml"
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--junit-xml=" + str(junit_xml_path),
        "--color=yes"
    ]

    logger.info(f"Executing: {' '.join(cmd)}")

    start_time = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=False,  # Stream to stdout/stderr for visibility
            text=True,
            timeout=3600  # 1 hour timeout for the whole suite
        )
    except subprocess.TimeoutExpired:
        logger.error("Test suite execution timed out after 1 hour.")
        return 1
    except Exception as e:
        logger.error(f"Failed to execute pytest: {e}")
        return 1

    end_time = datetime.now()
    duration = end_time - start_time

    if result.returncode == 0:
        logger.info("=" * 60)
        logger.info("SUCCESS: All tests passed.")
        logger.info(f"Duration: {duration}")
        logger.info(f"JUnit XML report saved to: {junit_xml_path}")
        logger.info(f"Detailed log saved to: {output_log}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("FAILURE: One or more tests failed.")
        logger.error(f"Duration: {duration}")
        logger.error(f"Check logs at: {output_log}")
        logger.error(f"JUnit XML report saved to: {junit_xml_path}")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(run_pytest_suite())
