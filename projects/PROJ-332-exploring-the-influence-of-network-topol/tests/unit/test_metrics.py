import pytest
import pandas as pd
import numpy as np
from regression_analysis import detect_percolation_threshold

class TestPercolationThresholdLogic:
    """Test percolation threshold detection logic (80% connectivity cutoff)"""
    
    def test_percolation_threshold_logic(self):
        """Verify 80% connectivity cutoff logic"""
        # Create test data with known connectivity pattern
        data = pd.DataFrame({
            'avg_degree': [2.0, 3.0, 4.0, 5.0, 6.0],
            'percolation_flag': [0.0, 0.5, 0.75, 0.85, 0.95]  # Connectivity fraction
        })
        
        # Threshold should be 5.0 (first degree with >= 0.8 connectivity)
        threshold = detect_percolation_threshold(data, threshold=0.8)
        
        assert threshold == 5.0, f"Expected threshold 5.0, got {threshold}"
    
    def test_percolation_threshold_no_threshold_found(self):
        """Test when no degree meets threshold"""
        data = pd.DataFrame({
            'avg_degree': [2.0, 3.0, 4.0],
            'percolation_flag': [0.2, 0.4, 0.6]
        })
        
        threshold = detect_percolation_threshold(data, threshold=0.8)
        
        assert threshold is None, "Expected None when no threshold met"
    
    def test_percolation_threshold_exact_match(self):
        """Test when exact threshold is met"""
        data = pd.DataFrame({
            'avg_degree': [2.0, 3.0, 4.0],
            'percolation_flag': [0.5, 0.8, 0.9]
        })
        
        threshold = detect_percolation_threshold(data, threshold=0.8)
        
        assert threshold == 3.0, f"Expected threshold 3.0, got {threshold}"
    
    def test_percolation_threshold_empty_data(self):
        """Test with empty DataFrame"""
        data = pd.DataFrame(columns=['avg_degree', 'percolation_flag'])
        
        threshold = detect_percolation_threshold(data)
        
        assert threshold is None, "Expected None for empty data"
    
    def test_percolation_threshold_single_row(self):
        """Test with single row meeting threshold"""
        data = pd.DataFrame({
            'avg_degree': [4.0],
            'percolation_flag': [1.0]
        })
        
        threshold = detect_percolation_threshold(data, threshold=0.8)
        
        assert threshold == 4.0, f"Expected threshold 4.0, got {threshold}"
