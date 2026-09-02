"""
Study Counter (Task T014a).

Counts unique (author, year) pairs in extracted_studies.csv.
Output: data/processed/study_count.json
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def get_input_path() -> Path:
    """Returns the path to extracted_studies.csv."""
    return get_project_root() / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Returns the path to study_count.json."""
    return get_project_root() / "data" / "processed" / "study_count.json"

def ensure_directory(path: Path) -> None:
    """Ensures the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def load_extracted_studies(path: Path) -> List[Dict[str, Any]]:
    """
    Loads studies from a CSV file.
    Returns an empty list if the file does not exist.
    """
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def count_unique_studies(studies: List[Dict[str, Any]]) -> int:
    """
    Counts unique (author, year) pairs.
    Ignores rows where author or year is missing/empty.
    """
    unique_keys: Set[Tuple[str, str]] = set()
    for study in studies:
        author = study.get('author', '').strip()
        year = study.get('year', '').strip()
        if author and year:
            unique_keys.add((author, year))
    return len(unique_keys)

def save_study_count(count: int, path: Path) -> None:
    """
    Saves the study count to a JSON file.
    Output format: {"N": <count>}
    """
    ensure_directory(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"N": count}, f, indent=2)

def run_study_counter() -> int:
    """
    Main execution logic for the study counter.
    Reads extracted_studies.csv, counts unique studies, and writes study_count.json.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("study_counter")

    input_path = get_input_path()
    output_path = get_output_path()

    logger.info(f"Loading studies from: {input_path}")
    studies = load_extracted_studies(input_path)

    N = count_unique_studies(studies)

    logger.info(f"Unique studies counted: {N}")
    save_study_count(N, output_path)
    logger.info(f"Saved study count to: {output_path}")

    return 0

def main() -> int:
    """Entry point."""
    try:
        return run_study_counter()
    except Exception as e:
        logging.error(f"Error in study counter: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())