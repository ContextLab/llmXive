import json
import pytest
from pathlib import Path

from main import generate_ingestion_summary

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SUMMARY_FILE = PROCESSED_DIR / "ingestion_summary.json"

REQUIRED_CELL_TYPES = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']

def test_ingestion_summary_schema():
    """
    Contract test validating the schema of data/processed/ingestion_summary.json.
    
    Validates:
    1. File exists.
    2. 'total_peaks' is an integer.
    3. 'cell_types' is a list containing exactly the expected cell type strings.
    4. 'parsed_count' is an integer.
    """
    assert SUMMARY_FILE.exists(), f"Output file {SUMMARY_FILE} does not exist. Run main.py first."

    with open(SUMMARY_FILE, 'r') as f:
        data = json.load(f)

    # Validate top-level keys
    assert 'total_peaks' in data, "Missing 'total_peaks' key"
    assert 'cell_types' in data, "Missing 'cell_types' key"
    assert 'parsed_count' in data, "Missing 'parsed_count' key"

    # Validate types
    assert isinstance(data['total_peaks'], int), f"'total_peaks' must be an int, got {type(data['total_peaks'])}"
    assert isinstance(data['cell_types'], list), f"'cell_types' must be a list, got {type(data['cell_types'])}"
    assert isinstance(data['parsed_count'], int), f"'parsed_count' must be an int, got {type(data['parsed_count'])}"

    # Validate cell_types content
    assert set(data['cell_types']) == set(REQUIRED_CELL_TYPES), (
        f"'cell_types' list mismatch. Expected {REQUIRED_CELL_TYPES}, got {data['cell_types']}"
    )
