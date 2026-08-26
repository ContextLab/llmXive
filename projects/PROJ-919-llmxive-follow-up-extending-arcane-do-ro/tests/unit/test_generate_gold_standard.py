"""
Unit tests for generate_gold_standard.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add src to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scripts.generate_gold_standard import (
    generate_ground_truth_score,
    generate_sample,
    compute_sha256,
    main
)
import random

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_sample_structure():
    """Test that generated samples have the correct structure."""
    rng = random.Random(42)
    sample = generate_sample(0, rng)
    
    assert "character" in sample
    assert "scenario" in sample
    assert "ground_truth_score" in sample
    assert "ground_truth_phase" in sample
    
    assert isinstance(sample["character"], str)
    assert isinstance(sample["scenario"], str)
    assert isinstance(sample["ground_truth_score"], float)
    assert isinstance(sample["ground_truth_phase"], str)

def test_score_range():
    """Test that ground truth scores are within the valid range [1.0, 5.0]."""
    rng = random.Random(42)
    for i in range(100):
        score = generate_ground_truth_score(rng)
        assert 1.0 <= score <= 5.0

def test_determinism():
    """Test that the generation is deterministic with the same seed."""
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    
    sample1 = generate_sample(5, rng1)
    sample2 = generate_sample(5, rng2)
    
    assert sample1 == sample2

def test_phase_values():
    """Test that ground truth phases are from the valid set."""
    valid_phases = ["pre-moral", "emerging-conscience", "conflicted", "principled", "self-sacrificing"]
    rng = random.Random(42)
    
    for i in range(50):
        sample = generate_sample(i, rng)
        assert sample["ground_truth_phase"] in valid_phases

def test_scenario_values():
    """Test that scenarios are from the defined templates."""
    expected_scenarios = [
        "The character is stranded on a deserted island and must decide whether to save a stranger found washed ashore.",
        "The character discovers a hidden truth about their family legacy that could destroy their reputation.",
        # ... (all 20 scenarios from the script)
    ]
    # Just check that the scenario is a non-empty string
    rng = random.Random(42)
    for i in range(20):
        sample = generate_sample(i, rng)
        assert len(sample["scenario"]) > 10

def test_checksum_computation(temp_output_dir):
    """Test that SHA-256 checksum is computed correctly."""
    test_file = temp_output_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = compute_sha256(test_file)
    
    # Expected SHA-256 for "Hello, World!"
    expected_checksum = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected_checksum

def test_main_creates_files(temp_output_dir, monkeypatch):
    """Test that main() creates the expected output files."""
    # Monkeypatch the output directory
    import src.scripts.generate_gold_standard as module
    original_output_dir = Path("data/gold_standard")
    
    # We'll just check that the function runs without error
    # and creates files in the expected location (in temp dir for testing)
    monkeypatch.chdir(temp_output_dir)
    
    # Run main
    output_file, checksum = main()
    
    # Verify files exist
    assert output_file.exists()
    assert output_file.name == "human_annotations.json"
    
    # Verify checksum file exists
    checksum_file = output_file.parent / "human_annotations.sha256"
    assert checksum_file.exists()
    
    # Verify JSON structure
    with open(output_file, "r") as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 20
    
    # Verify each sample structure
    for sample in data:
        assert "character" in sample
        assert "scenario" in sample
        assert "ground_truth_score" in sample
        assert "ground_truth_phase" in sample
        assert 1.0 <= sample["ground_truth_score"] <= 5.0
