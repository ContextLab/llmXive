"""
Tests for the data_loader module.

These tests verify that the LocalArchiveLoader correctly loads data from
local archives and fails appropriately when data is missing or corrupted.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from PIL import Image

from src.lib.data_loader import (
    LocalArchiveLoader,
    DataLoaderError,
    load_from_local_archive,
    load_stimuli_manifest,
    verify_stimuli_archive,
)
from src.lib.utils import compute_file_checksum


@pytest.fixture
def temp_archive_environment():
    """Create a temporary archive environment for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir)
        
        # Create test files
        csv_file = archive_root / "test_data.csv"
        csv_data = "id,name,value\n1,test1,100\n2,test2,200\n"
        csv_file.write_text(csv_data)
        
        json_file = archive_root / "test_data.json"
        json_data = {"key1": "value1", "key2": 123}
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        # Create a test image
        img_file = archive_root / "test_image.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_file)
        
        # Create manifest with checksums
        manifest = {
            "version": "1.0",
            "checksums": {
                "test_data.csv": compute_file_checksum(csv_file),
                "test_data.json": compute_file_checksum(json_file),
                "test_image.png": compute_file_checksum(img_file),
            }
        }
        manifest_file = archive_root / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        yield archive_root

@pytest.fixture
def temp_csv_environment():
    """Create a temporary environment with just a CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir)
        
        csv_file = archive_root / "data.csv"
        csv_data = "a,b,c\n1,2,3\n4,5,6\n"
        csv_file.write_text(csv_data)
        
        yield archive_root

@pytest.fixture
def temp_json_environment():
    """Create a temporary environment with just a JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir)
        
        json_file = archive_root / "config.json"
        json_data = {"setting1": True, "setting2": 42}
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        yield archive_root

