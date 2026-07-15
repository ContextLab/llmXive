"""
Contract test for SHAP output format.
"""
import pytest
import json
import numpy as np
from code.interpret.shap_analysis import validate_consensus

@pytest.fixture
def sample_shap_values():
    """Create sample SHAP values."""
    features = ['polarizability', 'kinetic_diameter', 'molecular_weight', 'surface_area']
    shap_values = {
        'polarizability': np.array([0.5, -0.3, 0.8, 0.2]),
        'kinetic_diameter': np.array([-0.2, 0.4, -0.1, 0.6]),
        'molecular_weight': np.array([0.1, 0.1, 0.1, 0.1]),
        'surface_area': np.array([-0.1, -0.1, -0.1, -0.1])
    }
    return shap_values

@pytest.fixture
def sample_feature_importance():
    """Create sample feature importance data."""
    return {
        'polarizability': 0.45,
        'kinetic_diameter': 0.30,
        'molecular_weight': 0.15,
        'surface_area': 0.10
    }

@pytest.fixture
def consensus_list():
    """Return the literature consensus list of important features."""
    return [
        'polarizability',
        'kinetic_diameter',
        'lennard_jones_energy',
        'quadrupole_moment',
        'molecular_volume'
    ]

def test_validate_consensus_structure(sample_feature_importance, consensus_list):
    """Test that consensus validation returns expected structure."""
    # Get top 3 features by importance
    top_features = sorted(
        sample_feature_importance.keys(),
        key=lambda k: sample_feature_importance[k],
        reverse=True
    )[:3]
    
    result = validate_consensus(top_features, consensus_list)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'matched_features' in result, "Missing matched_features"
    assert 'unmatched_features' in result, "Missing unmatched_features"
    assert 'consensus_score' in result, "Missing consensus_score"
    assert 'is_passed' in result, "Missing is_passed"
    
    # Check that matched and unmatched are lists
    assert isinstance(result['matched_features'], list), "matched_features should be a list"
    assert isinstance(result['unmatched_features'], list), "unmatched_features should be a list"
    
    # Check that consensus_score is numeric
    assert isinstance(result['consensus_score'], (int, float)), "consensus_score should be numeric"
    
    # Check that is_passed is boolean
    assert isinstance(result['is_passed'], bool), "is_passed should be boolean"

def test_validate_consensus_logic(sample_feature_importance, consensus_list):
    """Test that consensus validation logic is correct."""
    # Get top 3 features by importance
    top_features = sorted(
        sample_feature_importance.keys(),
        key=lambda k: sample_feature_importance[k],
        reverse=True
    )[:3]
    
    result = validate_consensus(top_features, consensus_list)
    
    # polarizability and kinetic_diameter are in consensus list
    expected_matched = ['polarizability', 'kinetic_diameter']
    expected_unmatched = ['molecular_weight']
    
    assert set(result['matched_features']) == set(expected_matched), \
        f"Expected matched: {expected_matched}, got: {result['matched_features']}"
    assert set(result['unmatched_features']) == set(expected_unmatched), \
        f"Expected unmatched: {expected_unmatched}, got: {result['unmatched_features']}"
    
    # Consensus score should be 2/3 (66.7%)
    assert result['consensus_score'] == pytest.approx(0.667, abs=0.01), \
        f"Expected consensus score ~0.667, got {result['consensus_score']}"

def test_validate_consensus_threshold(sample_feature_importance, consensus_list):
    """Test that the is_passed flag respects the threshold."""
    top_features = sorted(
        sample_feature_importance.keys(),
        key=lambda k: sample_feature_importance[k],
        reverse=True
    )[:3]
    
    result = validate_consensus(top_features, consensus_list)
    
    # With 2/3 features matching, should pass the 50% threshold
    assert result['is_passed'] is True, \
        "Should pass with 66.7% consensus (>= 50% threshold)"

def test_validate_consensus_json_serializable(sample_feature_importance, consensus_list):
    """Test that the result can be serialized to JSON."""
    top_features = sorted(
        sample_feature_importance.keys(),
        key=lambda k: sample_feature_importance[k],
        reverse=True
    )[:3]
    
    result = validate_consensus(top_features, consensus_list)
    
    # Should be able to serialize to JSON
    json_str = json.dumps(result)
    assert json_str is not None, "JSON serialization should succeed"
    
    # Should be able to deserialize back
    loaded = json.loads(json_str)
    assert loaded == result, "Deserialized JSON should match original"