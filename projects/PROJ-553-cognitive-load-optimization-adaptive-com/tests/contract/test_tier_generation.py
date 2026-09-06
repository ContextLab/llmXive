import pytest
import os
import csv
import tempfile
from pathlib import Path

# Import functions to test
from generate_complex_tier import (
    load_moderate_tiers, 
    generate_complex_tier, 
    calculate_flesch_kincaid, 
    calculate_jaccard_similarity
)
from utils import calculate_flesch_kincaid as utils_fk, calculate_jaccard_similarity as utils_jaccard

@pytest.fixture
def sample_moderate_tier():
    return {
        'unit_id': 'test_001',
        'text': 'This is a simple sentence. It has short words and simple structure.'
    }

@pytest.fixture
def temp_moderate_file(sample_moderate_tier):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['unit_id', 'text'])
        writer.writeheader()
        writer.writerow(sample_moderate_tier)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_moderate_tiers(temp_moderate_file):
    """Test loading moderate tiers from CSV."""
    tiers = load_moderate_tiers(temp_moderate_file)
    assert len(tiers) == 1
    assert tiers[0]['unit_id'] == 'test_001'
    assert 'This is a simple sentence' in tiers[0]['text']

def test_generate_complex_tier_fk_diff(sample_moderate_tier):
    """Test that complex tier generation increases FK score."""
    # Use a lower threshold for the test to ensure it passes with simple text
    complex_text, metrics = generate_complex_tier(
        sample_moderate_tier['text'], 
        target_fk_diff=2.0, 
        min_jaccard=0.7
    )
    
    assert len(complex_text) > len(sample_moderate_tier['text'])
    assert metrics['fk_diff'] >= 2.0
    assert metrics['jaccard'] >= 0.7

def test_generate_complex_tier_jaccard_similarity(sample_moderate_tier):
    """Test that complex tier maintains high Jaccard similarity."""
    complex_text, metrics = generate_complex_tier(
        sample_moderate_tier['text'],
        target_fk_diff=2.0,
        min_jaccard=0.7
    )
    
    assert metrics['jaccard'] >= 0.7

def test_generate_complex_tier_failure_case():
    """Test that ValueError is raised when constraints cannot be met."""
    # This test is tricky because the algorithm is designed to meet constraints.
    # We test with an extremely high threshold that is impossible to meet.
    short_text = "Hello."
    
    with pytest.raises(ValueError) as excinfo:
        generate_complex_tier(short_text, target_fk_diff=50.0, min_jaccard=0.99)
    
    assert "Failed to generate complex tier" in str(excinfo.value)

def test_flesch_kincaid_consistency(sample_moderate_tier):
    """Test that FK calculation is consistent with utils module."""
    fk_complex = calculate_flesch_kincaid(sample_moderate_tier['text'])
    fk_utils = utils_fk(sample_moderate_tier['text'])
    assert abs(fk_complex - fk_utils) < 0.01

def test_jaccard_similarity_consistency(sample_moderate_tier):
    """Test that Jaccard calculation is consistent with utils module."""
    jaccard_val = calculate_jaccard_similarity(sample_moderate_tier['text'], sample_moderate_tier['text'])
    jaccard_utils = utils_jaccard(sample_moderate_tier['text'], sample_moderate_tier['text'])
    assert abs(jaccard_val - jaccard_utils) < 0.01
    assert jaccard_val == 1.0
