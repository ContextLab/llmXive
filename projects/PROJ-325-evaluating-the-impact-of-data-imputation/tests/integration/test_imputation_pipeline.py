"""
Integration tests for the Complete-Case analysis logic in imputation_pipeline.py.

These tests verify that:
1. Complete-case filtering correctly removes rows with missing values.
2. Design variables are preserved and checked.
3. The variance estimation step runs successfully on complete cases.
4. Error handling works when no complete cases exist.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from imputation_pipeline import perform_complete_case_analysis, run_complete_case_pipeline
from data_ingestion import detect_missingness


@pytest.fixture
def sample_survey_data():
    """
    Creates a synthetic DataFrame mimicking survey data with design variables
    and some missing values.
    """
    data = {
        'id': range(1, 11),
        'weight': [1.0] * 10,
        'psu': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
        'strata': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
        'hours': [40.0, 35.0, np.nan, 45.0, 30.0, np.nan, 50.0, 40.0, 35.0, 42.0],
        'age': [30, 25, 40, 35, 28, 32, 45, 29, 31, 33]
    }
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def sample_survey_data_no_complete():
    """
    Creates a DataFrame where the target variable is missing for all rows
    (or combined with design variables missing such that no row is complete).
    """
    data = {
        'id': range(1, 6),
        'weight': [1.0, 1.0, 1.0, 1.0, 1.0],
        'psu': [1, 1, 2, 2, 3],
        'strata': [1, 1, 2, 2, 3],
        'hours': [np.nan, np.nan, np.nan, np.nan, np.nan], # All missing
        'age': [30, 25, 40, 35, 28]
    }
    return pd.DataFrame(data)


def test_perform_complete_case_analysis_filters_correctly(sample_survey_data):
    """
    Test that perform_complete_case_analysis correctly filters out rows
    with missing values in the target variable or design variables.
    """
    df = sample_survey_data
    target_var = 'hours'
    design_vars = ['weight', 'psu', 'strata']

    filtered_df, summary = perform_complete_case_analysis(df, target_var, design_vars)

    # Expected: Rows 3 and 6 (index 2 and 5) have NaN in 'hours'
    # So we expect 10 - 2 = 8 rows remaining.
    assert len(filtered_df) == 8, f"Expected 8 rows, got {len(filtered_df)}"
    assert summary['total_rows'] == 10
    assert summary['complete_rows'] == 8
    assert summary['dropped_rows'] == 2
    assert summary['missing_count'] == 2
    assert summary['status'] == 'success'

    # Verify no NaN in target or design columns
    assert filtered_df[target_var].notna().all()
    for col in design_vars:
        assert filtered_df[col].notna().all()


def test_perform_complete_case_analysis_missing_design_vars(sample_survey_data):
    """
    Test that the function raises an error if design variables are missing
    from the DataFrame.
    """
    df = sample_survey_data.drop(columns=['psu'])
    target_var = 'hours'
    design_vars = ['weight', 'psu', 'strata']

    with pytest.raises(ValueError) as excinfo:
        perform_complete_case_analysis(df, target_var, design_vars)
    
    assert "Design variables missing" in str(excinfo.value)
    assert "psu" in str(excinfo.value)


def test_perform_complete_case_analysis_no_complete_cases(sample_survey_data_no_complete):
    """
    Test behavior when no complete cases exist.
    """
    df = sample_survey_data_no_complete
    target_var = 'hours'
    design_vars = ['weight', 'psu', 'strata']

    filtered_df, summary = perform_complete_case_analysis(df, target_var, design_vars)

    assert len(filtered_df) == 0
    assert summary['complete_rows'] == 0
    assert summary['status'] == 'failure'


def test_run_complete_case_pipeline_success(sample_survey_data):
    """
    Test the full pipeline including variance estimation.
    """
    df = sample_survey_data
    target_var = 'hours'
    design_vars = ['weight', 'psu', 'strata']

    result = run_complete_case_pipeline(df, target_var, design_vars)

    assert result['status'] == 'success'
    assert result['target_variable'] == target_var
    assert 'variance_estimate' in result
    assert result['variance_estimate'] is not None
    assert 'mean' in result['variance_estimate']
    assert 'variance' in result['variance_estimate']
    assert result['summary']['complete_rows'] == 8


def test_run_complete_case_pipeline_failure_no_cases(sample_survey_data_no_complete):
    """
    Test the full pipeline when no complete cases exist.
    """
    df = sample_survey_data_no_complete
    target_var = 'hours'
    design_vars = ['weight', 'psu', 'strata']

    result = run_complete_case_pipeline(df, target_var, design_vars)

    assert result['status'] == 'failure'
    assert result['variance_estimate'] is None
    assert 'error' in result