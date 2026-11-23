import pytest
import pandas as pd
from pathlib import Path
import json

# Import functions to test
from validate_tiers import (
    calculate_tier_metrics,
    validate_constraints,
    validate_constraints,
)

@pytest.fixture
def sample_tiers():
    """Create sample DataFrames for testing."""
    simple = pd.DataFrame({
        'interaction_id': [1, 2],
        'text': [
            "The cat sat on the mat.",
            "A dog runs fast."
        ]
    })
    moderate = pd.DataFrame({
        'interaction_id': [1, 2],
        'text': [
            "The feline animal rested on the woven rug.",
            "A canine animal moves with speed."
        ]
    })
    complex = pd.DataFrame({
        'interaction_id': [1, 2],
        'text': [
            "The felid, a domesticated carnivore, assumed a recumbent position upon the fibrous floor covering.",
            "The canine, a swift quadruped, exhibits rapid locomotion."
        ]
    })
    source = pd.DataFrame({
        'interaction_id': [1, 2],
        'text': [
            "The cat sat on the mat.",
            "A dog runs fast."
        ]
    })
    return simple, moderate, complex, source

def test_calculate_tier_metrics_structure(sample_tiers):
    simple, moderate, complex, source = sample_tiers
    metrics = calculate_tier_metrics(simple, moderate, complex, source)
    
    assert isinstance(metrics, list)
    assert len(metrics) == 2
    
    # Check keys
    required_keys = [
        'row_index', 'fk_simple', 'fk_moderate', 'fk_complex',
        'jaccard_simple', 'jaccard_complex',
        'sem_sim_simple', 'sem_sim_complex',
        'fk_diff_simple', 'fk_diff_complex'
    ]
    for m in metrics:
        for key in required_keys:
            assert key in m, f"Missing key: {key}"

def test_validate_constraints_pass():
    # Create metrics that should pass
    metrics = [
        {
            "row_index": 0,
            "fk_diff_simple": 10.0,
            "fk_diff_complex": 10.0,
            "jaccard_simple": 0.90,
            "jaccard_complex": 0.90,
            "sem_sim_simple": 0.95,
            "sem_sim_complex": 0.95,
        }
    ]
    is_valid, errors = validate_constraints(metrics)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_constraints_fail_fk():
    metrics = [
        {
            "row_index": 0,
            "fk_diff_simple": 3.0,  # < 5.0
            "fk_diff_complex": 10.0,
            "jaccard_simple": 0.90,
            "jaccard_complex": 0.90,
            "sem_sim_simple": 0.95,
            "sem_sim_complex": 0.95,
        }
    ]
    is_valid, errors = validate_constraints(metrics)
    assert is_valid is False
    assert any("FK diff (Simple vs Moderate)" in e for e in errors)

def test_validate_constraints_fail_jaccard():
    metrics = [
        {
            "row_index": 0,
            "fk_diff_simple": 10.0,
            "fk_diff_complex": 10.0,
            "jaccard_simple": 0.80,  # < 0.85
            "jaccard_complex": 0.90,
            "sem_sim_simple": 0.95,
            "sem_sim_complex": 0.95,
        }
    ]
    is_valid, errors = validate_constraints(metrics)
    assert is_valid is False
    assert any("Jaccard Simple" in e for e in errors)

def test_validate_constraints_fail_semantic():
    metrics = [
        {
            "row_index": 0,
            "fk_diff_simple": 10.0,
            "fk_diff_complex": 10.0,
            "jaccard_simple": 0.90,
            "jaccard_complex": 0.90,
            "sem_sim_simple": 0.85,  # < 0.90
            "sem_sim_complex": 0.95,
        }
    ]
    is_valid, errors = validate_constraints(metrics)
    assert is_valid is False
    assert any("Semantic Sim Simple" in e for e in errors)
