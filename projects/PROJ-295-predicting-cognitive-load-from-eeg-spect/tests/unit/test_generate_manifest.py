import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.data.generate_manifest import (
    calculate_file_checksum,
    generate_manifest,
    update_state
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_file(temp_dir):
    file_path = os.path.join(temp_dir, "test_file.tsv")
    with open(file_path, "w") as f:
        f.write("col1\tcol2\nval1\tval2\n")
    return file_path

def test_calculate_file_checksum(mock_file):
    checksum = calculate_file_checksum(mock_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

@patch('code.data.generate_manifest.fetch_remote_checksum')
@patch('code.data.generate_manifest.verify_dataset_integrity')
def test_generate_manifest_success(mock_verify, mock_fetch, mock_file, temp_dir):
    # Setup mocks
    mock_fetch.return_value = {
        'version': '1.0.0',
        'checksum': 'a' * 64,
        'size': 100
    }
    mock_verify.return_value = True

    output_path = os.path.join(temp_dir, "manifest.yaml")
    
    # We need to pass a path that contains the mock_file
    # The function expects dataset_path to be the parent of the filename
    dataset_path = os.path.dirname(mock_file)
    filename = os.path.basename(mock_file)

    manifest_data = generate_manifest("ds_test", dataset_path, output_path, filename)

    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data['dataset_id'] == "ds_test"
    assert data['version'] == '1.0.0'
    assert len(data['files']) == 1
    assert data['files'][0]['name'] == filename
    assert data['files'][0]['verified_against_source'] is True

@patch('code.data.generate_manifest.fetch_remote_checksum')
def test_generate_manifest_missing_local(mock_fetch, temp_dir):
    # Mock remote success but local file missing
    mock_fetch.return_value = {
        'version': '1.0.0',
        'checksum': 'a' * 64,
        'size': 100
    }

    output_path = os.path.join(temp_dir, "manifest.yaml")
    dataset_path = temp_dir
    filename = "missing_file.tsv"

    with pytest.raises(FileNotFoundError):
        generate_manifest("ds_test", dataset_path, output_path, filename)

@patch('code.data.generate_manifest.fetch_remote_checksum')
def test_generate_manifest_checksum_mismatch(mock_fetch, mock_file, temp_dir):
    # Mock remote checksum different from local
    mock_fetch.return_value = {
        'version': '1.0.0',
        'checksum': 'b' * 64, # Different checksum
        'size': 100
    }

    output_path = os.path.join(temp_dir, "manifest.yaml")
    dataset_path = os.path.dirname(mock_file)
    filename = os.path.basename(mock_file)

    with pytest.raises(ValueError, match="Checksum verification failed"):
        generate_manifest("ds_test", dataset_path, output_path, filename)

@patch('code.data.generate_manifest.fetch_remote_checksum')
def test_generate_manifest_no_remote(mock_fetch, mock_file, temp_dir):
    # Mock remote failure
    mock_fetch.return_value = None

    output_path = os.path.join(temp_dir, "manifest.yaml")
    dataset_path = os.path.dirname(mock_file)
    filename = os.path.basename(mock_file)

    manifest_data = generate_manifest("ds_test", dataset_path, output_path, filename)

    assert manifest_data['files'][0]['verified_against_source'] is False
    assert "Remote metadata unavailable" in manifest_data['files'][0]['verification_message']

@patch('code.data.generate_manifest.fetch_remote_checksum')
def test_update_state(mock_fetch, mock_file, temp_dir):
    mock_fetch.return_value = None # Force local-only mode
    
    dataset_path = os.path.dirname(mock_file)
    filename = os.path.basename(mock_file)
    output_path = os.path.join(temp_dir, "manifest.yaml")
    state_path = os.path.join(temp_dir, "state.yaml")

    manifest_data = generate_manifest("ds_test", dataset_path, output_path, filename)
    update_state(manifest_data, state_path)

    assert os.path.exists(state_path)
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    assert 'last_manifest_update' in state
    assert 'dataset' in state
    assert state['dataset']['id'] == 'ds_test'
    assert filename in state['dataset']['files_checksums']