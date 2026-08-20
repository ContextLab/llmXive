"""
Integration test for correlation and regression on mock data.

This test verifies the analysis pipeline (Kendall's tau and regression) works
end-to-end on a deterministic mock dataset. It ensures that the statistical
methods handle censored data (upper limits) correctly and that the output
schema matches expectations.

Note: This test uses a small, deterministic mock dataset to avoid external
dependencies and ensure reproducibility. It does not use real exoplanet data.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the analysis functions from the project code
# These names must match the public API surface in code/analysis.py
from analysis import (
    load_analysis_data,
    quality_control_filter,
    compute_censored_kendall_tau,
    run_bootstrap_ci,
    save_bootstrap_results,
)
from config import get_config


class MockDataGenerator:
    """Generates a deterministic mock dataset for testing analysis functions."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)

    def generate_dataset(self, n_samples: int = 50) -> pd.DataFrame:
        """
        Generate a mock dataset with:
        - planet_name: unique identifiers
        - temperature: equilibrium temperature (K)
        - water_mixing_ratio: log10 water abundance
        - is_upper_limit: boolean flag for censored data
        - snr: signal-to-noise ratio
        - resolution: spectral resolution
        - mass: planetary mass (Mjup)
        - metallicity: atmospheric metallicity (Z/Zsun)
        """
        # Generate base data
        temperatures = np.linspace(800, 2500, n_samples) + np.random.normal(0, 50, n_samples)

        # Create a correlation: higher temperature -> higher water abundance (with noise)
        # But add some censored values (upper limits)
        true_water = 0.02 * temperatures - 10 + np.random.normal(0, 0.5, n_samples)

        # Create upper limits for low SNR cases
        snr_values = np.random.lognormal(2, 0.5, n_samples)
        is_upper_limit = snr_values < 50  # Low SNR -> upper limit

        # For upper limits, set water abundance to a detection limit
        detection_limits = true_water - np.abs(np.random.normal(0.5, 0.2, n_samples))
        water_mixing_ratio = np.where(is_upper_limit, detection_limits, true_water)

        # Generate other metadata
        planet_names = [f"Planet_{i:03d}" for i in range(n_samples)]
        masses = np.random.uniform(0.5, 5.0, n_samples)  # Mjup
        metallicities = np.random.uniform(0.1, 10.0, n_samples)  # Z/Zsun
        resolutions = np.random.uniform(50, 200, n_samples)

        df = pd.DataFrame({
            "planet_name": planet_names,
            "temperature": temperatures,
            "water_mixing_ratio": water_mixing_ratio,
            "is_upper_limit": is_upper_limit,
            "snr": snr_values,
            "resolution": resolutions,
            "mass": masses,
            "metallicity": metallicities,
        })

        return df

