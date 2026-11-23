import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function under test
# Adjust import path based on project structure
from code.ingest import split_dataset, split_test_set
from code.seed import set_seed, get_seed

class TestSplitDataset:
    """Tests for T014: split_dataset function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "aggregated_clean.csv")
        self.output_norm = os.path.join(self.temp_dir, "normalized_only.csv")
        self.output_raw = os.path.join(self.temp_dir, "raw_only.csv")
        self.summary_file = os.path.join(self.temp_dir, "split_summary.json")

        # Create a mock dataset
        data = {
            'pulse_duration': [10, 20, 30, 40, 50],
            'power': [100, 200, 300, 400, 500],
            'wear_rate': [0.1, 0.2, 0.3, 0.4, 0.5],
            'normalization_method': ['normalized', 'normalized', 'raw', 'normalized', 'raw']
        }
        self.df = pd.DataFrame(data)
        self.df.to_csv(self.input_file, index=False)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_split_correctness(self):
        """Test that the dataset is split correctly based on normalization_method."""
        df_norm, df_raw, summary = split_dataset(
            self.input_file,
            self.output_norm,
            self.output_raw,
            self.summary_file
        )

        # Check counts
        assert summary['normalized_count'] == 3
        assert summary['raw_count'] == 2
        assert summary['total_count'] == 5

        # Check content
        assert all(df_norm['normalization_method'] == 'normalized')
        assert all(df_raw['normalization_method'] == 'raw')

    def test_files_written(self):
        """Test that output files are created."""
        split_dataset(
            self.input_file,
            self.output_norm,
            self.output_raw,
            self.summary_file
        )

        assert os.path.exists(self.output_norm)
        assert os.path.exists(self.output_raw)
        assert os.path.exists(self.summary_file)

    def test_missing_column_error(self):
        """Test that ValueError is raised if normalization_method is missing."""
        # Create a file without the required column
        bad_data = {'pulse_duration': [10, 20], 'power': [100, 200]}
        bad_df = pd.DataFrame(bad_data)
        bad_df.to_csv(self.input_file, index=False)

        with pytest.raises(ValueError, match="Required column 'normalization_method'"):
            split_dataset(
                self.input_file,
                self.output_norm,
                self.output_raw,
                self.summary_file
            )

class TestSplitTestSet:
    """Tests for T014b: split_test_set function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "normalized_only.csv")
        self.output_test = os.path.join(self.temp_dir, "test_split.csv")
        self.output_indices = os.path.join(self.temp_dir, "test_split_indices.npy")

        # Create a mock dataset with at least 20 rows for a meaningful split
        np.random.seed(42)
        n_rows = 50
        data = {
            'pulse_duration': np.random.randint(10, 100, n_rows),
            'power': np.random.randint(100, 500, n_rows),
            'wear_rate': np.random.rand(n_rows),
            'pattern_geometry': np.random.choice(['A', 'B', 'C'], n_rows)
        }
        self.df = pd.DataFrame(data)
        self.df.to_csv(self.input_file, index=False)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_held_out_indices(self):
        """
        Test that split_test_set generates a strictly held-out test split.
        Verifies that the output indices are distinct and the test split is valid.
        """
        set_seed(42)  # Ensure reproducibility
        
        df_test, indices = split_test_set(
            self.input_file,
            self.output_test,
            self.output_indices,
            test_ratio=0.2
        )

        # Verify files created
        assert os.path.exists(self.output_test)
        assert os.path.exists(self.output_indices)

        # Verify indices are a numpy array
        assert isinstance(indices, np.ndarray)
        
        # Verify indices are within range
        n_rows = len(self.df)
        assert np.all(indices >= 0)
        assert np.all(indices < n_rows)

        # Verify no duplicate indices
        assert len(indices) == len(np.unique(indices))

        # Verify test split size
        expected_test_size = int(n_rows * 0.2)
        # Allow for rounding differences if n_rows is small, but for 50 it should be exact
        assert len(indices) == expected_test_size

        # Verify the test CSV content matches the indices
        df_test_loaded = pd.read_csv(self.output_test)
        assert len(df_test_loaded) == len(indices)

        # Verify that the test data corresponds to the selected indices
        # (Check a few specific values to ensure correctness)
        for i, idx in enumerate(indices[:3]):
            assert df_test_loaded.iloc[i]['pulse_duration'] == self.df.iloc[idx]['pulse_duration']

    def test_deterministic_with_seed(self):
        """Test that the split is deterministic when the seed is fixed."""
        set_seed(123)
        _, indices_1 = split_test_set(
            self.input_file,
            self.output_test,
            self.output_indices,
            test_ratio=0.2
        )

        set_seed(123)
        _, indices_2 = split_test_set(
            self.input_file,
            self.output_test,
            self.output_indices,
            test_ratio=0.2
        )

        np.testing.assert_array_equal(indices_1, indices_2)

    def test_invalid_ratio(self):
        """Test that ValueError is raised for invalid test_ratio."""
        with pytest.raises(ValueError, match="test_ratio must be between 0 and 1"):
            split_test_set(
                self.input_file,
                self.output_test,
                self.output_indices,
                test_ratio=1.5
            )

    def test_small_dataset_error(self):
        """Test that ValueError is raised for datasets too small to split."""
        # Create a very small dataset
        small_data = {'pulse_duration': [10, 20], 'power': [100, 200]}
        small_df = pd.DataFrame(small_data)
        small_file = os.path.join(self.temp_dir, "small.csv")
        small_df.to_csv(small_file, index=False)

        with pytest.raises(ValueError, match="Dataset too small"):
            split_test_set(
                small_file,
                self.output_test,
                self.output_indices,
                test_ratio=0.5
            )
