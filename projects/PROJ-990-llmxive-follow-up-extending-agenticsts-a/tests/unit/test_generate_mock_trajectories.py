"""
Unit tests for T003b: Generate Mock Trajectories
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import hashlib

# Mock the environment variable for testing
@pytest.fixture
def dev_mode_enabled():
    original = os.environ.get('DEV_MODE')
    os.environ['DEV_MODE'] = 'true'
    yield
    if original is None:
        os.environ.pop('DEV_MODE', None)
    else:
        os.environ['DEV_MODE'] = original

@pytest.fixture
def dev_mode_disabled():
    original = os.environ.get('DEV_MODE')
    os.environ.pop('DEV_MODE', None)
    yield
    if original is not None:
        os.environ['DEV_MODE'] = original

def test_dev_mode_check_enabled(dev_mode_enabled):
    """Test that check_dev_mode passes when DEV_MODE=true"""
    from generate_mock_trajectories import check_dev_mode
    # Should not raise
    result = check_dev_mode()
    assert result is True

def test_dev_mode_check_disabled(dev_mode_disabled):
    """Test that check_dev_mode raises when DEV_MODE is not true"""
    from generate_mock_trajectories import check_dev_mode
    with pytest.raises(RuntimeError, match="DEV_MODE is not set to 'true'"):
        check_dev_mode()

def test_hash_generation():
    """Test deterministic hash generation"""
    from generate_mock_trajectories import generate_hash
    seed = "test_seed_123"
    h1 = generate_hash(seed)
    h2 = generate_hash(seed)
    assert h1 == h2
    assert len(h1) == 64  # SHA256 hex length

def test_mock_trajectory_structure(dev_mode_enabled, tmp_path):
    """Test that generated mock trajectories have the correct structure"""
    # We need to temporarily override the output path or create a mock
    # Since the function creates the file, we'll test the logic by importing
    # and checking the generated content if we can intercept it.
    
    # Instead, let's test the create_mock_trajectories function logic directly
    # by mocking the file write or just checking the data structure.
    from generate_mock_trajectories import create_mock_trajectories, load_schema_fields
    
    # Mock schema fields to ensure we have expected fields
    import generate_mock_trajectories as gm
    original_load = gm.load_schema_fields
    gm.load_schema_fields = lambda: [
        "trajectory_id", "turn", "legal_moves", "win", "loss", 
        "initial_state_hash", "layer_utility", "context_tokens"
    ]
    
    try:
        data = create_mock_trajectories()
        assert len(data) > 0
        
        for record in data:
            assert "trajectory_id" in record
            assert "turn" in record
            assert "legal_moves" in record
            assert "win" in record
            assert "loss" in record
            assert "initial_state_hash" in record
            assert isinstance(record["legal_moves"], list)
            assert isinstance(record["win"], bool)
            assert isinstance(record["loss"], bool)
            assert len(record["initial_state_hash"]) == 64
    finally:
        gm.load_schema_fields = original_load

def test_main_execution(dev_mode_enabled, tmp_path):
    """Test the main function execution"""
    from generate_mock_trajectories import main
    import sys
    
    # Create a temporary directory for output
    test_output_dir = tmp_path / "data" / "fixtures"
    test_output_dir.mkdir(parents=True)
    
    # We need to patch the output path in the module or run it in a way
    # that uses our temp dir. Since the module hardcodes "data/fixtures",
    # we will just verify the logic by checking if the file would be created
    # if we change the working directory or if we mock the path.
    
    # For this test, we'll just ensure the function returns 0 when DEV_MODE is true
    # and the directory can be created.
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # The module uses relative paths, so changing cwd affects it
        result = main()
        assert result == 0
        
        # Check if file was created
        output_file = tmp_path / "data" / "fixtures" / "mock_trajectories.jsonl"
        assert output_file.exists()
        
        # Validate content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            for line in lines:
                record = json.loads(line)
                assert "trajectory_id" in record
    finally:
        os.chdir(original_cwd)