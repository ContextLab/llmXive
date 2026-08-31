"""
Tract Counter (Task T008c).

Reads extracted_studies.csv and counts distinct tracts.
Output: data/derived/tract_count.json
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Set, Optional, Dict, Any

def get_input_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "data" / "derived" / "tract_count.json"

def load_extracted_studies(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def extract_tract_names(studies: list) -> Set[str]:
    tracts = set()
    for study in studies:
        tract = study.get('tract_name', '').strip()
        if tract:
            tracts.add(tract.lower())
    return tracts

def count_unique_tracts(tracts: Set[str]) -> int:
    return len(tracts)

def save_tract_count(count: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump({"k": count}, f, indent=2)

def run_tract_counter() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("tract_counter")
    
    input_path = get_input_path()
    output_path = get_output_path()
    
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}. Writing k=0.")
        save_tract_count(0, output_path)
        return 0
    
    studies = load_extracted_studies(input_path)
    tracts = extract_tract_names(studies)
    k = count_unique_tracts(tracts)
    
    save_tract_count(k, output_path)
    logger.info(f"Distinct tracts counted: {k}")
    return 0

def main() -> int:
    return run_tract_counter()

if __name__ == "__main__":
    sys.exit(main())