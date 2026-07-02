"""
Tests for the data manifest loader.
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from code.data.manifest import ManifestLoader, load_manifest, get_manifest_source_type
from code.utils.exceptions import PipelineException


@pytest.fixture
def valid_manifest_content():
    """Return a valid manifest dictionary."""
    return {
        "version": "1.0",
        "source_type": "SIMULATED",
        "description": "Test manifest",
        "created_at": "2024-01-01T00:00:00Z",
        "datasets": [
            {
                "name": "test_snps",
                "path": "raw/test_snps.csv",
                "type": "SNP",
                "format": "csv",
                "description": "Test SNP data",
                "checksum": "abc123"
            }
        ]
    }


@pytest.fixture
def temp_manifest_file(valid_manifest_content):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False
    ) as f:
        yaml.dump(valid_manifest_content, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


class TestManifestLoader:
    """Tests for ManifestLoader class."""

    def test_load_valid_manifest(self, temp_manifest_file):
        """Test loading a valid manifest file."""
        loader = ManifestLoader(temp_manifest_file)
        data = loader.load()

        assert data["version"] == "1.0"
        assert data["source_type"] == "SIMULATED"
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["type"] == "SNP"

    def test_load_missing_file(self):
        """Test loading a non-existent file raises exception."""
        loader = ManifestLoader(Path("/nonexistent/path/manifest.yaml"))
        with pytest.raises(PipelineException) as exc_info:
            loader.load()
        assert exc_info.value.code == "MANIFEST_NOT_FOUND"

    def test_validate_missing_required_field(self, valid_manifest_content):
        """Test validation fails when required field is missing."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            del valid_manifest_content["version"]
            yaml.dump(valid_manifest_content, f)
            temp_path = Path(f.name)

        try:
            loader = ManifestLoader(temp_path)
            with pytest.raises(PipelineException) as exc_info:
                loader.load()
            assert exc_info.value.code == "MANIFEST_MISSING_FIELD"
        finally:
            os.unlink(temp_path)

    def test_get_source_type(self, temp_manifest_file):
        """Test getting source type from manifest."""
        loader = ManifestLoader(temp_manifest_file)
        source_type = loader.get_source_type()
        assert source_type == "SIMULATED"

    def test_get_datasets(self, temp_manifest_file):
        """Test getting datasets from manifest."""
        loader = ManifestLoader(temp_manifest_file)
        datasets = loader.get_datasets()
        assert len(datasets) == 1
        assert datasets[0]["name"] == "test_snps"

    def test_get_dataset_by_type(self, temp_manifest_file):
        """Test getting dataset by type."""
        loader = ManifestLoader(temp_manifest_file)
        dataset = loader.get_dataset_by_type("SNP")
        assert dataset is not None
        assert dataset["name"] == "test_snps"

        dataset_none = loader.get_dataset_by_type("METABOLITE")
        assert dataset_none is None

    def test_get_dataset_path(self, temp_manifest_file):
        """Test getting resolved dataset path."""
        loader = ManifestLoader(temp_manifest_file)
        path = loader.get_dataset_path("SNP")
        assert path is not None
        assert path.name == "test_snps.csv"
        assert path.parent.name == "raw"

class TestLoadManifestFunctions:
    """Tests for convenience functions."""

    def test_load_manifest(self, temp_manifest_file):
        """Test load_manifest function."""
        data = load_manifest(temp_manifest_file)
        assert data["version"] == "1.0"
        assert "datasets" in data

    def test_get_manifest_source_type(self, temp_manifest_file):
        """Test get_manifest_source_type function."""
        source_type = get_manifest_source_type(temp_manifest_file)
        assert source_type == "SIMULATED"