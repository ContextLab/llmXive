"""
Unit tests for data retrieval and filtering logic.

This module contains tests for the data filtering logic implemented in
code/data/preprocessing.py, specifically focusing on:
1. test_filter_logic: Verifies the core filtering criteria (non-NULL SMILES and logPapp).
2. test_pass_rate_calculation: Verifies the calculation of the pass rate.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or the path is set correctly
project_root = Path(__file__).parent.parent
if str(project_root / 'code') not in sys.path:
    sys.path.insert(0, str(project_root / 'code'))

from data.preprocessing import load_raw_data, preprocess_data, write_clean_data


def create_mock_raw_dataframe() -> pd.DataFrame:
    """
    Creates a mock DataFrame simulating the output of code/data/retrieval.py.
    Includes cases for valid records, NULL SMILES, NULL logPapp, and valid protocol_metadata.
    """
    data = {
        'smiles': [
            'CCO',  # Valid
            None,   # NULL SMILES
            'CCC',  # Valid
            '',     # Empty string (treated as invalid)
            'CCN',  # Valid
            None,   # NULL SMILES
            'CSC',  # Valid
        ],
        'logPapp': [
            -5.0,  # Valid
            -6.0,  # Valid
            None,  # NULL logPapp
            -7.0,  # Valid
            None,  # NULL logPapp
            -8.0,  # Valid
            -9.0,  # Valid
        ],
        'assay_id': [
            'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'
        ],
        'protocol_metadata': [
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
            {'lab_id': 'L1', 'temperature': 37.0, 'passage': 5},
        ]
    }
    return pd.DataFrame(data)


def test_filter_logic(tmp_path: Path):
    """
    Verifies that the filtering logic correctly removes records with NULL or empty SMILES
    and NULL logPapp.

    Requirements:
    - Input: Mock data with 7 records (2 NULL SMILES, 1 empty SMILES, 2 NULL logPapp).
    - Expected Output: 4 valid records.
    """
    # Arrange
    input_df = create_mock_raw_dataframe()
    input_file = tmp_path / 'raw_input.csv'
    output_file = tmp_path / 'filtered_output.csv'

    # Save mock data to simulate raw file
    input_df.to_csv(input_file, index=False)

    # Act
    # Load raw data
    raw_df = load_raw_data(input_file)

    # Preprocess (filter)
    filtered_df, stats = preprocess_data(raw_df)

    # Write clean data (just to ensure the function works end-to-end)
    write_clean_data(filtered_df, output_file)

    # Assert
    # Original count
    assert len(raw_df) == 7

    # Filtered count
    # Valid: Index 0 (CCO), 2 (CCC), 4 (CCN), 6 (CSC) -> 4 records
    # Invalid: Index 1 (None SMILES), 3 ('' SMILES), 5 (None SMILES) -> 3 records removed due to SMILES
    # Invalid: Index 2 (None logPapp - wait, index 2 is CCC with None logPapp? Let's recheck mock data)
    # Mock Data Review:
    # 0: CCO, -5.0 (Valid)
    # 1: None, -6.0 (Invalid SMILES)
    # 2: CCC, None (Invalid logPapp)
    # 3: '', -7.0 (Invalid SMILES)
    # 4: CCN, None (Invalid logPapp)
    # 5: None, -8.0 (Invalid SMILES)
    # 6: CSC, -9.0 (Valid)
    # Total Valid: 0, 6 -> 2 records.
    # Total Invalid: 1, 2, 3, 4, 5 -> 5 records.

    assert len(filtered_df) == 2, f"Expected 2 valid records, got {len(filtered_df)}"

    # Verify specific columns are not null
    assert filtered_df['smiles'].notna().all(), "Filtered data contains NULL SMILES"
    assert filtered_df['logPapp'].notna().all(), "Filtered data contains NULL logPapp"
    
    # Verify empty strings are removed
    assert (filtered_df['smiles'] != '').all(), "Filtered data contains empty SMILES strings"


def test_pass_rate_calculation(tmp_path: Path):
    """
    Verifies that the pass rate is calculated correctly based on the number of
    valid records versus the total number of input records.

    Formula: Pass Rate = (Valid Count / Total Count) * 100
    """
    # Arrange
    input_df = create_mock_raw_dataframe()
    input_file = tmp_path / 'raw_input.csv'
    output_file = tmp_path / 'filtered_output.csv'

    input_df.to_csv(input_file, index=False)

    # Act
    raw_df = load_raw_data(input_file)
    filtered_df, stats = preprocess_data(raw_df)

    # Calculate expected pass rate
    total_records = len(raw_df)
    valid_records = len(filtered_df)
    expected_pass_rate = (valid_records / total_records) * 100

    # Assert
    # Check that stats dictionary contains the pass rate
    assert 'pass_rate' in stats, "stats dictionary missing 'pass_rate' key"
    
    # Verify the calculated pass rate matches expected
    actual_pass_rate = stats['pass_rate']
    assert np.isclose(actual_pass_rate, expected_pass_rate), \
        f"Expected pass rate {expected_pass_rate}, got {actual_pass_rate}"
    
    # Verify total and valid counts in stats
    assert stats['total_records'] == total_records
    assert stats['valid_records'] == valid_records
    
    # Verify excluded count
    expected_excluded = total_records - valid_records
    assert stats['excluded_records'] == expected_excluded