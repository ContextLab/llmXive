import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the functions to test
from validate import (
    calculate_effect_size_f2,
    calculate_power_regression,
    estimate_predictors_from_data,
    run_power_analysis
)

class TestCalculateEffectSizeF2:
    def test_medium_effect(self):
        # R^2 = 0.15 -> f^2 = 0.15 / 0.85 ≈ 0.176
        f2 = calculate_effect_size_f2(predictors=5, r_squared=0.15)
        expected = 0.15 / (1 - 0.15)
        assert abs(f2 - expected) < 1e-6

    def test_invalid_r_squared(self):
        with pytest.raises(ValueError):
            calculate_effect_size_f2(predictors=5, r_squared=1.0)

    def test_zero_r_squared(self):
        f2 = calculate_effect_size_f2(predictors=5, r_squared=0.0)
        assert f2 == 0.0

class TestCalculatePowerRegression:
    def test_high_power_large_sample(self):
        # Large sample should yield high power
        power = calculate_power_regression(sample_size=500, predictors=5, f2=0.15)
        assert power > 0.8

    def test_low_power_small_sample(self):
        # Small sample should yield low power
        power = calculate_power_regression(sample_size=20, predictors=5, f2=0.15)
        assert power < 0.5

    def test_insufficient_sample_size(self):
        # Sample size <= predictors
        power = calculate_power_regression(sample_size=5, predictors=5, f2=0.15)
        assert power == 0.0

    def test_zero_effect_size(self):
        power = calculate_power_regression(sample_size=100, predictors=5, f2=0.0)
        assert power == 0.0

class TestEstimatePredictorsFromData:
    def test_numeric_only(self):
        df = pd.DataFrame({
            'wear_rate': [1, 2, 3],
            'power': [10, 20, 30],
            'speed': [100, 200, 300]
        })
        count = estimate_predictors_from_data(df, target_col='wear_rate')
        assert count == 2  # power, speed

    def test_with_categorical(self):
        df = pd.DataFrame({
            'wear_rate': [1, 2, 3],
            'power': [10, 20, 30],
            'pattern': ['A', 'B', 'A']
        })
        count = estimate_predictors_from_data(df, target_col='wear_rate')
        # power (1) + pattern (2 unique -> 1 feature) = 2
        assert count == 2

    def test_empty_dataframe(self):
        df = pd.DataFrame({
            'wear_rate': [],
            'power': []
        })
        count = estimate_predictors_from_data(df, target_col='wear_rate')
        assert count == 1

    def test_multiple_categorical(self):
        df = pd.DataFrame({
            'wear_rate': [1, 2, 3, 4, 5, 6],
            'power': [10, 20, 30, 40, 50, 60],
            'pattern': ['A', 'B', 'C', 'A', 'B', 'C'],
            'material': ['X', 'X', 'X', 'Y', 'Y', 'Y']
        })
        count = estimate_predictors_from_data(df, target_col='wear_rate')
        # power (1) + pattern (3-1=2) + material (2-1=1) = 4
        assert count == 4

class TestRunPowerAnalysis:
    @pytest.fixture
    def temp_data_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "normalized_only.csv"
            # Create a realistic small dataset
            df = pd.DataFrame({
                'wear_rate': np.random.rand(150),
                'power': np.random.rand(150) * 100,
                'speed': np.random.rand(150) * 1000,
                'pattern': np.random.choice(['A', 'B', 'C'], 150),
                'normalization_method': ['normalized'] * 150
            })
            df.to_csv(data_path, index=False)
            yield str(data_path)
            # Cleanup handled by context manager

    def test_run_success(self, temp_data_file):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            result = run_power_analysis(
                data_path=temp_data_file,
                output_path=str(output_path),
                min_power_threshold=0.5 # Lower threshold for test
            )
            
            assert 'power' in result
            assert 'status' in result
            assert result['sample_size'] == 150
            assert result['n_predictors'] == 3  # power, speed, pattern (2 dummies)
            
            # Verify file was written
            assert output_path.exists()
            with open(output_path) as f:
                saved = json.load(f)
            assert saved['power'] == result['power']
            assert saved['status'] == result['status']

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            run_power_analysis(data_path="/nonexistent/path.csv")

    def test_missing_target_column(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "bad_data.csv"
            df = pd.DataFrame({
                'feature1': [1, 2, 3],
                'feature2': [4, 5, 6]
            })
            df.to_csv(data_path, index=False)
            
            output_path = Path(tmpdir) / "power_analysis.json"
            
            with pytest.raises(ValueError):
                run_power_analysis(data_path=str(data_path), output_path=str(output_path))

    def test_failed_power_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "small_data.csv"
            # Very small dataset to trigger failure
            df = pd.DataFrame({
                'wear_rate': [1, 2, 3, 4, 5],
                'power': [10, 20, 30, 40, 50],
                'normalization_method': ['normalized'] * 5
            })
            df.to_csv(data_path, index=False)
            
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # This should not raise an exception, but return failed status
            # The sys.exit(1) in run_power_analysis is only triggered if called as main
            result = run_power_analysis(
                data_path=str(data_path),
                output_path=str(output_path),
                min_power_threshold=0.8
            )
            
            assert result['status'] == 'failed'
            assert result['reason'] == 'insufficient_power'
            
            # Verify file content
            with open(output_path) as f:
                saved = json.load(f)
            assert saved['status'] == 'failed'
            assert saved['reason'] == 'insufficient_power'