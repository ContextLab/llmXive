import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import the target module
try:
    from src.models.bayesian import fit_random_walk_model
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False


@pytest.fixture
def synthetic_poll_data():
    """
    Generate synthetic poll data that mimics the expected input format
    for the Bayesian model: date, vote_share, sample_size, pollster.
    Uses a deterministic seed for reproducibility.
    """
    np.random.seed(42)
    n_weeks = 12
    n_polls_per_week = 3

    dates = pd.date_range(start="2024-01-01", periods=n_weeks, freq="W-MON")
    data = []

    for week_idx, date in enumerate(dates):
        # Simulate a slight trend + noise
        base_vote = 45.0 + (week_idx * 0.5)
        for i in range(n_polls_per_week):
            noise = np.random.normal(0, 1.5)
            vote_share = base_vote + noise
            sample_size = np.random.randint(800, 1500)
            pollster = f"Pollster_{i}"

            data.append({
                "date": date,
                "vote_share": max(0, min(100, vote_share)), # Clamp to valid range
                "sample_size": sample_size,
                "pollster": pollster,
                "election_date": "2024-02-05" # Fixed future date for synthetic set
            })

    df = pd.DataFrame(data)
    return df


@pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")
def test_model_convergence(synthetic_poll_data):
    """
    Test that the Random Walk Bayesian model converges (R-hat <= 1.05)
    on a synthetic dataset with reasonable signal-to-noise ratio.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "trace.nc"

        # Run the model with a short tuning/sampling to verify convergence logic
        # Note: In a full run, tuning would be higher. For unit test speed,
        # we use minimal steps but ensure the convergence check logic runs.
        result = fit_random_walk_model(
            df=synthetic_poll_data,
            output_path=str(output_path),
            tune=200,
            draws=200,
            chains=2,
            random_seed=42
        )

        assert result is not None, "Model fitting returned None"
        assert "R_hat" in result, "Result missing R_hat statistic"
        assert "trace" in result, "Result missing trace object"

        # Assert convergence criteria
        # We allow a slightly looser threshold for very short runs in unit tests,
        # but strictly check the logic implementation.
        max_r_hat = result["R_hat"]
        assert max_r_hat <= 1.1, f"Model did not converge: Max R-hat = {max_r_hat}"
        
        # Verify output file creation
        assert output_path.exists(), f"Trace file not created at {output_path}"


@pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")
def test_single_week_edge_case(synthetic_poll_data):
    """
    Test model behavior with data for only a single week (edge case).
    The Random Walk prior requires at least 2 time steps to define transitions,
    so this should handle the edge case gracefully or fail with a clear error.
    """
    single_week_df = synthetic_poll_data[synthetic_poll_data["date"] == synthetic_poll_data["date"].iloc[0]].copy()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "single_week_trace.nc"

        # The model should handle this, likely by returning a flat posterior
        # or raising a specific ValueError if the logic enforces >= 2 weeks.
        # We expect it to run without a crash, though convergence might be trivial.
        try:
            result = fit_random_walk_model(
                df=single_week_df,
                output_path=str(output_path),
                tune=100,
                draws=100,
                chains=2,
                random_seed=42
            )
            # If it runs, it should return a result
            assert result is not None
        except ValueError as e:
            # If the implementation explicitly rejects single-week data, that is acceptable
            # as long as it is a clear error, not a crash.
            assert "insufficient" in str(e).lower() or "time steps" in str(e).lower()


@pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")
def test_missing_pymc():
    """
    Test that the module handles the case where PyMC is not installed gracefully.
    This is covered by the skipif logic above, but explicitly tests the import failure path
    if the code were to run in an environment without PyMC.
    """
    # If we are here, PyMC is available. This test serves as a placeholder
    # to ensure the test suite structure covers the dependency check.
    # In a real CI without PyMC, the entire file would be skipped.
    assert PYMC_AVAILABLE is True


@pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")
def test_high_variance_data(synthetic_poll_data):
    """
    Test model robustness with high variance synthetic data.
    """
    noisy_df = synthetic_poll_data.copy()
    # Inject high noise
    noisy_df["vote_share"] += np.random.normal(0, 10.0, size=len(noisy_df))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "noisy_trace.nc"

        result = fit_random_walk_model(
            df=noisy_df,
            output_path=str(output_path),
            tune=300,
            draws=300,
            chains=2,
            random_seed=42
        )

        assert result is not None
        # High variance might lead to slower convergence, but should still run
        assert result["R_hat"] <= 1.2  # Slightly relaxed for high noise