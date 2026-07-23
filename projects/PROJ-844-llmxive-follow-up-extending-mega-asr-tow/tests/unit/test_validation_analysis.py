"""
Unit tests for code/validation_analysis.py
"""
import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from validation_analysis import (
    compute_human_based_collapse,
    compute_correlation
)

def test_compute_human_based_collapse():
    """Test human-based collapse point calculation."""
    # Mock data: SSS scores and human ratings
    stress_data = [
        {"intensity": 1, "sss": 0.9, "human_score": 5},
        {"intensity": 2, "sss": 0.7, "human_score": 4},
        {"intensity": 3, "sss": 0.5, "human_score": 3},  # Collapse point
        {"intensity": 4, "sss": 0.3, "human_score": 2},
        {"intensity": 5, "sss": 0.1, "human_score": 1}
    ]
    
    collapse_point = compute_human_based_collapse(stress_data)
    
    # Should identify intensity 3 as collapse point (score 3)
    assert collapse_point is not None

def test_compute_correlation():
    """Test correlation computation between SSS and human scores."""
    x = [0.9, 0.7, 0.5, 0.3, 0.1]
    y = [5, 4, 3, 2, 1]
    
    corr, p_value = compute_correlation(x, y)
    
    assert -1 <= corr <= 1
    assert 0 <= p_value <= 1
    # Should be strongly positive correlation
    assert corr > 0.8
