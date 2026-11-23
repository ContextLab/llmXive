"""
Integration test for full statistical comparison (User Story 3).

This test verifies the end-to-end statistical comparison pipeline:
1. Loads pre-computed fit results from US2 (T025)
2. Computes residuals (US3 T031)
3. Performs block-bootstrap permutation test (US3 T032)
4. Applies Holm-Bonferroni correction (US3 T033)
5. Generates results/residual_stats.csv (US3 T034)
6. Validates output structure and statistical properties

Prerequisites:
- US1 complete: data/processed/filtered_galaxies.csv exists
- US2 complete: results/fit_summary.csv exists with reduced_chi2 metrics
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import setup_logging, get_logger, set_global_seed
from code.fit import fit_all_galaxies, load_filtered_data
from code.metrics import compute_fit_metrics
from code.residuals import (
    calculate_residuals,
    block_bootstrap_permutation_test,
    holm_bonferroni_correction,
    generate_residual_stats
)
from code.config import load_config, ensure_dirs

# Configure logging for tests
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Set deterministic seed for reproducibility
set_global_seed(42)

class TestFullStatisticalComparison:
    """Integration tests for the full statistical comparison pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Set up temporary directories and clean up after test."""
        self.temp_dir = tmp_path
        self.data_dir = self.temp_dir / "data"
        self.results_dir = self.temp_dir / "results"
        self.code_dir = project_root / "code"

        # Create required directories
        (self.data_dir / "processed").mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Mock config for testing
        self.config = {
            "data_dir": str(self.data_dir),
            "results_dir": str(self.results_dir),
            "seed": 42,
            "alpha": 0.05,
            "bootstrap_samples": 1000,
            "block_size": 5
        }

        yield

        # Cleanup handled by tmp_path fixture

    def _create_mock_fit_summary(self, n_galaxies: int = 5) -> pd.DataFrame:
        """Create a mock fit_summary.csv with realistic data for testing."""
        galaxy_ids = [f"NGC-{i:04d}" for i in range(1001, 1001 + n_galaxies)]
        models = ["MOND", "NFW"]

        records = []
        for gid in galaxy_ids:
            for model in models:
                # Simulate realistic fit metrics
                chi2_red = np.random.uniform(0.8, 2.5)
                aic = np.random.uniform(100, 500)
                bic = np.random.uniform(110, 520)
                n_params = 2 if model == "MOND" else 3
                n_points = np.random.randint(15, 100)

                records.append({
                    "galaxy_id": gid,
                    "model": model,
                    "chi2_reduced": chi2_red,
                    "aic": aic,
                    "bic": bic,
                    "n_params": n_params,
                    "n_points": n_points,
                    "converged": True
                })

        df = pd.DataFrame(records)
        output_path = self.results_dir / "fit_summary.csv"
        df.to_csv(output_path, index=False)
        return df

    def _create_mock_filtered_data(self, n_galaxies: int = 5) -> pd.DataFrame:
        """Create mock filtered galaxy data with rotation curves."""
        records = []
        for i in range(n_galaxies):
            galaxy_id = f"NGC-{1001 + i:04d}"
            n_points = np.random.randint(15, 30)
            r = np.linspace(1, 10, n_points)
            v = 50 + 10 * np.sin(r) + np.random.normal(0, 2, n_points)
            v_err = np.ones(n_points) * 2.0

            for j in range(n_points):
                records.append({
                    "galaxy_id": galaxy_id,
                    "radial_distance": r[j],
                    "velocity": v[j],
                    "velocity_uncertainty": v_err[j]
                })

        df = pd.DataFrame(records)
        output_path = self.data_dir / "processed" / "filtered_galaxies.csv"
        df.to_csv(output_path, index=False)
        return df

    def test_full_pipeline_execution(self):
        """
        Test the complete statistical comparison pipeline end-to-end.

        Verifies:
        1. Data loading succeeds
        2. Residuals are computed correctly
        3. Block-bootstrap produces valid p-values
        4. Holm-Bonferroni correction is applied
        5. Output CSV is generated with expected schema
        """
        logger.info("Starting full statistical comparison integration test")

        # Step 1: Create mock input data
        logger.info("Creating mock fit summary and filtered data")
        fit_summary = self._create_mock_fit_summary(n_galaxies=5)
        filtered_data = self._create_mock_filtered_data(n_galaxies=5)

        # Verify inputs exist
        assert fit_summary is not None
        assert filtered_data is not None
        assert len(fit_summary) == 10  # 5 galaxies * 2 models
        assert len(filtered_data) > 0

        # Step 2: Calculate residuals for all galaxies and models
        logger.info("Calculating residuals")
        residuals_df = calculate_residuals(
            filtered_data=filtered_data,
            fit_summary=fit_summary,
            results_dir=self.results_dir
        )

        assert residuals_df is not None
        assert "galaxy_id" in residuals_df.columns
        assert "model" in residuals_df.columns
        assert "residual" in residuals_df.columns
        assert len(residuals_df) > 0

        # Step 3: Perform block-bootstrap permutation test
        logger.info("Running block-bootstrap permutation test")
        bootstrap_results = block_bootstrap_permutation_test(
            residuals_df=residuals_df,
            n_samples=self.config["bootstrap_samples"],
            block_size=self.config["block_size"],
            alpha=self.config["alpha"]
        )

        assert bootstrap_results is not None
        assert isinstance(bootstrap_results, dict)
        assert "p_values" in bootstrap_results
        assert "bootstrap_stats" in bootstrap_results

        # Verify p-values are in valid range [0, 1]
        for model, p_val in bootstrap_results["p_values"].items():
            assert 0.0 <= p_val <= 1.0, f"Invalid p-value for {model}: {p_val}"

        # Step 4: Apply Holm-Bonferroni correction
        logger.info("Applying Holm-Bonferroni correction")
        corrected_results = holm_bonferroni_correction(
            p_values=bootstrap_results["p_values"],
            alpha=self.config["alpha"]
        )

        assert corrected_results is not None
        assert "corrected_p_values" in corrected_results
        assert "rejections" in corrected_results

        # Verify corrected p-values are in valid range
        for model, p_val in corrected_results["corrected_p_values"].items():
            assert 0.0 <= p_val <= 1.0, f"Invalid corrected p-value for {model}: {p_val}"

        # Step 5: Generate residual statistics CSV
        logger.info("Generating residual statistics CSV")
        stats_df = generate_residual_stats(
            residuals_df=residuals_df,
            bootstrap_results=bootstrap_results,
            corrected_results=corrected_results,
            output_path=self.results_dir / "residual_stats.csv"
        )

        # Step 6: Validate output file
        logger.info("Validating output file")
        output_path = self.results_dir / "residual_stats.csv"
        assert output_path.exists(), "residual_stats.csv was not created"

        output_df = pd.read_csv(output_path)

        # Check required columns
        required_columns = [
            "galaxy_id",
            "model",
            "residual_mean",
            "residual_median",
            "residual_std",
            "p_value_bootstrap",
            "p_value_corrected",
            "significant"
        ]

        for col in required_columns:
            assert col in output_df.columns, f"Missing required column: {col}"

        # Check data types and ranges
        assert output_df["residual_mean"].notna().all()
        assert output_df["residual_std"].notna().all()
        assert output_df["p_value_bootstrap"].between(0, 1).all()
        assert output_df["p_value_corrected"].between(0, 1).all()
        assert output_df["significant"].isin([True, False]).all()

        # Verify we have entries for all galaxy-model combinations
        expected_rows = len(fit_summary)
        assert len(output_df) == expected_rows, \
            f"Expected {expected_rows} rows, got {len(output_df)}"

        logger.info("Full statistical comparison pipeline test PASSED")
        print(f"Output file created at: {output_path}")
        print(f"Summary:\n{output_df[['galaxy_id', 'model', 'p_value_bootstrap', 'p_value_corrected', 'significant']]}")

    def test_bootstrap_reproducibility(self):
        """Test that block-bootstrap produces reproducible results with fixed seed."""
        logger.info("Testing bootstrap reproducibility")

        # Create fresh data
        fit_summary = self._create_mock_fit_summary(n_galaxies=3)
        filtered_data = self._create_mock_filtered_data(n_galaxies=3)

        # Run first time
        residuals_df = calculate_residuals(filtered_data, fit_summary, self.results_dir)
        set_global_seed(42)
        results_1 = block_bootstrap_permutation_test(
            residuals_df,
            n_samples=500,
            block_size=3,
            alpha=0.05
        )

        # Run second time with same seed
        set_global_seed(42)
        results_2 = block_bootstrap_permutation_test(
            residuals_df,
            n_samples=500,
            block_size=3,
            alpha=0.05
        )

        # Compare p-values
        for model in results_1["p_values"]:
            assert np.isclose(
                results_1["p_values"][model],
                results_2["p_values"][model],
                rtol=1e-10
            ), f"Non-reproducible p-value for {model}"

        logger.info("Bootstrap reproducibility test PASSED")

    def test_holm_bonferroni_logic(self):
        """Test that Holm-Bonferroni correction correctly adjusts p-values."""
        logger.info("Testing Holm-Bonferroni logic")

        # Create test p-values (sorted ascending)
        test_p_values = {
            "MOND": 0.01,
            "NFW": 0.03,
            "Modified_MOND": 0.06,
            "NFW_Prior": 0.10
        }

        # Apply correction
        corrected = holm_bonferroni_correction(test_p_values, alpha=0.05)

        # Verify monotonicity of corrected p-values
        sorted_models = sorted(test_p_values.keys(), key=lambda x: test_p_values[x])
        corrected_sorted = [corrected["corrected_p_values"][m] for m in sorted_models]

        for i in range(1, len(corrected_sorted)):
            assert corrected_sorted[i] >= corrected_sorted[i-1], \
                "Corrected p-values should be monotonically non-decreasing"

        # Verify at least the smallest p-value is adjusted
        assert corrected["corrected_p_values"]["MOND"] >= test_p_values["MOND"]

        # Verify rejection logic
        # With alpha=0.05, MOND (0.01) and NFW (0.03) should potentially be rejected
        # depending on the correction
        assert "rejections" in corrected
        assert isinstance(corrected["rejections"], dict)

        logger.info("Holm-Bonferroni logic test PASSED")

    def test_empty_input_handling(self):
        """Test that the pipeline handles empty inputs gracefully."""
        logger.info("Testing empty input handling")

        # Create empty fit summary
        empty_fit = pd.DataFrame(columns=["galaxy_id", "model", "chi2_reduced"])
        empty_fit_path = self.results_dir / "fit_summary.csv"
        empty_fit.to_csv(empty_fit_path, index=False)

        # Create empty filtered data
        empty_data = pd.DataFrame(columns=["galaxy_id", "radial_distance", "velocity"])
        empty_data_path = self.data_dir / "processed" / "filtered_galaxies.csv"
        empty_data.to_csv(empty_data_path, index=False)

        # Should raise or return empty results without crashing
        try:
            residuals_df = calculate_residuals(empty_data, empty_fit, self.results_dir)
            if residuals_df is not None and len(residuals_df) == 0:
                logger.info("Empty input handled correctly (returned empty DataFrame)")
            else:
                logger.warning("Empty input did not return expected empty DataFrame")
        except Exception as e:
            logger.info(f"Empty input raised exception (acceptable): {e}")

        logger.info("Empty input handling test completed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
