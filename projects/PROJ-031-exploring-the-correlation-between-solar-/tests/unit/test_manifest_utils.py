"""
Unit tests for manifest_utils.py.
"""
import pytest
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from manifest_utils import (
    load_manifest,
    save_manifest,
    ensure_sources_initialized,
    update_source_status,
    write_manifest_after_ingestion,
    validate_manifest_integrity,
    REQUIRED_SOURCES
)

@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file for testing."""
    fd, path = tempfile.mkstemp(suffix='.yaml')
    try:
        data = {
            'sources': {
                'dst_indices': {
                    'status': 'Verified',
                    'url': 'http://test.com',
                    'retrieved_at': '2023-01-01',
                    'record_count': 100
                }
            }
        }
        with os.fdopen(fd, 'w') as f:
            yaml.dump(data, f)
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)

@patch('manifest_utils.MANIFEST_PATH')
def test_load_manifest_success(mock_path, temp_manifest):
    """Test successful manifest loading."""
    mock_path.exists.return_value = True
    mock_path.__truediv__.return_value = Path(temp_manifest)
    
    # Temporarily override MANIFEST_PATH for the test
    with patch('manifest_utils.MANIFEST_PATH', Path(temp_manifest)):
        manifest = load_manifest()
        assert 'sources' in manifest
        assert 'dst_indices' in manifest['sources']

@patch('manifest_utils.MANIFEST_PATH')
def test_load_manifest_missing(mock_path):
    """Test loading missing manifest raises error."""
    mock_path.exists.return_value = False
    
    with pytest.raises(FileNotFoundError):
        load_manifest()

@patch('manifest_utils.MANIFEST_PATH')
def test_ensure_sources_initialized(mock_path, temp_manifest):
    """Test that ensure_sources_initialized adds missing sources."""
    with patch('manifest_utils.MANIFEST_PATH', Path(temp_manifest)):
        manifest = load_manifest()
        updated = ensure_sources_initialized(manifest)
        
        for source in REQUIRED_SOURCES:
            assert source in updated['sources']
            assert 'status' in updated['sources'][source]
            assert 'last_verified_at' in updated['sources'][source]

@patch('manifest_utils.MANIFEST_PATH')
def test_update_source_status(mock_path, temp_manifest):
    """Test updating source status."""
    with patch('manifest_utils.MANIFEST_PATH', Path(temp_manifest)):
        manifest = load_manifest()
        updated = update_source_status(
            source_name='dst_indices',
            status='Failed',
            record_count=200,
            manifest=manifest
        )
        
        assert updated['sources']['dst_indices']['status'] == 'Failed'
        assert updated['sources']['dst_indices']['record_count'] == 200
        assert updated['sources']['dst_indices']['last_verified_at'] is not None

@patch('manifest_utils.MANIFEST_PATH')
def test_validate_manifest_integrity_valid(mock_path, temp_manifest):
    """Test validation of valid manifest."""
    with patch('manifest_utils.MANIFEST_PATH', Path(temp_manifest)):
        manifest = load_manifest()
        # Ensure all sources are present
        manifest = ensure_sources_initialized(manifest)
        
        assert validate_manifest_integrity(manifest) is True

@patch('manifest_utils.MANIFEST_PATH')
def test_validate_manifest_integrity_invalid(mock_path, temp_manifest):
    """Test validation of invalid manifest."""
    with patch('manifest_utils.MANIFEST_PATH', Path(temp_manifest)):
        manifest = load_manifest()
        # Remove required field
        manifest['sources']['dst_indices'].pop('status', None)
        
        assert validate_manifest_integrity(manifest) is False

@patch('manifest_utils.save_manifest')
@patch('manifest_utils.load_manifest')
def test_write_manifest_after_ingestion(mock_load, mock_save, temp_manifest):
    """Test writing manifest after ingestion."""
    mock_load.return_value = {'sources': {'dst_indices': {'status': 'Pending'}}}
    
    write_manifest_after_ingestion(
        source_name='dst_indices',
        status='Verified',
        url='http://test.com',
        record_count=100
    )
    
    mock_load.assert_called_once()
    mock_save.assert_called_once()