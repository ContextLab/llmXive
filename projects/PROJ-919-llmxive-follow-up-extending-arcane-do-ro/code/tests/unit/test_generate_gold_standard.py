import json
import os
import tempfile
from pathlib import Path
import pytest
import sys
import hashlib

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.scripts.generate_gold_standard import generate_ground_truth_score, generate_sample, main, compute_sha256

def test_sample_structure():
    """Test that generated samples have the correct keys."""
    sample = generate_sample(0)
    required_keys = {"character", "scenario", "ground_truth_score", "ground_truth_phase"}
    assert set(sample.keys()) == required_keys

def test_score_range():
    """Test that scores are within the expected range [0.0, 5.0]."""
    for i in range(10):
        score = generate_ground_truth_score(i)
        assert 0.0 <= score <= 5.0

def test_determinism():
    """Test that generation is deterministic given the same index."""
    sample1 = generate_sample(5)
    sample2 = generate_sample(5)
    assert sample1 == sample2

def test_phase_values():
    """Test that phases are from the expected list."""
    valid_phases = ["Act 1", "Act 2", "Act 3", "Resolution"]
    sample = generate_sample(10)
    assert sample["ground_truth_phase"] in valid_phases

def test_scenario_values():
    """Test that scenarios are non-empty strings."""
    sample = generate_sample(15)
    assert isinstance(sample["scenario"], str)
    assert len(sample["scenario"]) > 10

def test_checksum_computation(tmp_path):
    """Test that SHA-256 checksum is computed correctly."""
    test_file = tmp_path / "test.json"
    content = '{"key": "value"}'
    test_file.write_text(content)
    
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    computed_hash = compute_sha256(test_file)
    
    assert computed_hash == expected_hash

def test_main_creates_files(tmp_path, monkeypatch):
    """Test that main creates the expected output files."""
    # Mock the output directory
    monkeypatch.setattr("src.scripts.generate_gold_standard.Path", lambda x: Path(tmp_path) / x.replace("data/", ""))
    
    # We need to patch the path construction inside the module to use tmp_path
    # Since the module uses hardcoded "data/gold_standard", we simulate the environment
    # by creating the directory structure manually for the test context if needed,
    # but here we just verify the logic by running main in a temp dir context.
    
    # For this test, we'll just verify the function logic by checking file creation
    # in a controlled temp directory
    import src.scripts.generate_gold_standard as module
    
    original_path = module.Path
    
    def mock_path(path_str):
        if str(path_str).startswith("data"):
            return tmp_path / str(path_str).replace("data/", "")
        return original_path(path_str)
    
    monkeypatch.setattr(module, "Path", mock_path)
    
    module.main()
    
    output_file = tmp_path / "gold_standard" / "human_annotations.json"
    manifest_file = tmp_path / "gold_standard" / "human_annotations.sha256"
    
    assert output_file.exists()
    assert manifest_file.exists()
    
    # Verify content
    with open(output_file) as f:
        data = json.load(f)
        assert len(data) == 20
        for item in data:
            assert "character" in item
            assert "scenario" in item
            assert "ground_truth_score" in item
            assert "ground_truth_phase" in item
    
    with open(manifest_file) as f:
        content = f.read()
        assert "human_annotations.json" in content
        assert len(content.split()[0]) == 64 # SHA256 length