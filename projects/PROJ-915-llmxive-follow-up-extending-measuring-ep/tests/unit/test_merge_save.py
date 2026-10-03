"""
Unit tests for merge_save.py (T025).
"""
import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from merge_save import merge_datasets, load_features, load_responses, load_labels
from error_handling import DataRetrievalError, DependencyError

@pytest.fixture
def mock_config(tmp_path):
    return {
        "paths": {
            "processed_features": str(tmp_path / "features.csv"),
            "interim": str(tmp_path / "interim"),
            "labeled_responses": str(tmp_path / "interim" / "labeled_responses.csv")
        }
    }

@pytest.fixture
def mock_features_df():
    return pd.DataFrame({
        "prompt_id": [1, 2, 3],
        "raw_text": ["text1", "text2", "text3"],
        "modal_freq": [0.1, 0.2, 0.3],
        "imperative_ratio": [0.5, 0.6, 0.7]
    })

@pytest.fixture
def mock_responses_df():
    return pd.DataFrame({
        "prompt_id": [1, 2, 3],
        "response_text": ["resp1", "resp2", "resp3"],
        "model_name": ["m1", "m1", "m1"]
    })

@pytest.fixture
def mock_labels_df():
    return pd.DataFrame({
        "prompt_id": [1, 2, 3],
        "adherence_label": [0, 1, 2],
        "safety_refusal": [False, True, False]
    })

def test_merge_datasets_success(mock_features_df, mock_responses_df, mock_labels_df):
    """Test successful merge of all three dataframes."""
    result = merge_datasets(mock_features_df, mock_responses_df, mock_labels_df)
    
    assert len(result) == 3
    assert "prompt_id" in result.columns
    assert "raw_text" in result.columns
    assert "response_text" in result.columns
    assert "adherence_label" in result.columns
    assert "safety_refusal" in result.columns
    
    # Check specific values
    assert result.loc[0, "raw_text"] == "text1"
    assert result.loc[0, "response_text"] == "resp1"
    assert result.loc[0, "adherence_label"] == 0

def test_merge_datasets_missing_prompt_id(mock_features_df, mock_responses_df, mock_labels_df):
    """Test that merge fails if prompt_id is missing in one of the dataframes."""
    # Remove prompt_id from labels
    bad_labels = mock_labels_df.drop(columns=["prompt_id"])
    
    with pytest.raises(DependencyError):
        merge_datasets(mock_features_df, mock_responses_df, bad_labels)

def test_merge_datasets_inner_join(mock_features_df, mock_responses_df, mock_labels_df):
    """Test that merge performs inner join (only matching prompt_ids are kept)."""
    # Modify responses to have a different set of prompt_ids
    bad_responses = pd.DataFrame({
        "prompt_id": [4, 5, 6],
        "response_text": ["r4", "r5", "r6"],
        "model_name": ["m1", "m1", "m1"]
    })
    
    result = merge_datasets(mock_features_df, bad_responses, mock_labels_df)
    assert len(result) == 0

def test_merge_datasets_missing_required_columns(mock_features_df, mock_responses_df, mock_labels_df):
    """Test that merge fails if required columns are missing in the final result."""
    # Remove adherence_label from labels
    bad_labels = mock_labels_df.drop(columns=["adherence_label"])
    
    with pytest.raises(DependencyError):
        merge_datasets(mock_features_df, mock_responses_df, bad_labels)