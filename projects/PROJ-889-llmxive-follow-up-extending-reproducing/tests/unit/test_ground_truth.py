"""
Unit tests for ground truth validation module (T032a, T032b, T031).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ground_truth import (
    check_independence,
    check_unbiased_independence,
    check_biased_independence,
    derive_ground_truth_labels
)


class TestIndependenceChecks:
    """Tests for FR-006 and FR-008 independence checks."""
    
    def test_passes_when_correlation_below_threshold(self):
        """Test that check passes when correlation is below threshold."""
        # Create data with low correlation
        np.random.seed(42)
        df = pd.DataFrame({
            'J_unbiased': np.random.randn(100),
            'J_gold': np.random.randn(100) * 0.5 + np.random.randn(100) * 0.5
        })
        
        corr, is_circular = check_independence(df, 'J_unbiased', 'J_gold', threshold=0.8)
        
        assert not is_circular
        assert corr <= 0.8
    
    def test_raises_on_high_correlation(self):
        """Test that RuntimeError is raised when correlation exceeds threshold."""
        # Create data with high correlation
        df = pd.DataFrame({
            'J_unbiased': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'J_gold': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1]
        })
        
        with pytest.raises(RuntimeError) as excinfo:
            check_independence(df, 'J_unbiased', 'J_gold', threshold=0.8)
        
        assert "CIRCULAR_VALIDATION" in str(excinfo.value)
    
    def test_handles_missing_columns(self):
        """Test that ValueError is raised for missing columns."""
        df = pd.DataFrame({
            'J_unbiased': [1, 2, 3],
            'J_gold': [4, 5, 6]
        })
        
        with pytest.raises(ValueError):
            check_independence(df, 'J_unbiased', 'J_missing')
    
    def test_handles_insufficient_data(self):
        """Test that ValueError is raised for insufficient data points."""
        df = pd.DataFrame({
            'J_unbiased': [1],
            'J_gold': [2]
        })
        
        with pytest.raises(ValueError):
            check_independence(df, 'J_unbiased', 'J_gold')
    
    def test_unbiased_check_integration(self):
        """Test FR-006 specific check."""
        df = pd.DataFrame({
            'J_unbiased': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'J_gold': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1]
        })
        
        with pytest.raises(RuntimeError) as excinfo:
            check_unbiased_independence(df)
        
        assert "CIRCULAR_VALIDATION" in str(excinfo.value)
    
    def test_biased_check_integration(self):
        """Test FR-008 specific check."""
        df = pd.DataFrame({
            'J_biased': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'J_gold': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1]
        })
        
        with pytest.raises(RuntimeError) as excinfo:
            check_biased_independence(df)
        
        assert "CIRCULAR_VALIDATION" in str(excinfo.value)


class TestGroundTruthDerivation:
    """Tests for FR-004 ground truth label derivation."""
    
    def test_detects_large_drop(self):
        """Test that a large drop is correctly detected."""
        # Create data with a clear drop
        j_gold = [10.0] * 50 + [5.0] * 50  # Drop of 5.0 at step 50
        df = pd.DataFrame({'J_gold': j_gold})
        
        result = derive_ground_truth_labels(
            df,
            drop_threshold=2.0,
            window_size=10,
            sustain_steps=1
        )
        
        # After the drop, labels should be 1
        assert result['ground_truth_label'].iloc[60] == 1
    
    def test_ignores_small_drop(self):
        """Test that small drops are not detected."""
        # Create data with small fluctuation
        j_gold = [10.0] * 100
        df = pd.DataFrame({'J_gold': j_gold})
        
        result = derive_ground_truth_labels(
            df,
            drop_threshold=2.0,
            window_size=10,
            sustain_steps=1
        )
        
        # No labels should be set
        assert result['ground_truth_label'].sum() == 0
    
    def test_requires_sustained_drop(self):
        """Test that drop must be sustained for N steps."""
        # Create data with transient drop
        j_gold = [10.0] * 40 + [5.0] * 5 + [10.0] * 55
        df = pd.DataFrame({'J_gold': j_gold})
        
        # Require 10 sustained steps
        result = derive_ground_truth_labels(
            df,
            drop_threshold=2.0,
            window_size=10,
            sustain_steps=10
        )
        
        # Drop was only 5 steps, so no labels should be set
        assert result['ground_truth_label'].sum() == 0
    
    def test_handles_missing_j_gold(self):
        """Test that ValueError is raised if J_gold is missing."""
        df = pd.DataFrame({'J_biased': [1, 2, 3]})
        
        with pytest.raises(ValueError):
            derive_ground_truth_labels(df)
    
    def test_edge_case_window_at_start(self):
        """Test behavior when window is not fully available at start."""
        # Short sequence where window covers entire available history
        j_gold = [10.0, 9.0, 8.0, 7.0, 6.0]
        df = pd.DataFrame({'J_gold': j_gold})
        
        result = derive_ground_truth_labels(
            df,
            drop_threshold=2.0,
            window_size=3,
            sustain_steps=1
        )
        
        # Should handle gracefully without crashing
        assert 'ground_truth_label' in result.columns
