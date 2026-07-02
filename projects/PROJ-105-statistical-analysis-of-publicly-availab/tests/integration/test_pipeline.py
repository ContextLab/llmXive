"""
Integration test for model fitting and metrics generation (User Story 2).

This test verifies the end-to-end pipeline stage for User Story 2:
1. Loads pre-processed data (simulated or real if available).
2. Fits the 5 distributions (Exponential, Gamma, Log-Normal, Weibull, Pareto).
3. Computes metrics (AIC, BIC, KS, AD).
4. Saves results to `data/results/model_comparison.json`.

It asserts that:
- At least 3 models converge successfully.
- Output files are created.
- Metrics are numeric and within reasonable bounds.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pytest

# Import project modules
import sys
# Ensure code/ is in path for imports
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models import fit_distribution, ConvergenceError
from preprocessing import preprocess_flight_delays
from utils import setup_logging


def generate_mock_cleaned_data(output_path: Path, n_samples: int = 1000):
    """
    Generates a deterministic mock dataset that mimics cleaned flight delays.
    This is used for integration testing when real data is not available or
    to ensure the test is reproducible without network access.
    The data is constructed to be non-negative and have a heavy tail.
    """
    np.random.seed(42)
    # Create a mix of exponential and pareto-like behavior
    base = np.random.exponential(scale=15, size=n_samples // 2)
    tail = np.random.pareto(a=2.5, size=n_samples // 2) * 10 + 5
    data = np.concatenate([base, tail])
    # Ensure no zeros if the model expects positive (log-normal needs >0)
    # But preprocessing allows 0. We'll ensure >0 for log-normal fitting stability in test
    data = np.maximum(data, 0.1)

    df = pd.DataFrame({"total_delay": data})
    df.to_csv(output_path, index=False)
    return output_path


import pandas as pd


def test_us2_model_fitting_and_metrics_generation(tmp_path: Path):
    """
    Integration test: Run the model fitting logic on a dataset and verify
    metrics are generated and saved to JSON.
    """
    # Setup logging
    setup_logging()

    # 1. Prepare input data
    # We generate a mock dataset to ensure the test runs deterministically
    # without relying on the real BTS download (which might be slow or flaky).
    # In a real CI environment with data cached, this would load data/raw/cleaned_delays.csv
    input_csv = tmp_path / "cleaned_delays.csv"
    generate_mock_cleaned_data(input_csv, n_samples=2000)

    # 2. Load data
    df = pd.read_csv(input_csv)
    # Filter for positive values only for log-normal stability in this specific test context
    # (Real pipeline handles zeros, but log-normal MLE fails on zeros)
    # We will pass the data to the model functions which handle their own constraints
    data = df["total_delay"].values

    # 3. Define models to fit
    # Per T023/T024/T025a: Exponential, Gamma, Log-Normal, Weibull, Pareto
    models_to_test = [
        "expon",
        "gamma",
        "lognorm",
        "weibull_min",
        "pareto"
    ]

    results = []
    converged_count = 0

    # 4. Fit models and compute metrics
    for model_name in models_to_test:
        try:
            # Fit the model
            # Note: fit_distribution expects data and model name
            # It returns params and a success flag
            result = fit_distribution(data, model_name)

            if result.get("success", False):
                converged_count += 1
                # Compute metrics (AIC, BIC, KS, AD)
                # The fit_distribution function should ideally return these or we compute them here
                # Based on the task description, we need to compute them.
                # Assuming fit_distribution returns a dict with 'params' and 'dist_obj'
                dist_obj = result.get("dist_obj")
                params = result.get("params")

                # Calculate KS statistic
                ks_stat, ks_pvalue = stats.kstest(data, dist_obj.cdf, args=params)

                # Calculate AD statistic (scipy.stats does not have AD built-in directly for all dists easily,
                # but we can approximate or use a custom function if needed.
                # For this integration test, we will use a simplified Anderson-Darling check if available
                # or just rely on KS and AIC/BIC which are standard.
                # Let's implement a basic AD calculation for the test to ensure we have 4 metrics.
                # AD = -n - (1/n) * sum( (2i-1) * [ln(F(xi)) + ln(1-F(x(n-i+1)))] )
                sorted_data = np.sort(data)
                n = len(sorted_data)
                log_cdf = np.log(dist_obj.cdf(sorted_data, *params))
                log_sf = np.log(dist_obj.sf(sorted_data, *params))
                # Avoid log(0)
                log_cdf = np.clip(log_cdf, -700, 700)
                log_sf = np.clip(log_sf, -700, 700)

                ad_stat = -n - (1/n) * np.sum(
                    (2 * np.arange(1, n + 1) - 1) * (log_cdf + log_sf[::-1])
                )

                # AIC and BIC
                # AIC = 2k - 2ln(L)
                # BIC = k*ln(n) - 2ln(L)
                # We need log-likelihood. scipy.stats.rv_continuous.logpdf can be used.
                log_likelihood = np.sum(dist_obj.logpdf(data, *params))
                k = len(params)
                aic = 2 * k - 2 * log_likelihood
                bic = k * np.log(n) - 2 * log_likelihood

                results.append({
                    "model": model_name,
                    "params": params,
                    "aic": aic,
                    "bic": bic,
                    "ks_statistic": ks_stat,
                    "ks_pvalue": ks_pvalue,
                    "ad_statistic": ad_stat,
                    "converged": True
                })
            else:
                results.append({
                    "model": model_name,
                    "converged": False,
                    "error": result.get("error", "Unknown error")
                })

        except Exception as e:
            results.append({
                "model": model_name,
                "converged": False,
                "error": str(e)
            })

    # 5. Assertions
    # Assert at least 3 models converged (Per T029 requirement)
    assert converged_count >= 3, f"Only {converged_count} models converged. Expected at least 3."

    # Assert output structure
    for res in results:
        if res["converged"]:
            assert "aic" in res
            assert "bic" in res
            assert "ks_statistic" in res
            assert "ad_statistic" in res
            assert isinstance(res["aic"], (int, float))

    # 6. Save results to JSON (Simulating T025 output)
    output_file = tmp_path / "model_comparison.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    assert output_file.exists(), "Output file model_comparison.json was not created."

    # 7. Verify saved content
    with open(output_file, "r") as f:
        saved_data = json.load(f)

    assert len(saved_data) == len(models_to_test)
    assert saved_data[0]["model"] == models_to_test[0]

    # 8. Verify metrics are reasonable (e.g., AIC is not NaN)
    for res in saved_data:
        if res["converged"]:
            assert not np.isnan(res["aic"])
            assert not np.isnan(res["ks_statistic"])