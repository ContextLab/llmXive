"""
Unit tests for code/data/fetch_data.py
Verifies that the script exists, is importable, and contains the expected logic structure.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

def test_fetch_data_script_exists():
    """Verify the script file exists."""
    script_path = code_dir / "data" / "fetch_data.py"
    assert script_path.exists(), f"Script {script_path} does not exist."

def test_fetch_data_importable():
    """Verify the script can be imported without errors."""
    try:
        import data.fetch_data
        assert hasattr(data.fetch_data, 'main'), "fetch_data.py must have a main function."
    except ImportError as e:
        pytest.fail(f"Failed to import fetch_data.py: {e}")

def test_fetch_data_logic_structure():
    """Verify the script contains the expected logic components."""
    script_path = code_dir / "data" / "fetch_data.py"
    content = script_path.read_text()

    # Check for required imports
    assert "from data.validate_logs import" in content, "Must import from validate_logs."
    assert "check_logs_exist" in content, "Must use check_logs_exist."
    assert "fetch_voxceleb2_dataset" in content, "Must use fetch_voxceleb2_dataset."
    
    # Check for strict failure logic (no synthetic fallback)
    assert "sys.exit(1)" in content, "Must exit on failure."
    assert "No real source available" in content or "Failed to fetch data" in content, "Must log failure clearly."
    
    # Check for state update
    assert "update_state_with_dataset" in content, "Must update state."

def test_fetch_data_cli_args():
    """Verify the script accepts expected CLI arguments."""
    script_path = code_dir / "data" / "fetch_data.py"
    content = script_path.read_text()
    
    assert "argparse" in content, "Must use argparse."
    assert "--force-fetch" in content, "Must support --force-fetch flag."