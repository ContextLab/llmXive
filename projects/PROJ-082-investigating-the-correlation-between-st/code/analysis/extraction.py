"""
Qualitative Extraction (Narrative Path)

Reads `data/raw/studies.csv` (ensured by T056) and extracts qualitative descriptors
using `nlp_logic.py` for rows lacking both `r` and `n`. Writes `data/processed/qualitative_data.json`.

Output MUST include `author`, `year`, `tract`, and `qualitative_desc` fields.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from sibling modules using the exact API surface provided
from extraction.nlp_logic import extract_tract_descriptors
from utils.config import get_project_root

# Configure logging
logger = logging.getLogger(__name__)

def load_lexicon() -> Dict[str, Any]:
    """
    Load the tract lexicon from code/config/tract_lexicon.yaml.
    """
    project_root = get_project_root()
    lexicon_path = project_root / "code" / "config" / "tract_lexicon.yaml"

    if not lexicon_path.exists():
        raise FileNotFoundError(f"Lexicon file not found at {lexicon_path}")

    import yaml
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_methodology() -> Dict[str, Any]:
    """
    Load the narrative methodology from data/config/narrative_methodology.yaml.
    """
    project_root = get_project_root()
    methodology_path = project_root / "data" / "config" / "narrative_methodology.yaml"

    if not methodology_path.exists():
        raise FileNotFoundError(f"Methodology file not found at {methodology_path}")

    import yaml
    with open(methodology_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_qualitative_descriptors(
    row: Dict[str, Any],
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any]
) -> Optional[str]:
    """
    Extract qualitative descriptors for a single row if it lacks both 'r' and 'n'.
    Uses the NLP logic defined in extraction.nlp_logic.
    """
    # Check if both r and n are missing or empty
    r_val = row.get('r')
    n_val = row.get('n')

    # Treat None, empty string, or 'NaN' as missing
    def is_missing(val):
        if val is None:
            return True
        if isinstance(val, str) and val.strip() == '':
            return True
        if isinstance(val, str) and val.lower() == 'nan':
            return True
        try:
            if float(val) != float(val):  # NaN check
                return True
        except (ValueError, TypeError):
            pass
        return False

    if not is_missing(r_val) or not is_missing(n_val):
        # Row has quantitative data, skip qualitative extraction
        return None

    # Prepare text for extraction.
    # We assume the 'tract' column or a description column contains the text to analyze.
    # If 'tract' is the only source, we use it. If there's a 'description' or 'notes' column, use that.
    text_to_analyze = row.get('tract', '')
    if not text_to_analyze:
        # Fallback to other potential text columns if 'tract' is empty
        for key in ['description', 'notes', 'abstract', 'text']:
            if key in row and row[key]:
                text_to_analyze = str(row[key])
                break

    if not text_to_analyze:
        return None

    # Call the NLP logic function
    # The function signature from API surface: extract_tract_descriptors(text, lexicon, scheme)
    result = extract_tract_descriptors(text_to_analyze, lexicon, scheme)

    if result and 'qualitative_desc' in result:
        return result['qualitative_desc']

    return None

def save_qualitative_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the extracted qualitative data to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved qualitative data to {output_path}")

def run_extraction(input_path: Path, output_path: Path) -> int:
    """
    Main extraction logic:
    1. Load lexicon and methodology.
    2. Read input CSV.
    3. Filter rows missing 'r' and 'n'.
    4. Extract qualitative descriptors.
    5. Save results to JSON.
    """
    # Load configuration
    try:
        lexicon = load_lexicon()
        scheme = load_methodology()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    extracted_records = []

    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}. Creating empty output.")
        save_qualitative_data([], output_path)
        return 0

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                try:
                    desc = extract_qualitative_descriptors(row, lexicon, scheme)
                    if desc:
                        record = {
                            "author": row.get('author', 'Unknown'),
                            "year": row.get('year', 'Unknown'),
                            "tract": row.get('tract', 'Unknown'),
                            "qualitative_desc": desc
                        }
                        extracted_records.append(record)
                        logger.debug(f"Extracted qualitative data for row {row_num}: {record['author']}")
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error reading input file {input_path}: {e}")
        return 1

    save_qualitative_data(extracted_records, output_path)
    logger.info(f"Extraction complete. Found {len(extracted_records)} records with qualitative data.")
    return 0

def main() -> int:
    """
    Entry point for the extraction script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = get_project_root()
    input_path = project_root / "data" / "raw" / "studies.csv"
    output_path = project_root / "data" / "processed" / "qualitative_data.json"

    logger.info(f"Starting qualitative extraction from {input_path}")
    return run_extraction(input_path, output_path)

if __name__ == "__main__":
    sys.exit(main())