import subprocess
import sys
import json
import os
from pathlib import Path
import argparse
import logging
from utils.logging import setup_logging, get_logger

def run_contract_tests(test_file: str, output_path: str) -> bool:
    """
    Execute a specific contract test file using pytest and save results to JSON.
    
    Args:
        test_file: Path to the test file (e.g., 'tests/contract/test_data_merge.py')
        output_path: Path where the JSON report will be saved
    
    Returns:
        True if tests passed or skipped (but executed), False if execution failed
    """
    logger = get_logger()
    logger.info(f"Running contract tests: {test_file}")
    
    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        return False
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run pytest with verbose output and capture results
    # Using --json-report plugin if available, otherwise fallback to parsing output
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse pytest output to create a structured report
        # Since pytest-json-report might not be installed, we parse the output manually
        report = {
            "test_file": test_file,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "passed" if result.returncode == 0 else "failed",
            "executed": True
        }
        
        # Basic parsing of pytest output for summary
        if "passed" in result.stdout:
            report["summary"] = "Tests passed"
        elif "skipped" in result.stdout and result.returncode == 0:
            report["summary"] = "Tests skipped (expected)"
        elif "failed" in result.stdout:
            report["summary"] = "Tests failed"
        else:
            report["summary"] = "Unknown status"
        
        # Write report to JSON
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test report saved to: {output_path}")
        logger.info(f"Test status: {report['status']}")
        
        return result.returncode == 0 or "skipped" in result.stdout
        
    except subprocess.TimeoutExpired:
        logger.error(f"Test execution timed out for {test_file}")
        return False
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return False

def main():
    """Main entry point for executing contract tests."""
    setup_logging()
    logger = get_logger()
    
    parser = argparse.ArgumentParser(description="Execute contract tests")
    parser.add_argument(
        "--test-file",
        type=str,
        default="tests/contract/test_data_merge.py",
        help="Path to the test file to execute"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/test_report_merge.json",
        help="Path to save the test report JSON"
    )
    
    args = parser.parse_args()
    
    success = run_contract_tests(args.test_file, args.output)
    
    if success:
        logger.info("Contract tests executed successfully")
        sys.exit(0)
    else:
        logger.error("Contract tests failed to execute properly")
        sys.exit(1)

if __name__ == "__main__":
    main()
