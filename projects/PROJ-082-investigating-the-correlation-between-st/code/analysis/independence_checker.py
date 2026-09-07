"""
Independence Checker Module

Scans extracted_studies.csv for multiple tracts from the same study (same author/year).
Logs warnings for potential non-independence and writes independence_status.json.
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/independence_checker.log')
    ]
)
logger = logging.getLogger(__name__)


def get_input_path():
    """Return the path to the extracted studies CSV."""
    return Path('data/processed/extracted_studies.csv')


def get_output_path():
    """Return the path to the independence status JSON."""
    return Path('data/derived/independence_status.json')


def ensure_directory(file_path):
    """Ensure the directory for a file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def load_extracted_studies(input_path):
    """
    Load the extracted studies CSV file.

    Args:
        input_path (Path): Path to the CSV file.

    Returns:
        List[Dict]: List of study records.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or has no data rows.
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    studies = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)

    if not studies:
        logger.warning("Input file is empty or contains no data rows.")
        # Return empty list to allow downstream logic to handle N=0 gracefully
        return []

    logger.info(f"Loaded {len(studies)} studies from {input_path}")
    return studies


def check_independence(studies):
    """
    Check for multiple tracts from the same study (author/year).

    Args:
        studies (List[Dict]): List of study records.

    Returns:
        Tuple[bool, List[Dict]]: (independence_assumed, warnings)
    """
    # Group studies by (author, year)
    study_groups = defaultdict(list)
    for study in studies:
        author = study.get('author', '').strip()
        year = study.get('year', '').strip()
        tract = study.get('tract', '').strip()
        # Create a unique key for the study
        study_key = (author, year)
        study_groups[study_key].append(tract)

    warnings = []
    non_independent_groups = []

    for (author, year), tracts in study_groups.items():
        if len(tracts) > 1:
            # Multiple tracts from the same study detected
            non_independent_groups.append({
                'author': author,
                'year': year,
                'tract_count': len(tracts),
                'tracts': tracts
            })
            warning_msg = f"Non-independence detected: Study '{author} ({year})' has {len(tracts)} tracts: {tracts}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)

    if non_independent_groups:
        logger.warning(f"Found {len(non_independent_groups)} study(ies) with multiple tracts. Independence assumption may be violated.")
        independence_assumed = False
    else:
        logger.info("No non-independence detected. All studies have unique (author, year) pairs.")
        independence_assumed = True

    return independence_assumed, warnings, non_independent_groups


def save_independence_status(output_path, independence_assumed, warnings, non_independent_groups):
    """
    Save the independence status to a JSON file.

    Args:
        output_path (Path): Path to the output JSON file.
        independence_assumed (bool): Whether independence is assumed.
        warnings (List[str]): List of warning messages.
        non_independent_groups (List[Dict]): Details of non-independent groups.
    """
    ensure_directory(output_path)

    result = {
        'independence_assumed': independence_assumed,
        'timestamp': datetime.now().isoformat(),
        'warning_count': len(warnings),
        'warnings': warnings,
        'non_independent_studies': non_independent_groups
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Independence status saved to {output_path}")


def run_independence_checker():
    """
    Main function to run the independence checker.

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    try:
        input_path = get_input_path()
        output_path = get_output_path()

        logger.info("Starting independence check...")

        # Load studies
        studies = load_extracted_studies(input_path)

        if not studies:
            # No studies to check - assume independence (trivially true)
            logger.info("No studies found. Independence assumed (trivially true).")
            save_independence_status(output_path, True, [], [])
            return 0

        # Check independence
        independence_assumed, warnings, non_independent_groups = check_independence(studies)

        # Save results
        save_independence_status(output_path, independence_assumed, warnings, non_independent_groups)

        logger.info("Independence check completed.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during independence check: {e}", exc_info=True)
        return 1


def main():
    """Entry point for the independence checker script."""
    exit_code = run_independence_checker()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()