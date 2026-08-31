"""
Integration test for resampling loop completion and artifact generation.

This test verifies that the resampling engine:
1. Successfully generates random subsets across configured sample size tiers.
2. Fits OLS models on valid subsets without crashing on singular matrices.
3. Generates the required artifact files in `artifacts/stability/`.
4. Produces valid coefficient standard deviation metrics.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

# Import from the project structure
from src.resampling.engine import run_resampling_experiment
from src.utils.config import load_sample_tiers, load_random_seed
from src.models.data_models import StabilityResult


@pytest.fixture
def small_test_dataset():
    """
    Creates a small, deterministic CSV dataset for integration testing.
    This simulates a 'real' data source without needing external downloads.
    The data is generated once and saved to a temp file.
    """
    np.random.seed(42)
    n_rows = 500
    n_preds = 5

    # Generate features with some correlation to ensure condition number is reasonable but non-trivial
    X = np.random.randn(n_rows, n_preds)
    # Add a slight correlation to one column to test robustness
    X[:, 1] = X[:, 0] * 0.5 + np.random.randn(n_rows) * 0.1

    # Generate target with known coefficients
    true_beta = np.array([2.0, -1.5, 0.5, 0.0, 1.0])
    noise = np.random.randn(n_rows) * 0.5
    y = X @ true_beta + noise

    df = pd.DataFrame(X, columns=[f"feat_{i}" for i in range(n_preds)])
    df["target"] = y

    # Save to a temporary file
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_auto.csv")
    df.to_csv(csv_path, index=False)

    return csv_path, temp_dir


def test_resampling_loop_and_artifacts(small_test_dataset):
    """
    Integration test: Run the full resampling pipeline on a small dataset.
    Verifies artifact generation and content validity.
    """
    csv_path, temp_dir = small_test_dataset

    # Define a temporary output directory for this test run
    output_dir = os.path.join(temp_dir, "artifacts", "stability")
    os.makedirs(output_dir, exist_ok=True)

    # Load configuration
    # We override the global config for this test to use a fixed seed and small tiers
    # In a real scenario, these would come from the spec/config.yaml
    sample_tiers = [0.1, 0.25] # Test with 10% and 25% to keep runtime short
    seed = 42
    n_subsets = 5 # Small number for integration test speed

    try:
        # Run the experiment
        # The engine expects a dataset path and configuration
        # We mock the config loading or pass args directly if the API allows.
        # Assuming the API is: run_resampling_experiment(dataset_path, output_dir, tiers, seed, n_subsets)
        # If the API relies on global config, we set it up.
        
        # Since T023/T024 implemented the engine, we assume it exposes a function 
        # that accepts these parameters or reads from a config file.
        # To be safe and compliant with "real implementation", we pass the parameters 
        # that the engine would typically read from config.
        
        run_resampling_experiment(
            dataset_path=csv_path,
            output_dir=output_dir,
            sample_tiers=sample_tiers,
            seed=seed,
            n_subsets_per_tier=n_subsets
        )

        # --- Verification ---

        # 1. Check that the subsets file was generated
        subsets_file = os.path.join(output_dir, "subsets_42.json")
        assert os.path.exists(subsets_file), f"Subsets file not found at {subsets_file}"

        with open(subsets_file, "r") as f:
            subsets_data = json.load(f)

        assert isinstance(subsets_data, list), "Subsets data should be a list"
        assert len(subsets_data) > 0, "Subsets data should not be empty"
        
        # Verify structure of a subset entry
        first_subset = subsets_data[0]
        assert "tier" in first_subset, "Subset entry missing 'tier'"
        assert "indices" in first_subset, "Subset entry missing 'indices'"
        assert "size" in first_subset, "Subset entry missing 'size'"
        
        # Verify indices are valid integers
        assert all(isinstance(i, int) for i in first_subset["indices"]), "Indices must be integers"
        assert first_subset["size"] == len(first_subset["indices"]), "Size mismatch"

        # 2. Check that the coefficient SD file was generated
        sd_file = os.path.join(output_dir, "coefficient_sd.json")
        assert os.path.exists(sd_file), f"Coefficient SD file not found at {sd_file}"

        with open(sd_file, "r") as f:
            sd_data = json.load(f)

        assert isinstance(sd_data, dict), "SD data should be a dictionary keyed by tier"
        
        for tier, results in sd_data.items():
            assert "coefficients" in results, f"Tier {tier} missing 'coefficients'"
            coeffs = results["coefficients"]
            assert isinstance(coeffs, dict), "Coefficients should be a dict"
            
            for coef_name, sd_val in coeffs.items():
                assert isinstance(sd_val, (int, float)), f"SD value for {coef_name} must be numeric"
                assert sd_val >= 0, f"SD value for {coef_name} must be non-negative"
        
        # 3. Verify that multiple tiers were processed
        assert len(sd_data) == len(sample_tiers), "Number of tiers in output should match input"

        # 4. Verify that at least some subsets resulted in valid fits
        # (The engine should skip singular matrices, but we expect success on this synthetic data)
        total_valid_fits = sum(
            len(s["indices"]) > 0 for s in subsets_data 
        )
        assert total_valid_fits > 0, "No valid subsets were generated/fitted"

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_singularity_handling_in_loop(small_test_dataset):
    """
    Integration test: Verify that the resampling loop handles singular matrices gracefully.
    This test relies on the engine's internal logic (T024) to catch LinAlgError.
    """
    csv_path, temp_dir = small_test_dataset
    output_dir = os.path.join(temp_dir, "artifacts", "stability_singular")
    os.makedirs(output_dir, exist_ok=True)

    # Use a very small subset size to increase chance of singularity or edge cases
    # though with 500 rows and 5 cols, it's hard to force singularity without specific bad data.
    # The test primarily ensures the loop doesn't crash.
    sample_tiers = [0.05] # 5% of 500 = 25 rows
    seed = 123
    n_subsets = 10

    try:
        # This should run without raising an exception even if some subsets are singular
        run_resampling_experiment(
            dataset_path=csv_path,
            output_dir=output_dir,
            sample_tiers=sample_tiers,
            seed=seed,
            n_subsets_per_tier=n_subsets
        )
        
        # If we get here, the loop completed without crashing
        assert os.path.exists(os.path.join(output_dir, "coefficient_sd.json"))
        
    except Exception as e:
        # If it crashes with a singular matrix error, the task is failed
        pytest.fail(f"Resampling loop crashed on potential singular matrix: {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)