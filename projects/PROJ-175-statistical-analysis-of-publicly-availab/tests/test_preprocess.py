import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the functions to test
from code.data.preprocess import (
    levenshtein_similarity,
    normalize_ingredient_name,
    build_canonical_map,
    process_chunk_normalize,
    log_event
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_canonical_map():
    """Create a sample canonical ingredient map."""
    return {
        "tomato": "Tomato",
        "onion": "Onion",
        "garlic": "Garlic",
        "salt": "Salt",
        "pepper": "Black Pepper",
        "olive oil": "Olive Oil",
        "chicken breast": "Chicken Breast",
        "ground beef": "Ground Beef",
        "pasta": "Pasta",
        "rice": "Rice"
    }

def test_levenshtein_similarity_exact_match():
    """Test that exact matches return distance 0."""
    assert levenshtein_similarity("tomato", "tomato") == 0
    assert levenshtein_similarity("Onion", "onion") == 0

def test_levenshtein_similarity_small_difference():
    """Test Levenshtein distance for small differences."""
    # "tomatoes" vs "tomato" -> 2 edits (s, e)
    assert levenshtein_similarity("tomatoes", "tomato") == 2
    # "garlic" vs "garlick" -> 1 edit
    assert levenshtein_similarity("garlic", "garlick") == 1

def test_levenshtein_similarity_large_difference():
    """Test Levenshtein distance for large differences."""
    # "salt" vs "pepper" -> very different
    assert levenshtein_similarity("salt", "pepper") > 2

def test_normalize_ingredient_name_exact_match(sample_canonical_map):
    """Test normalization with exact match."""
    result, status = normalize_ingredient_name("tomato", sample_canonical_map)
    assert result == "Tomato"
    assert status == "mapped"

def test_normalize_ingredient_name_within_threshold(sample_canonical_map):
    """Test normalization with Levenshtein distance <= 2."""
    result, status = normalize_ingredient_name("tomatoes", sample_canonical_map)
    assert result == "Tomato"
    assert status == "mapped"

def test_normalize_ingredient_name_exceeds_threshold(sample_canonical_map):
    """Test normalization when distance exceeds threshold."""
    result, status = normalize_ingredient_name("strawberry", sample_canonical_map)
    assert result is None
    assert status == "excluded"

def test_normalize_ingredient_name_empty_input(sample_canonical_map):
    """Test normalization with empty or None input."""
    result, status = normalize_ingredient_name("", sample_canonical_map)
    assert result is None
    assert status == "excluded"

    result, status = normalize_ingredient_name(None, sample_canonical_map)
    assert result is None
    assert status == "excluded"

def test_process_chunk_normalize(sample_canonical_map):
    """Test chunk normalization with a sample dataframe."""
    data = {
        'ingredient_1': ['tomato', 'onion', 'garlic', 'strawberry', ''],
        'ingredient_2': ['olive oil', 'pepper', 'salt', 'chicken', 'rice']
    }
    df = pd.DataFrame(data)
    
    normalized_df, counts = process_chunk_normalize(df, sample_canonical_map)
    
    # Check counts
    assert counts["mapped"] > 0
    assert counts["excluded"] >= 0
    
    # Check that excluded items are NaN
    assert pd.isna(normalized_df.loc[3, 'ingredient_1'])  # strawberry
    assert pd.isna(normalized_df.loc[4, 'ingredient_1'])  # empty
    
    # Check that mapped items are normalized
    assert normalized_df.loc[0, 'ingredient_1'] == "Tomato"
    assert normalized_df.loc[1, 'ingredient_1'] == "Onion"

def test_build_canonical_map_empty():
    """Test canonical map building with no data."""
    # This should return an empty map or a minimal map
    canonical_map = build_canonical_map()
    assert isinstance(canonical_map, dict)

def test_log_event_creates_file(temp_dir):
    """Test that log_event creates the log file if it doesn't exist."""
    # Temporarily change LOG_FILE path for testing
    import code.data.preprocess as preprocess_module
    original_log_file = preprocess_module.LOG_FILE
    test_log_file = Path(temp_dir) / "test_log.json"
    preprocess_module.LOG_FILE = test_log_file
    
    try:
        log_event("Test event", {"key": "value"})
        assert test_log_file.exists()
        
        with open(test_log_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        assert logs[0]["message"] == "Test event"
        assert logs[0]["key"] == "value"
    finally:
        preprocess_module.LOG_FILE = original_log_file

def test_log_event_appends_to_existing(temp_dir):
    """Test that log_event appends to existing log file."""
    import code.data.preprocess as preprocess_module
    original_log_file = preprocess_module.LOG_FILE
    test_log_file = Path(temp_dir) / "test_log.json"
    preprocess_module.LOG_FILE = test_log_file
    
    try:
        # Write initial log
        log_event("First event")
        
        # Append another log
        log_event("Second event")
        
        with open(test_log_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 2
        assert logs[0]["message"] == "First event"
        assert logs[1]["message"] == "Second event"
    finally:
        preprocess_module.LOG_FILE = original_log_file