"""
Unit tests for data filtering logic in code/data/preprocessing.py.
These tests verify the filtering logic and pass rate calculation as required by T011.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root or the path is configured correctly
project_root = Path(__file__).resolve().parent.parent
if str(project_root / 'code') not in sys.path:
    sys.path.insert(0, str(project_root / 'code'))

from data.preprocessing import (
    load_raw_data,
    parse_protocol_metadata,
    check_protocol_heterogeneity,
    preprocess_data,
    write_clean_data
)


def create_mock_raw_data(tmp_path):
    """Helper to create a mock CSV file for testing."""
    data = [
        {
            "smiles": "CCO",
            "logPapp": -4.5,
            "assay_id": "1",
            "protocol_metadata": json.dumps({"standard_type": "MEASUREMENT", "heterogeneity_score": 0.1})
        },
        {
            "smiles": "CC(C)C",
            "logPapp": -5.2,
            "assay_id": "2",
            "protocol_metadata": json.dumps({"standard_type": "MEASUREMENT", "heterogeneity_score": 0.2})
        },
        {
            "smiles": None,
            "logPapp": -4.0,
            "assay_id": "3",
            "protocol_metadata": json.dumps({"standard_type": "MEASUREMENT", "heterogeneity_score": 0.1})
        },
        {
            "smiles": "CCCC",
            "logPapp": None,
            "assay_id": "4",
            "protocol_metadata": json.dumps({"standard_type": "MEASUREMENT", "heterogeneity_score": 0.1})
        },
        {
            "smiles": "CCCCC",
            "logPapp": -6.0,
            "assay_id": "5",
            "protocol_metadata": json.dumps({"standard_type": "ESTIMATE", "heterogeneity_score": 0.9})
        },
        {
            "smiles": "CCCCCC",
            "logPapp": -6.5,
            "assay_id": "6",
            "protocol_metadata": json.dumps({"standard_type": "MEASUREMENT", "heterogeneity_score": 0.8})
        }
    ]
    csv_path = tmp_path / "mock_raw.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


def test_filter_logic(tmp_path):
    """
    Test that the filtering logic correctly removes records with NULL SMILES,
    NULL logPapp, and those excluded due to protocol heterogeneity.
    """
    csv_path = create_mock_raw_data(tmp_path)
    output_path = tmp_path / "filtered_output.csv"

    # Load raw data
    raw_df = load_raw_data(csv_path)

    # Parse protocol metadata
    raw_df['protocol_metadata_parsed'] = raw_df['protocol_metadata'].apply(parse_protocol_metadata)

    # Check heterogeneity (exclude if standard_type != 'MEASUREMENT' or heterogeneity_score > 0.7)
    # Based on typical logic inferred from task descriptions
    heterogeneity_mask = raw_df['protocol_metadata_parsed'].apply(
        lambda x: check_protocol_heterogeneity(x, threshold=0.7)
    )

    # Apply filters
    filtered_df = preprocess_data(
        raw_df,
        smiles_col='smiles',
        logPapp_col='logPapp',
        heterogeneity_mask=heterogeneity_mask
    )

    # Assertions
    assert len(filtered_df) == 2, f"Expected 2 valid records, got {len(filtered_df)}"
    
    # Check that NULL SMILES and NULL logPapp are removed
    assert filtered_df['smiles'].isnull().sum() == 0
    assert filtered_df['logPapp'].isnull().sum() == 0

    # Check that 'ESTIMATE' type and high heterogeneity scores are removed
    # Record 5: ESTIMATE (removed)
    # Record 6: MEASUREMENT but heterogeneity_score 0.8 > 0.7 (removed)
    # Record 0, 1: Valid
    # Record 2: NULL SMILES (removed)
    # Record 3: NULL logPapp (removed)
    
    smiles_list = filtered_df['smiles'].tolist()
    assert "CCO" in smiles_list
    assert "CC(C)C" in smiles_list
    assert "CCCCC" not in smiles_list
    assert "CCCCCC" not in smiles_list


def test_pass_rate_calculation(tmp_path):
    """
    Test that the pass rate is calculated correctly.
    Pass rate = (Number of valid records) / (Total number of raw records)
    """
    csv_path = create_mock_raw_data(tmp_path)
    output_path = tmp_path / "filtered_output.csv"

    raw_df = load_raw_data(csv_path)
    total_records = len(raw_df)

    raw_df['protocol_metadata_parsed'] = raw_df['protocol_metadata'].apply(parse_protocol_metadata)
    heterogeneity_mask = raw_df['protocol_metadata_parsed'].apply(
        lambda x: check_protocol_heterogeneity(x, threshold=0.7)
    )

    filtered_df = preprocess_data(
        raw_df,
        smiles_col='smiles',
        logPapp_col='logPapp',
        heterogeneity_mask=heterogeneity_mask
    )

    valid_records = len(filtered_df)
    pass_rate = valid_records / total_records if total_records > 0 else 0.0

    # Expected: 2 valid out of 6 total
    expected_pass_rate = 2 / 6

    assert abs(pass_rate - expected_pass_rate) < 1e-6, f"Pass rate {pass_rate} does not match expected {expected_pass_rate}"

    # Verify the pass rate is reported (log or returned value check if applicable)
    # Since preprocess_data returns the dataframe, we calculate it here to verify the logic
    assert 0.3333 <= pass_rate <= 0.3334