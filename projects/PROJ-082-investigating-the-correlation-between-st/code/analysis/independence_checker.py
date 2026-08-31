import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Attempt to import logger utilities if available in the project
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback if utils.logger is not present or import fails
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_input_path() -> Path:
    """Return the path to extracted_studies.csv."""
    return get_project_root() / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Return the path to independence_status.json."""
    return get_project_root() / "data" / "derived" / "independence_status.json"

def ensure_directory(path: Path) -> None:
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def load_extracted_studies(input_path: Path) -> List[Dict[str, Any]]:
    """Load the extracted studies CSV file."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return []

    studies = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                studies.append(row)
        logger.info(f"Loaded {len(studies)} studies from {input_path}")
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return []

    return studies

def check_independence(studies: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, int]]:
    """
    Check for multiple tracts from the same study.
    
    Returns:
        Tuple of (is_independent, list_of_warnings, tract_counts_per_study)
    """
    if not studies:
        logger.warning("No studies found to check for independence.")
        return True, [], {}

    # Group tracts by study identifier (author, year)
    study_tracts: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    
    for study in studies:
        author = study.get('author', '').strip()
        year = study.get('year', '').strip()
        tract = study.get('tract_name', study.get('tract', '')).strip()
        
        if not author or not year:
            logger.warning(f"Study missing author or year: {study}")
            continue
        
        if not tract:
            continue

        key = (author, year)
        study_tracts[key].append(tract)

    warnings = []
    dependent_studies = []

    for (author, year), tracts in study_tracts.items():
        unique_tracts = set(tracts)
        if len(unique_tracts) > 1:
            dependent_studies.append((author, year, len(unique_tracts)))
            msg = f"Dependence detected: Study ({author}, {year}) includes {len(unique_tracts)} distinct tracts: {', '.join(unique_tracts)}"
            warnings.append(msg)
            logger.warning(msg)

    is_independent = len(dependent_studies) == 0
    tract_counts = {f"{a}_{y}": len(set(t)) for (a, y), t in study_tracts.items()}

    return is_independent, warnings, tract_counts

def save_independence_status(output_path: Path, is_independent: bool, warnings: List[str], tract_counts: Dict[str, int]) -> None:
    """Save the independence status to a JSON file."""
    ensure_directory(output_path)
    
    status = {
        "independence_assumed": is_independent,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "warnings_count": len(warnings),
        "warnings": warnings,
        "study_tract_counts": tract_counts
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

    logger.info(f"Independence status saved to {output_path}")
    logger.info(f"Independence assumed: {is_independent}")

def run_independence_checker(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> bool:
    """
    Main function to run the independence check.
    
    Args:
        input_path: Optional path to input CSV. Defaults to data/processed/extracted_studies.csv.
        output_path: Optional path to output JSON. Defaults to data/derived/independence_status.json.
        
    Returns:
        True if check completed successfully, False otherwise.
    """
    input_path = input_path or get_input_path()
    output_path = output_path or get_output_path()

    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist. Cannot check independence.")
        # Even if input is missing, we write a status indicating failure/unknown
        # But per task spec, we scan extracted_studies.csv. If missing, we can't scan.
        # We write a status with independence_assumed=False or True? 
        # The task says "scans ... and writes". If file missing, we can't scan.
        # Let's write a status indicating we couldn't verify, so assumed=False (safe)
        status = {
            "independence_assumed": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "warnings_count": 1,
            "warnings": ["Input file missing, independence cannot be verified."],
            "study_tract_counts": {}
        }
        ensure_directory(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        return False

    studies = load_extracted_studies(input_path)
    
    if not studies:
        logger.warning("No studies loaded. Assuming independence (no data to violate it).")
        save_independence_status(output_path, True, [], {})
        return True

    is_independent, warnings, tract_counts = check_independence(studies)
    save_independence_status(output_path, is_independent, warnings, tract_counts)

    return True

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    success = run_independence_checker()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())