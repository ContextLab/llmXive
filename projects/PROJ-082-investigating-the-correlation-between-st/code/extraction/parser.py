"""
Parser module for extracting study data from CSV and JSON files.
Handles parsing of effect sizes (r, n) and qualitative descriptors.
"""
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.logger import get_logger, log_fallback
from utils.validator import filter_valid_studies, validate_study_row

logger = get_logger(__name__)

# Specific neural circuitry terms to search for in qualitative analysis
NEURAL_TERMS = [
    "arcuate", "cingulum", "uncinate", "corpus callosum",
    "superior longitudinal fasciculus", "inferior longitudinal fasciculus",
    "slf", "ilf", "af", "cb"
]

# Directional verbs for association detection
DIRECTIONAL_VERBS = [
    "increased", "decreased", "correlated", "associated", "linked", "related"
]


def parse_row(
    row: Dict[str, Any],
    r_col: str = "r",
    n_col: str = "n",
    tract_col: str = "tract",
    notes_col: str = "notes"
) -> Dict[str, Any]:
    """
    Parses a single row from a study record.
    Validates effect sizes and extracts qualitative descriptors.
    """
    study_id = row.get("study_id", f"Row_{row.get('row_index', 'unknown')}")
    
    # Validate effect sizes first
    is_valid, error_msg = validate_study_row(row, "study_id", r_col, n_col)
    
    if not is_valid:
        # Return a record indicating the study is invalid/excluded
        return {
            "study_id": study_id,
            "valid": False,
            "error": error_msg,
            "r": None,
            "n": None,
            "tract": None,
            "qualitative_notes": None
        }

    r_val = row.get(r_col)
    n_val = row.get(n_col)
    
    # Ensure types
    if isinstance(r_val, str):
        r_val = float(r_val)
    if isinstance(n_val, str):
        n_val = int(float(n_val))

    tract = row.get(tract_col, "")
    notes = row.get(notes_col, "")

    # Extract qualitative descriptors if notes exist
    qualitative_notes = None
    if notes:
        qualitative_notes = extract_descriptors(notes, tract)

    return {
        "study_id": study_id,
        "valid": True,
        "r": r_val,
        "n": n_val,
        "tract": tract if tract else None,
        "qualitative_notes": qualitative_notes
    }


def extract_descriptors(text: str, tract_name: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Extracts directional descriptors from text based on proximity to neural terms.
    """
    if not text:
        return None

    text_lower = text.lower()
    found_terms = []

    # Check for specific neural terms
    for term in NEURAL_TERMS:
        if term in text_lower:
            found_terms.append(term)

    if not found_terms:
        return None

    # Determine direction if possible
    direction = "neutral"
    for verb in DIRECTIONAL_VERBS:
        if verb in text_lower:
            if "increased" in text_lower or "positive" in text_lower:
                direction = "positive"
            elif "decreased" in text_lower or "negative" in text_lower:
                direction = "negative"
            break

    return {
        "tracts": found_terms,
        "direction": direction,
        "raw_text": text
    }


def parse_csv_file(
    file_path: Union[str, Path],
    r_col: str = "r",
    n_col: str = "n",
    tract_col: str = "tract",
    notes_col: str = "notes"
) -> List[Dict[str, Any]]:
    """
    Parses a CSV file into a list of study records.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    studies = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            row["row_index"] = idx + 1 # 1-based index for logging
            parsed = parse_row(row, r_col, n_col, tract_col, notes_col)
            studies.append(parsed)

    # Filter out invalid studies immediately during parsing to match T017 requirement
    valid_studies, _ = filter_valid_studies(studies, r_col, n_col, "study_id")
    
    logger.info(f"Parsed {len(studies)} rows, {len(valid_studies)} valid studies.")
    return valid_studies


def parse_json_file(
    file_path: Union[str, Path],
    r_col: str = "r",
    n_col: str = "n",
    tract_col: str = "tract",
    notes_col: str = "notes"
) -> List[Dict[str, Any]]:
    """
    Parses a JSON file into a list of study records.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_studies = data
    elif isinstance(data, dict) and "studies" in data:
        raw_studies = data["studies"]
    else:
        raise ValueError("JSON must be a list of studies or an object with a 'studies' key")

    studies = []
    for idx, row in enumerate(raw_studies):
        if not isinstance(row, dict):
            continue
        row["row_index"] = idx
        parsed = parse_row(row, r_col, n_col, tract_col, notes_col)
        studies.append(parsed)

    valid_studies, _ = filter_valid_studies(studies, r_col, n_col, "study_id")
    logger.info(f"Parsed {len(studies)} rows, {len(valid_studies)} valid studies.")
    return valid_studies


def parse_input(
    file_path: Union[str, Path],
    r_col: str = "r",
    n_col: str = "n",
    tract_col: str = "tract",
    notes_col: str = "notes"
) -> List[Dict[str, Any]]:
    """
    Dispatches parsing based on file extension.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.csv':
        return parse_csv_file(file_path, r_col, n_col, tract_col, notes_col)
    elif suffix == '.json':
        return parse_json_file(file_path, r_col, n_col, tract_col, notes_col)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def extract_descriptors_to_json(
    studies: List[Dict[str, Any]],
    output_path: Union[str, Path]
) -> None:
    """
    Extracts qualitative notes from valid studies and saves to JSON.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    qualitative_data = []
    for study in studies:
        if study.get("qualitative_notes"):
            qualitative_data.append({
                "study_id": study["study_id"],
                "notes": study["qualitative_notes"]
            })

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(qualitative_data, f, indent=2)
    
    logger.info(f"Saved qualitative notes to {path}")
