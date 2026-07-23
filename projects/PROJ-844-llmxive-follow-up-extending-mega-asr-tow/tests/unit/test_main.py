import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from main import pre_flight_data_check, get_config

def test_pre_flight_data_check_missing_dirs():
    """Test pre-flight check with missing directories."""
    config = get_config()
    # Temporarily modify config to point to non-existent dirs
    config["paths"]["data_raw"] = "/tmp/llmxive_test_nonexistent_raw"
    config["paths"]["data_derived"] = "/tmp/llmxive_test_nonexistent_derived"
    config["paths"]["data_validation"] = "/tmp/llmxive_test_nonexistent_validation"
    
    # This should create the directories, so we expect True
    result = pre_flight_data_check(config)
    assert result is True  # It creates them if missing
    
    # Clean up
    for p in [config["paths"]["data_raw"], config["paths"]["data_derived"], config["paths"]["data_validation"]]:
        if os.path.exists(p):
            os.rmdir(p)

def test_pre_flight_data_check_existing_dirs():
    """Test pre-flight check with existing directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = get_config()
        config["paths"]["data_raw"] = tmpdir
        config["paths"]["data_derived"] = tmpdir
        config["paths"]["data_validation"] = tmpdir
        
        result = pre_flight_data_check(config)
        assert result is True
