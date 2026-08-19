import csv
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ENRICHMENT_FILE = PROCESSED_DIR / "enrichment_matrix.csv"

REQUIRED_CELL_TYPES = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']

def test_enrichment_matrix_schema():
    """
    Contract test validating the schema of data/processed/enrichment_matrix.csv.
    
    Validates:
    1. File exists.
    2. Contains required columns: motif_id, cell_type, p_value, q_value.
    3. motif_id is a string.
    4. q_value is a float.
    5. cell_type contains only expected values.
    """
    assert ENRICHMENT_FILE.exists(), f"Output file {ENRICHMENT_FILE} does not exist. Run main.py first."

    with open(ENRICHMENT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        fieldnames = reader.fieldnames
        assert fieldnames is not None, "CSV file is empty or has no headers"
        assert 'motif_id' in fieldnames, "Missing 'motif_id' column"
        assert 'cell_type' in fieldnames, "Missing 'cell_type' column"
        assert 'p_value' in fieldnames, "Missing 'p_value' column"
        assert 'q_value' in fieldnames, "Missing 'q_value' column"

        rows = list(reader)
        assert len(rows) > 0, "CSV file has no data rows"

        for i, row in enumerate(rows):
            # Validate motif_id is string (already string from CSV, but check non-empty)
            assert isinstance(row['motif_id'], str), f"Row {i}: 'motif_id' must be string"
            assert row['motif_id'], f"Row {i}: 'motif_id' cannot be empty"

            # Validate q_value is float
            try:
                q_val = float(row['q_value'])
                assert isinstance(q_val, float), f"Row {i}: 'q_value' must be convertible to float"
            except ValueError:
                pytest.fail(f"Row {i}: 'q_value' value '{row['q_value']}' is not a valid float")

            # Validate cell_type
            assert row['cell_type'] in REQUIRED_CELL_TYPES, (
                f"Row {i}: Unexpected cell_type '{row['cell_type']}'. Expected one of {REQUIRED_CELL_TYPES}"
            )