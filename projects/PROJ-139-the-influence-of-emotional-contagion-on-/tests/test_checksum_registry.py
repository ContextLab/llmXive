import json
import os
import tempfile
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.checksum_registry import (
    compute_file_hash,
    find_artifacts,
    record_checksums,
    update_project_state
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file with known content."""
    file_path = temp_dir / "test_file.txt"
    content = "This is test content for checksum verification."
    file_path.write_text(content)
    return file_path


def test_compute_file_hash(temp_file):
    """Test that compute_file_hash returns the correct SHA-256 hash."""
    content = temp_file.read_text()
    expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    actual_hash = compute_file_hash(temp_file)
    
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length


def test_compute_file_hash_content_change(temp_dir):
    """Test that hash changes when file content changes."""
    file_path = temp_dir / "mutable.txt"
    
    # Write initial content
    file_path.write_text("content v1")
    hash1 = compute_file_hash(file_path)
    
    # Change content
    file_path.write_text("content v2")
    hash2 = compute_file_hash(file_path)
    
    assert hash1 != hash2


def test_compute_file_hash_missing_file(temp_dir):
    """Test that compute_file_hash raises FileNotFoundError for missing files."""
    missing_path = temp_dir / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_path)


def test_find_artifacts(temp_dir):
    """Test artifact discovery in directory structure."""
    # Create nested structure
    (temp_dir / "subdir").mkdir()
    (temp_dir / "file1.txt").write_text("a")
    (temp_dir / "subdir" / "file2.csv").write_text("b")
    (temp_dir / "file3.json").write_text("c")
    
    artifacts = find_artifacts([temp_dir])
    
    assert len(artifacts) == 3
    assert any("file1.txt" in str(p) for p in artifacts)
    assert any("file2.csv" in str(p) for p in artifacts)
    assert any("file3.json" in str(p) for p in artifacts)


def test_find_artifacts_with_extension_filter(temp_dir):
    """Test artifact discovery with extension filtering."""
    (temp_dir / "data.txt").write_text("a")
    (temp_dir / "data.csv").write_text("b")
    (temp_dir / "data.json").write_text("c")
    
    # Filter for CSV and JSON only
    artifacts = find_artifacts([temp_dir], extensions=['.csv', '.json'])
    
    assert len(artifacts) == 2
    assert not any("data.txt" in str(p) for p in artifacts)


def test_record_checksums(temp_dir):
    """Test recording checksums to a registry file."""
    # Create test files
    file1 = temp_dir / "a.txt"
    file2 = temp_dir / "b.txt"
    file1.write_text("content1")
    file2.write_text("content2")
    
    registry_path = temp_dir / "registry.json"
    
    # Record checksums
    checksums = record_checksums([file1, file2], registry_path)
    
    # Verify registry file exists and is valid JSON
    assert registry_path.exists()
    with open(registry_path) as f:
        loaded = json.load(f)
        
    assert len(loaded) == 2
    assert file1.name in str(list(loaded.keys())[0]) or file2.name in str(list(loaded.keys())[1])
    
    # Verify hashes are correct
    for path_str, hash_val in checksums.items():
        p = Path(path_str)
        if p.exists():
            expected = compute_file_hash(p)
            assert hash_val == expected


def test_update_project_state(temp_dir):
    """Test updating project state YAML with checksums."""
    state_path = temp_dir / "project_state.yaml"
    checksums = {
        "data/file1.csv": "hash1",
        "data/file2.csv": "hash2"
    }
    
    update_project_state(state_path, checksums)
    
    assert state_path.exists()
    
    # Verify content
    import yaml
    with open(state_path) as f:
        data = yaml.safe_load(f)
        
    assert 'artifact_checksums' in data
    assert data['artifact_checksums'] == checksums
    assert 'last_updated' in data


def test_main_integration(temp_dir, monkeypatch):
    """Integration test for main() function with mocked paths."""
    # Create dummy directories and files
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "test.csv").write_text("test")
    
    state_dir = temp_dir / "state"
    state_dir.mkdir()
    (state_dir / "projects").mkdir()
    
    # Mock config to return our temp directories
    mock_paths = MagicMock()
    mock_paths.raw_data = data_dir
    mock_paths.processed_data = data_dir
    mock_paths.code_dir = temp_dir
    mock_paths.state_dir = state_dir
    mock_paths.docs_dir = temp_dir
    
    mock_config = MagicMock()
    mock_config.paths = mock_paths
    
    with patch('utils.checksum_registry.get_config', return_value=mock_config):
        from utils.checksum_registry import main
        main()
    
    # Verify outputs were created
    registry_path = state_dir / "checksum_registry.json"
    project_state_path = state_dir / "projects" / "PROJ-139-the-influence-of-emotional-contagion-on-.yaml"
    
    assert registry_path.exists()
    assert project_state_path.exists()