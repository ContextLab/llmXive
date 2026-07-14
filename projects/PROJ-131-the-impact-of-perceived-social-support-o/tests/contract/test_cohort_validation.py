"""
Contract tests for the synthetic cohort validation logic.
Ensures the validation script produces the expected schema and handles edge cases.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest

# Import the validation logic
from analysis.validation import calculate_smd, check_balance, check_harassment_variance, check_vif

class TestSMD:
    def test_calculate_smd_basic(self):
        # Group A: mean=10, var=4 (sd=2)
        # Group B: mean=12, var=4 (sd=2)
        # SMD = (10-12) / sqrt((4+4)/2) = -2 / 2 = -1.0 -> abs is 1.0
        g1 = pd.Series([10, 10, 10, 10])
        g2 = pd.Series([12, 12, 12, 12])
        s = calculate_smd(g1, g2)
        assert abs(s - 1.0) < 0.001

    def test_calculate_smd_zero_variance(self):
        # If both variances are 0, SMD should be 0.0 to avoid division by zero
        g1 = pd.Series([5, 5, 5])
        g2 = pd.Series([5, 5, 5])
        s = calculate_smd(g1, g2)
        assert s == 0.0

class TestBalance:
    def test_check_balance_schema(self):
        # Create a mock dataframe
        df = pd.DataFrame({
            'dataset_source': ['A', 'A', 'B', 'B'],
            'age': [20, 22, 25, 27],
            'income': [50000, 52000, 48000, 51000]
        })
        covariates = ['age', 'income']
        result = check_balance(covariates, df)
        
        assert isinstance(result, dict)
        assert 'age' in result
        assert 'income' in result
        assert all(isinstance(v, float) for v in result.values())

class TestHarassmentVariance:
    def test_check_variance_pass(self):
        # SD > 0.5, N > 30
        data = np.random.normal(0, 1, 100) # SD ~ 1
        df = pd.DataFrame({'harassment': data})
        is_valid, sd, n = check_harassment_variance(df, 'harassment')
        assert is_valid
        assert n == 100
        assert sd > 0.5

    def test_check_variance_fail_sd(self):
        # SD <= 0.5
        data = np.ones(100) # SD = 0
        df = pd.DataFrame({'harassment': data})
        is_valid, sd, n = check_harassment_variance(df, 'harassment')
        assert not is_valid
        assert sd == 0.0

    def test_check_variance_fail_n(self):
        # N < 30
        data = np.random.normal(0, 1, 20)
        df = pd.DataFrame({'harassment': data})
        is_valid, sd, n = check_harassment_variance(df, 'harassment')
        assert not is_valid
        assert n == 20

class TestVIF:
    def test_check_vif_basic(self):
        # Create data with low correlation
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.rand(100),
            'x2': np.random.rand(100),
            'x3': np.random.rand(100)
        })
        is_valid, vifs = check_vif(df, ['x1', 'x2', 'x3'])
        assert is_valid
        assert all(v < 5 for v in vifs.values())

    def test_check_vif_high_correlation(self):
        # Create data with high correlation
        x = np.random.rand(100)
        df = pd.DataFrame({
            'x1': x,
            'x2': x + np.random.normal(0, 0.01, 100), # Almost identical
            'x3': np.random.rand(100)
        })
        is_valid, vifs = check_vif(df, ['x1', 'x2', 'x3'])
        # VIF should be high for x1 and x2
        assert not is_valid
        assert vifs['x1'] > 5 or vifs['x2'] > 5

class TestIntegration:
    def test_full_validation_flow(self):
        """Simulate the full validation flow with a synthetic cohort file."""
        # Create a temporary directory and file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "cohort.csv")
            output_path = os.path.join(tmpdir, "report.json")
            
            # Generate valid synthetic data
            np.random.seed(42)
            n = 200
            df = pd.DataFrame({
                'dataset_source': ['A'] * 100 + ['B'] * 100,
                'age': np.random.normal(30, 10, n),
                'gender': np.random.choice([0, 1], n),
                'education': np.random.normal(14, 3, n),
                'income': np.random.normal(50000, 10000, n),
                'social_support': np.random.normal(50, 10, n),
                'harassment_exposure': np.random.normal(0.5, 0.8, n), # SD > 0.5
                'harassment_severity': np.random.normal(2, 1, n),
                'weight': np.ones(n)
            })
            df.to_csv(input_path, index=False)
            
            # Run validation
            from analysis.validation import validate_synthetic_cohort
            success = validate_synthetic_cohort(input_path, output_path)
            
            assert success
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['overall_status'] == 'PASS'
            assert report['harassment_check']['passed']
            assert report['vif_check']['passed']
            assert all(v <= 0.1 for v in report['smd'].values())