"""
Tests for data_loader module.
"""

import os
import tempfile
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import pandas as pd

from src.lib.data_loader import (
    load_stimuli_from_archive,
    load_csv_from_archive,
    load_json_from_archive,
    verify_archive_integrity,
    DataLoaderError
)
from src.lib.utils import compute_file_checksum


@pytest.fixture
def temp_archive_environment():
    """Create a temporary archive with test images and checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir) / "stimuli"
        archive_dir.mkdir()
        
        # Create test images
        test_images = {}
        for i in range(3):
            img_path = archive_dir / f"test_image_{i}.png"
            img = Image.new('RGB', (100, 100), color=(i * 50, i * 50, i * 50))
            img.save(img_path)
            
            # Compute and store checksum
            checksum = compute_file_checksum(str(img_path))
            test_images[f"test_image_{i}.png"] = checksum
        
        # Create checksum file
        checksum_file = Path(tmpdir) / "checksums.json"
        with open(checksum_file, 'w') as f:
            json.dump(test_images, f)
        
        yield {
            'archive_dir': str(archive_dir),
            'checksum_file': str(checksum_file),
            'temp_dir': tmpdir
        }


@pytest.fixture
def temp_csv_environment():
    """Create a temporary archive with test CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir) / "data"
        archive_dir.mkdir()
        
        # Create test CSV
        csv_path = archive_dir / "test_data.csv"
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['a', 'b', 'c'],
            'score': [10.5, 20.3, 30.1]
        })
        df.to_csv(csv_path, index=False)
        
        yield {
            'archive_dir': str(archive_dir),
            'filename': 'test_data.csv',
            'temp_dir': tmpdir
        }


@pytest.fixture
def temp_json_environment():
    """Create a temporary archive with test JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir) / "config"
        archive_dir.mkdir()
        
        # Create test JSON
        json_path = archive_dir / "test_config.json"
        data = {
            'experiment_id': 'exp_001',
            'participants': 20,
            'settings': {
                'seed': 42,
                'threshold': 0.5
            }
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        yield {
            'archive_dir': str(archive_dir),
            'filename': 'test_config.json',
            'temp_dir': tmpdir
        }


class TestLocalLoadSuccess:
    """Test that local loading from archives works correctly."""

    def test_load_stimuli_from_archive_success(self, temp_archive_environment):
        """Test loading images from a verified local archive."""
        result = load_stimuli_from_archive(
            temp_archive_environment['archive_dir'],
            temp_archive_environment['checksum_file']
        )
        
        assert len(result) == 3
        assert all(item['filename'].startswith('test_image_') for item in result)
        assert all('image' in item for item in result)
        assert all(item['checksum'] for item in result)

    def test_load_stimuli_with_invalid_checksum_fails(self, temp_archive_environment):
        """Test that loading fails when checksums don't match."""
        # Modify checksum file to have wrong checksum
        with open(temp_archive_environment['checksum_file'], 'r') as f:
            checksums = json.load(f)
        
        # Change first checksum
        first_key = list(checksums.keys())[0]
        checksums[first_key] = "invalid_checksum_12345"
        
        with open(temp_archive_environment['checksum_file'], 'w') as f:
            json.dump(checksums, f)
        
        with pytest.raises(DataLoaderError) as exc_info:
            load_stimuli_from_archive(
                temp_archive_environment['archive_dir'],
                temp_archive_environment['checksum_file']
            )
        
        assert "No valid images found" in str(exc_info.value)

    def test_load_csv_from_archive_success(self, temp_csv_environment):
        """Test loading CSV from a local archive."""
        df = load_csv_from_archive(
            temp_csv_environment['archive_dir'],
            temp_csv_environment['filename']
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ['id', 'value', 'score']
        assert df.iloc[0]['id'] == 1

    def test_load_csv_missing_file_fails(self, temp_csv_environment):
        """Test that loading fails for missing CSV files."""
        with pytest.raises(DataLoaderError) as exc_info:
            load_csv_from_archive(
                temp_csv_environment['archive_dir'],
                'nonexistent.csv'
            )
        
        assert "CSV file not found" in str(exc_info.value)

    def test_load_json_from_archive_success(self, temp_json_environment):
        """Test loading JSON from a local archive."""
        data = load_json_from_archive(
            temp_json_environment['archive_dir'],
            temp_json_environment['filename']
        )
        
        assert isinstance(data, dict)
        assert data['experiment_id'] == 'exp_001'
        assert data['participants'] == 20
        assert data['settings']['seed'] == 42

    def test_load_json_missing_file_fails(self, temp_json_environment):
        """Test that loading fails for missing JSON files."""
        with pytest.raises(DataLoaderError) as exc_info:
            load_json_from_archive(
                temp_json_environment['archive_dir'],
                'nonexistent.json'
            )
        
        assert "JSON file not found" in str(exc_info.value)

    def test_verify_archive_integrity_success(self, temp_archive_environment):
        """Test archive integrity verification."""
        results = verify_archive_integrity(
            temp_archive_environment['archive_dir'],
            temp_archive_environment['checksum_file']
        )
        
        assert results['archive_exists']
        assert results['checksum_file_exists']
        assert results['total_files'] == 3
        assert results['verified_files'] == 3
        assert results['failed_files'] == 0
        assert results['missing_files'] == 0
        assert results['integrity_valid']

    def test_verify_archive_integrity_with_missing_files(self, temp_archive_environment):
        """Test integrity verification with missing files."""
        # Remove one image
        archive_path = Path(temp_archive_environment['archive_dir'])
        (archive_path / 'test_image_0.png').unlink()
        
        results = verify_archive_integrity(
            temp_archive_environment['archive_dir'],
            temp_archive_environment['checksum_file']
        )
        
        assert results['missing_files'] == 1
        assert results['verified_files'] == 2
        assert not results['integrity_valid']

    def test_load_from_nonexistent_archive_fails(self):
        """Test that loading from nonexistent archive fails."""
        with pytest.raises(DataLoaderError) as exc_info:
            load_stimuli_from_archive(
                '/nonexistent/path',
                '/nonexistent/checksums.json'
            )
        
        assert "Archive directory not found" in str(exc_info.value)

    def test_load_from_missing_checksum_file_fails(self, temp_archive_environment):
        """Test that loading fails when checksum file is missing."""
        with pytest.raises(DataLoaderError) as exc_info:
            load_stimuli_from_archive(
                temp_archive_environment['archive_dir'],
                '/nonexistent/checksums.json'
            )
        
        assert "Checksum file not found" in str(exc_info.value)