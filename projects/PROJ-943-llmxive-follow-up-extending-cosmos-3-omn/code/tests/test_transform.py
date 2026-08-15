"""
Unit tests for the transformation logic in scripts/transform.py.
Verifies L2 norm calculation, text keyword matching, and composite rule application.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.transform import (
    load_schema,
    compute_l2_norm_first_k,
    check_text_keywords,
    apply_composite_rule,
    process_dataset
)


def test_l2_norm_exact():
    """Test L2 norm calculation with a known vector."""
    # Vector [0.6, 0.8, 0.0] -> sqrt(0.36 + 0.64) = 1.0
    vector = [0.6, 0.8, 0.0, 0.1]
    norm = compute_l2_norm_first_k(vector, k=3)
    assert abs(norm - 1.0) < 1e-6


def test_l2_norm_short_vector():
    """Test L2 norm calculation when vector is shorter than k."""
    vector = [0.5, 0.5]
    # Should handle gracefully or raise; based on impl, let's assume it processes available
    # If implementation requires exact k, this might raise. Assuming it takes min(len, k).
    # For this test, we assume it works on available elements or pads.
    # Let's assume it takes the first k, if less than k, it takes all.
    # sqrt(0.25 + 0.25) = sqrt(0.5) approx 0.707
    norm = compute_l2_norm_first_k(vector, k=3)
    expected = (0.5**2 + 0.5**2)**0.5
    assert abs(norm - expected) < 1e-6


def test_text_keywords_match():
    """Test text keyword detection."""
    text = "This is a Safety Constraint example."
    keywords = ["Safety Constraint", "Warning"]
    assert check_text_keywords(text, keywords) is True


def test_text_keywords_no_match():
    """Test text keyword detection when no match found."""
    text = "This is a normal action."
    keywords = ["Safety Constraint", "Warning"]
    assert check_text_keywords(text, keywords) is False


def test_composite_rule_violated():
    """Test composite rule when both conditions are met (AND operator)."""
    schema = {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND"
    }
    actions = [0.8, 0.6, 0.0] # Norm > 0.5
    text = "Action with Safety Constraint"
    result = apply_composite_rule(actions, text, schema)
    assert result == "constraint_violated"


def test_composite_rule_satisfied_norm_low():
    """Test composite rule when norm is low."""
    schema = {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND"
    }
    actions = [0.1, 0.1, 0.1] # Norm < 0.5
    text = "Action with Safety Constraint"
    result = apply_composite_rule(actions, text, schema)
    assert result == "constraint_satisfied"


def test_composite_rule_satisfied_text_missing():
    """Test composite rule when text keyword is missing."""
    schema = {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND"
    }
    actions = [0.8, 0.6, 0.0] # Norm > 0.5
    text = "Normal action description"
    result = apply_composite_rule(actions, text, schema)
    assert result == "constraint_satisfied"


def test_composite_rule_satisfied_both_false():
    """Test composite rule when both conditions are false."""
    schema = {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND"
    }
    actions = [0.1, 0.1, 0.1] # Norm < 0.5
    text = "Normal action description"
    result = apply_composite_rule(actions, text, schema)
    assert result == "constraint_satisfied"


def test_apply_composite_rule_invalid_actions():
    """Test composite rule with invalid actions (empty or non-numeric)."""
    schema = {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND"
    }
    actions = []
    text = "Action with Safety Constraint"
    # Should handle empty vector gracefully, likely resulting in norm 0 -> satisfied
    result = apply_composite_rule(actions, text, schema)
    assert result == "constraint_satisfied"
