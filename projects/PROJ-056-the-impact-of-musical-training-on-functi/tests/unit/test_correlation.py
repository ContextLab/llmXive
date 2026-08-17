"""
Unit tests for correlation analysis module (User Story 3)
"""
import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.correlation import (
    compute_connectivity_strength,
    compute_correlation_with_training,
    calculate_correlation_ci,
    load_musicians_connectivity_data
)


class TestComputeConnectivityStrength:
    """Tests for extract connectivity strength from matrices"""

    def test_upper_triangle_extraction(self):
        """Test that only upper triangle (excluding diagonal) is extracted"""
        matrix = np.array([
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.2],
            [0.3, 0.2, 1.0]
        ])
        
        strength = compute_connectivity_strength(matrix, mask_diagonal=True)
        
        # Should have 3 values: (0,1), (0,2), (1,2)
        assert len(strength) == 3
        assert np.allclose(strength, [0.5, 0.3, 0.2])

    def test_no_diagonal_mask(self):
        """Test extraction without diagonal masking"""
        matrix = np.array([
            [1.0, 0.5],
            [0.5, 1.0]
        ])
        
        strength = compute_connectivity_strength(matrix, mask_diagonal=False)
        
        # Should have 2 values (off-diagonal only)
        assert len(strength) == 2
        assert np.allclose(strength, [0.5, 0.5])


class TestComputeCorrelationWithTraining:
    """Tests for correlation computation between training and connectivity"""

    def test_pearson_correlation_positive(self):
        """Test Pearson correlation with known positive relationship"""
        # Create mock data: training years and connectivity values
        musicians_df = pd.DataFrame({
            'subject_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'years_of_training': [2.0, 3.0, 4.0, 5.0, 6.0]
        })
        
        # Create connectivity matrices with increasing values
        connectivity_dict = {
            'S1': np.array([[1.0, 0.5], [0.5, 1.0]]),
            'S2': np.array([[1.0, 0.6], [0.6, 1.0]]),
            'S3': np.array([[1.0, 0.7], [0.7, 1.0]]),
            'S4': np.array([[1.0, 0.8], [0.8, 1.0]]),
            'S5': np.array([[1.0, 0.9], [0.9, 1.0]])
        }
        
        result = compute_correlation_with_training(musicians_df, connectivity_dict, method='pearson')
        
        # Check that we got results
        assert len(result) == 1  # Only one connection (ROI0-ROI1)
        assert result['connection_id'].iloc[0] == 'ROI0-ROI1'
        
        # Correlation should be positive and significant
        assert result['r_value'].iloc[0] > 0.9
        assert result['p_value'].iloc[0] < 0.05

    def test_spearman_correlation(self):
        """Test Spearman correlation computation"""
        musicians_df = pd.DataFrame({
            'subject_id': ['S1', 'S2', 'S3', 'S4'],
            'years_of_training': [1.0, 2.0, 3.0, 4.0]
        })
        
        connectivity_dict = {
            'S1': np.array([[1.0, 0.1], [0.1, 1.0]]),
            'S2': np.array([[1.0, 0.2], [0.2, 1.0]]),
            'S3': np.array([[1.0, 0.3], [0.3, 1.0]]),
            'S4': np.array([[1.0, 0.4], [0.4, 1.0]])
        }
        
        result = compute_correlation_with_training(musicians_df, connectivity_dict, method='spearman')
        
        assert len(result) == 1
        assert result['r_value'].iloc[0] > 0.9
        assert result['p_value'].iloc[0] < 0.05

    def test_insufficient_samples(self):
        """Test handling of insufficient samples"""
        musicians_df = pd.DataFrame({
            'subject_id': ['S1', 'S2'],
            'years_of_training': [1.0, 2.0]
        })
        
        connectivity_dict = {
            'S1': np.array([[1.0, 0.5], [0.5, 1.0]]),
            'S2': np.array([[1.0, 0.6], [0.6, 1.0]])
        }
        
        # With only 2 samples, correlation should return NaN
        result = compute_correlation_with_training(musicians_df, connectivity_dict, method='pearson')
        
        assert pd.isna(result['r_value'].iloc[0])


class TestCalculateCorrelationCI:
    """Tests for confidence interval calculation"""

    def test_ci_calculation(self):
        """Test that confidence intervals are calculated correctly"""
        df = pd.DataFrame({
            'connection_id': ['C1', 'C2'],
            'r_value': [0.5, -0.3],
            'p_value': [0.01, 0.05],
            'n_samples': [50, 50]
        })
        
        result = calculate_correlation_ci(df, confidence_level=0.95)
        
        # Check that CI columns were added
        assert 'ci_lower' in result.columns
        assert 'ci_upper' in result.columns
        
        # Check that CI bounds are reasonable
        assert result['ci_lower'].iloc[0] < result['r_value'].iloc[0]
        assert result['ci_upper'].iloc[0] > result['r_value'].iloc[0]
        
        # For r=0.5, CI should be roughly [0.23, 0.70] with n=50
        assert 0.2 < result['ci_lower'].iloc[0] < 0.4
        assert 0.6 < result['ci_upper'].iloc[0] < 0.8

    def test_ci_with_small_sample(self):
        """Test CI calculation with small sample size (wider interval)"""
        df = pd.DataFrame({
            'connection_id': ['C1'],
            'r_value': [0.5],
            'p_value': [0.01],
            'n_samples': [10]
        })
        
        result = calculate_correlation_ci(df, confidence_level=0.95)
        
        # CI should be wider for small n
        ci_width = result['ci_upper'].iloc[0] - result['ci_lower'].iloc[0]
        assert ci_width > 0.5  # Should be quite wide for n=10


class TestLoadMusiciansData:
    """Tests for loading musicians data"""

    def test_filter_musicians(self, tmp_path):
        """Test that only musicians are loaded"""
        # Create temporary subjects file
        subjects_file = tmp_path / "subjects_cleaned.csv"
        subjects_df = pd.DataFrame({
            'subject_id': ['S1', 'S2', 'S3', 'S4'],
            'years_of_training': [0.5, 1.5, 2.5, 0.3],
            'group': ['non_musician', 'musician', 'musician', 'non_musician']
        })
        subjects_df.to_csv(subjects_file, index=False)
        
        # Create empty connectivity directory
        connectivity_dir = tmp_path / "connectivity_matrices"
        connectivity_dir.mkdir()
        
        musicians_df, _ = load_musicians_connectivity_data(
            str(subjects_file), str(connectivity_dir)
        )
        
        # Should have 2 musicians (years >= 1.0)
        assert len(musicians_df) == 2
        assert all(musicians_df['years_of_training'] >= 1.0)

    def test_no_musicians_error(self, tmp_path):
        """Test error when no musicians found"""
        subjects_file = tmp_path / "subjects_cleaned.csv"
        subjects_df = pd.DataFrame({
            'subject_id': ['S1', 'S2'],
            'years_of_training': [0.2, 0.5],
            'group': ['non_musician', 'non_musician']
        })
        subjects_df.to_csv(subjects_file, index=False)
        
        connectivity_dir = tmp_path / "connectivity_matrices"
        connectivity_dir.mkdir()
        
        with pytest.raises(ValueError, match="No musicians found"):
            load_musicians_connectivity_data(
                str(subjects_file), str(connectivity_dir)
            )

    def test_missing_file_error(self, tmp_path):
        """Test error when subjects file is missing"""
        with pytest.raises(FileNotFoundError):
            load_musicians_connectivity_data(
                "nonexistent.csv", str(tmp_path)
            )
