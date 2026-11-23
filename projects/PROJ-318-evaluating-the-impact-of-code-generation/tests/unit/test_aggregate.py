import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from code.aggregate import (
    find_batch_files,
    load_batch_file,
    consolidate_batches,
    verify_structure,
    save_results
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_find_batch_files_no_files(temp_dir):
    """Test finding batch files when directory is empty."""
    files = find_batch_files(temp_dir)
    assert files == []

def test_find_batch_files_with_files(temp_dir):
    """Test finding batch files with correct naming."""
    # Create dummy files
    (temp_dir / "generation_batch_repo1.json").touch()
    (temp_dir / "generation_batch_repo2.json").touch()
    (temp_dir / "other_file.json").touch()
    
    files = find_batch_files(temp_dir)
    assert len(files) == 2
    assert "generation_batch_repo1.json" in [f.name for f in files]
    assert "generation_batch_repo2.json" in [f.name for f in files]
    # Check sorted order
    assert files[0].name == "generation_batch_repo1.json"
    assert files[1].name == "generation_batch_repo2.json"

def test_load_batch_file_valid(temp_dir):
    """Test loading a valid JSON file."""
    data = [
        {"method_name": "foo", "ast_params": ["x", "y"]},
        {"method_name": "bar", "ast_params": []}
    ]
    file_path = temp_dir / "generation_batch_test.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    result = load_batch_file(file_path)
    assert result == data
    assert len(result) == 2

def test_load_batch_file_invalid_json(temp_dir):
    """Test loading a file with invalid JSON."""
    file_path = temp_dir / "generation_batch_bad.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json }")
    
    result = load_batch_file(file_path)
    assert result == []

def test_load_batch_file_not_list(temp_dir):
    """Test loading a file that is JSON but not a list."""
    file_path = temp_dir / "generation_batch_dict.json"
    with open(file_path, 'w') as f:
        json.dump({"key": "value"}, f)
    
    result = load_batch_file(file_path)
    assert result == []

def test_consolidate_batches(temp_dir):
    """Test consolidating multiple batch files."""
    # Create two batch files
    data1 = [{"id": 1, "ast_params": ["a"]}, {"id": 2}]
    data2 = [{"id": 3, "ast_params": ["b", "c"]}]
    
    with open(temp_dir / "generation_batch_1.json", 'w') as f:
        json.dump(data1, f)
    with open(temp_dir / "generation_batch_2.json", 'w') as f:
        json.dump(data2, f)
    
    files = find_batch_files(temp_dir)
    result = consolidate_batches(files)
    
    assert len(result) == 3
    assert result[0]["id"] == 1
    assert result[2]["id"] == 3
    # Check ast_params preservation
    assert result[0]["ast_params"] == ["a"]
    assert result[2]["ast_params"] == ["b", "c"]

def test_verify_structure_valid(temp_dir):
    """Test verifying a valid structure."""
    valid_data = [
        {
            "method_name": "test",
            "repo_name": "repo",
            "human_docstring": "Doc",
            "generated_docstring": "Doc",
            "ast_params": ["x"]
        }
    ]
    assert verify_structure(valid_data) is True

def test_verify_structure_missing_key(temp_dir):
    """Test verifying data with missing keys (should warn but return True if dict)."""
    # The function currently logs warnings but returns True if it's a dict
    # unless it encounters a non-dict or invalid ast_params type
    data = [
        {
            "method_name": "test",
            # missing repo_name, human_docstring, etc.
            "ast_params": ["x"]
        }
    ]
    assert verify_structure(data) is True

def test_verify_structure_invalid_ast_params(temp_dir):
    """Test verifying data with invalid ast_params type."""
    data = [
        {
            "method_name": "test",
            "ast_params": "not a list"
        }
    ]
    assert verify_structure(data) is False

def test_verify_structure_empty(temp_dir):
    """Test verifying empty list."""
    assert verify_structure([]) is False

def test_save_results(temp_dir):
    """Test saving results to a file."""
    data = [{"key": "value", "ast_params": [1, 2]}]
    output_path = temp_dir / "results.json"
    
    save_results(data, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == data