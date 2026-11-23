import sys
import os
import logging
from pathlib import Path
import subprocess
import argparse

def run_pytest_suite(output_path: str = "tests/results/junit.xml"):
    """
    Runs the pytest suite for the project and generates a JUnit XML report.
    
    Args:
        output_path: Relative path from project root where the JUnit XML report will be saved.
    
    Returns:
        int: Exit code of the pytest process.
    """
    # Ensure the output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Construct the pytest command
    # Using junit-xml format to generate the report
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        f"--junitxml={output_file}",
        "code/tests"  # Target the tests directory inside code/
    ]
    
    logging.info(f"Running pytest with command: {' '.join(cmd)}")
    logging.info(f"Output will be written to: {output_file.absolute()}")
    
    try:
        # Run the command
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            logging.info(f"Pytest suite completed successfully. Report saved to {output_file}")
        else:
            logging.warning(f"Pytest suite completed with exit code {result.returncode}. Report saved to {output_file}")
        
        return result.returncode
        
    except FileNotFoundError:
        logging.error("Pytest not found. Please ensure pytest is installed in the environment.")
        return 1
    except Exception as e:
        logging.error(f"An error occurred while running pytest: {e}")
        return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Run the full pytest suite and generate JUnit report.")
    parser.add_argument(
        "--output",
        type=str,
        default="tests/results/junit.xml",
        help="Path to the output JUnit XML file."
    )
    
    args = parser.parse_args()
    exit_code = run_pytest_suite(args.output)
    sys.exit(exit_code)