def test_analysis_pipeline_on_mock_data():
    """
    Integration test: Run the full analysis pipeline on mock data.

    This test:
    1. Generates a deterministic mock dataset
    2. Saves it to a temporary CSV
    3. Loads it via the analysis module
    4. Runs quality control filtering
    5. Computes censored Kendall's tau
    6. Runs bootstrap confidence intervals
    7. Verifies the outputs are valid and non-empty
    """
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Step 1: Generate mock data
        mock_gen = MockDataGenerator(seed=42)
        mock_df = mock_gen.generate_dataset(n_samples=50)

        # Save mock data to a temporary CSV
        input_file = tmp_path / "mock_analysis_data.csv"
        mock_df.to_csv(input_file, index=False)

        # Step 2: Load data via analysis module
        # Note: load_analysis_data expects a DataFrame or path
        loaded_df = load_analysis_data(input_file)
        assert loaded_df is not None
        assert len(loaded_df) > 0
        assert "water_mixing_ratio" in loaded_df.columns
        assert "is_upper_limit" in loaded_df.columns
        assert "temperature" in loaded_df.columns

        # Step 3: Apply quality control filter
        qc_df = quality_control_filter(loaded_df)
        assert qc_df is not None
        assert len(qc_df) > 0
        # QC should remove extreme outliers but keep most data
        assert len(qc_df) <= len(loaded_df)

        # Step 4: Compute censored Kendall's tau
        # The function should handle is_upper_limit column
        tau_result = compute_censored_kendall_tau(qc_df)
        assert tau_result is not None
        assert "tau" in tau_result
        assert "p_value" in tau_result
        # Tau should be between -1 and 1
        assert -1.0 <= tau_result["tau"] <= 1.0
        # P-value should be between 0 and 1
        assert 0.0 <= tau_result["p_value"] <= 1.0

        # Step 5: Run bootstrap confidence intervals
        bootstrap_results = run_bootstrap_ci(
            qc_df,
            n_iterations=100,  # Reduced for faster testing
            random_state=42
        )
        assert bootstrap_results is not None
        assert "ci_lower" in bootstrap_results
        assert "ci_upper" in bootstrap_results
        assert "ci_width" in bootstrap_results
        assert bootstrap_results["ci_lower"] < bootstrap_results["ci_upper"]

        # Step 6: Save bootstrap results to verify file I/O
        output_file = tmp_path / "bootstrap_ci_test.json"
        save_bootstrap_results(bootstrap_results, output_file)
        assert output_file.exists()

        # Step 7: Verify saved JSON is valid
        with open(output_file, "r") as f:
            saved_results = json.load(f)
        assert saved_results["ci_lower"] == bootstrap_results["ci_lower"]
        assert saved_results["ci_upper"] == bootstrap_results["ci_upper"]

        # Step 8: Verify that the correlation is detectable in our mock data
        # Since we generated a positive correlation, tau should be positive
        # (though with noise and censoring, it might be small)
        # We assert it's not exactly zero or negative to confirm the pipeline works
        assert tau_result["tau"] > 0, "Expected positive correlation in mock data"

        # Step 9: Verify that censored data handling works
        # Count how many upper limits we have
        n_upper_limits = qc_df["is_upper_limit"].sum()
        assert n_upper_limits > 0, "Mock data should have some upper limits"
        assert n_upper_limits < len(qc_df), "Not all data should be upper limits"

        # Step 10: Verify that the pipeline handles edge cases
        # Try with a subset of data that has only uncensored values
        uncensored_df = qc_df[~qc_df["is_upper_limit"]].copy()
        if len(uncensored_df) > 10:
            tau_uncensored = compute_censored_kendall_tau(uncensored_df)
            assert tau_uncensored is not None
            assert "tau" in tau_uncensored

        # Try with a subset that has only censored values
        censored_df = qc_df[qc_df["is_upper_limit"]].copy()
        if len(censored_df) > 10:
            # This might fail gracefully or return a specific value for censored-only data
            try:
                tau_censored = compute_censored_kendall_tau(censored_df)
                # If it succeeds, it should return a valid tau
                assert tau_censored is not None
            except Exception:
                # If it fails, that's acceptable for censored-only data
                pass

        print("Integration test passed successfully!")
        print(f"  - Loaded {len(loaded_df)} samples")
        print(f"  - QC filtered to {len(qc_df)} samples")
        print(f"  - Kendall's tau: {tau_result['tau']:.4f} (p={tau_result['p_value']:.4f})")
        print(f"  - Bootstrap CI: [{bootstrap_results['ci_lower']:.4f}, {bootstrap_results['ci_upper']:.4f}]")
        print(f"  - Upper limits: {n_upper_limits} ({n_upper_limits/len(qc_df)*100:.1f}%)")


def test_analysis_with_varying_censorship_rates():
    """
    Test that the analysis pipeline handles different rates of censored data.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Generate datasets with different censorship rates
        for censor_rate in [0.1, 0.3, 0.5]:
            mock_gen = MockDataGenerator(seed=42)
            mock_df = mock_gen.generate_dataset(n_samples=100)

            # Artificially adjust censorship rate
            n_samples = len(mock_df)
            n_censored = int(n_samples * censor_rate)
            mock_df.loc[mock_df.index[:n_censored], "is_upper_limit"] = True

            # Save and load
            input_file = tmp_path / f"mock_censor_{censor_rate}.csv"
            mock_df.to_csv(input_file, index=False)

            loaded_df = load_analysis_data(input_file)
            qc_df = quality_control_filter(loaded_df)

            # Run analysis
            tau_result = compute_censored_kendall_tau(qc_df)
            bootstrap_results = run_bootstrap_ci(qc_df, n_iterations=50, random_state=42)

            # Verify results are valid
            assert tau_result is not None
            assert "tau" in tau_result
            assert bootstrap_results is not None
            assert "ci_lower" in bootstrap_results

            print(f"Censorship rate {censor_rate:.1f}: tau={tau_result['tau']:.4f}, CI=[{bootstrap_results['ci_lower']:.4f}, {bootstrap_results['ci_upper']:.4f}]")


if __name__ == "__main__":
    # Run tests when executed directly
    test_analysis_pipeline_on_mock_data()
    test_analysis_with_varying_censorship_rates()
    print("All integration tests passed!")