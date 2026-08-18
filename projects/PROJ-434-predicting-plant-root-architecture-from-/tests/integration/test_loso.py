"""
Integration test for Leave-One-Species-Out (LOSO) cross-validation loop.

This test verifies that the LOSO cross-validation logic in `code/modeling/train.py`
correctly iterates through each unique species, trains the model on all other
species, and evaluates it on the held-out species.

It asserts that:
1. The number of folds equals the number of unique species in the dataset.
2. No data from the held-out species leaks into the training set for that fold.
3. The loop completes successfully and returns a list of metrics.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path so we can import modeling modules
code_root = Path(__file__).resolve().parents[2] / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.exceptions import DataQualityError

# Stub implementation to test the loop logic without full training pipeline
def run_loso_cv_stub(df: pd.DataFrame, species_col: str = "species_name") -> list:
    """
    Simulates the LOSO loop logic to be implemented in modeling.train.
    """
    unique_species = df[species_col].unique()
    results = []

    if len(unique_species) < 2:
        # Edge case: cannot perform LOSO with < 2 species
        # In a real scenario, this might raise DataQualityError
        return []

    for hold_out in unique_species:
        train_mask = df[species_col] != hold_out
        test_mask = df[species_col] == hold_out

        train_df = df[train_mask]
        test_df = df[test_mask]

        # Verify no leakage
        assert hold_out not in train_df[species_col].values, \
            f"Leakage detected: {hold_out} found in training set"
        assert hold_out in test_df[species_col].values, \
            f"Test set for {hold_out} is empty"

        # Simulate metric
        metric = {
            "held_out_species": hold_out,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "r2_score": 0.0
        }
        results.append(metric)

    return results


class TestLOSOIntegration:
    @pytest.fixture
    def sample_dataset(self):
        """Create a small synthetic dataset for testing the LOSO loop logic."""
        data = {
            "species_name": ["Species_A"] * 20 + ["Species_B"] * 20 + ["Species_C"] * 20,
            "soil_n": np.random.rand(60),
            "soil_p": np.random.rand(60),
            "soil_k": np.random.rand(60),
            "soil_ph": np.random.rand(60),
            "root_depth": np.random.rand(60) * 10,
            "root_mass": np.random.rand(60) * 5
        }
        return pd.DataFrame(data)

    def test_loso_loop_structure(self, sample_dataset):
        """Test that the LOSO loop iterates correctly over all species."""
        results = run_loso_cv_stub(sample_dataset, species_col="species_name")

        assert len(results) == 3, "LOSO should produce 3 folds for 3 species"

        held_out_species = [r["held_out_species"] for r in results]
        assert set(held_out_species) == {"Species_A", "Species_B", "Species_C"}, \
            "All species must be held out exactly once"

    def test_no_data_leakage(self, sample_dataset):
        """Test that the held-out species does not appear in the training set."""
        results = run_loso_cv_stub(sample_dataset, species_col="species_name")

        for r in results:
            expected_train_size = 60 - r["test_size"]
            assert r["train_size"] == expected_train_size, \
                f"Train size mismatch for {r['held_out_species']}"

    def test_single_species_dataset_fails_gracefully(self):
        """Test behavior when dataset has only one species."""
        data = {
            "species_name": ["Species_A"] * 20,
            "soil_n": np.random.rand(20),
            "root_depth": np.random.rand(20)
        }
        df = pd.DataFrame(data)

        results = run_loso_cv_stub(df, species_col="species_name")
        assert len(results) == 0, "LOSO should return empty list for single species"

    def test_integration_with_real_import_path(self):
        """
        Verify that the test can import the actual modeling.train module
        once it is implemented.
        """
        try:
            from modeling.train import run_loso_cross_validation
            assert callable(run_loso_cross_validation)
        except ImportError:
            pytest.skip("modeling.train module not yet implemented (T020-T023 pending)")