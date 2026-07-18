import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.data.clean import clean_elastic_data
from src.utils.logging import get_logger

@pytest.fixture
def sample_fcc_data(tmp_path):
    """Create a temporary CSV with sample FCC data including edge cases."""
    data = {
        'id': ['MP-1', 'MP-2', 'MP-3', 'MP-4', 'MP-5'],
        'formula': ['Al', 'Cu', 'Au', 'Ag', 'Fe'], # Fe is BCC usually, but we test logic
        'phase': ['FCC', 'fcc', 'Face-Centered Cubic', 'BCC', 'FCC'],
        'C11': [100.0, 168.0, 192.0, 120.0, 230.0],
        'C12': [50.0, 121.0, 163.0, 90.0, 135.0],
        'C44': [28.0, 75.0, 42.0, 30.0, 116.0],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "raw_input.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def logger():
    return get_logger("test_clean")

def test_clean_fcc_filter(sample_fcc_data, tmp_path, logger):
    """Test that only FCC entries are kept."""
    output_path = tmp_path / "output_clean.csv"
    
    df_result = clean_elastic_data(
        input_path=sample_fcc_data,
        output_path=str(output_path),
        logger=logger
    )
    
    assert len(df_result) == 4, "Should keep 4 FCC entries (MP-1, MP-2, MP-3, MP-5)"
    assert 'BCC' not in df_result['phase'].values, "BCC entry should be removed"
    assert all(df_result['phase'].astype(str).str.lower().str.contains('fcc'))

def test_clean_division_by_zero(tmp_path, logger):
    """Test that entries where C11 == C12 are excluded."""
    data = {
        'id': ['MP-6', 'MP-7'],
        'phase': ['FCC', 'FCC'],
        'C11': [100.0, 100.0],
        'C12': [50.0, 100.0], # MP-7 has C11 == C12
        'C44': [28.0, 28.0],
    }
    input_path = tmp_path / "input_div_zero.csv"
    pd.DataFrame(data).to_csv(input_path, index=False)
    output_path = tmp_path / "output_div_zero.csv"

    df_result = clean_elastic_data(
        input_path=str(input_path),
        output_path=str(output_path),
        logger=logger
    )
    
    assert len(df_result) == 1, "Should exclude the row where C11 == C12"
    assert df_result.iloc[0]['id'] == 'MP-6'

def test_clean_a1_calculation(tmp_path, logger):
    """Test that A1 is calculated correctly: A1 = 2*C44 / (C11 - C12)"""
    data = {
        'id': ['MP-8'],
        'phase': ['FCC'],
        'C11': [100.0],
        'C12': [50.0],
        'C44': [25.0],
    }
    input_path = tmp_path / "input_calc.csv"
    pd.DataFrame(data).to_csv(input_path, index=False)
    output_path = tmp_path / "output_calc.csv"

    df_result = clean_elastic_data(
        input_path=str(input_path),
        output_path=str(output_path),
        logger=logger
    )
    
    # Expected: 2 * 25 / (100 - 50) = 50 / 50 = 1.0
    expected_a1 = 1.0
    assert abs(df_result.iloc[0]['A1'] - expected_a1) < 1e-6

def test_clean_missing_columns_raises(tmp_path, logger):
    """Test that missing C11, C12, or C44 raises an error."""
    data = {
        'id': ['MP-9'],
        'phase': ['FCC'],
        'C11': [100.0],
        # Missing C12 and C44
    }
    input_path = tmp_path / "input_missing.csv"
    pd.DataFrame(data).to_csv(input_path, index=False)
    output_path = tmp_path / "output_missing.csv"

    with pytest.raises(ValueError, match="Missing required columns"):
        clean_elastic_data(
            input_path=str(input_path),
            output_path=str(output_path),
            logger=logger
        )

def test_clean_handles_nan_values(tmp_path, logger):
    """Test that rows with NaN in elastic constants are excluded."""
    data = {
        'id': ['MP-10', 'MP-11'],
        'phase': ['FCC', 'FCC'],
        'C11': [100.0, np.nan],
        'C12': [50.0, 50.0],
        'C44': [25.0, 25.0],
    }
    input_path = tmp_path / "input_nan.csv"
    pd.DataFrame(data).to_csv(input_path, index=False)
    output_path = tmp_path / "output_nan.csv"

    df_result = clean_elastic_data(
        input_path=str(input_path),
        output_path=str(output_path),
        logger=logger
    )
    
    assert len(df_result) == 1
    assert df_result.iloc[0]['id'] == 'MP-10'

def test_clean_output_file_created(sample_fcc_data, tmp_path, logger):
    """Test that the output file is actually created on disk."""
    output_path = tmp_path / "test_output.csv"
    
    clean_elastic_data(
        input_path=sample_fcc_data,
        output_path=str(output_path),
        logger=logger
    )
    
    assert output_path.exists(), "Output file should be created"
    assert output_path.stat().st_size > 0, "Output file should not be empty"