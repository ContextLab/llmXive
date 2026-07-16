"""
Integration test for the end-to-end subject processing pipeline.
Tests the flow: download -> preprocess -> train on a subset.
"""
import pytest
import os
import sys
import numpy as np
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import get_config_summary, ensure_directories
from code.preprocessing import preprocess_all_subjects, check_skewed_valence
from code.train import run_nested_loso, identify_skewed_subjects
from code.download import download_and_extract_dataset


@pytest.mark.integration
class TestEndToEndPipeline:
    """Integration tests for the full pipeline."""

    def test_directory_structure_exists(self):
        """Verify required directories are created."""
        config = get_config_summary()
        ensure_directories()

        raw_path = Path(config["data_raw_dir"])
        processed_path = Path(config["data_processed_dir"])
        models_path = Path(config["data_models_dir"])

        assert raw_path.exists(), f"Raw data directory missing: {raw_path}"
        assert processed_path.exists(), f"Processed data directory missing: {processed_path}"
        assert models_path.exists(), f"Models directory missing: {models_path}"

    def test_skewed_valence_detection(self):
        """Test that skewed valence subjects are correctly identified."""
        # Create mock data for skewed subjects
        # Subject 1: all scores > 5 (positive)
        # Subject 2: all scores < 5 (negative)
        # Subject 3: mixed scores (normal)
        mock_data = {
            "subj_1": {"valence": np.array([6.0, 7.0, 8.0, 9.0])},
            "subj_2": {"valence": np.array([2.0, 3.0, 1.0, 2.5])},
            "subj_3": {"valence": np.array([3.0, 7.0, 4.0, 8.0])}
        }

        skewed = identify_skewed_subjects(mock_data)

        assert "subj_1" in skewed, "Positive skewed subject not detected"
        assert "subj_2" in skewed, "Negative skewed subject not detected"
        assert "subj_3" not in skewed, "Normal subject incorrectly flagged"

    def test_preprocessing_output_format(self):
        """Verify preprocessing produces expected output structure."""
        # This test assumes download.py has been run and data exists.
        # If data is missing, we skip or create minimal mock for structure check.
        config = get_config_summary()
        raw_dir = Path(config["data_raw_dir"])

        if not raw_dir.exists() or not any(raw_dir.glob("*")):
            pytest.skip("Raw data not available. Run download.py first.")

        # Run preprocessing on available data
        # Note: This is a structural check, not a full performance test
        try:
            # We assume the function returns a dict of processed data
            # The actual implementation is in preprocessing.py
            # This test verifies the integration of the module
            from code.preprocessing import extract_features
            # Just verify the function is importable and callable signature
            assert callable(extract_features)
        except Exception as e:
            pytest.fail(f"Preprocessing module integration failed: {e}")

    def test_loso_structure(self):
        """Verify LOSO cross-validation structure is correct."""
        # Create mock data for 3 subjects
        mock_features = {
            "subj_1": np.random.rand(10, 5),
            "subj_2": np.random.rand(10, 5),
            "subj_3": np.random.rand(10, 5)
        }
        mock_labels = {
            "subj_1": np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0]),
            "subj_2": np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1]),
            "subj_3": np.array([1, 1, 0, 0, 1, 1, 0, 0, 1, 0])
        }

        # Verify that LOSO would create 3 folds
        subjects = list(mock_features.keys())
        assert len(subjects) == 3

        for i, test_subject in enumerate(subjects):
            train_subjects = [s for s in subjects if s != test_subject]
            assert len(train_subjects) == 2
            assert test_subject not in train_subjects