class TestLocalLoadSuccess:
    """Tests for successful loading from local archives."""
    
    def test_loader_initialization(self, temp_archive_environment):
        """Test that the loader initializes correctly."""
        loader = LocalArchiveLoader(temp_archive_environment)
        assert loader.archive_root == temp_archive_environment
    
    def test_loader_fails_on_missing_root(self):
        """Test that loader raises error on missing archive root."""
        with pytest.raises(DataLoaderError):
            LocalArchiveLoader("/nonexistent/path")
    
    def test_load_manifest_success(self, temp_archive_environment):
        """Test successful manifest loading."""
        loader = LocalArchiveLoader(temp_archive_environment)
        manifest = loader.load_manifest()
        
        assert "version" in manifest
        assert "checksums" in manifest
        assert "test_data.csv" in manifest["checksums"]
    
    def test_load_csv_success(self, temp_archive_environment):
        """Test successful CSV loading."""
        loader = LocalArchiveLoader(temp_archive_environment)
        df = loader.load_csv("test_data.csv", verify_checksum=False)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "value"]
        assert df.iloc[0]["name"] == "test1"
    
    def test_load_csv_with_checksum(self, temp_archive_environment):
        """Test CSV loading with checksum verification."""
        loader = LocalArchiveLoader(temp_archive_environment)
        manifest = loader.load_manifest()
        df = loader.load_csv("test_data.csv", verify_checksum=True, manifest=manifest)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
    
    def test_load_json_success(self, temp_archive_environment):
        """Test successful JSON loading."""
        loader = LocalArchiveLoader(temp_archive_environment)
        data = loader.load_json("test_data.json", verify_checksum=False)
        
        assert isinstance(data, dict)
        assert data["key1"] == "value1"
        assert data["key2"] == 123
    
    def test_load_json_with_checksum(self, temp_archive_environment):
        """Test JSON loading with checksum verification."""
        loader = LocalArchiveLoader(temp_archive_environment)
        manifest = loader.load_manifest()
        data = loader.load_json("test_data.json", verify_checksum=True, manifest=manifest)
        
        assert isinstance(data, dict)
        assert data["key1"] == "value1"
    
    def test_load_image_success(self, temp_archive_environment):
        """Test successful image loading."""
        loader = LocalArchiveLoader(temp_archive_environment)
        img = loader.load_image("test_image.png", verify_checksum=False)
        
        assert isinstance(img, Image.Image)
        assert img.size == (100, 100)
        assert img.mode == "RGB"
    
    def test_load_image_with_checksum(self, temp_archive_environment):
        """Test image loading with checksum verification."""
        loader = LocalArchiveLoader(temp_archive_environment)
        manifest = loader.load_manifest()
        img = loader.load_image("test_image.png", verify_checksum=True, manifest=manifest)
        
        assert isinstance(img, Image.Image)
        assert img.size == (100, 100)
    
    def test_list_files_success(self, temp_archive_environment):
        """Test listing files in archive."""
        loader = LocalArchiveLoader(temp_archive_environment)
        files = loader.list_files(".")
        
        assert len(files) == 4  # csv, json, png, manifest
        assert any("test_data.csv" in str(f) for f in files)
    
    def test_list_files_with_extension(self, temp_archive_environment):
        """Test listing files with extension filter."""
        loader = LocalArchiveLoader(temp_archive_environment)
        files = loader.list_files(".", extension=".csv")
        
        assert len(files) == 1
        assert "test_data.csv" in str(files[0])
    
    def test_load_from_local_archive_csv(self, temp_archive_environment):
        """Test the convenience function for CSV loading."""
        df = load_from_local_archive(
            temp_archive_environment,
            "csv",
            "test_data.csv",
            verify_checksum=False
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
    
    def test_load_from_local_archive_json(self, temp_archive_environment):
        """Test the convenience function for JSON loading."""
        data = load_from_local_archive(
            temp_archive_environment,
            "json",
            "test_data.json",
            verify_checksum=False
        )
        
        assert isinstance(data, dict)
        assert data["key1"] == "value1"
    
    def test_load_from_local_archive_image(self, temp_archive_environment):
        """Test the convenience function for image loading."""
        img = load_from_local_archive(
            temp_archive_environment,
            "image",
            "test_image.png",
            verify_checksum=False
        )
        
        assert isinstance(img, Image.Image)
    
    def test_load_stimuli_manifest(self, temp_archive_environment):
        """Test loading stimuli manifest."""
        manifest = load_stimuli_manifest(temp_archive_environment)
        
        assert "checksums" in manifest
        assert "test_data.csv" in manifest["checksums"]
    
    def test_verify_stimuli_archive(self, temp_archive_environment):
        """Test verifying archive checksums."""
        results = verify_stimuli_archive(temp_archive_environment)
        
        assert len(results) == 3  # csv, json, png (not manifest)
        for file_path, is_valid in results:
            assert is_valid, f"Checksum verification failed for {file_path}"

class TestLocalLoadFailure:
    """Tests for failure cases in local archive loading."""
    
    def test_load_csv_missing_file(self, temp_archive_environment):
        """Test error when CSV file is missing."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        with pytest.raises(DataLoaderError, match="CSV file not found"):
            loader.load_csv("nonexistent.csv")
    
    def test_load_json_missing_file(self, temp_archive_environment):
        """Test error when JSON file is missing."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        with pytest.raises(DataLoaderError, match="JSON file not found"):
            loader.load_json("nonexistent.json")
    
    def test_load_image_missing_file(self, temp_archive_environment):
        """Test error when image file is missing."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        with pytest.raises(DataLoaderError, match="Image file not found"):
            loader.load_image("nonexistent.png")
    
    def test_load_csv_checksum_mismatch(self, temp_archive_environment):
        """Test error when CSV checksum doesn't match."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        # Corrupt the CSV file
        csv_file = temp_archive_environment / "test_data.csv"
        csv_file.write_text("corrupted,data\n")
        
        manifest = loader.load_manifest()
        
        with pytest.raises(DataLoaderError, match="Checksum mismatch"):
            loader.load_csv("test_data.csv", verify_checksum=True, manifest=manifest)
    
    def test_load_json_checksum_mismatch(self, temp_archive_environment):
        """Test error when JSON checksum doesn't match."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        # Corrupt the JSON file
        json_file = temp_archive_environment / "test_data.json"
        json_file.write_text('{"corrupted": true}')
        
        manifest = loader.load_manifest()
        
        with pytest.raises(DataLoaderError, match="Checksum mismatch"):
            loader.load_json("test_data.json", verify_checksum=True, manifest=manifest)
    
    def test_load_image_checksum_mismatch(self, temp_archive_environment):
        """Test error when image checksum doesn't match."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        # Replace image with different content
        img_file = temp_archive_environment / "test_image.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(img_file)
        
        manifest = loader.load_manifest()
        
        with pytest.raises(DataLoaderError, match="Checksum mismatch"):
            loader.load_image("test_image.png", verify_checksum=True, manifest=manifest)
    
    def test_load_manifest_missing(self, temp_archive_environment):
        """Test error when manifest file is missing."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        # Remove manifest
        manifest_file = temp_archive_environment / "manifest.json"
        manifest_file.unlink()
        
        with pytest.raises(DataLoaderError, match="Manifest file not found"):
            loader.load_manifest()
    
    def test_list_files_missing_directory(self, temp_archive_environment):
        """Test error when listing non-existent directory."""
        loader = LocalArchiveLoader(temp_archive_environment)
        
        with pytest.raises(DataLoaderError, match="Directory not found"):
            loader.list_files("nonexistent_dir")
    
    def test_load_from_local_archive_invalid_type(self, temp_archive_environment):
        """Test error for unsupported file type."""
        with pytest.raises(DataLoaderError, match="Unsupported file type"):
            load_from_local_archive(
                temp_archive_environment,
                "xml",
                "test.xml",
                verify_checksum=False
            )