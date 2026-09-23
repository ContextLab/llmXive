import pytest
import os
import json
import tempfile
import subprocess
import sys
from pathlib import Path

# Import the function directly for unit testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from data.synthetic import generate_synthetic_data, validate_schema

class TestSyntheticGenerator:
    """Contract tests for synthetic data generation."""

    def test_synthetic_produces_known_variance(self):
        """
        Test that the generated data has a variance close to the specified true_variance.
        Note: Due to sampling noise, we check within a tolerance.
        """
        n = 10000  # Large N to reduce sampling noise
        true_mean = 50.0
        true_variance = 100.0
        seed = 42

        df = generate_synthetic_data(
            n=n,
            true_mean=true_mean,
            true_variance=true_variance,
            missing_rate=0.0,  # No missingness for this test
            mechanism="MCAR",
            seed=seed
        )

        # Calculate sample variance (ddof=1)
        # We expect the sample variance to be close to true_variance
        sample_var = df["value"].var(ddof=1)
        
        # Tolerance: 10% for sample variance with N=10000
        tolerance = 0.10 * true_variance
        
        assert abs(sample_var - true_variance) < tolerance, \
            f"Sample variance {sample_var} differs from true variance {true_variance} by more than {tolerance}"

    def test_synthetic_mcar_independence(self):
        """
        Test that for MCAR, missingness is independent of the value.
        We check that the mean of observed values is close to the mean of missing values (conceptually).
        Since we mask randomly, the observed subset should be representative.
        """
        n = 10000
        true_mean = 50.0
        true_variance = 100.0
        missing_rate = 0.3
        seed = 123

        df = generate_synthetic_data(
            n=n,
            true_mean=true_mean,
            true_variance=true_variance,
            missing_rate=missing_rate,
            mechanism="MCAR",
            seed=seed
        )

        observed_mean = df.loc[~df["missing"], "value"].mean()
        # Theoretical expectation: observed_mean should be close to true_mean
        
        # Allow 5% tolerance
        tolerance = 0.05 * true_mean
        assert abs(observed_mean - true_mean) < tolerance, \
            f"MCAR Observed mean {observed_mean} is not close to true mean {true_mean}"

    def test_synthetic_mar_dependence(self):
        """
        Test that for MAR, missingness is dependent on the value.
        We expect the observed mean to deviate from the true mean.
        """
        n = 10000
        true_mean = 50.0
        true_variance = 100.0
        missing_rate = 0.3
        seed = 456

        df = generate_synthetic_data(
            n=n,
            true_mean=true_mean,
            true_variance=true_variance,
            missing_rate=missing_rate,
            mechanism="MAR",
            seed=seed
        )

        observed_mean = df.loc[~df["missing"], "value"].mean()
        
        # For MAR, we expect a deviation. 
        # We just check that it's NOT exactly the true mean (with a small buffer for noise)
        # and that the deviation is significant enough to be detected.
        # A strict equality check is bad, but we can check if the bias is > 1% of mean.
        bias = abs(observed_mean - true_mean)
        
        # If bias is very small (< 0.5%), it might be noise, but typically MAR creates bias.
        # We assert that the bias is NOT zero (within floating point) and likely > 0.1
        assert bias > 0.1, f"MAR mechanism did not produce expected bias. Observed mean: {observed_mean}"

    def test_schema_validation_pass(self):
        """Test that valid metadata passes schema validation."""
        metadata = {
            "true_mean": 50.0,
            "true_variance": 100.0,
            "missingness_mechanism": "MCAR"
        }
        assert validate_schema(metadata, "MCAR") is True

    def test_schema_validation_fail_missing_key(self):
        """Test that missing keys fail validation."""
        metadata = {
            "true_mean": 50.0,
            # missing true_variance
            "missingness_mechanism": "MCAR"
        }
        assert validate_schema(metadata, "MCAR") is False

    def test_cli_generation(self):
        """Test that the CLI script runs successfully and creates files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test.csv")
            meta_path = os.path.join(tmpdir, "test_meta.json")
            
            cmd = [
                sys.executable, "-m", "data.synthetic",
                "--n-rows", "100",
                "--true-mean", "50",
                "--true-variance", "100",
                "--missing-rate", "0.2",
                "--mechanism", "MAR",
                "--seed", "42",
                "--output-csv", csv_path,
                "--output-meta", meta_path,
                "--generate",
                "--validate-schema"
            ]
            
            # Run from the project root to ensure imports work
            project_root = Path(__file__).parent.parent.parent
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert os.path.exists(csv_path), "CSV file not created"
            assert os.path.exists(meta_path), "Meta file not created"
            
            # Verify meta content
            with open(meta_path, "r") as f:
                meta = json.load(f)
            assert meta["missingness_mechanism"] == "MAR"
            assert meta["n_rows"] == 100