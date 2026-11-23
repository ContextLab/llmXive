"""
tests/unit/test_splitter.py

Unit tests for the splitter module.
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from splitter import (
    load_processed_data,
    stratified_split,
    save_split_data,
    validate_split,
    VALIDATION_MIN_SIZE,
    SPLIT_RATIOS
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with trajectory data."""
    np.random.seed(42)
    n_trajectories = 100
    n_turns = 10

    data = []
    for traj_id in range(n_trajectories):
        for turn in range(n_turns):
            data.append({
                'trajectory_id': f'traj_{traj_id:03d}',
                'turn_number': turn,
                'health': np.random.randint(1, 100),
                'threat': np.random.randint(1, 50),
                'deck_size': np.random.randint(5, 20),
                'legal_moves_entropy': np.random.uniform(0, 5)
            })

    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_csv_file(sample_dataframe, temp_dir):
    """Create a sample CSV file for testing."""
    csv_path = os.path.join(temp_dir, 'test_input.csv')
    sample_dataframe.to_csv(csv_path, index=False)
    return csv_path

class TestLoadProcessedData:
    def test_load_existing_csv(self, sample_csv_file, sample_dataframe):
        """Test loading an existing CSV file."""
        df = load_processed_data(sample_csv_file)
        assert len(df) == len(sample_dataframe)
        assert 'trajectory_id' in df.columns
        assert 'legal_moves_entropy' in df.columns

    def test_missing_file_raises_error(self, temp_dir):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(os.path.join(temp_dir, 'nonexistent.csv'))

    def test_missing_columns_raises_error(self, temp_dir):
        """Test that missing required columns raises ValueError."""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        csv_path = os.path.join(temp_dir, 'bad.csv')
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError) as exc_info:
            load_processed_data(csv_path)
        assert "Missing required columns" in str(exc_info.value)

class TestStratifiedSplit:
    def test_split_produces_all_sets(self, sample_dataframe):
        """Test that split produces all four required sets."""
        splits = stratified_split(sample_dataframe)
        assert 'train' in splits
        assert 'ablation_train' in splits
        assert 'validation' in splits
        assert 'test' in splits

    def test_no_overlap_between_splits(self, sample_dataframe):
        """Test that there is no overlap between trajectory IDs in different splits."""
        splits = stratified_split(sample_dataframe)

        all_ids = {name: set(df['trajectory_id'].unique()) for name, df in splits.items()}

        for i, name1 in enumerate(all_ids):
            for name2 in list(all_ids.keys())[i+1:]:
                overlap = all_ids[name1].intersection(all_ids[name2])
                assert len(overlap) == 0, f"Overlap between {name1} and {name2}"

    def test_validation_minimum_size(self, sample_dataframe):
        """Test that validation set meets minimum size requirement."""
        splits = stratified_split(sample_dataframe)
        val_size = len(splits['validation']['trajectory_id'].unique())
        assert val_size >= VALIDATION_MIN_SIZE

    def test_total_coverage(self, sample_dataframe):
        """Test that all trajectories are included in exactly one split."""
        splits = stratified_split(sample_dataframe)

        all_ids = set(sample_dataframe['trajectory_id'].unique())
        split_ids = set()
        for df in splits.values():
            split_ids.update(df['trajectory_id'].unique())

        assert all_ids == split_ids

    def test_deterministic_with_seed(self, sample_dataframe):
        """Test that split is deterministic with fixed seed."""
        splits1 = stratified_split(sample_dataframe, seed=42)
        splits2 = stratified_split(sample_dataframe, seed=42)

        for key in splits1:
            ids1 = set(splits1[key]['trajectory_id'].unique())
            ids2 = set(splits2[key]['trajectory_id'].unique())
            assert ids1 == ids2

    def test_insufficient_data_for_min_validation(self):
        """Test error when data is too small for minimum validation."""
        small_df = pd.DataFrame({
            'trajectory_id': [f'traj_{i}' for i in range(10)],
            'turn_number': [0] * 10,
            'health': [50] * 10,
            'threat': [25] * 10,
            'deck_size': [10] * 10,
            'legal_moves_entropy': [1.0] * 10
        })

        # This should raise ValueError because we can't satisfy min validation size
        with pytest.raises(ValueError) as exc_info:
            stratified_split(small_df)
        assert "Cannot satisfy minimum validation size" in str(exc_info.value)

class TestSaveSplitData:
    def test_saves_all_csv_files(self, sample_dataframe, temp_dir):
        """Test that all CSV files are saved."""
        splits = stratified_split(sample_dataframe)
        file_paths = save_split_data(splits, temp_dir)

        assert 'train' in file_paths
        assert 'ablation_train' in file_paths
        assert 'validation' in file_paths
        assert 'test' in file_paths

        for name, path in file_paths.items():
            assert os.path.exists(path)

    def test_saves_validation_ids_json(self, sample_dataframe, temp_dir):
        """Test that validation_set_ids.json is created."""
        splits = stratified_split(sample_dataframe)
        file_paths = save_split_data(splits, temp_dir)

        assert 'validation_ids' in file_paths
        assert file_paths['validation_ids'].endswith('validation_set_ids.json')

        with open(file_paths['validation_ids'], 'r') as f:
            ids = json.load(f)

        assert isinstance(ids, list)
        assert len(ids) > 0

    def test_csv_content_matches_split(self, sample_dataframe, temp_dir):
        """Test that saved CSV content matches the split data."""
        splits = stratified_split(sample_dataframe)
        file_paths = save_split_data(splits, temp_dir)

        for split_name, path in file_paths.items():
            if split_name != 'validation_ids':
                saved_df = pd.read_csv(path)
                original_df = splits[split_name]

                assert len(saved_df) == len(original_df)
                assert set(saved_df.columns) == set(original_df.columns)

class TestValidateSplit:
    def test_valid_split(self, sample_dataframe):
        """Test validation passes for a valid split."""
        splits = stratified_split(sample_dataframe)
        results = validate_split(splits)

        assert results['valid'] is True
        assert len(results['errors']) == 0

    def test_invalid_validation_size(self):
        """Test validation fails when validation set is too small."""
        # Create a split with insufficient validation
        splits = {
            'train': pd.DataFrame({'trajectory_id': [f't{i}' for i in range(50)]}),
            'ablation_train': pd.DataFrame({'trajectory_id': [f't{i}' for i in range(50, 70)]}),
            'validation': pd.DataFrame({'trajectory_id': [f't{i}' for i in range(70, 75)]}),
            'test': pd.DataFrame({'trajectory_id': [f't{i}' for i in range(75, 100)]})
        }

        results = validate_split(splits, min_validation_size=20)
        assert results['valid'] is False
        assert any("minimum required" in err for err in results['errors'])

    def test_overlap_detection(self):
        """Test that overlap between splits is detected."""
        splits = {
            'train': pd.DataFrame({'trajectory_id': ['t1', 't2', 't3']}),
            'ablation_train': pd.DataFrame({'trajectory_id': ['t3', 't4']}),
            'validation': pd.DataFrame({'trajectory_id': ['t5']}),
            'test': pd.DataFrame({'trajectory_id': ['t6']})
        }

        results = validate_split(splits)
        assert results['valid'] is False
        assert any("Overlap detected" in err for err in results['errors'])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])