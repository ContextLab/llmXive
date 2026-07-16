"""Integration tests for data loading and validation."""

import os
import pytest

from download import (
    download_and_extract_dataset,
    extract_channels,
    validate_checksums,
    get_file_hash,
)
from config import (
    DATA_RAW_PATH,
    DATASET_URL,
    DATASET_CHECKSUMS,
)


class TestDataLoading:
    """Integration tests for dataset download and extraction."""

    def test_file_hash_generation(self):
        """Test that file hash generation works on existing files."""
        # If raw data exists, test hash generation
        if os.path.exists(DATA_RAW_PATH):
            files = [f for f in os.listdir(DATA_RAW_PATH) if f.endswith('.tar.gz')]
            if files:
                test_file = os.path.join(DATA_RAW_PATH, files[0])
                hash_val = get_file_hash(test_file)
                assert len(hash_val) == 64  # SHA256 hex length

    def test_extract_channels_logic(self):
        """Test channel extraction logic."""
        # This test verifies the logic of channel extraction
        # It assumes the data structure is as expected from the DEAP dataset

        # Mock data: simulate raw EMG channels
        # In a real test, this would be the actual data from the dataset
        mock_data = {
            "chan0": [1.0, 2.0, 3.0],
            "chan1": [4.0, 5.0, 6.0],
            "chan2": [7.0, 8.0, 9.0],
            "chan3": [10.0, 11.0, 12.0],
        }

        # Expected channels based on config (corrugator, zygomaticus, orbicularis)
        # Map mock channels to expected names
        channel_map = {
            "chan0": "corrugator",
            "chan1": "zygomaticus",
            "chan2": "orbicularis",
        }

        extracted = extract_channels(mock_data, channel_map)

        assert "corrugator" in extracted
        assert "zygomaticus" in extracted
        assert "orbicularis" in extracted
        assert len(extracted["corrugator"]) == 3
