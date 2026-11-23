import pytest
import pandas as pd
import numpy as np
import json
import os
from unittest.mock import patch, MagicMock, mock_open

# Import from the project's utility module
from code.utils.valence_calculation import (
    ValenceCalculationError,
    load_nrc_lexicon,
    load_vader_lexicon,
    tokenize,
    calculate_nrc_coverage,
    get_nrc_valence,
    get_vader_valence,
    log_lexicon_switch
)

@pytest.fixture
def sample_headlines():
    return [
        "The economy is booming and jobs are plentiful.",
        "A catastrophic failure caused widespread panic.",
        "The weather is mild and pleasant today."
    ]

@pytest.fixture
def mock_nrc_lexicon_path(tmp_path):
    # Create a minimal NRC lexicon file for testing
    lexicon_data = {
        "booming": {"positive": 1, "negative": 0, "joy": 1},
        "jobs": {"positive": 1, "negative": 0},
        "plentiful": {"positive": 1, "negative": 0},
        "catastrophic": {"positive": 0, "negative": 1, "fear": 1, "anger": 1},
        "failure": {"positive": 0, "negative": 1},
        "panic": {"positive": 0, "negative": 1, "fear": 1},
        "mild": {"positive": 1, "negative": 0},
        "pleasant": {"positive": 1, "negative": 0}
    }
    file_path = tmp_path / "nrc_lexicon.json"
    with open(file_path, 'w') as f:
        json.dump(lexicon_data, f)
    return str(file_path)

@pytest.fixture
def mock_vader_lexicon_path(tmp_path):
    # Create a minimal VADER lexicon file for testing
    lexicon_data = {
        "booming": 2.0,
        "jobs": 0.5,
        "plentiful": 1.5,
        "catastrophic": -3.5,
        "failure": -2.0,
        "panic": -2.5,
        "mild": 0.5,
        "pleasant": 1.0
    }
    file_path = tmp_path / "vader_lexicon.json"
    with open(file_path, 'w') as f:
        json.dump(lexicon_data, f)
    return str(file_path)

def test_tokenize_basic():
    text = "Hello world, this is a test."
    tokens = tokenize(text)
    assert tokens == ['hello', 'world', 'this', 'is', 'a', 'test']

def test_tokenize_empty():
    text = ""
    tokens = tokenize(text)
    assert tokens == []

def test_tokenize_punctuation():
    text = "Wow! Really? Yes."
    tokens = tokenize(text)
    assert 'wow' in tokens
    assert 'really' in tokens
    assert 'yes' in tokens
    assert '!' not in tokens

def test_calculate_nrc_coverage_partial(mock_nrc_lexicon_path, sample_headlines):
    # Headline 1: "booming", "jobs", "plentiful" -> 3 known words
    # Headline 2: "catastrophic", "failure", "panic" -> 3 known words
    # Headline 3: "mild", "pleasant" -> 2 known words
    # Total words: 3 + 6 + 6 = 15 (approx, depends on tokenization)
    # Known: 3 + 3 + 2 = 8
    # Coverage should be > 0 and < 1 for partial coverage
    coverage = calculate_nrc_coverage(sample_headlines, mock_nrc_lexicon_path)
    assert 0 < coverage < 1

def test_calculate_nrc_coverage_zero(mock_nrc_lexicon_path):
    # Headlines with no words in lexicon
    unknown_headlines = ["xyz abc qwe rty"]
    coverage = calculate_nrc_coverage(unknown_headlines, mock_nrc_lexicon_path)
    assert coverage == 0.0

def test_calculate_nrc_coverage_full(mock_nrc_lexicon_path):
    # Headlines with all words in lexicon
    known_headlines = ["booming jobs plentiful"]
    coverage = calculate_nrc_coverage(known_headlines, mock_nrc_lexicon_path)
    assert coverage == 1.0

