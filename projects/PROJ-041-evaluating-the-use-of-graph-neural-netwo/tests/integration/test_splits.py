"""
Test skeleton for Temporal Holdout split (T020).
Verifies that the split logic in code/data/splits.py produces
Train/Test sets with no data leakage (strictly temporal separation).
Depends on T009 (Implementation of create_temporal_split).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data.splits import create_temporal_split


class TestTemporalHoldoutSplit:
    """Tests for T009 implementation: Temporal Holdout validation strategy."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, "data")
        self.output_path = os.path.join(self.temp_dir, "output")
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _generate_test_csv(self, filename: str, n_rows: int = 1000):
        """Generate a synthetic CSV with a 'timestamp' column for testing logic."""
        # Create a simple time series: 0 to n_rows-1
        timestamps = list(range(n_rows))
        # Add some dummy features
        data = {
            "timestamp": timestamps,
            "feature_1": np.random.rand(n_rows),
            "feature_2": np.random.rand(n_rows),
            "label": np.random.randint(0, 2, n_rows)
        }
        df = pd.DataFrame(data)
        filepath = os.path.join(self.data_path, filename)
        df.to_csv(filepath, index=False)
        return filepath

    def test_split_creates_files(self):
        """Verify that create_temporal_split creates the expected output files."""
        input_file = self._generate_test_csv("test_flows.csv", n_rows=1000)
        
        # Run the split function
        train_file, test_file = create_temporal_split(
            input_file,
            output_dir=self.output_path,
            split_ratio=0.8
        )
        
        assert os.path.exists(train_file), f"Train file not created: {train_file}"
        assert os.path.exists(test_file), f"Test file not created: {test_file}"
        assert train_file.endswith("train_split.csv")
        assert test_file.endswith("test_split.csv")

    def test_no_data_leakage_timestamp_order(self):
        """
        Verify that all timestamps in the test set are strictly greater than
        the maximum timestamp in the train set.
        """
        n_rows = 1000
        split_ratio = 0.8
        input_file = self._generate_test_csv("test_flows.csv", n_rows=n_rows)
        
        train_file, test_file = create_temporal_split(
            input_file,
            output_dir=self.output_path,
            split_ratio=split_ratio
        )
        
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        max_train_ts = train_df["timestamp"].max()
        min_test_ts = test_df["timestamp"].min()
        
        # Assert strict temporal separation
        assert min_test_ts > max_train_ts, (
            f"Data leakage detected! "
            f"Max train timestamp ({max_train_ts}) >= Min test timestamp ({min_test_ts}). "
            "Train set must contain strictly earlier data than test set."
        )

    def test_split_ratio_accuracy(self):
        """Verify that the split ratio is approximately correct."""
        n_rows = 1000
        split_ratio = 0.8
        input_file = self._generate_test_csv("test_flows.csv", n_rows=n_rows)
        
        train_file, test_file = create_temporal_split(
            input_file,
            output_dir=self.output_path,
            split_ratio=split_ratio
        )
        
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        actual_train_ratio = len(train_df) / n_rows
        
        # Allow a small margin for integer rounding
        assert abs(actual_train_ratio - split_ratio) < 0.02, (
            f"Split ratio mismatch. Expected ~{split_ratio}, got {actual_train_ratio}"
        )

    def test_no_duplicate_rows(self):
        """Verify that no row appears in both train and test sets."""
        n_rows = 500
        input_file = self._generate_test_csv("test_flows.csv", n_rows=n_rows)
        
        train_file, test_file = create_temporal_split(
            input_file,
            output_dir=self.output_path,
            split_ratio=0.8
        )
        
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        # Check for duplicates based on timestamp (primary key in this context)
        train_timestamps = set(train_df["timestamp"].tolist())
        test_timestamps = set(test_df["timestamp"].tolist())
        
        intersection = train_timestamps.intersection(test_timestamps)
        
        assert len(intersection) == 0, (
            f"Data leakage detected! {len(intersection)} timestamps found in both sets."
        )

    def test_handles_empty_input_gracefully(self):
        """Verify behavior if input file is empty or has < 2 rows."""
        # Create an empty file
        empty_file = os.path.join(self.data_path, "empty.csv")
        with open(empty_file, "w") as f:
            f.write("timestamp,feature_1,label\n") # Header only
        
        with pytest.raises((ValueError, IndexError)):
            create_temporal_split(
                empty_file,
                output_dir=self.output_path,
                split_ratio=0.8
            )