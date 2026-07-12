import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.eval import calculate_correlation_and_hypothesis_test, main
import argparse

class TestEvalCorrelation:
    """Integration tests for T027b: Correlation and Hypothesis Testing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "test_anomaly_scores.parquet")
        self.output_path = os.path.join(self.temp_dir, "test_correlation.json")

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_correlation_calculation(self):
        """Test that Pearson correlation is calculated correctly."""
        # Create synthetic data with known correlation
        # Let's create a dataset where higher distance correlates with label 1
        n_samples = 100
        np.random.seed(42)
        
        # Generate distances: low for benign (0), high for jailbreak (1)
        distances = np.concatenate([
            np.random.normal(0, 1, n_samples // 2),   # Benign
            np.random.normal(5, 1, n_samples - n_samples // 2) # Jailbreak
        ])
        labels = np.array([0] * (n_samples // 2) + [1] * (n_samples - n_samples // 2))
        
        # Shuffle to simulate real data
        indices = np.random.permutation(n_samples)
        distances = distances[indices]
        labels = labels[indices]
        
        df = pd.DataFrame({
            'mahalanobis_distance': distances,
            'label': labels
        })
        
        results = calculate_correlation_and_hypothesis_test(df, 'mahalanobis_distance', 'label')
        
        # Check that r is positive and significant
        assert results['pearson_r'] > 0.3, f"Expected r > 0.3, got {results['pearson_r']}"
        assert results['p_value'] < 0.05, f"Expected p < 0.05, got {results['p_value']}"
        assert results['condition_met'] is True
        assert results['sample_size'] == n_samples

    def test_correlation_no_correlation(self):
        """Test case where there is no correlation."""
        n_samples = 100
        np.random.seed(42)
        
        # Generate random distances and labels with no relationship
        distances = np.random.normal(0, 1, n_samples)
        labels = np.random.randint(0, 2, n_samples)
        
        df = pd.DataFrame({
            'mahalanobis_distance': distances,
            'label': labels
        })
        
        results = calculate_correlation_and_hypothesis_test(df, 'mahalanobis_distance', 'label')
        
        # r might be small, p might be > 0.05
        # The condition_met should be False if neither threshold is met
        # We just check the calculation runs without error
        assert isinstance(results['pearson_r'], float)
        assert isinstance(results['p_value'], float)
        assert 'condition_met' in results

    def test_main_function(self):
        """Test the main function with file I/O."""
        # Create input data
        n_samples = 50
        np.random.seed(123)
        distances = np.concatenate([
            np.random.normal(0, 0.5, n_samples // 2),
            np.random.normal(3, 0.5, n_samples - n_samples // 2)
        ])
        labels = np.array([0] * (n_samples // 2) + [1] * (n_samples - n_samples // 2))
        
        df = pd.DataFrame({
            'mahalanobis_distance': distances,
            'label': labels
        })
        df.to_parquet(self.input_path)
        
        # Run main
        args = argparse.Namespace(
            input=self.input_path,
            output=self.output_path,
            score_column='mahalanobis_distance',
            label_column='label'
        )
        
        main(args)
        
        # Verify output file exists and contains valid JSON
        assert os.path.exists(self.output_path)
        with open(self.output_path, 'r') as f:
            results = json.load(f)
        
        assert 'pearson_r' in results
        assert 'p_value' in results
        assert 'condition_met' in results
        assert results['condition_met'] is True  # With this synthetic data, it should be met

    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({
            'other_col': [1, 2, 3],
            'label': [0, 1, 0]
        })
        
        with pytest.raises(ValueError, match="Score column"):
            calculate_correlation_and_hypothesis_test(df, 'mahalanobis_distance', 'label')

    def test_invalid_data_types(self):
        """Test error handling for invalid data types."""
        df = pd.DataFrame({
            'mahalanobis_distance': ['a', 'b', 'c'],
            'label': [0, 1, 0]
        })
        
        with pytest.raises(ValueError, match="must contain numeric values"):
            calculate_correlation_and_hypothesis_test(df, 'mahalanobis_distance', 'label')