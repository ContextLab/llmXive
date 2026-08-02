import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_prompt_manifest import scan_prompt_directory, generate_manifest, main
from code.src.config import PROJECT_ROOT


@pytest.fixture
def temp_prompt_dir():
    """Create a temporary directory with mock prompt files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir)
        
        # Create valid prompt files
        valid_prompts = [
            ("seed_42_logical_ascending.json", {"seed": "42", "strategy": "logical_ascending", "examples": [1, 2, 3]}),
            ("seed_42_logical_random.json", {"seed": "42", "strategy": "logical_random", "examples": [1, 2, 3]}),
            ("seed_100_logical_ascending.json", {"seed": "100", "strategy": "logical_ascending", "examples": [1, 2, 3, 4, 5]}),
            ("seed_100_original_cds.json", {"seed": "100", "strategy": "original_cds", "examples": [1, 2]}),
        ]
        
        for filename, content in valid_prompts:
            file_path = prompt_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f)
        
        # Create an invalid JSON file
        invalid_file = prompt_dir / "bad_file.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        # Create a file with wrong naming convention
        weird_file = prompt_dir / "weird_name.txt"
        with open(weird_file, 'w', encoding='utf-8') as f:
            f.write("not json")
        
        yield prompt_dir


@pytest.fixture
def temp_manifest_file():
    """Create a temporary output path for the manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "manifest.json"


def test_scan_prompt_directory_success(temp_prompt_dir):
    """Test that scan_prompt_directory correctly identifies and parses valid prompt files."""
    results = scan_prompt_directory(temp_prompt_dir)
    
    assert len(results) == 4  # 4 valid JSON files
    
    # Check that we found the expected seeds and strategies
    seeds = [r["seed"] for r in results]
    strategies = [r["strategy"] for r in results]
    
    assert "42" in seeds
    assert "100" in seeds
    assert "logical_ascending" in strategies
    assert "logical_random" in strategies
    assert "original_cds" in strategies
    
    # Check structure of an entry
    entry = results[0]
    assert "seed" in entry
    assert "strategy" in entry
    assert "file_path" in entry
    assert "absolute_path" in entry
    assert "num_examples" in entry


def test_scan_prompt_directory_empty(tmp_path):
    """Test scanning an empty directory."""
    results = scan_prompt_directory(tmp_path)
    assert results == []


def test_scan_prompt_directory_nonexistent():
    """Test scanning a non-existent directory."""
    fake_path = Path("/nonexistent/path/that/does/not/exist")
    results = scan_prompt_directory(fake_path)
    assert results == []


def test_scan_prompt_directory_invalid_format(temp_prompt_dir):
    """Test that invalid JSON files and wrong naming conventions are skipped."""
    results = scan_prompt_directory(temp_prompt_dir)
    
    # Should skip the invalid JSON and the .txt file
    # Only the 4 valid JSON files should be included
    assert len(results) == 4
    
    # Ensure no entry points to the invalid file
    file_paths = [r["file_path"] for r in results]
    assert "bad_file.json" not in [Path(p).name for p in file_paths]
    assert "weird_name.txt" not in [Path(p).name for p in file_paths]


def test_generate_manifest(temp_prompt_dir, temp_manifest_file):
    """Test that generate_manifest creates a correct manifest file."""
    manifest = generate_manifest(temp_prompt_dir, temp_manifest_file)
    
    # Check manifest structure
    assert "metadata" in manifest
    assert "prompts" in manifest
    
    # Check metadata
    meta = manifest["metadata"]
    assert meta["total_prompts"] == 4
    assert len(meta["strategies_found"]) == 3
    assert len(meta["seeds_found"]) == 2
    assert "logical_ascending" in meta["strategies_found"]
    
    # Check that the file was actually written
    assert temp_manifest_file.exists()
    
    # Verify file contents match the returned manifest
    with open(temp_manifest_file, 'r', encoding='utf-8') as f:
        saved_manifest = json.load(f)
    
    assert saved_manifest == manifest


def test_generate_manifest_sorting(temp_prompt_dir, temp_manifest_file):
    """Test that the manifest entries are sorted correctly."""
    manifest = generate_manifest(temp_prompt_dir, temp_manifest_file)
    
    # Check that seeds and strategies in metadata are sorted
    assert manifest["metadata"]["seeds_found"] == sorted(manifest["metadata"]["seeds_found"])
    assert manifest["metadata"]["strategies_found"] == sorted(manifest["metadata"]["strategies_found"])


def test_generate_manifest_empty_directory(tmp_path, temp_manifest_file):
    """Test generating a manifest from an empty directory."""
    manifest = generate_manifest(tmp_path, temp_manifest_file)
    
    assert manifest["metadata"]["total_prompts"] == 0
    assert manifest["metadata"]["strategies_found"] == []
    assert manifest["metadata"]["seeds_found"] == []
    assert manifest["prompts"] == []
    
    assert temp_manifest_file.exists()


def test_generate_manifest_creates_output_dir(tmp_path):
    """Test that generate_manifest creates the output directory if it doesn't exist."""
    output_dir = tmp_path / "nested" / "output"
    output_path = output_dir / "manifest.json"
    
    # Directory should not exist yet
    assert not output_dir.exists()
    
    # Create a dummy prompt file
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "test_123_strategy.json"
    with open(prompt_file, 'w') as f:
        json.dump({"examples": [1]}, f)
    
    manifest = generate_manifest(prompt_dir, output_path)
    
    # Directory should now exist
    assert output_dir.exists()
    assert output_path.exists()
    assert manifest["metadata"]["total_prompts"] == 1


def test_main_success(temp_prompt_dir, temp_manifest_file, capsys):
    """Test the main function with valid inputs."""
    # Mock the arguments
    test_args = [
        'generate_prompt_manifest',
        '--prompt_dir', str(temp_prompt_dir),
        '--output', str(temp_manifest_file)
    ]
    
    with patch('sys.argv', test_args):
        result = main()
    
    assert result == 0
    assert temp_manifest_file.exists()


def test_main_missing_directory(capsys):
    """Test the main function with a non-existent prompt directory."""
    fake_dir = Path("/nonexistent/dir")
    output_file = Path(tempfile.gettempdir()) / "test_manifest.json"
    
    test_args = [
        'generate_prompt_manifest',
        '--prompt_dir', str(fake_dir),
        '--output', str(output_file)
    ]
    
    with patch('sys.argv', test_args):
        result = main()
    
    # Should succeed (return 0) even if directory is empty/missing, just log a warning
    assert result == 0
    assert output_file.exists()