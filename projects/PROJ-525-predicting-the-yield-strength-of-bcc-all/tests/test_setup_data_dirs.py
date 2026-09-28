import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We will test the logic by mocking the environment paths
# since the real paths depend on the project root structure.

@pytest.fixture
def mock_env_paths(tmp_path):
    """Fixture to mock environment paths to a temporary directory."""
    data_root = tmp_path / "data"
    raw = data_root / "raw"
    processed = data_root / "processed"
    logs = data_root / "logs"
    
    return {
        "data": data_root,
        "raw": raw,
        "processed": processed,
        "logs": logs
    }

@pytest.fixture
def setup_module(mock_env_paths):
    """Setup the module under test with mocked paths."""
    with patch('code.setup_data_dirs.get_data_path', return_value=mock_env_paths["data"]), \
         patch('code.setup_data_dirs.get_raw_data_path', return_value=mock_env_paths["raw"]), \
         patch('code.setup_data_dirs.get_processed_data_path', return_value=mock_env_paths["processed"]), \
         patch('code.setup_data_dirs.get_logs_path', return_value=mock_env_paths["logs"]):
        
        # Reload the module to pick up the mocked paths if it were already imported
        # In a real test runner, we might need to use importlib.reload
        import code.setup_data_dirs
        import importlib
        importlib.reload(code.setup_data_dirs)
        yield code.setup_data_dirs

def test_create_gitkeep(setup_module, mock_env_paths):
    """Test that .gitkeep files are created in specified directories."""
    target_dir = mock_env_paths["raw"]
    
    # Ensure directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    setup_module.create_gitkeep(target_dir)
    
    gitkeep_file = target_dir / ".gitkeep"
    assert gitkeep_file.exists(), ".gitkeep file should be created"
    assert gitkeep_file.is_file(), ".gitkeep should be a file"

def test_setup_data_directories(setup_module, mock_env_paths):
    """Test that setup_data_directories creates all required directories and .gitkeep files."""
    setup_module.setup_data_directories()
    
    # Check that all directories exist
    assert mock_env_paths["data"].exists(), "data directory should exist"
    assert mock_env_paths["raw"].exists(), "raw directory should exist"
    assert mock_env_paths["processed"].exists(), "processed directory should exist"
    assert mock_env_paths["logs"].exists(), "logs directory should exist"
    
    # Check for .gitkeep files
    for dir_path in [mock_env_paths["data"], mock_env_paths["raw"], 
                     mock_env_paths["processed"], mock_env_paths["logs"]]:
        gitkeep = dir_path / ".gitkeep"
        assert gitkeep.exists(), f".gitkeep should exist in {dir_path}"

def test_generate_checksums(setup_module, mock_env_paths):
    """Test that generate_checksums creates a valid checksums.json file."""
    # Create a dummy file
    dummy_file = mock_env_paths["raw"] / "test.txt"
    dummy_file.write_text("test content")
    
    setup_module.generate_checksums()
    
    checksum_file = mock_env_paths["data"] / "checksums.json"
    assert checksum_file.exists(), "checksums.json should be created"
    
    with open(checksum_file) as f:
        checksums = json.load(f)
    
    assert "raw/test.txt" in checksums, "Checksum for test.txt should be present"
    assert checksums["raw/test.txt"], "Checksum value should not be empty"

def test_verify_checksums_success(setup_module, mock_env_paths):
    """Test verify_checksums returns True when files are intact."""
    # Create a dummy file
    dummy_file = mock_env_paths["raw"] / "verify_test.txt"
    dummy_file.write_text("verify content")
    
    # Generate checksums first
    setup_module.generate_checksums()
    
    # Verify should return True
    result = setup_module.verify_checksums()
    assert result is True, "Verification should pass for intact files"

def test_verify_checksums_failure(setup_module, mock_env_paths):
    """Test verify_checksums returns False when a file is modified."""
    # Create a dummy file
    dummy_file = mock_env_paths["raw"] / "tamper_test.txt"
    dummy_file.write_text("original content")
    
    # Generate checksums
    setup_module.generate_checksums()
    
    # Tamper with the file
    dummy_file.write_text("tampered content")
    
    # Verify should return False
    result = setup_module.verify_checksums()
    assert result is False, "Verification should fail for tampered files"

def test_main_success(setup_module, mock_env_paths, capsys):
    """Test that main() returns 0 on success."""
    # Create a dummy file so checksums are generated
    (mock_env_paths["raw"] / "main_test.txt").write_text("test")
    
    exit_code = setup_module.main()
    
    assert exit_code == 0, "Main should return 0 on success"
    captured = capsys.readouterr()
    assert "completed successfully" in captured.out

def test_main_failure_on_verify(setup_module, mock_env_paths, capsys):
    """Test that main() returns 1 if verification fails."""
    # Create a file and generate checksums
    dummy_file = mock_env_paths["raw"] / "fail_test.txt"
    dummy_file.write_text("content")
    setup_module.generate_checksums()
    
    # Tamper the file
    dummy_file.write_text("tampered")
    
    # Mock verify_checksums to return False to simulate failure without needing complex state
    # Actually, let's just let it run; the tampering above should cause verify_checksums to return False
    # inside main() if the logic is correct.
    
    exit_code = setup_module.main()
    
    # The main function checks the return of verify_checksums
    # If verify_checksums returns False, main should return 1
    assert exit_code == 1, "Main should return 1 if verification fails"
    captured = capsys.readouterr()
    assert "verification failed" in captured.out.lower() or "failed" in captured.out.lower()