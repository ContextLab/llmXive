import subprocess
import sys
import json
import os
from pathlib import Path
import argparse
import logging
from utils.logging import setup_logging, get_logger

def run_tests(test_file: str, output_file: str):
    """
    Run a specific pytest file and save the results to a JSON report.
    
    Args:
        test_file: Path to the test file (e.g., 'tests/integration/test_preprocessing.py')
        output_file: Path to save the JSON report (e.g., 'data/processed/test_report_preprocessing.json')
    
    Returns:
        dict: The test results summary
    """
    logger = get_logger()
    logger.info(f"Running integration tests: {test_file}")
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build pytest command with JSON output
    # Using --tb=short for concise traceback and -v for verbose
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",
        "--tb=short",
        "--json-report",
        f"--json-report-file={output_file}"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if pytest succeeded
        if result.returncode == 0:
            logger.info(f"Tests passed. Results saved to {output_file}")
        else:
            logger.warning(f"Some tests failed or were skipped. Exit code: {result.returncode}")
            logger.warning(f"stdout:\n{result.stdout}")
            logger.warning(f"stderr:\n{result.stderr}")
        
        # Load and return the results if the file was created
        if output_path.exists():
            with open(output_path, 'r') as f:
                report_data = json.load(f)
            
            # Create a summary
            summary = {
                "file": output_file,
                "total_tests": report_data.get("tests", []).__len__(),
                "passed": report_data.get("summary", {}).get("passed", 0),
                "failed": report_data.get("summary", {}).get("failed", 0),
                "skipped": report_data.get("summary", {}).get("skipped", 0),
                "errors": report_data.get("summary", {}).get("errors", 0),
                "duration": report_data.get("summary", {}).get("duration", 0),
                "status": "passed" if result.returncode == 0 else "failed"
            }
            
            logger.info(f"Test Summary: {summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped")
            return summary
        else:
            logger.error(f"JSON report file not created at {output_file}")
            return {"error": "Report file not created"}
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Run integration tests and save results.")
    parser.add_argument(
        "--test-file",
        type=str,
        default="tests/integration/test_preprocessing.py",
        help="Path to the test file to run"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/test_report_preprocessing.json",
        help="Path to save the JSON report"
    )
    args = parser.parse_args()
    
    setup_logging()
    logger = get_logger()
    
    logger.info("Starting integration test execution")
    results = run_tests(args.test_file, args.output)
    
    logger.info(f"Test execution completed. Status: {results.get('status', 'unknown')}")
    
    if "error" in results:
        sys.exit(1)

if __name__ == "__main__":
    main()
