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

def load_extracted_studies(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def count_unique_studies(studies: List[Dict[str, Any]]) -> int:
    unique_keys: Set[Tuple[str, str]] = set()
    for study in studies:
        author = study.get('author', '').strip()
        year = study.get('year', '').strip()
        if author and year:
            unique_keys.add((author, year))
    return len(unique_keys)

def save_study_count(count: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"N": count}, f, indent=2)

def run_study_counter() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("study_counter")
    
    input_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "extracted_studies.csv"
    output_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "study_count.json"
    
    studies = load_extracted_studies(input_path)
    N = count_unique_studies(studies)
    
    save_study_count(N, output_path)
    logger.info(f"Unique studies counted: {N}")
    return 0

def main() -> int:
    return run_study_counter()

if __name__ == "__main__":
    sys.exit(main())
