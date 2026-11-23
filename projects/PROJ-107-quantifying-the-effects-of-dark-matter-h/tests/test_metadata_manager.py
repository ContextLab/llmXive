import pytest
import os
import tempfile
import shutil
from pathlib import Path
import yaml
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.metadata_manager import (
    calculate_sha256,
    load_metadata,
    save_metadata,
    update_dataset_metadata,
    update_gap_status,
    count_rows_csv,
    count_rows_json
)
from utils.config import get_project_root

class TestMetadataManager:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary project structure for testing."""
        self.tmp_dir = tmp_path
        self.project_root = self.tmp_dir / "project"
        self.project_root.mkdir()
        
        # Create required directories
        (self.project_root / "data").mkdir()
        (self.project_root / "data" / "processed").mkdir()
        (self.project_root / "code").mkdir()
        
        # Create a temporary metadata file
        self.metadata_path = self.project_root / "data" / "metadata.yaml"
        initial_metadata = {
            "version": "1.0",
            "last_updated": "2023-10-27T12:00:00Z",
            "project": "PROJ-107-test",
            "pipeline_version": "1.0.0",
            "datasets": {
                "test_dataset": {
                    "associational_only": True,
                    "path": "data/processed/test.csv",
                    "checksum": None,
                    "row_count": None,
                    "status": "pending",
                    "description": "Test dataset"
                }
            },
            "flags": {},
            "gaps": {},
            "checksums": {"algorithm": "sha256", "files": []},
            "sampling_protocol": {}
        }
        
        with open(self.metadata_path, 'w') as f:
            yaml.dump(initial_metadata, f)
        
        # Mock the config functions to use our temp directory
        import utils.config
        import utils.metadata_manager
        
        self.original_get_project_root = utils.config.get_project_root
        utils.config.get_project_root = lambda: self.project_root
        utils.metadata_manager.get_project_root = lambda: self.project_root
        
        yield self.project_root
        
        # Restore original function
        utils.config.get_project_root = self.original_get_project_root
        utils.metadata_manager.get_project_root = self.original_get_project_root

    def test_load_metadata(self):
        """Test loading metadata from file."""
        metadata = load_metadata()
        assert metadata is not None
        assert metadata["version"] == "1.0"
        assert metadata["project"] == "PROJ-107-test"

    def test_update_dataset_metadata(self):
        """Test updating a dataset entry."""
        update_dataset_metadata(
            dataset_key="test_dataset",
            path="data/processed/test.csv",
            status="completed",
            description="Updated description"
        )
        
        metadata = load_metadata()
        assert metadata["datasets"]["test_dataset"]["status"] == "completed"
        assert metadata["datasets"]["test_dataset"]["description"] == "Updated description"

    def test_update_gap_status(self):
        """Test updating a gap entry."""
        update_gap_status("test_gap", "failed", "Test reason", "Not Measurable")
        
        metadata = load_metadata()
        assert "gaps" in metadata
        assert "test_gap" in metadata["gaps"]
        assert metadata["gaps"]["test_gap"]["status"] == "failed"
        assert metadata["gaps"]["test_gap"]["reason"] == "Test reason"
        assert metadata["gaps"]["test_gap"]["sc_004_status"] == "Not Measurable"

    def test_count_rows_csv(self):
        """Test counting rows in a CSV file."""
        csv_path = self.project_root / "data" / "processed" / "test.csv"
        
        with open(csv_path, 'w') as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            f.write("val3,val4\n")
        
        count = count_rows_csv(str(csv_path))
        assert count == 2

    def test_count_rows_json(self):
        """Test counting rows in a JSON file."""
        json_path = self.project_root / "data" / "processed" / "test.json"
        
        with open(json_path, 'w') as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
        
        count = count_rows_json(str(json_path))
        assert count == 3

    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        file_path = self.project_root / "data" / "processed" / "test.txt"
        
        with open(file_path, 'w') as f:
            f.write("test content")
        
        checksum = calculate_sha256(str(file_path))
        assert len(checksum) == 64
        assert isinstance(checksum, str)

    def test_save_metadata(self):
        """Test saving metadata to file."""
        metadata = load_metadata()
        metadata["test_key"] = "test_value"
        
        save_metadata(metadata)
        
        # Reload and verify
        reloaded = load_metadata()
        assert reloaded["test_key"] == "test_value"
