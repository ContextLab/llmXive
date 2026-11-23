"""
Unit tests for Task T090: Cue Intensity Weighting Schemes.

Verifies that the generated JSON file exists and contains the correct
structure and values for the four required schemes.
"""
import json
import os
import pytest
from pathlib import Path
from config import get_processed_data_dir

# Expected values from the task description
EXPECTED_SCHEMES = {
    "Primary": {"emoji": 0.4, "punctuation": 0.3, "text": 0.3},
    "Equal": {"emoji": 0.33, "punctuation": 0.33, "text": 0.33},
    "Emoji-Dominant": {"emoji": 0.6, "punctuation": 0.2, "text": 0.2},
    "Punctuation-Dominant": {"emoji": 0.2, "punctuation": 0.6, "text": 0.2}
}

@pytest.fixture
def weights_file_path():
    return get_processed_data_dir() / "cue_intensity_weights.json"

@pytest.fixture
def weights_data(weights_file_path):
    if not weights_file_path.exists():
        pytest.fail(f"File {weights_file_path} does not exist. Run code/090_define_cue_weights.py first.")
    
    with open(weights_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_file_exists(weights_file_path):
    """Verification: JSON file exists."""
    assert weights_file_path.exists(), "cue_intensity_weights.json must exist in data/processed/"

def test_has_four_schemes(weights_data):
    """Verification: JSON contains four scheme objects."""
    assert len(weights_data) == 4, f"Expected 4 schemes, found {len(weights_data)}"
    required_keys = {"Primary", "Equal", "Emoji-Dominant", "Punctuation-Dominant"}
    assert set(weights_data.keys()) == required_keys, f"Missing or extra schemes. Expected: {required_keys}, Found: {set(weights_data.keys())}"

def test_primary_scheme_weights(weights_data):
    """Verification: Primary (0.4/0.3/0.3)."""
    scheme = weights_data["Primary"]
    assert abs(scheme["emoji"] - 0.4) < 1e-6, "Primary emoji weight mismatch"
    assert abs(scheme["punctuation"] - 0.3) < 1e-6, "Primary punctuation weight mismatch"
    assert abs(scheme["text"] - 0.3) < 1e-6, "Primary text weight mismatch"

def test_equal_scheme_weights(weights_data):
    """Verification: Equal (0.33/0.33/0.33)."""
    scheme = weights_data["Equal"]
    assert abs(scheme["emoji"] - 0.33) < 1e-6, "Equal emoji weight mismatch"
    assert abs(scheme["punctuation"] - 0.33) < 1e-6, "Equal punctuation weight mismatch"
    assert abs(scheme["text"] - 0.33) < 1e-6, "Equal text weight mismatch"

def test_emoji_dominant_scheme_weights(weights_data):
    """Verification: Emoji-Dominant (0.6/0.2/0.2)."""
    scheme = weights_data["Emoji-Dominant"]
    assert abs(scheme["emoji"] - 0.6) < 1e-6, "Emoji-Dominant emoji weight mismatch"
    assert abs(scheme["punctuation"] - 0.2) < 1e-6, "Emoji-Dominant punctuation weight mismatch"
    assert abs(scheme["text"] - 0.2) < 1e-6, "Emoji-Dominant text weight mismatch"

def test_punctuation_dominant_scheme_weights(weights_data):
    """Verification: Punctuation-Dominant (0.2/0.6/0.2)."""
    scheme = weights_data["Punctuation-Dominant"]
    assert abs(scheme["emoji"] - 0.2) < 1e-6, "Punctuation-Dominant emoji weight mismatch"
    assert abs(scheme["punctuation"] - 0.6) < 1e-6, "Punctuation-Dominant punctuation weight mismatch"
    assert abs(scheme["text"] - 0.2) < 1e-6, "Punctuation-Dominant text weight mismatch"

def test_weights_sum_to_one(weights_data):
    """Verification: All scheme weights sum to 1.0 (within floating point tolerance)."""
    for name, scheme in weights_data.items():
        total = scheme["emoji"] + scheme["punctuation"] + scheme["text"]
        assert abs(total - 1.0) < 1e-5, f"Scheme '{name}' weights sum to {total}, expected 1.0"