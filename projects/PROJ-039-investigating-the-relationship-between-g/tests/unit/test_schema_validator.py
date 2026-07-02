"""
Unit tests for Schema Validator (T004)
"""
import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import SchemaValidator, validate_artifacts

@pytest.fixture
def validator():
    return SchemaValidator()

@pytest.fixture
def valid_microbiome_df():
    return pd.DataFrame({
        "subject_id": ["S1", "S2"],
        "age": [25.0, 30.0],
        "sex": ["M", "F"],
        "bmi": [22.0, 24.0],
        "taxa_A": [0.1, 0.2]
    })

@pytest.fixture
def valid_eeg_df():
    return pd.DataFrame({
        "subject_id": ["E1", "E2"],
        "age": [26.0, 31.0],
        "sex": ["M", "F"],
        "alpha_power": [10.5, 12.0]
    })

def test_validate_input_dataset_success(validator, valid_microbiome_df, valid_eeg_df):
    assert validator.validate_input_dataset(valid_microbiome_df, valid_eeg_df) is True

def test_validate_input_dataset_missing_microbiome_col(validator, valid_eeg_df):
    bad_df = valid_microbiome_df.drop(columns=["age"])
    assert validator.validate_input_dataset(bad_df, valid_eeg_df) is False

def test_validate_input_dataset_missing_eeg_col(validator, valid_microbiome_df):
    bad_df = valid_eeg_df.drop(columns=["alpha_power"])
    assert validator.validate_input_dataset(valid_microbiome_df, bad_df) is False

def test_validate_matched_pairs_success(validator):
    df = pd.DataFrame({
        "microbiome_subject_id": ["S1"],
        "eeg_subject_id": ["E1"],
        "age_diff": [1.0],
        "sex_match": [True],
        "bmi_diff": [0.5],
        "matching_score": [0.9]
    })
    assert validator.validate_matched_pairs(df) is True

def test_validate_matched_pairs_missing_col(validator):
    df = pd.DataFrame({
        "microbiome_subject_id": ["S1"],
        "eeg_subject_id": ["E1"]
    })
    assert validator.validate_matched_pairs(df) is False

def test_validate_distribution_groups_success(validator):
    df = pd.DataFrame({
        "subject_id": ["S1", "S2"],
        "group_label": ["High", "Low"],
        "abundance_metric": [10.0, 5.0],
        "alpha_power": [12.0, 11.0]
    })
    assert validator.validate_distribution_groups(df) is True

def test_validate_distribution_groups_invalid_label(validator):
    df = pd.DataFrame({
        "subject_id": ["S1"],
        "group_label": ["Invalid"],
        "abundance_metric": [10.0],
        "alpha_power": [12.0]
    })
    assert validator.validate_distribution_groups(df) is False

def test_validate_analysis_results_success(validator):
    results = {
        "path_selected": "Path A (Matching)",
        "n_pairs": 15,
        "statistical_test": "Spearman",
        "p_value": 0.03,
        "q_value": 0.05,
        "permutation_passed": True,
        "disclaimer": "Note: This analysis is associational only; no causal inference is made."
    }
    assert validator.validate_analysis_results(results) is True

def test_validate_analysis_results_invalid_path(validator):
    results = {
        "path_selected": "Path C (Fake)",
        "n_pairs": 15,
        "statistical_test": "Spearman",
        "p_value": 0.03,
        "q_value": 0.05,
        "permutation_passed": True,
        "disclaimer": "Note: This analysis is associational only; no causal inference is made."
    }
    assert validator.validate_analysis_results(results) is False

def test_validate_analysis_results_missing_disclaimer(validator):
    results = {
        "path_selected": "Path A (Matching)",
        "n_pairs": 15,
        "statistical_test": "Spearman",
        "p_value": 0.03,
        "q_value": 0.05,
        "permutation_passed": True
    }
    assert validator.validate_analysis_results(results) is False
