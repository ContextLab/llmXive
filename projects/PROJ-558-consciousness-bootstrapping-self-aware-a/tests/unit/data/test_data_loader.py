"""
Unit tests for the data_loader module.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# We cannot easily test the full download in a unit test due to network/size,
# so we test the helper functions and logic.
# We mock the dataset loading.

from code import data_loader


class MockDatasetItem:
    def __init__(self, text):
        self.text = text

    def __getitem__(self, key):
        return self.text if key == "text" else None


class MockDataset:
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


def test_concatenate_and_truncate():
    """
    Test the concatenation and truncation logic.
    """
    items = [
        MockDatasetItem("Hello "),
        MockDatasetItem("World "),
        MockDatasetItem("!")
    ]
    dataset = MockDataset(items)

    # Test no truncation
    result = data_loader.concatenate_and_truncate(dataset, 100)
    assert result == "Hello World !"
    assert len(result) == 13

    # Test truncation
    result = data_loader.concatenate_and_truncate(dataset, 10)
    assert result == "Hello Wo"
    assert len(result) == 10


def test_compute_checksum():
    """
    Test the checksum computation.
    """
    data = "test string"
    checksum = data_loader.compute_checksum(data)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)


def test_save_dataset_and_manifest():
    """
    Test saving data and updating manifest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.json")
        manifest_path = os.path.join(tmpdir, "manifest.json")

        data_loader.save_dataset_and_manifest(
            "Sample data",
            output_path,
            manifest_path
        )

        # Check file existence
        assert os.path.exists(output_path)
        assert os.path.exists(manifest_path)

        # Check content
        with open(output_path, "r") as f:
            content = json.load(f)
            assert content["content"] == "Sample data"

        # Check manifest
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            assert "pile_arxiv_truncated" in manifest
            assert manifest["pile_arxiv_truncated"]["checksum"] == data_loader.compute_checksum("Sample data")