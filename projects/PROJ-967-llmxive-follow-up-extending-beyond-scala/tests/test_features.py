import pytest
import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import ast

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss,
    compute_all_features
)

class TestVarianceAndRange:
    def test_normal_values(self):
        values = [1.0, 2.0, 3.0, 4.0]
        result = calculate_variance_and_range(values)
        assert abs(result['variance'] - 1.25) < 0.001
        assert abs(result['range'] - 3.0) < 0.001

    def test_zero_variance(self):
        values = [5.0, 5.0, 5.0]
        result = calculate_variance_and_range(values)
        assert result['variance'] == 0.0
        assert result['range'] == 0.0

    def test_empty_list(self):
        result = calculate_variance_and_range([])
        assert result['variance'] == 0.0
        assert result['range'] == 0.0

class TestEntropy:
    def test_uniform_distribution(self):
        # Uniform distribution of 4 items: p=0.25 each
        # Entropy = -4 * 0.25 * log2(0.25) = 2.0
        values = [1.0, 1.0, 1.0, 1.0]
        result = calculate_entropy(values)
        assert abs(result - 2.0) < 0.01

    def test_skewed_distribution(self):
        # One dominant value
        values = [10.0, 1.0, 1.0, 1.0]
        result = calculate_entropy(values)
        # Should be less than 2.0
        assert result < 2.0
        assert result > 0.0

    def test_zero_variance(self):
        values = [5.0, 5.0, 5.0]
        result = calculate_entropy(values)
        assert result == 0.0

class TestSkewnessKurtosis:
    def test_normal_values(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        result = calculate_skewness_and_kurtosis(values)
        # Skewness should be close to 0 for symmetric distribution
        assert abs(result['skewness']) < 0.1
        # Kurtosis for uniform-ish is negative (platykurtic)
        assert result['kurtosis'] < 0.5

    def test_small_list(self):
        values = [1.0, 2.0]
        result = calculate_skewness_and_kurtosis(values)
        assert result['skewness'] == 0.0
        assert result['kurtosis'] == 0.0

class TestGlobalEntanglement:
    def test_global_eigenvalue(self):
        # Create a mock dataframe with known covariance
        data = {
            'teacher_logits': [
                '[1.0, 2.0, 3.0, 4.0]',
                '[2.0, 4.0, 6.0, 8.0]',
                '[3.0, 6.0, 9.0, 12.0]',
                '[1.0, 1.0, 1.0, 1.0]'
            ]
        }
        df = pd.DataFrame(data)
        score = calculate_global_entanglement_score(df)
        assert isinstance(score, float)
        assert np.isfinite(score)

class TestFidelityLoss:
    def test_calculate_loss(self):
        data = {
            'student_scalar': [0.8, 0.5, 0.9],
            'primary_dimension': ['Alignment', 'Realism', 'Aesthetics'],
            'human_annotations': [
                "{'Alignment': 0.9, 'Realism': 0.5, 'Aesthetics': 0.8, 'Plausibility': 0.7}",
                "{'Alignment': 0.4, 'Realism': 0.6, 'Aesthetics': 0.5, 'Plausibility': 0.5}",
                "{'Alignment': 0.8, 'Realism': 0.5, 'Aesthetics': 0.9, 'Plausibility': 0.6}"
            ]
        }
        df = pd.DataFrame(data)
        df = calculate_dimensional_fidelity_loss(df)
        
        assert 'fidelity_loss' in df.columns
        assert abs(df.iloc[0]['fidelity_loss'] - 0.1) < 0.01
        assert abs(df.iloc[1]['fidelity_loss'] - 0.1) < 0.01
        assert abs(df.iloc[2]['fidelity_loss'] - 0.0) < 0.01

class TestIntegration:
    def test_compute_all_features(self, tmp_path):
        # Create a temporary input file
        input_path = tmp_path / "test_input.csv"
        data = {
            'sample_id': [1, 2, 3],
            'prompt': ['p1', 'p2', 'p3'],
            'image_path': ['i1', 'i2', 'i3'],
            'teacher_logits': [
                '[1.0, 2.0, 3.0, 4.0]',
                '[2.0, 4.0, 6.0, 8.0]',
                '[3.0, 6.0, 9.0, 12.0]'
            ],
            'student_scalar': [0.5, 0.6, 0.7],
            'primary_dimension': ['Alignment', 'Realism', 'Aesthetics'],
            'human_annotations': [
                "{'Alignment': 0.6, 'Realism': 0.5, 'Aesthetics': 0.5, 'Plausibility': 0.5}",
                "{'Alignment': 0.5, 'Realism': 0.7, 'Aesthetics': 0.5, 'Plausibility': 0.5}",
                "{'Alignment': 0.5, 'Realism': 0.5, 'Aesthetics': 0.8, 'Plausibility': 0.5}"
            ]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        output_path = tmp_path / "test_output.json"
        
        # Run the integration
        compute_all_features(str(input_path), str(output_path))
        
        # Verify output
        assert output_path.exists()
        with open(output_path) as f:
            features = json.load(f)
        
        assert isinstance(features, list)
        assert len(features) == 3
        
        # Check required keys
        required_keys = ['sample_id', 'variance', 'entropy', 'global_eigenvalue', 'fidelity_loss']
        for feat in features:
            for key in required_keys:
                assert key in feat, f"Missing key {key}"
                assert feat[key] is not None, f"Key {key} is null"
        
        # Check global eigenvalue is consistent across samples
        eigenvalues = [f['global_eigenvalue'] for f in features]
        assert all(abs(e - eigenvalues[0]) < 1e-6 for e in eigenvalues)