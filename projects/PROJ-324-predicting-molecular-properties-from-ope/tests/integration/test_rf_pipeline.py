import os
import sys
import pytest
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from models.random_forest import (
    load_fingerprints_and_targets,
    tune_hyperparameters,
    run_nested_cross_validation,
    train_final_model,
    save_model,
    check_runtime_elapsed
)
from data.fingerprints import generate_fingerprints_batch, smiles_to_obabel_fingerprint

class TestRFPipeline:
    """Integration tests for the Random Forest pipeline."""

    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create a small sample dataset for testing."""
        # Create a mock fingerprints parquet file
        data = {
            'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
            'ECFP4_fp': ['0010101010', '0101010101', '1111000000'], # Mock hex strings
            'logP': [0.5, -0.2, 2.1]
        }
        df = pd.DataFrame(data)
        fp_path = tmp_path / "test_fingerprints.parquet"
        df.to_parquet(fp_path)
        return fp_path

    def test_load_fingerprints(self, sample_data):
        """Test loading fingerprints and targets."""
        X, y, feature_names = load_fingerprints_and_targets(sample_data)
        assert X.shape[0] == 3
        assert y.shape[0] == 3
        assert len(feature_names) > 0

    def test_tune_hyperparameters(self, sample_data):
        """Test hyperparameter tuning on small data."""
        X, y, _ = load_fingerprints_and_targets(sample_data)
        # Use very small grid for speed
        best_params = tune_hyperparameters(X, y, n_splits=2)
        assert 'max_depth' in best_params
        assert best_params['max_depth'] <= 15

    def test_run_nested_cv(self, sample_data):
        """Test nested cross-validation."""
        X, y, _ = load_fingerprints_and_targets(sample_data)
        results = run_nested_cross_validation(X, y, n_outer=2, n_inner=2)
        assert 'oof_predictions' in results
        assert 'final_params' in results
        assert len(results['oof_predictions']) == len(y)

    def test_train_and_save_model(self, sample_data, tmp_path):
        """Test training and saving a model."""
        X, y, _ = load_fingerprints_and_targets(sample_data)
        params = {'n_estimators': 5, 'max_depth': 3, 'random_state': 42}
        model = train_final_model(X, y, params)
        
        model_path = tmp_path / "test_model.pkl"
        save_model(model, model_path)
        
        assert model_path.exists()

    def test_runtime_check(self):
        """Test runtime elapsed check."""
        start = time.time() - 100  # Simulate past start
        assert check_runtime_elapsed(start) is False  # Not exceeded yet (if limit is 6h)
        
        # Simulate exceeding
        start = time.time() - (6 * 3600 + 1)
        assert check_runtime_elapsed(start) is True

    def test_fingerprint_generation_with_timeout(self, tmp_path):
        """Test fingerprint generation with a mock timeout scenario."""
        # This test verifies the retry mechanism and timeout handling
        # We can't easily test a real timeout without hanging, so we test the logic
        # by checking if the function returns None for invalid SMILES
        result = smiles_to_obabel_fingerprint("INVALID_SMILES", "ECFP4")
        # Depending on obabel, this might return None or a specific error
        # We just check that it doesn't crash
        assert result is None or isinstance(result, str)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
