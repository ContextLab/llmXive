"""
Contract test for the Stimulus Generation task (T013).

This test verifies that:
1. The stimuli.csv file exists in data/raw/
2. The CSV has the correct schema (columns and data types)
3. All feature combinations are unique
4. The cue_intensity values are within the expected range [0, 1]
"""

import csv
import json
import os
import pytest
from pathlib import Path

from config import get_raw_data_dir, get_processed_data_dir

STIMULI_PATH = Path(get_raw_data_dir()) / "stimuli.csv"
WEIGHTS_PATH = Path(get_processed_data_dir()) / "cue_intensity_weights.json"

REQUIRED_COLUMNS = [
    "stimulus_id",
    "text",
    "emoji_count",
    "punctuation_type",
    "length_category",
    "scenario_id",
    "cue_intensity"
]

VALID_PUNCTUATION_TYPES = ["standard", "excessive"]
VALID_LENGTH_CATEGORIES = ["short", "long"]

def test_stimuli_file_exists():
    """Test that the stimuli.csv file exists."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"

def test_stimuli_schema():
    """Test that the stimuli.csv has the correct schema."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Check all required columns are present
        for col in REQUIRED_COLUMNS:
            assert col in headers, f"Missing required column: {col}"
        
        # Check for no extra columns
        assert set(headers) == set(REQUIRED_COLUMNS), f"Unexpected columns in CSV. Found: {headers}"

def test_stimuli_data_types():
    """Test that the data types in stimuli.csv are correct."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # emoji_count should be an integer
            assert row["emoji_count"].isdigit(), f"emoji_count is not an integer: {row['emoji_count']}"
            emoji_count = int(row["emoji_count"])
            assert 0 <= emoji_count <= 2, f"emoji_count out of range: {emoji_count}"
            
            # punctuation_type should be valid
            assert row["punctuation_type"] in VALID_PUNCTUATION_TYPES, \
                f"Invalid punctuation_type: {row['punctuation_type']}"
            
            # length_category should be valid
            assert row["length_category"] in VALID_LENGTH_CATEGORIES, \
                f"Invalid length_category: {row['length_category']}"
            
            # cue_intensity should be a float between 0 and 1
            cue_intensity = float(row["cue_intensity"])
            assert 0.0 <= cue_intensity <= 1.0, f"cue_intensity out of range: {cue_intensity}"

def test_unique_feature_combinations():
    """Test that all feature combinations are unique."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    seen_combinations = set()
    duplicates = []
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            combo = (
                row["emoji_count"],
                row["punctuation_type"],
                row["length_category"],
                row["scenario_id"]
            )
            
            if combo in seen_combinations:
                duplicates.append(row["stimulus_id"])
            else:
                seen_combinations.add(combo)
    
    assert len(duplicates) == 0, f"Found duplicate feature combinations: {duplicates}"

def test_stimulus_id_format():
    """Test that stimulus_id follows the expected format."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    import re
    pattern = r"^STIM_\d{4}$"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert re.match(pattern, row["stimulus_id"]), \
                f"Invalid stimulus_id format: {row['stimulus_id']}"

def test_scenario_id_format():
    """Test that scenario_id follows the expected format."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    import re
    pattern = r"^SCEN_\d{3}$"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert re.match(pattern, row["scenario_id"]), \
                f"Invalid scenario_id format: {row['scenario_id']}"

def test_text_not_empty():
    """Test that no text field is empty."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row["text"].strip() != "", f"Empty text found for stimulus {row['stimulus_id']}"

def test_cue_intensity_consistency():
    """Test that cue_intensity values are consistent with the weighting scheme."""
    if not WEIGHTS_PATH.exists():
        pytest.skip(f"Weights file not found at {WEIGHTS_PATH}")
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        weights_data = json.load(f)
    
    # Use the "equal" scheme if available
    weights = weights_data.get("equal", weights_data.get(list(weights_data.keys())[0]))
    
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emoji_count = int(row["emoji_count"])
            punct_type = row["punctuation_type"]
            length_cat = row["length_category"]
            reported_intensity = float(row["cue_intensity"])
            
            # Recalculate expected intensity
            emoji_score = min(emoji_count / 2.0, 1.0)
            punct_score = 1.0 if punct_type == "excessive" else 0.0
            length_score = 1.0 if length_cat == "long" else 0.0
            
            expected_intensity = (
                weights.get("emoji", 0.33) * emoji_score +
                weights.get("punctuation", 0.33) * punct_score +
                weights.get("length", 0.34) * length_score
            )
            
            # Allow small floating point differences
            assert abs(reported_intensity - expected_intensity) < 0.001, \
                f"Cue intensity mismatch for {row['stimulus_id']}: reported={reported_intensity}, expected={expected_intensity}"

def test_minimum_stimuli_count():
    """Test that we have generated a reasonable number of stimuli."""
    assert STIMULI_PATH.exists(), f"Stimuli file not found at {STIMULI_PATH}"
    
    with open(STIMULI_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = sum(1 for _ in reader)
    
    # We expect at least 10 scenarios * 3 emoji * 2 punct * 2 length = 120 stimuli
    assert count >= 120, f"Expected at least 120 stimuli, found {count}"