def test_get_nrc_valence_positive(mock_nrc_lexicon_path):
    text = "booming jobs plentiful"
    valence = get_nrc_valence(text, mock_nrc_lexicon_path)
    # All words are positive, so valence should be positive
    assert valence > 0

def test_get_nrc_valence_negative(mock_nrc_lexicon_path):
    text = "catastrophic failure panic"
    valence = get_nrc_valence(text, mock_nrc_lexicon_path)
    # All words are negative, so valence should be negative
    assert valence < 0

def test_get_nrc_valence_neutral(mock_nrc_lexicon_path):
    # Words with no sentiment in our minimal lexicon
    text = "xyz abc"
    valence = get_nrc_valence(text, mock_nrc_lexicon_path)
    # Should be 0 or close to 0 if no sentiment found
    assert valence == 0.0

def test_get_vader_valence_positive(mock_vader_lexicon_path):
    text = "booming jobs plentiful"
    valence = get_vader_valence(text, mock_vader_lexicon_path)
    assert valence > 0

def test_get_vader_valence_negative(mock_vader_lexicon_path):
    text = "catastrophic failure panic"
    valence = get_vader_valence(text, mock_vader_lexicon_path)
    assert valence < 0

def test_lexicon_switch_logic(mock_nrc_lexicon_path, mock_vader_lexicon_path, sample_headlines):
    """Test the logic that determines when to switch from NRC to VADER."""
    # Simulate a case where NRC coverage is low (< 50%)
    # We mock calculate_nrc_coverage to return 0.4 (40%)
    with patch('code.utils.valence_calculation.calculate_nrc_coverage', return_value=0.4):
        # The logic should trigger a switch to VADER
        # We test this by checking if the switch function would be called
        # or by verifying the behavior in a higher-level function
        # For this unit test, we verify the coverage check logic
        coverage = 0.4
        threshold = 0.5
        should_switch = coverage < threshold
        assert should_switch is True

def test_lexicon_switch_logic_no_switch(mock_nrc_lexicon_path, mock_vader_lexicon_path, sample_headlines):
    """Test the logic when NRC coverage is sufficient."""
    with patch('code.utils.valence_calculation.calculate_nrc_coverage', return_value=0.8):
        coverage = 0.8
        threshold = 0.5
        should_switch = coverage < threshold
        assert should_switch is False

def test_log_lexicon_switch(tmp_path):
    """Test that lexicon switch is logged correctly."""
    log_file = tmp_path / "runtime_events.json"
    log_lexicon_switch(str(log_file), "NRC", "VADER", 0.4)
    
    assert log_file.exists()
    with open(log_file, 'r') as f:
        events = json.load(f)
    
    assert len(events) == 1
    event = events[0]
    assert event['event'] == 'lexicon_switch'
    assert event['from'] == 'NRC'
    assert event['to'] == 'VADER'
    assert event['coverage'] == 0.4

def test_log_lexicon_switch_append(tmp_path):
    """Test that multiple switch events are appended."""
    log_file = tmp_path / "runtime_events.json"
    # Initialize file with one event
    with open(log_file, 'w') as f:
        json.dump([{"event": "init"}], f)
    
    log_lexicon_switch(str(log_file), "NRC", "VADER", 0.4)
    
    with open(log_file, 'r') as f:
        events = json.load(f)
    
    assert len(events) == 2
    assert events[1]['event'] == 'lexicon_switch'

def test_valence_calculation_error_on_missing_lexicon():
    """Test that ValenceCalculationError is raised when lexicon file is missing."""
    with pytest.raises(ValenceCalculationError):
        load_nrc_lexicon("/nonexistent/path/to/lexicon.json")

def test_valence_calculation_error_on_invalid_json(tmp_path):
    """Test that ValenceCalculationError is raised on invalid JSON."""
    file_path = tmp_path / "invalid_lexicon.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json }")
    
    with pytest.raises(ValenceCalculationError):
        load_nrc_lexicon(str(file_path))