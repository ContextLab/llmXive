"""
Integration test for statistical test selection (t-test vs Mann-Whitney).

This test verifies that the analysis module correctly selects the appropriate
statistical test (Student's t-test or Mann-Whitney U) based on the normality
of the data distribution (Shapiro-Wilk test).

It generates synthetic data distributions (Normal vs Non-Uniform) to validate
the logic in `code/analysis/statistical_test.py` without requiring the full
data acquisition pipeline to run.
"""
import os
import sys
import math
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.statistical_test import (
    run_shapiro_wilk,
    select_and_run_test,
    run_full_analysis
)
from utils.config import set_global_seed

# Set seed for reproducibility in this integration test
set_global_seed(42)


def generate_normal_data(n: int, mean: float = 0.0, std: float = 1.0) -> List[float]:
    """Generate a list of values from a normal distribution."""
    return np.random.normal(loc=mean, scale=std, size=n).tolist()


def generate_skewed_data(n: int) -> List[float]:
    """Generate a list of values from a skewed (exponential) distribution."""
    # Exponential distribution is clearly non-normal
    return np.random.exponential(scale=2.0, size=n).tolist()


def generate_uniform_data(n: int) -> List[float]:
    """Generate a list of values from a uniform distribution (often fails normality)."""
    return np.random.uniform(low=0.0, high=10.0, size=n).tolist()


class TestStatisticalTestSelection:
    """Integration tests for statistical test selection logic."""

    def setup_method(self):
        """Create temporary directories for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_output.parquet")

    def teardown_method(self):
        """Clean up temporary directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_shapiro_wilk_normal_data(self):
        """
        Verify that Shapiro-Wilk correctly identifies normal data as normal (p > 0.05).
        """
        data = generate_normal_data(n=100, mean=10.0, std=2.0)
        stat, p_value = run_shapiro_wilk(data)

        # With a normal distribution, p-value should be > 0.05 (fail to reject null)
        assert p_value > 0.05, f"Normal data incorrectly rejected: p={p_value}"
        print(f"Normal data Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f} -> PASS (Normal)")

    def test_shapiro_wilk_skewed_data(self):
        """
        Verify that Shapiro-Wilk correctly identifies skewed data as non-normal (p < 0.05).
        """
        data = generate_skewed_data(n=100)
        stat, p_value = run_shapiro_wilk(data)

        # With exponential distribution, p-value should be < 0.05 (reject null)
        assert p_value < 0.05, f"Skewed data incorrectly accepted as normal: p={p_value}"
        print(f"Skewed data Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f} -> PASS (Non-Normal)")

    def test_shapiro_wilk_uniform_data(self):
        """
        Verify that Shapiro-Wilk correctly identifies uniform data as non-normal.
        """
        data = generate_uniform_data(n=100)
        stat, p_value = run_shapiro_wilk(data)

        # Uniform distribution is not normal, p-value should be < 0.05
        assert p_value < 0.05, f"Uniform data incorrectly accepted as normal: p={p_value}"
        print(f"Uniform data Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f} -> PASS (Non-Normal)")

    def test_selection_ttest_path(self):
        """
        Verify that the pipeline selects t-test when data is normal.
        """
        group_a = generate_normal_data(50, mean=10.0, std=2.0)
        group_b = generate_normal_data(50, mean=12.0, std=2.0)

        result = select_and_run_test(group_a, group_b)

        # Should select 't-test'
        assert result["test_name"] == "t-test", f"Expected t-test, got {result['test_name']}"
        assert "statistic" in result
        assert "p_value" in result
        print(f"Selection Test (Normal): Selected {result['test_name']}, p={result['p_value']:.4f}")

    def test_selection_mann_whitney_path(self):
        """
        Verify that the pipeline selects Mann-Whitney U when data is non-normal.
        """
        group_a = generate_skewed_data(50)
        group_b = generate_skewed_data(50)

        result = select_and_run_test(group_a, group_b)

        # Should select 'mann-whitney'
        assert result["test_name"] == "mann-whitney", f"Expected mann-whitney, got {result['test_name']}"
        assert "statistic" in result
        assert "p_value" in result
        print(f"Selection Test (Skewed): Selected {result['test_name']}, p={result['p_value']:.4f}")

    def test_full_analysis_integration(self):
        """
        End-to-end integration test: Create a DataFrame, run full analysis,
        and verify output file is written correctly.
        """
        # Create a mock dataset
        np.random.seed(42)
        n_samples = 100
        
        # Mix of normal and non-normal to test robustness
        # Group A: Normal
        group_a = generate_normal_data(n_samples, mean=5.0, std=1.0)
        # Group B: Non-normal (Exponential)
        group_b = generate_skewed_data(n_samples)

        df = pd.DataFrame({
            "review_duration": group_a + group_b,
            "group": ["human"] * n_samples + ["llm"] * n_samples
        })

        # Run full analysis
        result = run_full_analysis(df, target_col="review_duration", group_col="group")

        # Verify result structure
        assert "test_name" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "is_significant" in result

        # Verify significance logic (p < 0.05)
        expected_significant = result["p_value"] < 0.05
        assert result["is_significant"] == expected_significant

        print(f"Full Analysis Result: {result['test_name']}, p={result['p_value']:.4f}, sig={result['is_significant']}")

        # Write to parquet to ensure the I/O path works
        temp_out = os.path.join(self.temp_dir, "analysis_result.parquet")
        # Convert result dict to a single-row DataFrame for saving
        res_df = pd.DataFrame([result])
        res_df.to_parquet(temp_out)

        assert os.path.exists(temp_out), "Output parquet file was not created"
        loaded_df = pd.read_parquet(temp_out)
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]["test_name"] == result["test_name"]
        print("Integration test passed: File I/O successful.")

if __name__ == "__main__":
    import pytest
    # Run the tests
    pytest.main([__file__, "-v"])

# Also run a quick smoke test if executed directly
if __name__ == "__main__" and "pytest" not in sys.modules:
    test_runner = TestStatisticalTestSelection()
    test_runner.setup_method()
    try:
        print("Running integration tests...")
        test_runner.test_shapiro_wilk_normal_data()
        test_runner.test_shapiro_wilk_skewed_data()
        test_runner.test_shapiro_wilk_uniform_data()
        test_runner.test_selection_ttest_path()
        test_runner.test_selection_mann_whitney_path()
        test_runner.test_full_analysis_integration()
        print("All integration tests passed.")
    finally:
        test_runner.teardown_method()
