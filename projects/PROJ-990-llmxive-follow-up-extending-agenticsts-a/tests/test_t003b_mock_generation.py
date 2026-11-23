"""
Tests for T003b: Generate Mock Trajectories

These tests verify that the mock generator:
1. Refuses to run if DEV_MODE is not set.
2. Produces valid JSONL.
3. Produces data matching the expected schema structure.
"""
import os
import json
import pytest
from pathlib import Path
import subprocess
import sys

# Path to the script
SCRIPT_PATH = Path("code/generate_mock_trajectories.py")
OUTPUT_PATH = Path("data/fixtures/mock_trajectories.jsonl")

@pytest.fixture(autouse=True)
def setup_teardown():
    # Ensure output file doesn't exist before test
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    yield
    # Cleanup after test if file was created
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

def test_fails_without_dev_mode():
    """Verify that the script raises an error if DEV_MODE is not 'true'."""
    # Ensure DEV_MODE is not set or is false
    env = os.environ.copy()
    env.pop("DEV_MODE", None)
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "DEV_MODE" in result.stderr or "DEV_MODE" in result.stdout

def test_succeeds_with_dev_mode():
    """Verify that the script runs successfully when DEV_MODE=true."""
    env = os.environ.copy()
    env["DEV_MODE"] = "true"
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert OUTPUT_PATH.exists(), "Output file was not created"

def test_output_is_valid_jsonl():
    """Verify the output file is valid JSONL and contains records."""
    env = os.environ.copy()
    env["DEV_MODE"] = "true"
    
    subprocess.run([sys.executable, str(SCRIPT_PATH)], env=env, check=True)
    
    assert OUTPUT_PATH.exists()
    
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "Output file is empty"
    
    for i, line in enumerate(lines):
        try:
            record = json.loads(line)
            assert isinstance(record, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Line {i+1} is not valid JSON: {line}")

def test_output_matches_schema_fields():
    """Verify that records contain required fields from the task description."""
    env = os.environ.copy()
    env["DEV_MODE"] = "true"
    
    subprocess.run([sys.executable, str(SCRIPT_PATH)], env=env, check=True)
    
    required_fields = [
        "trajectory_id", "turn", "legal_moves", "win", "loss", "initial_state_hash"
    ]
    
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            for field in required_fields:
                assert field in record, f"Missing required field '{field}' in record: {record}"
            
            # Verify types
            assert isinstance(record["trajectory_id"], str)
            assert isinstance(record["turn"], int)
            assert isinstance(record["legal_moves"], list)
            assert isinstance(record["win"], bool)
            assert isinstance(record["loss"], bool)
            assert isinstance(record["initial_state_hash"], str)