"""
Report verification script for T038a.

This script programmatically verifies that the generated report text from T038
explicitly contains the phrase "associational" or similar disclaimers.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_report(report_path: Path) -> str:
    """
    Load the report text from the generated JSON file.

    Args:
        report_path: Path to the report JSON file (e.g., data/analysis/report.json)

    Returns:
        The full text content of the report.

    Raises:
        FileNotFoundError: If the report file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If the expected 'report_text' key is missing.
    """
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'report_text' not in data:
        raise KeyError(f"Expected 'report_text' key missing in {report_path}. "
                       f"Available keys: {list(data.keys())}")

    return data['report_text']


def verify_disclaimers(text: str, required_terms: Optional[List[str]] = None) -> bool:
    """
    Verify that the report text contains required disclaimer terms.

    Args:
        text: The report text to verify.
        required_terms: List of terms to search for. Defaults to ["associational"].

    Returns:
        True if all required terms are found (case-insensitive), False otherwise.
    """
    if required_terms is None:
        required_terms = ["associational"]

    text_lower = text.lower()
    found_terms = []
    missing_terms = []

    for term in required_terms:
        if term.lower() in text_lower:
            found_terms.append(term)
        else:
            missing_terms.append(term)

    if missing_terms:
        logger.error(f"Missing required disclaimer terms: {missing_terms}")
        return False

    logger.info(f"Found required disclaimer terms: {found_terms}")
    return True


def main():
    """
    Main entry point for the report verification script.

    Usage:
        python code/src/analysis/verify_report.py --report-path data/analysis/report.json
    """
    parser = argparse.ArgumentParser(
        description="Verify that the generated report contains required disclaimers."
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        required=True,
        help="Path to the generated report JSON file (e.g., data/analysis/report.json)"
    )
    parser.add_argument(
        "--terms",
        type=str,
        nargs='+',
        default=["associational"],
        help="Space-separated list of required terms to verify in the report (default: 'associational')"
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading report from: {args.report_path}")
        report_text = load_report(args.report_path)
        logger.info(f"Report loaded. Length: {len(report_text)} characters")

        logger.info(f"Verifying presence of terms: {args.terms}")
        is_valid = verify_disclaimers(report_text, args.terms)

        if is_valid:
            logger.info("VERIFICATION PASSED: Report contains all required disclaimers.")
            sys.exit(0)
        else:
            logger.error("VERIFICATION FAILED: Report is missing required disclaimers.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report file: {e}")
        sys.exit(3)
    except KeyError as e:
        logger.error(f"Missing required key in report: {e}")
        sys.exit(4)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(5)


if __name__ == "__main__":
    main()
