import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.analyze import calculate_vif, save_vif_diagnostic_log, load_descriptors

class TestVIFAnalysis:
    """Integration tests for VIF calculation and diagnostic logging."""

    @pytest.fixture
    def sample_descriptors(self, tmp_path):
        """Create a sample descriptors CSV file for testing."""
        # Create a dataset with some multicollinearity
        np.random.seed(42)
        n_samples = 100
        
        # Create features with some correlation
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.8 + np.random.normal(0, 0.2, n_samples)  # Highly correlated with x1
        x3 = np.random.normal(0, 1, n_samples)
        x4 = np.random.normal(0, 1, n_samples)
        x5 = x3 + x4 + np.random.normal(0, 0.1, n_samples)  # Correlated with x3 and x4
        
        df = pd.DataFrame({
            'feature_1': x1,
            'feature_2': x2,
            'feature_3': x3,
            'feature_4': x4,
            'feature_5': x5
        })
        
        file_path = tmp_path / "test_descriptors.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    @pytest.fixture
    def sample_descriptors_high_vif(self, tmp_path):
        """Create a sample descriptors CSV file with high VIF features."""
        np.random.seed(123)
        n_samples = 100
        
        # Create strong multicollinearity
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n_samples)  # Very high correlation
        x3 = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame({
            'highly_collinear_1': x1,
            'highly_collinear_2': x2,
            'independent': x3
        })
        
        file_path = tmp_path / "test_high_vif_descriptors.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)

    def test_vif_calculation_basic(self, sample_descriptors):
        """Test basic VIF calculation on sample data."""
        df = load_descriptors(sample_descriptors)
        vif_df = calculate_vif(df)
        
        assert vif_df is not None
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert len(vif_df) == 5  # 5 features
        
        # Check that VIF values are positive
        assert all(vif_df['vif'] > 0)
        
        # Check that highly correlated features have higher VIF
        # feature_1 and feature_2 should have higher VIF than feature_3, feature_4, feature_5
        high_corr_vif = vif_df[vif_df['feature'].isin(['feature_1', 'feature_2'])]['vif'].mean()
        low_corr_vif = vif_df[vif_df['feature'].isin(['feature_3', 'feature_4', 'feature_5'])]['vif'].mean()
        
        assert high_corr_vif >= low_corr_vif, "Highly correlated features should have higher VIF"

    def test_vif_flagging_threshold(self, sample_descriptors_high_vif):
        """Test that VIF flagging works correctly with a threshold."""
        df = load_descriptors(sample_descriptors_high_vif)
        vif_df = calculate_vif(df)
        
        # Save to temporary file
        output_path = os.path.join(os.path.dirname(sample_descriptors_high_vif), "test_vif_log.json")
        save_vif_diagnostic_log(vif_df, output_path, threshold=5.0)
        
        # Verify the log file exists and contains correct data
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            log_data = json.load(f)
        
        assert 'threshold' in log_data
        assert log_data['threshold'] == 5.0
        assert 'flagged_features' in log_data
        assert 'all_vif_values' in log_data
        
        # Check that highly collinear features are flagged
        flagged = log_data['flagged_features']
        assert len(flagged) > 0, "At least one feature should be flagged with VIF > 5"
        
        # Verify flagged features actually have VIF > 5
        for feature in flagged:
            feature_vif = next(item['vif'] for item in log_data['all_vif_values'] if item['feature'] == feature)
            assert feature_vif > 5.0, f"Feature {feature} should have VIF > 5.0"

    def test_vif_diagnostic_log_structure(self, sample_descriptors):
        """Test the structure of the VIF diagnostic log."""
        df = load_descriptors(sample_descriptors)
        vif_df = calculate_vif(df)
        
        output_path = os.path.join(os.path.dirname(sample_descriptors), "test_log.json")
        save_vif_diagnostic_log(vif_df, output_path, threshold=5.0)
        
        with open(output_path, 'r') as f:
            log_data = json.load(f)
        
        # Check required keys
        required_keys = ['threshold', 'total_features', 'flagged_features', 'all_vif_values']
        for key in required_keys:
            assert key in log_data, f"Missing key: {key}"
        
        # Check all_vif_values structure
        for item in log_data['all_vif_values']:
            assert 'feature' in item
            assert 'vif' in item
            assert 'flagged' in item
            assert isinstance(item['vif'], (int, float, type(None)))
            assert isinstance(item['flagged'], bool)

    def test_vif_no_flagging_below_threshold(self, sample_descriptors):
        """Test that features below threshold are not flagged."""
        df = load_descriptors(sample_descriptors)
        vif_df = calculate_vif(df)
        
        output_path = os.path.join(os.path.dirname(sample_descriptors), "test_no_flag.json")
        # Use a very high threshold to ensure no features are flagged
        save_vif_diagnostic_log(vif_df, output_path, threshold=100.0)
        
        with open(output_path, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data['flagged_features']) == 0, "No features should be flagged with threshold=100.0"

    def test_vif_error_handling_empty_data(self, tmp_path):
        """Test VIF calculation with insufficient data."""
        # Create empty dataframe
        file_path = tmp_path / "empty_descriptors.csv"
        pd.DataFrame({'a': [], 'b': []}).to_csv(file_path, index=False)
        
        df = load_descriptors(str(file_path))
        
        with pytest.raises(ValueError):
            calculate_vif(df)

    def test_vif_error_handling_single_column(self, tmp_path):
        """Test VIF calculation with only one feature."""
        file_path = tmp_path / "single_col.csv"
        pd.DataFrame({'a': [1, 2, 3]}).to_csv(file_path, index=False)
        
        df = load_descriptors(str(file_path))
        
        with pytest.raises(ValueError):
            calculate_vif(df)
