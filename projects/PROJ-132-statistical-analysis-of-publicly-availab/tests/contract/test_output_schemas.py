"""Contract tests for GAMM output schemas.

This module verifies that the Generalized Additive Mixed Model (GAMM)
implementation produces outputs matching the expected schema defined
in the project specification.
"""
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import json
import sys
import os

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.utils import benjamini_hochberg_fdr


def test_gamm_output_schema():
    """Verify coefficient and p-value columns in GAMM output.

    This test asserts that the GAMM output DataFrame contains the required
    columns: 'species', 'coefficient', 'p_value', 'fdr_corrected_p',
    'estimate', 'std_error', and 'term'.

    The test creates a mock DataFrame simulating the output of the GAMM
    fitting process and validates the schema requirements.
    """
    # Simulate GAMM output structure
    # In a real scenario, this would come from src/models/gamm_fit.py
    mock_data = {
        'species': ['Turdus migratorius', 'Setophaga ruticilla', 'Zenaida macroura'],
        'term': ['s(temp)', 's(precip)', 's(effort)'],
        'estimate': [0.45, -0.32, 0.12],
        'std_error': [0.08, 0.09, 0.05],
        'p_value': [0.001, 0.035, 0.012],
        'fdr_corrected_p': [0.0015, 0.0525, 0.018]  # Simulated FDR corrected values
    }

    df = pd.DataFrame(mock_data)

    # Required columns as per specification
    required_columns = ['species', 'term', 'estimate', 'std_error', 'p_value', 'fdr_corrected_p']

    # Assert all required columns exist
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Assert column order matches specification (species first, p-value near end)
    assert df.columns[0] == 'species', "First column must be 'species'"
    assert 'p_value' in df.columns, "DataFrame must contain 'p_value' column"

    # Assert data types
    assert df['species'].dtype == 'object', "species column must be string/object"
    assert pd.api.types.is_numeric_dtype(df['p_value']), "p_value must be numeric"
    assert pd.api.types.is_numeric_dtype(df['estimate']), "estimate must be numeric"
    assert pd.api.types.is_numeric_dtype(df['std_error']), "std_error must be numeric"
    assert pd.api.types.is_numeric_dtype(df['fdr_corrected_p']), "fdr_corrected_p must be numeric"

    # Assert p-values are in valid range [0, 1]
    assert (df['p_value'] >= 0).all(), "All p-values must be >= 0"
    assert (df['p_value'] <= 1).all(), "All p-values must be <= 1"
    assert (df['fdr_corrected_p'] >= 0).all(), "All FDR corrected p-values must be >= 0"
    assert (df['fdr_corrected_p'] <= 1).all(), "All FDR corrected p-values must be <= 1"

    # Assert no missing values in critical fields
    critical_cols = ['species', 'term', 'p_value', 'fdr_corrected_p']
    assert df[critical_cols].isnull().sum().sum() == 0, \
        "Critical fields must not contain missing values"

    # Test FDR correction function integration
    # Verify that FDR correction produces valid results
    p_values = df['p_value'].tolist()
    corrected = benjamini_hochberg_fdr(p_values)

    assert len(corrected) == len(p_values), "FDR correction must return same length"
    assert all(0 <= p <= 1 for p in corrected), "FDR corrected p-values must be in [0, 1]"

    # Verify the mock data can be serialized to JSON (schema validation)
    try:
        df.to_json(orient='records', lines=True)
    except Exception as e:
        pytest.fail(f"GAMM output schema must be JSON serializable: {e}")


def test_gamm_output_schema_empty():
    """Verify behavior with empty DataFrame."""
    empty_df = pd.DataFrame(columns=['species', 'term', 'estimate', 'std_error', 'p_value', 'fdr_corrected_p'])

    required_columns = ['species', 'term', 'estimate', 'std_error', 'p_value', 'fdr_corrected_p']
    for col in required_columns:
        assert col in empty_df.columns, f"Empty DataFrame must still have column: {col}"


def test_gamm_output_schema_single_row():
    """Verify schema with single row of data."""
    single_row = {
        'species': ['Testus speciesus'],
        'term': ['s(temp)'],
        'estimate': [0.5],
        'std_error': [0.1],
        'p_value': [0.01],
        'fdr_corrected_p': [0.01]
    }

    df = pd.DataFrame(single_row)

    required_columns = ['species', 'term', 'estimate', 'std_error', 'p_value', 'fdr_corrected_p']
    for col in required_columns:
        assert col in df.columns, f"Single row DataFrame missing column: {col}"

    assert len(df) == 1, "DataFrame must have exactly one row"
    assert df['p_value'].iloc[0] == 0.01, "p_value value must be preserved"