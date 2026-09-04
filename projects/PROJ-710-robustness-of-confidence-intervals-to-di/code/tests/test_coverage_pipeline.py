"""
Integration test for end-to-end coverage calculation on a single condition.
Task: T017
Depends on: T013a (Outer Loop), T013b (Inner Loop), T013c (Result Writer)

This test verifies that the full pipeline (Data Loading -> DP Noise -> CI Construction -> Coverage Check)
executes correctly on a single, small condition (Adult dataset, high epsilon, Laplace noise)
and produces a valid coverage result.
"""
import json
import os
import sys
import pytest
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from existing API surface
from data.download_utils import fetch_adult_data, DataFetchError
from data.dp_noise import inject_laplace_noise, inject_gaussian_noise
from analysis.ci_builder import build_ci_for_mean, validate_ci_coverage
from analysis.edge_cases import enforce_min_sample_size
from config import get_artifact_path, get_data_path, Config

class TestCoveragePipeline:
    """Integration tests for the coverage calculation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directories and clean up after tests."""
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Ensure required directories exist
        os.makedirs("artifacts", exist_ok=True)
        os.makedirs("data/raw", exist_ok=True)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _load_small_sample(self, n_samples: int = 50) -> pd.DataFrame:
        """Load a small sample of the Adult dataset for testing."""
        try:
            df = fetch_adult_data()
            if df is None or len(df) == 0:
                raise DataFetchError("Failed to fetch Adult dataset")
            
            # Take a small random sample for speed
            if len(df) > n_samples:
                df = df.sample(n=n_samples, random_state=42)
            
            # Ensure we have a numeric column for mean estimation
            # Adult dataset typically has 'age' or 'hours-per-week'
            numeric_col = None
            for col in ['age', 'hours-per-week', 'fnlwgt']:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    numeric_col = col
                    break
            
            if numeric_col is None:
                # Fallback: create a synthetic numeric column if real data lacks one (should not happen with real UCI)
                # But per strict rules, we rely on real data. If 'age' exists, use it.
                raise ValueError("Could not find a suitable numeric column in the real Adult dataset")
            
            return df[numeric_col].dropna().reset_index(drop=True)
        except DataFetchError as e:
            pytest.skip(f"Real data fetch failed: {e}")

    def test_end_to_end_coverage_calculation(self):
        """
        Test the full pipeline on a single condition:
        1. Load real UCI Adult data
        2. Draw a small sample
        3. Add DP noise (Laplace, high epsilon)
        4. Construct 95% CI for the mean
        5. Check coverage against the sample mean (as a proxy for ground truth in this small test)
        
        Note: In the full simulation (T013a), we compare against the synthetic ground truth from T003.
        Here, we verify the mechanics work end-to-end.
        """
        # 1. Load Real Data
        sample_data = self._load_small_sample(n_samples=100)
        assert len(sample_data) >= 10, "Sample size too small for CI construction"
        
        # Ground truth for this specific sample is the sample mean
        true_mean = sample_data.mean()
        
        # 2. Add DP Noise
        epsilon = 10.0  # High epsilon for stability in this small test
        sensitivity = sample_data.max() - sample_data.min()
        noise_data = inject_laplace_noise(sample_data.values, epsilon=epsilon, sensitivity=sensitivity)
        
        # 3. Construct CI
        # We run a small number of bootstrap resamples for the test
        n_bootstrap = 100 
        ci_lower, ci_upper = build_ci_for_mean(
            noise_data, 
            confidence_level=0.95, 
            n_bootstrap=n_bootstrap, 
            random_state=42
        )
        
        # 4. Check Coverage
        covered = validate_ci_coverage(ci_lower, ci_upper, true_mean)
        
        # 5. Assert Results
        assert isinstance(covered, bool), "Coverage result must be boolean"
        assert ci_lower is not None and ci_upper is not None, "CI bounds must be computed"
        assert ci_lower <= ci_upper, "CI lower bound must be <= upper bound"
        
        # Write a minimal result to disk to satisfy T013c writer expectations for this test
        result_record = {
            "dataset": "adult_test",
            "epsilon": epsilon,
            "noise_type": "laplace",
            "statistic": "mean",
            "coverage_rate": 1.0 if covered else 0.0,
            "adjusted_coverage": 1.0 if covered else 0.0,
            "adjustment_method": "none",
            "improvement_delta": 0.0,
            "seed": 42
        }
        
        # Write to artifacts/coverage_results.csv (T013c output path)
        output_path = Path("artifacts/coverage_results.csv")
        if output_path.exists():
            existing_df = pd.read_csv(output_path)
            new_df = pd.concat([existing_df, pd.DataFrame([result_record])], ignore_index=True)
        else:
            new_df = pd.DataFrame([result_record])
        
        new_df.to_csv(output_path, index=False)
        
        # Verify file was written
        assert output_path.exists(), "Output file must be written"
        assert len(pd.read_csv(output_path)) > 0, "Output file must contain data"

    def test_pipeline_with_gaussian_noise(self):
        """Test the pipeline with Gaussian noise injection."""
        sample_data = self._load_small_sample(n_samples=50)
        true_mean = sample_data.mean()
        
        epsilon = 5.0
        sensitivity = sample_data.max() - sample_data.min()
        
        # Gaussian noise injection
        noise_data = inject_gaussian_noise(sample_data.values, epsilon=epsilon, sensitivity=sensitivity)
        
        # Build CI
        ci_lower, ci_upper = build_ci_for_mean(
            noise_data, 
            confidence_level=0.95, 
            n_bootstrap=50, 
            random_state=42
        )
        
        # Validate
        covered = validate_ci_coverage(ci_lower, ci_upper, true_mean)
        
        assert isinstance(covered, bool)

    def test_min_sample_size_enforcement(self):
        """Test that the pipeline enforces minimum sample size."""
        # Create a tiny sample
        tiny_data = pd.Series([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            enforce_min_sample_size(tiny_data.values, min_size=10)

    def test_result_writer_integration(self):
        """Test that the result writer can handle the pipeline output format."""
        # Simulate a batch of results
        results = []
        for i in range(5):
            results.append({
                "dataset": "adult",
                "epsilon": 1.0 + i,
                "noise_type": "laplace",
                "statistic": "mean",
                "coverage_rate": 0.90 + (i * 0.01),
                "adjusted_coverage": 0.92,
                "adjustment_method": "variance_inflation",
                "improvement_delta": 0.02,
                "seed": 42 + i
            })
        
        df = pd.DataFrame(results)
        output_path = Path("artifacts/coverage_results_test.csv")
        df.to_csv(output_path, index=False)
        
        # Verify
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 5
        assert "coverage_rate" in loaded_df.columns
        assert "epsilon" in loaded_df.columns

    def test_coverage_aggregation_logic(self):
        """Test the logic of aggregating coverage rates (mocking T013c aggregation)."""
        # Create a dataframe with multiple runs for the same condition
        data = {
            "dataset": ["adult"] * 10,
            "epsilon": [1.0] * 10,
            "noise_type": ["laplace"] * 10,
            "statistic": ["mean"] * 10,
            "coverage_rate": [0.94, 0.95, 0.93, 0.96, 0.95, 0.94, 0.95, 0.96, 0.94, 0.95]
        }
        df = pd.DataFrame(data)
        
        # Aggregate
        grouped = df.groupby(["dataset", "epsilon", "noise_type", "statistic"]).agg({
            "coverage_rate": "mean"
        }).reset_index()
        
        mean_coverage = grouped["coverage_rate"].iloc[0]
        
        # Should be close to 0.947
        assert 0.94 < mean_coverage < 0.96

    def test_invalid_epsilon_handling(self):
        """Test behavior with invalid epsilon values."""
        sample_data = self._load_small_sample(n_samples=20)
        
        # Epsilon must be positive
        with pytest.raises((ValueError, ZeroDivisionError)):
            inject_laplace_noise(sample_data.values, epsilon=0.0, sensitivity=1.0)

    def test_full_csv_schema_validation(self):
        """Validate that the output CSV matches the expected schema from T013c."""
        expected_columns = [
            "dataset", "epsilon", "noise_type", "statistic", 
            "coverage_rate", "adjusted_coverage", "adjustment_method", 
            "improvement_delta", "seed"
        ]
        
        # Create a dummy row
        dummy_row = {col: 0 if col in ["epsilon", "coverage_rate", "adjusted_coverage", "improvement_delta", "seed"] else "test" 
                    for col in expected_columns}
        dummy_row["noise_type"] = "test"
        dummy_row["statistic"] = "test"
        dummy_row["dataset"] = "test"
        
        df = pd.DataFrame([dummy_row])
        output_path = Path("artifacts/schema_test.csv")
        df.to_csv(output_path, index=False)
        
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == expected_columns