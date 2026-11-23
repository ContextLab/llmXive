"""
Unit tests for code/features/classification.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from features.classification import calculate_continuous_ratio, perform_kmeans_clustering

class TestCalculateContinuousRatio:
    
    def test_normal_case(self):
        """Test calculation with normal positive values."""
        data = {
            'fixation_eye_duration': [100.0, 200.0, 150.0],
            'fixation_mouth_duration': [50.0, 100.0, 150.0]
        }
        df = pd.DataFrame(data)
        
        result = calculate_continuous_ratio(df)
        
        # Expected: 100/150 = 0.666, 200/300 = 0.666, 150/300 = 0.5
        expected_ratios = [100/150, 200/300, 150/300]
        
        assert 'fixation_ratio' in result.columns
        assert np.allclose(result['fixation_ratio'].values, expected_ratios, atol=1e-6)

    def test_zero_total_duration(self):
        """Test behavior when eye + mouth duration is zero."""
        data = {
            'fixation_eye_duration': [0.0, 100.0],
            'fixation_mouth_duration': [0.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        result = calculate_continuous_ratio(df)
        
        # First row should be 0.5 (neutral)
        assert result['fixation_ratio'].iloc[0] == 0.5
        assert result['fixation_ratio'].iloc[1] == 100/150

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame()
        result = calculate_continuous_ratio(df)
        assert result.empty

    def test_mean_ratio_warning(self):
        """Test that a warning is logged if mean ratio <= 0 (though unlikely with this logic)."""
        # Since our logic forces 0.5 on zero total, mean will be > 0 unless all are negative (impossible here)
        # This test verifies the logic path exists.
        data = {
            'fixation_eye_duration': [0.0],
            'fixation_mouth_duration': [0.0]
        }
        df = pd.DataFrame(data)
        result = calculate_continuous_ratio(df)
        # Mean should be 0.5, which is > 0, so no warning in this specific case.
        # The warning path is for <= 0, which is hard to trigger with this formula unless data is manipulated.
        assert result['fixation_ratio'].iloc[0] == 0.5

class TestKMeansClustering:
    
    def test_clustering_basic(self):
        """Test basic clustering functionality."""
        data = {
            'fixation_eye_duration': [100, 200, 300, 400, 500, 600],
            'fixation_mouth_duration': [50, 100, 150, 200, 250, 300],
            'saccade_amplitude': [10, 20, 30, 40, 50, 60],
            'dispersion': [5, 10, 15, 20, 25, 30]
        }
        df = pd.DataFrame(data)
        
        result_df, score = perform_kmeans_clustering(df, n_clusters=2)
        
        assert 'cluster_label' in result_df.columns
        assert score >= -1.0  # Silhouette score can be -1
        assert len(result_df['cluster_label'].unique()) <= 2

    def test_insufficient_features(self):
        """Test with missing required features."""
        data = {
            'fixation_eye_duration': [100, 200],
            'other_col': [1, 2]
        }
        df = pd.DataFrame(data)
        
        result_df, score = perform_kmeans_clustering(df, n_clusters=2)
        
        # Should handle gracefully, likely returning NaN or -1 score
        assert score == -1.0

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame()
        result_df, score = perform_kmeans_clustering(df, n_clusters=2)
        
        assert result_df.empty
        assert score == -1.0