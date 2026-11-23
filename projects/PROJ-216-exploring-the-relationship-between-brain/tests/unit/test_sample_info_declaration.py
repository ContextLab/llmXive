import os
import json
import pytest
from pathlib import Path

# Import the function we are testing
from code.download import write_sample_info, main

def test_write_sample_info_creates_file(tmp_path, monkeypatch):
    """Test that write_sample_info creates the required JSON file."""
    # Change to temp directory to avoid polluting project root in tests
    monkeypatch.chdir(tmp_path)
    
    subjects = [
        {"id": "sub-01", "age": 25, "gender": "M", "fluid_intelligence_score": 105.0}
    ]
    
    write_sample_info(subjects, 10, "test_method", seed=123)
    
    output_path = Path('data/processed/sample_info.json')
    assert output_path.exists(), "sample_info.json should be created"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['total_available'] == 10
    assert data['subjects_used'] == 1
    assert data['sampling_method'] == 'test_method'
    assert data['seed'] == 123

def test_sample_info_schema(tmp_path, monkeypatch):
    """Verify the schema of sample_info.json matches requirements."""
    monkeypatch.chdir(tmp_path)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    subjects = [{"id": "s1"}]
    write_sample_info(subjects, 5, "random", seed=99)
    
    with open('data/processed/sample_info.json', 'r') as f:
        data = json.load(f)
    
    required_keys = ['total_available', 'subjects_used', 'sampling_method', 'seed']
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"

def test_main_creates_sample_info_in_test_mode(tmp_path, monkeypatch):
    """Test that main() creates sample_info.json when in test mode."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('TASKER_TEST_MODE', 'true')
    
    # Mock sys.argv to simulate command line call
    import sys
    original_argv = sys.argv
    sys.argv = ['download.py', '--sample-size', '5']
    
    try:
        main()
    finally:
        sys.argv = original_argv
    
    output_path = Path('data/processed/sample_info.json')
    assert output_path.exists(), "sample_info.json should be created by main() in test mode"