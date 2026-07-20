import os
import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

from utils.logger import log_generation_error

def verify_junit_report():
    """
    Verify that tests/results/junit.xml exists and contains no failures.
    Returns True if valid, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    junit_path = project_root / "tests" / "results" / "junit.xml"

    if not junit_path.exists():
        logging.error(f"JUnit report not found at {junit_path}")
        return False

    try:
        tree = ET.parse(junit_path)
        root = tree.getroot()

        # Check for failures or errors
        failures = root.attrib.get('failures', '0')
        errors = root.attrib.get('errors', '0')
        tests = root.attrib.get('tests', '0')

        logging.info(f"JUnit Report: {tests} tests, {failures} failures, {errors} errors")

        if int(failures) > 0 or int(errors) > 0:
            logging.error(f"JUnit report contains failures ({failures}) or errors ({errors})")
            return False

        logging.info("JUnit report verification passed: No failures or errors found.")
        return True

    except ET.ParseError as e:
        logging.error(f"Failed to parse JUnit XML: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during JUnit verification: {e}")
        return False

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    success = verify_junit_report()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()