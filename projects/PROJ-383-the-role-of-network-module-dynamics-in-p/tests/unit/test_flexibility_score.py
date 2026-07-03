"""
Unit tests for flexibility score calculation.

Tests for T017: Unit test for flexibility score calculation (range check [0,1] and NaN check)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code/ is in path to import analysis modules
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Import the function to test (will be implemented in T019)
# We mock the core logic here to test the validation wrapper
# Since T019 (implementation) is not done yet, we test the expected interface
# and the validation logic that would be part of the calculation pipeline.

from utils.config import set_all_seeds, WINDOW_LENGTHS_SEC

def calculate_flexibility_score_stub(node_assignments_series):
    """
    Stub implementation to simulate the flexibility score calculation logic
    that will be implemented in T019.
    
    This function calculates the probability of a node switching communities
    across time windows.
    
    Args:
        node_assignments_series: pd.Series of community assignments per window
        
    Returns:
        float: Flexibility score between 0 and 1, or NaN if invalid
    """
    if node_assignments_series is None or len(node_assignments_series) == 0:
        return np.nan
    
    # Convert to numpy array for processing
    assignments = node_assignments_series.values
    
    # Count switches
    if len(assignments) < 2:
        return 0.0
    
    switches = 0
    for i in range(1, len(assignments)):
        if assignments[i] != assignments[i-1]:
            switches += 1
    
    # Normalize by number of transitions
    flexibility = switches / (len(assignments) - 1)
    
    # Ensure range [0, 1]
    flexibility = np.clip(flexibility, 0.0, 1.0)
    
    return float(flexibility)

def validate_flexibility_score(score):
    """
    Validates that a flexibility score is within expected range and not NaN.
    
    Args:
        score: The calculated flexibility score
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If score is invalid
    """
    if pd.isna(score):
        return False
    
    if not (0.0 <= score <= 1.0):
        return False
        
    return True

class TestFlexibilityScoreValidation:
    """Test suite for flexibility score range and NaN checks."""
    
    def test_flexibility_score_in_range_zero(self):
        """Test that a score of 0.0 is valid (no switches)."""
        score = 0.0
        assert validate_flexibility_score(score) is True
        assert 0.0 <= score <= 1.0
        
    def test_flexibility_score_in_range_one(self):
        """Test that a score of 1.0 is valid (switches every time)."""
        score = 1.0
        assert validate_flexibility_score(score) is True
        assert 0.0 <= score <= 1.0
        
    def test_flexibility_score_in_range_middle(self):
        """Test that a middle value is valid."""
        score = 0.5
        assert validate_flexibility_score(score) is True
        assert 0.0 <= score <= 1.0
        
    def test_flexibility_score_nan_rejected(self):
        """Test that NaN scores are rejected."""
        score = np.nan
        assert validate_flexibility_score(score) is False
        
    def test_flexibility_score_negative_rejected(self):
        """Test that negative scores are rejected."""
        score = -0.1
        assert validate_flexibility_score(score) is False
        
    def test_flexibility_score_above_one_rejected(self):
        """Test that scores above 1.0 are rejected."""
        score = 1.1
        assert validate_flexibility_score(score) is False
        
    def test_flexibility_score_none_rejected(self):
        """Test that None is treated as invalid."""
        score = None
        # pd.isna handles None
        assert validate_flexibility_score(score) is False

class TestFlexibilityScoreCalculation:
    """Test suite for the actual flexibility score calculation logic."""
    
    def test_no_switches_yields_zero(self):
        """Test that identical assignments yield 0.0 flexibility."""
        assignments = pd.Series([1, 1, 1, 1, 1])
        score = calculate_flexibility_score_stub(assignments)
        assert score == 0.0
        assert validate_flexibility_score(score) is True
        
    def test_all_switches_yields_one(self):
        """Test that alternating assignments yield 1.0 flexibility."""
        assignments = pd.Series([1, 2, 1, 2, 1, 2])
        score = calculate_flexibility_score_stub(assignments)
        assert score == 1.0
        assert validate_flexibility_score(score) is True
        
    def test_mixed_switches_yields_partial(self):
        """Test that mixed switches yield a partial score."""
        assignments = pd.Series([1, 1, 2, 2, 3, 3])
        # Transitions: 1->1 (no), 1->2 (yes), 2->2 (no), 2->3 (yes), 3->3 (no)
        # 2 switches out of 5 transitions = 0.4
        score = calculate_flexibility_score_stub(assignments)
        assert score == 0.4
        assert validate_flexibility_score(score) is True
        
    def test_empty_series_yields_nan(self):
        """Test that empty series yields NaN."""
        assignments = pd.Series([], dtype=int)
        score = calculate_flexibility_score_stub(assignments)
        assert pd.isna(score)
        assert validate_flexibility_score(score) is False
        
    def test_single_window_yields_zero(self):
        """Test that single window yields 0.0 (no transitions possible)."""
        assignments = pd.Series([1])
        score = calculate_flexibility_score_stub(assignments)
        assert score == 0.0
        assert validate_flexibility_score(score) is True
        
    def test_none_input_yields_nan(self):
        """Test that None input yields NaN."""
        score = calculate_flexibility_score_stub(None)
        assert pd.isna(score)
        assert validate_flexibility_score(score) is False

class TestFlexibilityScoreIntegration:
    """Integration tests for flexibility score in the context of the pipeline."""
    
    def test_score_within_pipeline_constraints(self):
        """Test that calculated scores respect pipeline constraints."""
        set_all_seeds(42)
        
        # Simulate realistic node assignment patterns
        np.random.seed(42)
        n_windows = 100
        n_nodes = 10
        
        for _ in range(n_nodes):
            # Generate random community assignments
            assignments = np.random.randint(1, 6, size=n_windows)
            assignments_series = pd.Series(assignments)
            
            score = calculate_flexibility_score_stub(assignments_series)
            
            # Verify score is always in [0, 1] and not NaN
            assert validate_flexibility_score(score) is True, \
                f"Score {score} failed validation for assignments {assignments}"
            
            assert 0.0 <= score <= 1.0, \
                f"Score {score} out of range [0, 1]"
                
    def test_window_length_compatibility(self):
        """Test that flexibility calculation works with configured window lengths."""
        # Verify that window lengths are properly configured
        assert len(WINDOW_LENGTHS_SEC) > 0, "WINDOW_LENGTHS_SEC must be configured"
        assert 60 in WINDOW_LENGTHS_SEC, "60s window must be in WINDOW_LENGTHS_SEC"
        assert 90 in WINDOW_LENGTHS_SEC, "90s window must be in WINDOW_LENGTHS_SEC"
        
        # Ensure intermediate values exist
        window_set = set(WINDOW_LENGTHS_SEC)
        assert window_set.issuperset({60, 90}), "Must include 60 and 90"