"""
Contract tests for T090: Cue-Intensity Weighting Schemes.

Verifies that data/processed/cue_intensity_weights.json exists and contains
the exact numeric values specified in the task requirements.
"""
import json
import pytest
from pathlib import Path

from config import get_processed_data_dir


@pytest.fixture
def weights_file_path() -> Path:
    """Returns the path to the cue_intensity_weights.json file."""
    return get_processed_data_dir() / "cue_intensity_weights.json"

@pytest.fixture
def weights_data(weights_file_path: Path) -> dict:
    """Loads the weights data from the JSON file."""
    if not weights_file_path.exists():
        pytest.fail(f"File {weights_file_path} does not exist. Run code/090_define_cue_weights.py first.")
    
    with open(weights_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_file_exists(weights_file_path: Path) -> None:
    """Test that the output file exists."""
    assert weights_file_path.exists(), "cue_intensity_weights.json must exist in data/processed/"

def test_required_schemes_present(weights_data: dict) -> None:
    """Test that all three required schemes are present."""
    required_schemes = {"Equal", "Emoji-Dominant", "Punctuation-Dominant"}
    assert set(weights_data.keys()) == required_schemes, \
        f"Expected schemes {required_schemes}, got {set(weights_data.keys())}"

def test_equal_weights(weights_data: dict) -> None:
    """Test the Equal weighting scheme values."""
    expected = {"emoji": 0.33, "punctuation": 0.33, "length": 0.34}
    actual = weights_data["Equal"]
    assert actual == expected, f"Equal weights mismatch: expected {expected}, got {actual}"

def test_emoji_dominant_weights(weights_data: dict) -> None:
    """Test the Emoji-Dominant weighting scheme values."""
    expected = {"emoji": 0.6, "punctuation": 0.2, "length": 0.2}
    actual = weights_data["Emoji-Dominant"]
    assert actual == expected, f"Emoji-Dominant weights mismatch: expected {expected}, got {actual}"

def test_punctuation_dominant_weights(weights_data: dict) -> None:
    """Test the Punctuation-Dominant weighting scheme values."""
    expected = {"emoji": 0.2, "punctuation": 0.6, "length": 0.2}
    actual = weights_data["Punctuation-Dominant"]
    assert actual == expected, f"Punctuation-Dominant weights mismatch: expected {expected}, got {actual}"

def test_weights_sum_to_one(weights_data: dict) -> None:
    """Test that weights for each scheme sum to 1.0 (within floating point tolerance)."""
    for scheme_name, weights in weights_data.items():
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6, \
            f"Weights for {scheme_name} sum to {total}, expected 1.0"