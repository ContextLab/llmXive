import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import yaml
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.verify_dataset import verify_dataset, compute_sha256, LocalMetadataManager

class TestVerifyDatasetLogic:
    @pytest.fixture
    def temp_parquet(self, tmp_path):
        """Create a temporary parquet file with dummy data."""
        file_path = tmp_path / "test_data.parquet"
        df = pd.DataFrame({
            "col1": range(50000),
            "col2": ["data"] * 50000
        })
        df.to_parquet(file_path)
        return file_path

    @pytest.fixture
    def small_parquet(self, tmp_path):
        """Create a temporary parquet file with too few rows."""
        file_path = tmp_path / "small_data.parquet"
        df = pd.DataFrame({
            "col1": range(100),
            "col2": ["data"] * 100
        })
        df.to_parquet(file_path)
        return file_path

    def test_compute_sha256(self, temp_parquet):
        """Test SHA256 computation."""
        checksum = compute_sha256(temp_parquet)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_verify_success(self, temp_parquet, tmp_path):
        """Test successful verification."""
        meta_path = tmp_path / "metadata.yaml"
        result = verify_dataset(
            file_path=temp_parquet,
            min_rows=45000,
            metadata_path=meta_path,
            dataset_name="test_dataset"
        )
        
        assert result["success"] is True
        assert result["row_count"] == 50000
        assert "sha256" in result
        assert meta_path.exists()

    def test_verify_fails_row_count(self, small_parquet, tmp_path):
        """Test verification fails when rows < min_rows."""
        meta_path = tmp_path / "metadata.yaml"
        result = verify_dataset(
            file_path=small_parquet,
            min_rows=45000,
            metadata_path=meta_path
        )
        
        assert result["success"] is False
        assert "Row count" in result.get("error", "")

    def test_verify_file_not_found(self, tmp_path):
        """Test verification fails for missing file."""
        result = verify_dataset(
            file_path=tmp_path / "nonexistent.parquet",
            min_rows=45000
        )
        
        assert result["success"] is False
        assert "File not found" in result.get("error", "")

    def test_metadata_update(self, temp_parquet, tmp_path):
        """Test that metadata.yaml is updated correctly."""
        meta_path = tmp_path / "metadata.yaml"
        verify_dataset(
            file_path=temp_parquet,
            metadata_path=meta_path,
            dataset_name="test_ds"
        )
        
        assert meta_path.exists()
        with open(meta_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "datasets" in data
        assert "test_ds" in data["datasets"]
        assert data["datasets"]["test_ds"]["row_count"] == 50000
        assert "sha256" in data["datasets"]["test_ds"]

    def test_local_metadata_manager(self, tmp_path):
        """Test LocalMetadataManager class directly."""
        meta_path = tmp_path / "test_meta.yaml"
        manager = LocalMetadataManager(meta_path)
        
        manager.update_dataset("ds1", {"key": "value"})
        
        assert meta_path.exists()
        with open(meta_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["datasets"]["ds1"]["key"] == "value"