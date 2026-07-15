"""
Unit tests for checksum utilities (T029d).

Tests for:
- File checksum computation
- Checksum verification
- Metadata registration for datasets
"""
import os
import json
import tempfile
import pytest
from code.utils.checksum_utils import (
    compute_file_checksum,
    verify_checksum,
    ensure_metadata_file_exists,
    load_simulation_metadata,
    save_simulation_metadata,
    register_dataset_checksum
)

def test_compute_file_checksum():
    """Test that checksum computation produces consistent results."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        checksum1 = compute_file_checksum(temp_path)
        checksum2 = compute_file_checksum(temp_path)
        
        # Same file should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum1)
    finally:
        os.unlink(temp_path)

def test_compute_file_checksum_different_content():
    """Test that different content produces different checksums."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
        f1.write("Content A")
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
        f2.write("Content B")
        path2 = f2.name
    
    try:
        checksum1 = compute_file_checksum(path1)
        checksum2 = compute_file_checksum(path2)
        
        assert checksum1 != checksum2
    finally:
        os.unlink(path1)
        os.unlink(path2)

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content for verification")
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        assert verify_checksum(temp_path, checksum) is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_failure():
    """Test failed checksum verification with wrong checksum."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name
    
    try:
        wrong_checksum = "a" * 64  # Invalid checksum
        assert verify_checksum(temp_path, wrong_checksum) is False
    finally:
        os.unlink(temp_path)

def test_register_dataset_checksum():
    """Test that dataset checksums are properly registered in metadata."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4")
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        
        # Register the dataset
        register_dataset_checksum(
            name="Test_Dataset",
            source="test:123",
            file_path=temp_path,
            checksum=checksum
        )
        
        # Load metadata and verify
        metadata = load_simulation_metadata()
        datasets = metadata.get('datasets', [])
        
        assert len(datasets) >= 1
        
        # Find our dataset
        found = False
        for ds in datasets:
            if ds['name'] == "Test_Dataset":
                assert ds['source'] == "test:123"
                assert ds['checksum'] == checksum
                assert ds['path'] == os.path.relpath(temp_path, 'data')
                assert 'downloaded_at' in ds
                found = True
                break
        
        assert found, "Test dataset not found in metadata"
    finally:
        os.unlink(temp_path)

def test_update_existing_dataset_checksum():
    """Test that registering the same dataset updates its entry."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4")
        temp_path = f.name
    
    try:
        checksum1 = compute_file_checksum(temp_path)
        register_dataset_checksum(
            name="Update_Test",
            source="test:456",
            file_path=temp_path,
            checksum=checksum1
        )
        
        # Change the file content
        with open(temp_path, 'w') as f:
            f.write("Different content")
        
        checksum2 = compute_file_checksum(temp_path)
        register_dataset_checksum(
            name="Update_Test",
            source="test:789",
            file_path=temp_path,
            checksum=checksum2
        )
        
        # Load metadata and verify update
        metadata = load_simulation_metadata()
        datasets = metadata.get('datasets', [])
        
        update_test_datasets = [ds for ds in datasets if ds['name'] == "Update_Test"]
        assert len(update_test_datasets) == 1  # Should be updated, not duplicated
        assert update_test_datasets[0]['checksum'] == checksum2
        assert update_test_datasets[0]['source'] == "test:789"
    finally:
        os.unlink(temp_path)

def test_metadata_file_creation():
    """Test that metadata file is created if it doesn't exist."""
    # This test assumes the metadata file might not exist
    ensure_metadata_file_exists()
    assert os.path.exists('data/simulation_metadata.json')
    
    metadata = load_simulation_metadata()
    assert 'schema_version' in metadata
    assert 'created_at' in metadata
    assert 'datasets' in metadata
    assert 'runs' in metadata
