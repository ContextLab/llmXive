"""
Unit tests for T026: Survey Simulation Module.
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from survey_sim import (
    SurveyRandomizationError,
    build_variant_map,
    generate_latin_square_order,
    create_participant_sequences,
    generate_synthetic_responses
)
from config import seed_everything

def test_build_variant_map():
    """Test that variants are correctly mapped to scenario IDs."""
    variants = [
        {"id": "v1", "scenario_id": "s1", "salience_level": "low"},
        {"id": "v2", "scenario_id": "s1", "salience_level": "high"},
        {"id": "v3", "scenario_id": "s2", "salience_level": "medium"}
    ]
    
    variant_map = build_variant_map(variants)
    
    assert "s1" in variant_map
    assert "s2" in variant_map
    assert len(variant_map["s1"]) == 2
    assert len(variant_map["s2"]) == 1
    
    # Check salience levels
    s1_levels = [v["salience_level"] for v in variant_map["s1"]]
    assert "low" in s1_levels
    assert "high" in s1_levels

def test_generate_latin_square_order():
    """Test Latin Square generation logic."""
    seed_everything(42)
    scenarios = ["s1", "s2", "s3", "s4"]
    n_levels = 2
    
    # Must be divisible
    sequences = generate_latin_square_order(scenarios, n_levels)
    
    assert len(sequences) == len(scenarios) // n_levels
    # Check that each sequence contains unique scenarios
    for seq in sequences:
        assert len(seq) == len(set(seq))

def test_create_participant_sequences_no_duplicate_salience():
    """
    Verify that a single participant does not see the same scenario 
    with the same salience level twice.
    """
    seed_everything(42)
    
    scenarios = [
        {"id": "s1"}, {"id": "s2"}, {"id": "s3"}, {"id": "s4"}
    ]
    
    variants = [
        {"id": "v1", "scenario_id": "s1", "salience_level": "low"},
        {"id": "v2", "scenario_id": "s1", "salience_level": "high"},
        {"id": "v3", "scenario_id": "s2", "salience_level": "low"},
        {"id": "v4", "scenario_id": "s2", "salience_level": "high"},
        {"id": "v5", "scenario_id": "s3", "salience_level": "low"},
        {"id": "v6", "scenario_id": "s3", "salience_level": "high"},
        {"id": "v7", "scenario_id": "s4", "salience_level": "low"},
        {"id": "v8", "scenario_id": "s4", "salience_level": "high"}
    ]
    
    variants_map = build_variant_map(variants)
    
    sequences = create_participant_sequences(scenarios, variants_map, n_participants=4, seed=42)
    
    for seq_data in sequences:
        seen_pairs = set()
        for item in seq_data["sequence"]:
            pair = (item["scenario_id"], item["salience_level"])
            assert pair not in seen_pairs, f"Duplicate scenario/salience pair found: {pair}"
            seen_pairs.add(pair)

def test_generate_synthetic_responses_structure():
    """Test that synthetic responses have the correct structure."""
    seed_everything(42)
    
    sequences = [
        {
            "participant_id": "P001",
            "sequence": [
                {"scenario_id": "s1", "stimulus_id": "v1", "salience_level": "low", "order": 0}
            ]
        }
    ]
    
    responses = generate_synthetic_responses(sequences, seed=42)
    
    assert len(responses) == 1
    r = responses[0]
    assert "participant_id" in r
    assert "stimulus_id" in r
    assert "scenario_id" in r
    assert "salience_level" in r
    assert "rating" in r
    assert "timestamp" in r
    assert 1 <= r["rating"] <= 5