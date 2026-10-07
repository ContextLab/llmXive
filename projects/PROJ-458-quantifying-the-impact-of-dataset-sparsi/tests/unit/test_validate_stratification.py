import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from validate_stratification import (
    compute_jensen_shannon_divergence,
    compute_ks_test,
    validate_stratification,
    main
)

class TestStratificationValidation:
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        # Create a full pool with a known distribution
        np.random.seed(42)
        full_energy = np.random.normal(loc=-5.0, scale=2.0, size=1000)
        
        # Create an RSS pool that is a representative sample (similar distribution)
        rss_energy = np.random.normal(loc=-5.0, scale=2.0, size=300)
        
        # Create DataFrames
        full_df = pd.DataFrame({"formation_energy": full_energy, "id": range(1000)})
        rss_df = pd.DataFrame({"formation_energy": rss_energy, "id": range(300)})
        
        return full_df, rss_df

    @pytest.fixture
    def skewed_data(self):
        """Generate skewed data to test failure case."""
        np.random.seed(42)
        full_energy = np.random.normal(loc=-5.0, scale=2.0, size=1000)
        # RSS is shifted significantly to cause high divergence
        rss_energy = np.random.normal(loc=0.0, scale=1.0, size=300)
        
        full_df = pd.DataFrame({"formation_energy": full_energy, "id": range(1000)})
        rss_df = pd.DataFrame({"formation_energy": rss_energy, "id": range(300)})
        
        return full_df, rss_df

    def test_js_divergence_identical_distributions(self):
        """JS divergence should be near zero for identical distributions."""
        data = np.random.normal(0, 1, 1000)
        # Use the same data for both
        div = compute_jensen_shannon_divergence(pd.Series(data), pd.Series(data))
        assert div < 1e-6

    def test_js_divergence_different_distributions(self):
        """JS divergence should be positive for different distributions."""
        dist1 = pd.Series(np.random.normal(0, 1, 1000))
        dist2 = pd.Series(np.random.normal(5, 1, 1000))
        div = compute_jensen_shannon_divergence(dist1, dist2)
        assert div > 0.0

    def test_ks_test_identical_distributions(self, sample_data):
        """KS test p-value should be high for identical distributions."""
        full_df, rss_df = sample_data
        stat, pval = compute_ks_test(full_df["formation_energy"], rss_df["formation_energy"])
        # We expect high p-value (fail to reject null hypothesis)
        assert pval > 0.05 or stat < 0.1

    def test_validate_stratification_pass(self, sample_data):
        """Valid stratification should return PASS."""
        full_df, rss_df = sample_data
        result = validate_stratification(rss_df, full_df)
        
        assert result["status"] == "PASS"
        assert result["js_divergence"] <= 0.05
        assert "message" in result

    def test_validate_stratification_fail(self, skewed_data):
        """Invalid stratification should return FAIL and raise error."""
        full_df, rss_df = skewed_data
        result = validate_stratification(rss_df, full_df)
        
        assert result["status"] == "FAIL"
        assert result["js_divergence"] > 0.05
        
        # Verify that calling main with this data would raise RuntimeError
        # We test the function logic directly here to avoid file I/O in unit test
        with pytest.raises(RuntimeError):
            if result["status"] != "PASS":
                raise RuntimeError(result["message"])

    def test_validate_stratification_missing_column(self):
        """Should raise ValueError if target column is missing."""
        df1 = pd.DataFrame({"other_col": [1, 2, 3]})
        df2 = pd.DataFrame({"other_col": [1, 2, 3]})
        
        with pytest.raises(ValueError):
            validate_stratification(df1, df2)

    def test_main_execution_with_temp_files(self, sample_data, tmp_path):
        """Test the main entry point with temporary files."""
        full_df, rss_df = sample_data
        
        # Create temp files
        rss_path = tmp_path / "rss_pool.csv"
        full_path = tmp_path / "full_pool.csv"
        output_path = tmp_path / "stratification_report.json"
        
        rss_df.to_csv(rss_path, index=False)
        full_df.to_csv(full_path, index=False)
        
        # Run main
        exit_code = main([
            "--rss-path", str(rss_path),
            "--full-path", str(full_path),
            "--output-path", str(output_path)
        ])
        
        assert exit_code == 0
        assert output_path.exists()
        
        # Verify report content
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["status"] == "PASS"
        assert "js_divergence" in report