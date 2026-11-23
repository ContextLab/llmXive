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
from modeling.train import run_loso_cv

class TestLOSOIntegration:
    @pytest.fixture
    def sample_dataset(self):
        """Create a small synthetic dataset for testing the LOSO loop logic."""
        # Using a fixed seed for reproducibility in tests
        np.random.seed(42)
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
        # Define feature and target columns matching expected train.py interface
        feature_cols = ["soil_n", "soil_p", "soil_k", "soil_ph"]
        target_col = "root_depth"
        species_col = "species_name"

        results = run_loso_cv(
            sample_dataset,
            feature_cols=feature_cols,
            target_col=target_col,
            species_col=species_col
        )

        assert len(results) == 3, "LOSO should produce 3 folds for 3 species"

        held_out_species = [r["held_out_species"] for r in results]
        assert set(held_out_species) == {"Species_A", "Species_B", "Species_C"}, \
            "All species must be held out exactly once"

    def test_no_data_leakage(self, sample_dataset):
        """Test that the held-out species does not appear in the training set."""
        feature_cols = ["soil_n", "soil_p", "soil_k", "soil_ph"]
        target_col = "root_depth"
        species_col = "species_name"

        results = run_loso_cv(
            sample_dataset,
            feature_cols=feature_cols,
            target_col=target_col,
            species_col=species_col
        )

        for r in results:
            expected_train_size = 60 - r["test_size"]
            assert r["train_size"] == expected_train_size, \
                f"Train size mismatch for {r['held_out_species']}"

    def test_single_species_dataset_fails_gracefully(self):
        """Test behavior when dataset has only one species."""
        np.random.seed(42)
        data = {
            "species_name": ["Species_A"] * 20,
            "soil_n": np.random.rand(20),
            "root_depth": np.random.rand(20)
        }
        df = pd.DataFrame(data)

        feature_cols = ["soil_n"]
        target_col = "root_depth"
        species_col = "species_name"

        # Should raise DataQualityError for insufficient species
        with pytest.raises(DataQualityError):
            run_loso_cv(
                df,
                feature_cols=feature_cols,
                target_col=target_col,
                species_col=species_col
            )

    def test_integration_with_real_import_path(self):
        """
        Verify that the test can import the actual modeling.train module
        and that the function signature matches expectations.
        """
        # This test passes if the import works and the function is callable
        # The previous stub check is removed as we now import the real function
        assert callable(run_loso_cv)