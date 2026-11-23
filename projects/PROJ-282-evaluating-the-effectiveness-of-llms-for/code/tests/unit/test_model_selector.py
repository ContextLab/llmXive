import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.model_selector import get_compatible_models, select_model
from src.utils.config import get_candidate_models

@pytest.fixture
def mock_candidate_models():
    # Simulate the candidate list from T004
    return [
        "facebook/opt-125m",
        "google/flan-t5-base",
        "microsoft/phi-2",
        "stabilityai/stable-code-3b"
    ]

@pytest.fixture
def mock_capability_log(tmp_path):
    log_path = tmp_path / "model_capability_check.json"
    data = {
        "passed_models": [
            "facebook/opt-125m",
            "microsoft/phi-2"
        ],
        "failed_models": {
            "google/flan-t5-base": "Tokenizer error for C language",
            "stabilityai/stable-code-3b": "Memory error"
        }
    }
    with open(log_path, 'w') as f:
        json.dump(data, f)
    return str(log_path)

def test_get_compatible_models_filters_correctly(mock_candidate_models, mock_capability_log):
    with patch('src.utils.model_selector.get_candidate_models', return_value=mock_candidate_models):
        result = get_compatible_models(capability_check_log_path=mock_capability_log)
        
        # Should be sorted alphabetically and only include passed models
        expected = ["facebook/opt-125m", "microsoft/phi-2"]
        assert result == expected

def test_select_model_picks_first(mock_candidate_models, mock_capability_log):
    with patch('src.utils.model_selector.get_candidate_models', return_value=mock_candidate_models):
        selected = select_model(capability_check_log_path=mock_capability_log)
        assert selected == "facebook/opt-125m"

def test_select_model_no_compatible(mock_candidate_models, tmp_path):
    # Create a log where no models passed
    log_path = tmp_path / "model_capability_check.json"
    data = {
        "passed_models": [],
        "failed_models": {m: "error" for m in mock_candidate_models}
    }
    with open(log_path, 'w') as f:
        json.dump(data, f)

    with patch('src.utils.model_selector.get_candidate_models', return_value=mock_candidate_models):
        selected = select_model(capability_check_log_path=str(log_path))
        assert selected is None

def test_get_compatible_models_missing_log(mock_candidate_models):
    # If log is missing, it should return all candidates (assuming they passed)
    with patch('src.utils.model_selector.get_candidate_models', return_value=mock_candidate_models):
        result = get_compatible_models(capability_check_log_path="/nonexistent/path.json")
        # Should return all, sorted
        assert result == sorted(mock_candidate_models)
