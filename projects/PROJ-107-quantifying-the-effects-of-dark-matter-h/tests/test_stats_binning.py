import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.stats import (
    bin_halo_by_shape,
    kruskal_wallis_test,
    mann_whitney_u_test,
    ks_test,
    run_binning_tests
)

class TestShapeBinningLogic:
    """Test the shape binning logic (FR-003/FR-004)."""

    def test_bin_halo_by_shape_prolate(self):
        """Test that c/a < 0.5 is classified as prolate."""
        df = pd.DataFrame({"c_a_ratio": [0.1, 0.3, 0.49]})
        bins = bin_halo_by_shape(df)
        assert all(bins == "prolate")

    def test_bin_halo_by_shape_triaxial(self):
        """Test that 0.5 <= c/a <= 0.8 is classified as triaxial."""
        df = pd.DataFrame({"c_a_ratio": [0.5, 0.6, 0.8]})
        bins = bin_halo_by_shape(df)
        assert all(bins == "triaxial")

    def test_bin_halo_by_shape_spherical(self):
        """Test that c/a > 0.8 is classified as spherical."""
        df = pd.DataFrame({"c_a_ratio": [0.81, 0.9, 1.0]})
        bins = bin_halo_by_shape(df)
        assert all(bins == "spherical")

    def test_bin_halo_by_shape_nan(self):
        """Test handling of NaN values."""
        df = pd.DataFrame({"c_a_ratio": [np.nan, 0.5]})
        bins = bin_halo_by_shape(df)
        assert pd.isna(bins.iloc[0])
        assert bins.iloc[1] == "triaxial"

class TestBinningStatisticalTests:
    """Test the statistical tests for binning."""

    def test_kruskal_wallis_test(self):
        """Test Kruskal-Wallis test function."""
        groups = {
            "prolate": pd.Series([1, 2, 3, 4, 5]),
            "triaxial": pd.Series([10, 11, 12, 13, 14]),
            "spherical": pd.Series([20, 21, 22, 23, 24])
        }
        stat, pval = kruskal_wallis_test(groups, "value")
        assert not np.isnan(pval)
        assert pval < 0.05  # Should be significant given the separation

    def test_mann_whitney_u_test(self):
        """Test Mann-Whitney U test function."""
        g1 = pd.Series([1, 2, 3])
        g2 = pd.Series([10, 11, 12])
        stat, pval = mann_whitney_u_test(g1, g2)
        assert not np.isnan(pval)
        assert pval < 0.05

    def test_ks_test(self):
        """Test Kolmogorov-Smirnov test function."""
        g1 = pd.Series(np.random.normal(0, 1, 100))
        g2 = pd.Series(np.random.normal(2, 1, 100))
        stat, pval = ks_test(g1, g2)
        assert not np.isnan(pval)

    def test_run_binning_tests_integration(self):
        """Test the full integration of run_binning_tests with mock data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            chunks_dir = tmpdir / "matched_chunks"
            chunks_dir.mkdir()
            output_file = tmpdir / "binning_tests.csv"

            # Create mock matched chunks
            mock_data = pd.DataFrame({
                "halo_id": range(100),
                "mass": np.random.uniform(1e12, 1e14, 100),
                "c_a_ratio": np.random.uniform(0.1, 1.0, 100),
                "sfr": np.random.uniform(0, 100, 100),
                "effective_radius": np.random.uniform(1, 10, 100),
                "stellar_mass": np.random.uniform(1e9, 1e11, 100)
            })
            
            # Split into 2 chunks
            chunk1 = mock_data.iloc[:50]
            chunk2 = mock_data.iloc[50:]
            
            chunk1.to_csv(chunks_dir / "match_001.csv", index=False)
            chunk2.to_csv(chunks_dir / "match_002.csv", index=False)

            # Run tests
            result_df = run_binning_tests(
                matched_chunks_dir=chunks_dir,
                output_path=output_file,
                property_cols=["sfr", "effective_radius", "stellar_mass"]
            )

            # Verify output file exists and has content
            assert output_file.exists()
            assert len(result_df) > 0
            
            # Verify columns
            expected_cols = [
                "test_type", "property", "comparison", 
                "statistic", "p_value", "significant_at_0.01"
            ]
            assert all(col in result_df.columns for col in expected_cols)
            
            # Verify test types present
            test_types = result_df["test_type"].unique()
            assert "kruskal_wallis" in test_types
            assert "mann_whitney_u" in test_types
            assert "kolmogorov_smirnov" in test_types
            
            # Verify significant_at_0.01 is boolean
            assert result_df["significant_at_0.01"].dtype == bool

if __name__ == "__main__":
    pytest.main([__file__, "-v"])