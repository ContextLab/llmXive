import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.data_merge import merge_datasets, apply_outlier_capping, validate_schemas

@pytest.fixture
def gaze_data():
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P2', 'P2'],
        'headline_id': ['H1', 'H2', 'H1', 'H2'],
        'fixation_duration': [100, 150, 120, 130],
        'roi_type': ['headline_body', 'headline_body', 'headline_body', 'headline_body']
    })

@pytest.fixture
def outcome_data():
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P2', 'P2'],
        'headline_id': ['H1', 'H2', 'H1', 'H2'],
        'belief_rating': [5, 4, 3, 5],
        'headline_text': ['Headline 1', 'Headline 2', 'Headline 3', 'Headline 4']
    })

@pytest.fixture
def valence_data():
    return pd.DataFrame({
        'headline_id': ['H1', 'H2'],
        'valence_score': [0.8, -0.5],
        'lexicon_used': ['NRC', 'NRC']
    })

def test_merge_datasets_basic(gaze_data, outcome_data, valence_data):
    merged = merge_datasets(gaze_data, outcome_data, valence_data)
    assert len(merged) == 4
    assert 'belief_rating' in merged.columns
    assert 'valence_score' in merged.columns
    assert 'fixation_duration' in merged.columns

def test_merge_datasets_missing_keys(gaze_data, outcome_data, valence_data):
    # Remove a key from outcome_data
    outcome_data_no_key = outcome_data.drop(columns=['headline_id'])
    with pytest.raises(ValueError):
        merge_datasets(gaze_data, outcome_data_no_key, valence_data)

def test_apply_outlier_capping_basic():
    data = pd.DataFrame({
        'cognitive_reflection_score': [1, 2, 3, 4, 5, 100, -50]
    })
    capped = apply_outlier_capping(data, 'cognitive_reflection_score', 1, 99)
    # The extreme values should be capped
    assert capped['cognitive_reflection_score'].max() < 100
    assert capped['cognitive_reflection_score'].min() > -50

def test_apply_outlier_capping_no_outliers():
    data = pd.DataFrame({
        'cognitive_reflection_score': [1, 2, 3, 4, 5]
    })
    original = data.copy()
    capped = apply_outlier_capping(data, 'cognitive_reflection_score', 1, 99)
    # No changes expected
    assert capped.equals(original)

def test_validate_schemas_valid(gaze_data, outcome_data):
    required_columns = {
        'gaze': ['participant_id', 'headline_id', 'fixation_duration'],
        'outcome': ['participant_id', 'headline_id', 'belief_rating']
    }
    is_valid, errors = validate_schemas({'gaze': gaze_data, 'outcome': outcome_data}, required_columns)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_schemas_missing_columns(gaze_data, outcome_data):
    # Remove a required column
    outcome_data_no_col = outcome_data.drop(columns=['belief_rating'])
    required_columns = {
        'gaze': ['participant_id', 'headline_id', 'fixation_duration'],
        'outcome': ['participant_id', 'headline_id', 'belief_rating']
    }
    is_valid, errors = validate_schemas({'gaze': gaze_data, 'outcome': outcome_data_no_col}, required_columns)
    assert is_valid is False
    assert 'belief_rating' in errors[0]
