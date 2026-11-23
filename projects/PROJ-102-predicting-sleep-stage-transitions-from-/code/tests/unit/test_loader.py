"""
Unit tests for the EpochLoader module.

Tests data loading functionality, file validation, and iteration logic.
"""

import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.loader import EpochLoader, load_processed_data, create_dataloader_for_training


class TestEpochLoader:
    """Tests for the EpochLoader class."""

    @pytest.fixture
    def temp_parquet_files(self, tmp_path):
        """Create temporary Parquet files for testing."""
        # Create test directories
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Create sample epochs data
        epochs_data = pd.DataFrame({
            'subject_id': ['HL01', 'HL01', 'HL02', 'HL02'],
            'epoch_index': [0, 1, 0, 1],
            'stage': [1, 2, 1, 2],
            'timestamp': [0, 30, 0, 30],
            'is_transition': [False, False, False, False],
            'signal_data': [
                np.random.randn(3000),
                np.random.randn(3000),
                np.random.randn(3000),
                np.random.randn(3000)
            ]
        })
        epochs_path = processed_dir / "epochs.parquet"
        epochs_data.to_parquet(epochs_path)

        # Create sample transition windows data
        transition_data = pd.DataFrame({
            'subject_id': ['HL01', 'HL02'],
            'transition_stage_from': [1, 2],
            'transition_stage_to': [2, 1],
            'transition_timestamp': [30, 30],
            'window_index': [0, 0],
            'is_valid': [True, True],
            'signal_data': [
                np.random.randn(6000),
                np.random.randn(6000)
            ]
        })
        transition_path = processed_dir / "transition_windows.parquet"
        transition_data.to_parquet(transition_path)

        # Create sample pre-transition windows data
        pre_transition_data = pd.DataFrame({
            'subject_id': ['HL01', 'HL02'],
            'transition_stage_from': [1, 2],
            'transition_stage_to': [2, 1],
            'transition_timestamp': [30, 30],
            'window_index': [0, 0],
            'is_valid': [True, True],
            'signal_data': [
                np.random.randn(6000),
                np.random.randn(6000)
            ]
        })
        pre_transition_path = processed_dir / "pre_transition_windows.parquet"
        pre_transition_data.to_parquet(pre_transition_path)

        return {
            'epochs': epochs_path,
            'transition': transition_path,
            'pre_transition': pre_transition_path
        }

    def test_loader_initialization(self, temp_parquet_files):
        """Test that EpochLoader initializes correctly with valid files."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        assert loader.epochs_path == temp_parquet_files['epochs']
        assert loader.transition_windows_path == temp_parquet_files['transition']
        assert loader.pre_transition_path == temp_parquet_files['pre_transition']
        assert loader.streaming is False

    def test_loader_missing_files(self, tmp_path):
        """Test that EpochLoader raises error for missing files."""
        non_existent = tmp_path / "non_existent.parquet"

        with pytest.raises(FileNotFoundError):
            EpochLoader(
                epochs_path=non_existent,
                transition_windows_path=non_existent,
                pre_transition_path=non_existent
            )

    def test_load_epochs(self, temp_parquet_files):
        """Test loading epochs data."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        epochs_list = list(loader.load_epochs())
        assert len(epochs_list) == 1
        df = epochs_list[0]
        assert len(df) == 4
        assert 'subject_id' in df.columns
        assert 'stage' in df.columns

    def test_load_epochs_with_subject_filter(self, temp_parquet_files):
        """Test loading epochs with subject filtering."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            subject_ids=['HL01'],
            streaming=False
        )

        epochs_list = list(loader.load_epochs())
        assert len(epochs_list) == 1
        df = epochs_list[0]
        assert len(df) == 2
        assert all(df['subject_id'] == 'HL01')

    def test_load_transition_windows(self, temp_parquet_files):
        """Test loading transition windows."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        transition_list = list(loader.load_transition_windows('centered'))
        assert len(transition_list) == 1
        df = transition_list[0]
        assert len(df) == 2
        assert 'transition_stage_from' in df.columns
        assert 'transition_stage_to' in df.columns

    def test_load_pre_transition_windows(self, temp_parquet_files):
        """Test loading pre-transition windows."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        pre_transition_list = list(loader.load_transition_windows('pre'))
        assert len(pre_transition_list) == 1
        df = pre_transition_list[0]
        assert len(df) == 2

    def test_load_eog_signals_missing(self, temp_parquet_files, tmp_path):
        """Test loading EOG signals when file is missing."""
        eog_path = tmp_path / "eog.parquet"

        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            eog_path=eog_path,
            streaming=False
        )

        eog_df = loader.load_eog_signals()
        assert eog_df is None

    def test_load_eog_signals_present(self, temp_parquet_files, tmp_path):
        """Test loading EOG signals when file exists."""
        eog_data = pd.DataFrame({
            'subject_id': ['HL01'],
            'eog_signal': [np.random.randn(3000)]
        })
        eog_path = tmp_path / "eog.parquet"
        eog_data.to_parquet(eog_path)

        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            eog_path=eog_path,
            streaming=False
        )

        eog_df = loader.load_eog_signals()
        assert eog_df is not None
        assert len(eog_df) == 1

    def test_get_epoch_metadata(self, temp_parquet_files):
        """Test getting epoch metadata."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        metadata = loader.get_epoch_metadata()
        assert 'subject_id' in metadata.columns
        assert 'stage' in metadata.columns
        assert 'epoch_index' in metadata.columns

    def test_iterate_by_subject(self, temp_parquet_files):
        """Test iterating over data by subject."""
        loader = EpochLoader(
            epochs_path=temp_parquet_files['epochs'],
            transition_windows_path=temp_parquet_files['transition'],
            pre_transition_path=temp_parquet_files['pre_transition'],
            streaming=False
        )

        subjects = list(loader.iterate_by_subject('epochs'))
        assert len(subjects) == 2  # HL01 and HL02
        assert subjects[0][0] == 'HL01'
        assert subjects[1][0] == 'HL02'


