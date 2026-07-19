import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path to allow relative imports if run as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from analysis.tract_mapping import harmonize_tract_list, load_tract_mapping_config

logger = get_logger(__name__)

def load_extracted_studies(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV (or JSON if stored as such) from T013.
    Expects a file with at least one column containing tract information.
    For this implementation, we assume the CSV has a 'tract' or 'harmonized_tract' column,
    or we extract from 'qualitative_desc' if needed (though T013 should have normalized).
    We will look for 'tract', 'harmonized_tract', or 'qualitative_desc'.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    studies = []
    try:
        # Attempt to load as CSV first, as per T013 output description
        import csv
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                studies.append(row)
    except Exception as e:
        # Fallback to JSON if CSV fails, though T013 specifies CSV
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                studies = json.load(f)
        except Exception as json_err:
            raise RuntimeError(f"Failed to parse input as CSV or JSON: {e}, {json_err}")

    return studies

def extract_tract_names(studies: List[Dict[str, Any]]) -> List[str]:
    """
    Extract tract names from the study records.
    Prioritizes 'harmonized_tract' if present (from T013/T008), then 'tract', then 'qualitative_desc'.
    """
    tract_names = []
    for study in studies:
        # Priority 1: Already harmonized tract
        if 'harmonized_tract' in study and study['harmonized_tract']:
            tract_names.append(study['harmonized_tract'])
        # Priority 2: Raw tract field
        elif 'tract' in study and study['tract']:
            tract_names.append(study['tract'])
        # Priority 3: Qualitative description (fallback, though T013 should have parsed this)
        elif 'qualitative_desc' in study and study['qualitative_desc']:
            # If it's a list or string, handle accordingly
            desc = study['qualitative_desc']
            if isinstance(desc, str):
                # Simple heuristic: if it looks like a tract name, add it
                # In a full NLP pipeline, this would be more complex, but T013 should have done the heavy lifting
                # We assume T013 populated 'tract' or 'harmonized_tract' if found.
                # If we are here, we might need to parse, but for T008c we rely on T013's extraction.
                # If T013 failed to extract, we might get noise here.
                # We will just add it if it's not empty, trusting T013's logic or T008 harmonization.
                # However, to be safe and count unique *tracts*, we should ideally only count valid tract names.
                # Since T013 uses T008, we assume 'tract' or 'harmonized_tract' is the source of truth.
                # If both are missing, we skip.
                pass
    return tract_names

def count_unique_tracts(tract_names: List[str]) -> int:
    """
    Count the number of unique tract names.
    """
    unique_tracts = set()
    for name in tract_names:
        if name:
            # Normalize again to be sure, in case T013 didn't fully clean
            # T008 (harmonize_tract_list) is the canonical harmonizer
            # We can pass a list of one to get the standard name
            harmonized = harmonize_tract_list([name])
            if harmonized:
                unique_tracts.add(harmonized[0])
    return len(unique_tracts)

def save_tract_count(count: int, output_path: Path) -> None:
    """
    Save the tract count to a JSON file.
    Format: {"k": <count>}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"k": count}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved tract count: {count} to {output_path}")

def run_tract_counting(input_path: Path, output_path: Path) -> int:
    """
    Main logic for T008c.
    1. Load extracted studies from T013.
    2. Extract tract names.
    3. Apply harmonization (T008) to ensure uniqueness.
    4. Count unique tracts.
    5. Save to JSON.
    """
    logger.info(f"Starting tract counting for {input_path}")
    
    studies = load_extracted_studies(input_path)
    if not studies:
        logger.warning("No studies found in input file. Tract count will be 0.")
        count = 0
    else:
        tract_names = extract_tract_names(studies)
        count = count_unique_tracts(tract_names)
    
    save_tract_count(count, output_path)
    return count

def main():
    """
    Entry point for script execution.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "processed" / "extracted_studies.csv"
    output_file = project_root / "data" / "processed" / "tract_count.json"

    # Allow command line override
    if len(sys.argv) >= 3:
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])

    try:
        count = run_tract_counting(input_file, output_file)
        print(f"Tract count (k): {count}")
        return 0
    except Exception as e:
        logger.error(f"Tract counting failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
