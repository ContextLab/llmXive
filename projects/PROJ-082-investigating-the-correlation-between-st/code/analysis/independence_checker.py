"""
Independence Checker Module for PROJ-082.

This module scans the extracted studies CSV for multiple tracts reported
from the same study (same author/year pair). It logs warnings for potential
non-independence and writes a status report to data/derived/independence_status.json.
"""

import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Import shared utilities from existing API surface
from utils.config import get_project_root, ensure_directory

# Configure logger
logger = logging.getLogger(__name__)

def get_input_path() -> Path:
    """Return the path to the extracted studies CSV."""
    root = get_project_root()
    return root / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Return the path to the independence status JSON output."""
    root = get_project_root()
    return root / "data" / "derived" / "independence_status.json"

def ensure_directory(path: Path) -> None:
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def load_extracted_studies(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV file.

    Args:
        input_path: Path to the CSV file.

    Returns:
        List of dictionaries representing each row.

    Raises:
        FileNotFoundError: If the input file does not exist.
        Exception: If the file is malformed.
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    studies = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                studies.append(row)
    except Exception as e:
        logger.error(f"Error reading CSV file {input_path}: {e}")
        raise

    return studies

def check_independence(studies: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check for potential non-independence in the study list.

    Non-independence is flagged if multiple rows share the same (author, year)
    but report different tracts. This implies the same study contributed multiple
    effect sizes, violating the independence assumption of standard meta-analysis.

    Args:
        studies: List of study dictionaries.

    Returns:
        A tuple (assumed_independent, warnings).
        - assumed_independent: True if no duplicates found, False otherwise.
        - warnings: List of warning dictionaries with details.
    """
    # Group by (author, year)
    study_groups = defaultdict(list)
    for idx, study in enumerate(studies):
        # Handle potential missing keys gracefully
        author = study.get('author', 'Unknown').strip()
        year = study.get('year', 'Unknown').strip()
        tract = study.get('tract', 'Unknown').strip()

        # Normalize year to string for consistent grouping
        key = (author, str(year))
        study_groups[key].append({
            'index': idx,
            'tract': tract,
            'author': author,
            'year': year
        })

    warnings = []
    has_duplicates = False

    for key, rows in study_groups.items():
        if len(rows) > 1:
            has_duplicates = True
            tracts = [r['tract'] for r in rows]
            unique_tracts = set(tracts)

            if len(unique_tracts) > 1:
                # Multiple distinct tracts from same study -> Non-independence
                warnings.append({
                    'author': key[0],
                    'year': key[1],
                    'count': len(rows),
                    'tracts': unique_tracts,
                    'message': f"Study {key[0]} ({key[1]}) reports {len(rows)} effect sizes for {len(unique_tracts)} distinct tracts: {', '.join(unique_tracts)}. This violates the independence assumption."
                })
            else:
                # Same tract reported multiple times (e.g., different regions or just duplicates)
                # Still a potential issue for weighting, but less severe than different tracts.
                # We log it as a warning for review.
                warnings.append({
                    'author': key[0],
                    'year': key[1],
                    'count': len(rows),
                    'tracts': unique_tracts,
                    'message': f"Study {key[0]} ({key[1]}) reports {len(rows)} effect sizes for the same tract: {unique_tracts.pop()}. Check for data entry duplication."
                })

    return not has_duplicates, warnings

def save_independence_status(output_path: Path, assumed_independent: bool, warnings: List[Dict[str, Any]]) -> None:
    """
    Save the independence check results to a JSON file.

    Args:
        output_path: Path to the output JSON file.
        assumed_independent: Boolean flag indicating if independence is assumed.
        warnings: List of warning details.
    """
    ensure_directory(output_path)

    result = {
        'independence_assumed': assumed_independent,
        'total_studies_checked': len(warnings) if warnings else 0, # This logic is slightly off, better to pass total count or count from input
        'warnings_count': len(warnings),
        'warnings': warnings,
        'generated_at': datetime.utcnow().isoformat() + "Z"
    }

    # Correct the total_studies_checked logic if we want total rows checked,
    # but the task asks for status based on warnings. Let's include a count of warnings.
    # Actually, let's just report the warnings and the boolean flag.
    # We can add 'total_studies' if we pass it, but for now we focus on the warnings.
    
    # Re-structure to be more useful:
    final_result = {
        'independence_assumed': assumed_independent,
        'warning_count': len(warnings),
        'warnings': warnings,
        'generated_at': datetime.utcnow().isoformat() + "Z"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2)

    logger.info(f"Independence status saved to {output_path}")

def run_independence_checker() -> Dict[str, Any]:
    """
    Main entry point for the independence checking logic.

    Returns:
        Dictionary with the status and results.
    """
    input_path = get_input_path()
    output_path = get_output_path()

    logger.info(f"Starting independence check on {input_path}")

    try:
        studies = load_extracted_studies(input_path)
        logger.info(f"Loaded {len(studies)} studies from {input_path}")

        if not studies:
            logger.warning("No studies found in input file. Assuming independence trivially.")
            save_independence_status(output_path, True, [])
            return {'independence_assumed': True, 'warnings': []}

        assumed_independent, warnings = check_independence(studies)

        save_independence_status(output_path, assumed_independent, warnings)

        return {
            'independence_assumed': assumed_independent,
            'warnings_count': len(warnings),
            'output_path': str(output_path)
        }

    except FileNotFoundError as e:
        logger.error(f"Failed to run independence check: {e}")
        # If input is missing, we cannot assume independence.
        # We write a status indicating failure or missing data.
        ensure_directory(output_path)
        error_result = {
            'independence_assumed': False,
            'error': str(e),
            'warnings': [],
            'generated_at': datetime.utcnow().isoformat() + "Z"
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        raise

def main() -> int:
    """Command-line entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        result = run_independence_checker()
        if result['independence_assumed']:
            logger.info("Independence assumption holds.")
            return 0
        else:
            logger.warning(f"Independence assumption VIOLATED. {result['warnings_count']} warnings found.")
            return 0  # Return 0 to allow pipeline to continue, but log the warning
    except Exception as e:
        logger.critical(f"Independence checker failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())