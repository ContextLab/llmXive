"""
Unit tests for src.utils.data_loader module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.data_loader import (
    compute_sha256,
    filter_test_split,
    load_mbpp_subset,
    record_artifact_hash,
    select_subset,
)


class TestDataLoader:
    def test_compute_sha256_deterministic(self):
        """Test that the checksum is deterministic for the same input."""
        data = [{"id": 1, "code": "print(1)"}, {"id": 2, "code": "print(2)"}]
        hash1 = compute_sha256(data)
        hash2 = compute_sha256(data)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_compute_sha256_different_data(self):
        """Test that different data produces different hashes."""
        data1 = [{"id": 1}]
        data2 = [{"id": 2}]
        assert compute_sha256(data1) != compute_sha256(data2)

    def test_filter_test_split_missing(self):
        """Test error when test split is missing."""
        mock_dataset = {"train": []}  # No 'test' key
        with pytest.raises(ValueError, match="The 'test' split is not available"):
            filter_test_split(mock_dataset)

    def test_filter_test_split_present(self):
        """Test successful filtering when test split exists."""
        mock_dataset = {"test": [{"id": 1}], "train": []}
        result = filter_test_split(mock_dataset)
        assert result == [{"id": 1}]

    def test_select_subset_reduces_count(self):
        """Test that select_subset returns the requested number of items."""
        data = [{"id": i} for i in range(100)]
        subset = select_subset(data, num_tasks=10, seed=42)
        assert len(subset) == 10

    def test_select_subset_returns_all_if_fewer(self):
        """Test that select_subset returns all items if dataset is smaller than requested."""
        data = [{"id": i} for i in range(5)]
        subset = select_subset(data, num_tasks=10, seed=42)
        assert len(subset) == 5

    def test_select_subset_deterministic(self):
        """Test that select_subset is deterministic with same seed."""
        data = [{"id": i} for i in range(100)]
        subset1 = select_subset(data, num_tasks=10, seed=123)
        subset2 = select_subset(data, num_tasks=10, seed=123)
        assert subset1 == subset2

    def test_record_artifact_hash_creates_file(self):
        """Test that record_artifact_hash creates the state file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            project_id = "TEST-001"
            record_artifact_hash(
                project_root=project_root,
                project_id=project_id,
                dataset_name="test_ds",
                hash_value="abc123",
                subset_size=10,
            )
            state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
            assert state_file.exists()

    @patch("src.utils.data_loader.load_dataset")
    def test_load_mbpp_subset_integration_mock(self, mock_load_dataset):
        """Test the full flow with mocked dataset loading."""
        # Mock the dataset structure
        mock_test_split = [{"id": i, "code": f"code_{i}"} for i in range(50)]
        mock_dataset = {"test": mock_test_split}
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            tasks = load_mbpp_subset(
                num_tasks=50,
                seed=42,
                project_root=project_root,
                project_id="TEST-002",
            )

            assert len(tasks) == 50
            assert tasks[0]["id"] == 0  # Deterministic selection

            # Verify state file was updated
            state_file = project_root / "state" / "projects" / "TEST-002.yaml"
            assert state_file.exists()
            
            # Verify content
            import yaml
            with open(state_file, "r") as f:
                content = yaml.safe_load(f)
            
            assert "artifact_hashes" in content
            assert "mbpp_test_subset" in content["artifact_hashes"]
            assert content["artifact_hashes"]["mbpp_test_subset"]["hash"] is not None
            assert content["artifact_hashes"]["mbpp_test_subset"]["size"] == 50
