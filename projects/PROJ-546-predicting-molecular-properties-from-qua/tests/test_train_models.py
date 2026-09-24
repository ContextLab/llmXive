"""
Unit tests for code/train_models.py (T021).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from train_models import (
    load_data_semi,
    load_data_dft,
    load_locked_splits,
    train_and_evaluate_fold,
    train_models
)


class TestLoadLockedSplits:
    def test_load_valid_splits(self, tmp_path):
        splits_data = {
            "train_indices": [0, 1, 2],
            "test_indices": [3, 4],
            "random_state": 42
        }
        splits_path = tmp_path / "splits.json"
        with open(splits_path, 'w') as f:
            json.dump(splits_data, f)

        result = load_locked_splits(splits_path)
        assert result == splits_data
        assert result['random_state'] == 42

    def test_load_missing_keys(self, tmp_path):
        splits_data = {
            "train_indices": [0, 1],
            "random_state": 42
        }
        splits_path = tmp_path / "splits.json"
        with open(splits_path, 'w') as f:
            json.dump(splits_data, f)

        with pytest.raises(ValueError, match="missing required keys"):
            load_locked_splits(splits_path)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_locked_splits(tmp_path / "nonexistent.json")


class TestLoadData:
    def test_load_semi_valid(self, tmp_path):
        csv_content = """molecule_id,HOMO_energy,LUMO_energy,mayer_bond_order,experimental_barrier
        mol1,-5.0,-1.0,0.5,10.0
        mol2,-5.2,-1.1,0.6,11.0"""
        csv_path = tmp_path / "descriptors_semi.csv"
        with open(csv_path, 'w') as f:
            f.write(csv_content)

        ids, features, targets = load_data_semi(csv_path)
        assert len(ids) == 2
        assert ids[0] == "mol1"
        assert np.allclose(features[0], [-5.0, -1.0, 0.5])
        assert targets[0] == 10.0

    def test_load_semi_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_data_semi(tmp_path / "nonexistent.csv")

    def test_load_semi_bad_row(self, tmp_path):
        csv_content = """molecule_id,HOMO_energy,LUMO_energy,mayer_bond_order,experimental_barrier
        mol1,-5.0,-1.0,0.5,10.0
        mol2,bad,-1.1,0.6,11.0"""
        csv_path = tmp_path / "descriptors_semi.csv"
        with open(csv_path, 'w') as f:
            f.write(csv_content)

        # Should skip bad row but not crash
        ids, features, targets = load_data_semi(csv_path)
        assert len(ids) == 1


class TestTrainAndEvaluate:
    def test_train_rf(self):
        X_train = np.array([[1.0, 2.0], [3.0, 4.0]])
        y_train = np.array([10.0, 20.0])
        X_test = np.array([[2.0, 3.0]])
        y_test = np.array([15.0])

        model, mae = train_and_evaluate_fold(X_train, y_train, X_test, y_test, "Test", 42)
        assert model is not None
        assert mae >= 0.0
        assert hasattr(model, 'predict')


class TestTrainModelsIntegration:
    @patch('train_models.load_locked_splits')
    @patch('train_models.load_data_semi')
    @patch('train_models.load_data_dft')
    @patch('train_models.joblib.dump')
    def test_full_training_run(
        self, mock_dump, mock_load_dft, mock_load_semi, mock_load_splits, tmp_path
    ):
        # Setup mock data
        splits_data = {
            "train_indices": [0],
            "test_indices": [1],
            "random_state": 42
        }
        mock_load_splits.return_value = splits_data

        semi_ids = ["m1", "m2"]
        semi_features = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        semi_targets = [10.0, 20.0]
        mock_load_semi.return_value = (semi_ids, semi_features, semi_targets)

        dft_ids = ["m1", "m2"]
        dft_features = [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]
        dft_targets = [10.0, 20.0]
        mock_load_dft.return_value = (dft_ids, dft_features, dft_targets)

        # Mock selected_subset.json existence
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        subset_path = state_dir / "selected_subset.json"
        with open(subset_path, 'w') as f:
            json.dump({"molecule_ids": ["m1", "m2"]}, f)

        # Patch paths to use tmp_path
        with patch('train_models.STATE_DIR', state_dir), \
             patch('train_models.DATA_DIR', tmp_path), \
             patch('train_models.MODELS_DIR', tmp_path / "models"):

            result = train_models()

            assert 'mae_semi' in result
            assert 'mae_dft' in result
            assert mock_dump.call_count == 2