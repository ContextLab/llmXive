"""
Contract test for T013: Verify hard abort logic (E-DATA-001).

This test simulates a missing 'adhesion_energy' field or a dataset with <100 rows
and asserts that `code/data/clean.py` raises `DataError` with the specific
error code and message, preventing silent fallback to synthetic data.

Plan Override: Validates the "hard abort" strategy overriding Spec FR-001's NIST fallback.
"""
import os
import sys
import tempfile
import csv
import pytest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.exceptions import DataError
from data.clean import clean_and_validate


def test_hard_abort_missing_adhesion_energy():
    """
    Verify that clean_and_validate raises DataError (E-DATA-001)
    when the 'adhesion_energy' column is missing from the input data.
    """
    # Create a temporary CSV file with missing 'adhesion_energy' column
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        # Header missing 'adhesion_energy'
        writer.writerow(['polymer_smiles', 'filler_smiles'])
        writer.writerow(['CCO', 'CC'])
        writer.writerow(['CCCO', 'CCC'])
        temp_input_path = f.name

    temp_output_path = tempfile.mktemp(suffix='_curated.csv')

    try:
        # Attempt to clean and validate
        # This should raise DataError
        clean_and_validate(temp_input_path, temp_output_path)
        pytest.fail("Expected DataError to be raised for missing adhesion_energy column.")
    except DataError as e:
        # Verify the specific error code and message pattern
        error_msg = str(e)
        assert "E-DATA-001" in error_msg, f"Expected error code E-DATA-001 in message: {error_msg}"
        assert "adhesion_energy" in error_msg, f"Expected 'adhesion_energy' mentioned in error: {error_msg}"
        assert "missing" in error_msg.lower() or "field" in error_msg.lower(), \
            f"Expected 'missing' or 'field' in error: {error_msg}"
    finally:
        # Cleanup
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


def test_hard_abort_insufficient_rows():
    """
    Verify that clean_and_validate raises DataError (E-DATA-001)
    when the dataset has fewer than 100 rows.
    """
    # Create a temporary CSV file with <100 rows (e.g., 10 rows)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['polymer_smiles', 'filler_smiles', 'adhesion_energy'])
        for i in range(10):  # Only 10 rows
            writer.writerow([f'CC{i}', f'CC{i}', f'{0.5 + i * 0.1}'])
        temp_input_path = f.name

    temp_output_path = tempfile.mktemp(suffix='_curated.csv')

    try:
        # Attempt to clean and validate
        # This should raise DataError
        clean_and_validate(temp_input_path, temp_output_path)
        pytest.fail("Expected DataError to be raised for insufficient row count (<100).")
    except DataError as e:
        # Verify the specific error code and message pattern
        error_msg = str(e)
        assert "E-DATA-001" in error_msg, f"Expected error code E-DATA-001 in message: {error_msg}"
        assert "100" in error_msg or "row" in error_msg.lower(), \
            f"Expected row count threshold mentioned in error: {error_msg}"
    finally:
        # Cleanup
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)