class TestLoadProcessedData:
    """Tests for the load_processed_data convenience function."""

    @pytest.fixture
    def temp_data_files(self, tmp_path):
        """Create temporary data files."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Create minimal test data
        epochs = pd.DataFrame({
            'subject_id': ['HL01'],
            'stage': [1],
            'timestamp': [0],
            'epoch_index': [0],
            'is_transition': [False],
            'signal_data': [np.random.randn(3000)]
        })
        (processed_dir / "epochs.parquet").to_parquet(processed_dir / "epochs.parquet")

        transition = pd.DataFrame({
            'subject_id': ['HL01'],
            'transition_stage_from': [1],
            'transition_stage_to': [2],
            'transition_timestamp': [30],
            'window_index': [0],
            'is_valid': [True],
            'signal_data': [np.random.randn(6000)]
        })
        transition.to_parquet(processed_dir / "transition_windows.parquet")

        pre_transition = pd.DataFrame({
            'subject_id': ['HL01'],
            'transition_stage_from': [1],
            'transition_stage_to': [2],
            'transition_timestamp': [30],
            'window_index': [0],
            'is_valid': [True],
            'signal_data': [np.random.randn(6000)]
        })
        pre_transition.to_parquet(processed_dir / "pre_transition_windows.parquet")

        return {
            'epochs': processed_dir / "epochs.parquet",
            'transition': processed_dir / "transition_windows.parquet",
            'pre_transition': processed_dir / "pre_transition_windows.parquet"
        }

    def test_load_all_data(self, temp_data_files):
        """Test loading all processed data."""
        data = load_processed_data(
            epochs_path=temp_data_files['epochs'],
            transition_windows_path=temp_data_files['transition'],
            pre_transition_path=temp_data_files['pre_transition']
        )

        assert 'epochs' in data
        assert 'transition_windows' in data
        assert 'pre_transition_windows' in data
        assert len(data['epochs']) == 1
        assert len(data['transition_windows']) == 1
        assert len(data['pre_transition_windows']) == 1


class TestCreateDataloaderForTraining:
    """Tests for the create_dataloader_for_training function."""

    @pytest.fixture
    def temp_pre_transition_file(self, tmp_path):
        """Create a temporary pre-transition file."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        data = pd.DataFrame({
            'subject_id': ['HL01', 'HL01', 'HL01', 'HL02'],
            'transition_stage_from': [1, 2, 1, 2],
            'transition_stage_to': [2, 1, 2, 1],
            'transition_timestamp': [30, 30, 30, 30],
            'window_index': [0, 1, 0, 0],
            'is_valid': [True, True, True, True],
            'signal_data': [
                np.random.randn(6000),
                np.random.randn(6000),
                np.random.randn(6000),
                np.random.randn(6000)
            ]
        })
        path = processed_dir / "pre_transition_windows.parquet"
        data.to_parquet(path)
        return path

    def test_create_dataloader(self, temp_pre_transition_file):
        """Test creating a training dataloader."""
        batches = list(create_dataloader_for_training(
            pre_transition_path=temp_pre_transition_file,
            batch_size=2,
            shuffle=False
        ))

        assert len(batches) == 2  # 4 samples / batch_size 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2

    def test_create_dataloader_with_shuffling(self, temp_pre_transition_file):
        """Test dataloader with shuffling."""
        # Run multiple times to verify shuffling works
        batches1 = list(create_dataloader_for_training(
            pre_transition_path=temp_pre_transition_file,
            batch_size=2,
            shuffle=True
        ))
        batches2 = list(create_dataloader_for_training(
            pre_transition_path=temp_pre_transition_file,
            batch_size=2,
            shuffle=True
        ))

        # At least one order should be different (probabilistic)
        # We just verify it doesn't crash and produces batches
        assert len(batches1) == 2
        assert len(batches2) == 2