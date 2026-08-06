import os
import json
import tempfile
import hashlib
import pytest
from unittest.mock import patch, MagicMock

from code.config import get_config
from code.utils.logging_utils import setup_logging

# Import the functions to test
# Note: We import from the module path relative to code/
from code import code_010_populate_checksums as populate_checksums_module

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_files(temp_dir):
    """Create mock CSV files for testing."""
    file1_path = os.path.join(temp_dir, "file1.csv")
    file2_path = os.path.join(temp_dir, "file2.csv")
    
    with open(file1_path, "w") as f:
        f.write("col1,col2\nval1,val2\n")
        
    with open(file2_path, "w") as f:
        f.write("data\n123\n")
        
    return {
        "file1": file1_path,
        "file2": file2_path
    }

def test_calculate_sha256(temp_dir):
    """Test SHA-256 calculation."""
    test_file = os.path.join(temp_dir, "test.txt")
    content = b"test content for hashing"
    with open(test_file, "wb") as f:
        f.write(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    calculated_hash = populate_checksums_module.calculate_sha256(test_file)
    
    assert calculated_hash == expected_hash
    assert len(calculated_hash) == 64  # SHA-256 hex length

def test_validate_files_exist_all_exist(mock_files, temp_dir):
    """Test validation when all files exist."""
    logger = setup_logging("test")
    result = populate_checksums_module.validate_files_exist(mock_files, logger)
    assert result is True

def test_validate_files_exist_missing_file(mock_files, temp_dir):
    """Test validation when a file is missing."""
    files_with_missing = mock_files.copy()
    files_with_missing["missing_file"] = "/nonexistent/path.csv"
    
    logger = setup_logging("test")
    result = populate_checksums_module.validate_files_exist(files_with_missing, logger)
    assert result is False

def test_populate_checksums_success(mock_files, temp_dir):
    """Test successful checksum population."""
    checksums_path = os.path.join(temp_dir, "checksums.json")
    source_info = {
        "file1": {"source_url": "http://example.com/file1", "version": "1.0"},
        "file2": {"source_url": "http://example.com/file2", "version": "1.0"}
    }
    
    logger = setup_logging("test")
    result = populate_checksums_module.populate_checksums(
        file_paths=mock_files,
        checksums_path=checksums_path,
        source_info=source_info,
        logger=logger
    )
    
    assert os.path.exists(checksums_path)
    assert "file1" in result
    assert "file2" in result
    assert "hash" in result["file1"]
    assert "hash" in result["file2"]
    assert result["file1"]["source_url"] == "http://example.com/file1"
    assert result["file1"]["version"] == "1.0"
    
    # Verify the hash is correct
    with open(mock_files["file1"], "rb") as f:
        expected_hash = hashlib.sha256(f.read()).hexdigest()
    assert result["file1"]["hash"] == expected_hash

def test_populate_checksums_missing_file(mock_files, temp_dir):
    """Test that missing files raise FileNotFoundError."""
    files_with_missing = mock_files.copy()
    files_with_missing["missing"] = "/nonexistent.csv"
    
    checksums_path = os.path.join(temp_dir, "checksums.json")
    logger = setup_logging("test")
    
    with pytest.raises(FileNotFoundError):
        populate_checksums_module.populate_checksums(
            file_paths=files_with_missing,
            checksums_path=checksums_path,
            source_info={},
            logger=logger
        )

def test_main_function_success(mock_files, temp_dir):
    """Test the main function with existing files."""
    # Mock get_config to return our temp dir
    mock_config = {
        "data_raw_dir": temp_dir,
        "data_processed_dir": os.path.join(temp_dir, "processed"),
        "data_assets_dir": os.path.join(temp_dir, "assets"),
        "code_dir": os.path.join(temp_dir, "code"),
        "artifacts_dir": os.path.join(temp_dir, "artifacts"),
        "tests_dir": os.path.join(temp_dir, "tests")
    }
    
    # Create the required files
    ref_path = os.path.join(temp_dir, "reference_substructures_raw.csv")
    kin_path = os.path.join(temp_dir, "kinetic_dataset_raw.csv")
    
    with open(ref_path, "w") as f:
        f.write("substructure,smiles\nA,CCO\n")
    with open(kin_path, "w") as f:
        f.write("cid,rate\n123,0.5\n")
    
    with patch("code.010_populate_checksums.get_config", return_value=mock_config):
        with patch("code.010_populate_checksums.ensure_directories"):
            # This should not raise an exception
            try:
                populate_checksums_module.main()
            except SystemExit as e:
                if e.code != 0:
                    raise
    
    checksums_path = os.path.join(temp_dir, "checksums.json")
    assert os.path.exists(checksums_path)
    
    with open(checksums_path, "r") as f:
        data = json.load(f)
    
    assert "reference_substructures" in data
    assert "kinetic_dataset" in data
    assert data["reference_substructures"]["hash"] is not None
    assert data["kinetic_dataset"]["hash"] is not None