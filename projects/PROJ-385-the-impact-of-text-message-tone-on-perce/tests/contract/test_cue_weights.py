"""
Contract test for cue intensity weighting schemes (T090).

This test verifies that the cue_intensity_weights.json file contains
the correct weighting schemes with normalized values.
"""

import json
import pytest
from pathlib import Path

from config import get_processed_data_dir

WEIGHTS_PATH = Path(get_processed_data_dir()) / "cue_intensity_weights.json"

def test_weights_file_exists():
    """Test that the weights file exists."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"

def test_weights_schema():
    """Test that the weights file has the correct structure."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check that we have the three expected schemes
    expected_schemes = ["equal", "emoji_dominant", "punctuation_dominant"]
    for scheme in expected_schemes:
        assert scheme in data, f"Missing scheme: {scheme}"
        
        # Check that each scheme has the three required keys
        weights = data[scheme]
        assert "emoji" in weights, f"Missing 'emoji' key in {scheme}"
        assert "punctuation" in weights, f"Missing 'punctuation' key in {scheme}"
        assert "length" in weights, f"Missing 'length' key in {scheme}"

def test_weights_sum_to_one():
    """Test that all weighting schemes sum to exactly 1.0."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for scheme_name, weights in data.items():
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-10, \
            f"Scheme '{scheme_name}' sums to {total}, not 1.0"

def test_equal_scheme_values():
    """Test that the equal scheme has approximately equal distribution."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    equal_weights = data["equal"]
    
    # Check that all values are approximately 0.3333333333
    for key, value in equal_weights.items():
        assert abs(value - 0.3333333333) < 0.0000000002, \
            f"Equal weight for '{key}' is {value}, expected ~0.3333333333"

def test_emoji_dominant_scheme():
    """Test that the emoji-dominant scheme has majority weight on emoji."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    emoji_weights = data["emoji_dominant"]
    
    # Emoji should have the highest weight (0.6)
    assert emoji_weights["emoji"] > emoji_weights["punctuation"]
    assert emoji_weights["emoji"] > emoji_weights["length"]
    assert abs(emoji_weights["emoji"] - 0.6) < 0.01

def test_punctuation_dominant_scheme():
    """Test that the punctuation-dominant scheme has high weight on punctuation."""
    assert WEIGHTS_PATH.exists(), f"Weights file not found at {WEIGHTS_PATH}"
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    punct_weights = data["punctuation_dominant"]
    
    # Punctuation should have the highest weight (0.6)
    assert punct_weights["punctuation"] > punct_weights["emoji"]
    assert punct_weights["punctuation"] > punct_weights["length"]
    assert abs(punct_weights["punctuation"] - 0.6) < 0.01