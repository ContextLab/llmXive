import os
import pytest
import tempfile
from pathlib import Path
import yaml

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils import (
    check_halt_signal,
    write_halt_signal,
    ensure_state_dir,
    calculate_exclusion_ratio,
    enforce_exclusion_ratio_threshold,
    calculate_processing_success_rate,
    enforce_success_rate_threshold,
    check_sample_size_power_analysis
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_check_halt_signal_no_signal(temp_state_dir):
    """Test check_halt_signal returns False when no signal exists."""
    assert check_halt_signal(temp_state_dir) is False

def test_check_halt_signal_with_signal(temp_state_dir):
    """Test check_halt_signal returns True when signal exists."""
    write_halt_signal(temp_state_dir, "Test halt reason")
    assert check_halt_signal(temp_state_dir) is True

def test_check_halt_signal_default_path(monkeypatch):
    """Test check_halt_signal with default path."""
    # Create a temporary directory and set as default state
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a halt signal
        write_halt_signal(tmpdir)
        
        # Mock os.path.exists to return True for our test
        original_exists = os.path.exists
        def mock_exists(path):
            if path.endswith("HALT_SIGNAL.yaml"):
                return True
            return original_exists(path)
        
        monkeypatch.setattr(os.path, 'exists', mock_exists)
        assert check_halt_signal() is True

def test_check_halt_signal_signature_positional(temp_state_dir):
    """Test check_halt_signal accepts positional argument."""
    write_halt_signal(temp_state_dir)
    assert check_halt_signal(temp_state_dir) is True

def test_check_halt_signal_signature_keyword(temp_state_dir):
    """Test check_halt_signal accepts keyword argument."""
    write_halt_signal(temp_state_dir)
    assert check_halt_signal(state_dir=temp_state_dir) is True

def test_write_halt_signal_creates_file(temp_state_dir):
    """Test write_halt_signal creates the correct file."""
    write_halt_signal(temp_state_dir, "Test reason")
    
    halt_file = os.path.join(temp_state_dir, "HALT_SIGNAL.yaml")
    assert os.path.exists(halt_file)
    
    with open(halt_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["halt"] is True
    assert data["reason"] == "Test reason"

def test_ensure_state_dir_creates_directory(temp_state_dir):
    """Test ensure_state_dir creates the directory if it doesn't exist."""
    new_dir = os.path.join(temp_state_dir, "new_state")
    assert not os.path.exists(new_dir)
    
    ensure_state_dir(new_dir)
    assert os.path.exists(new_dir)

def test_calculate_exclusion_ratio():
    """Test exclusion ratio calculation."""
    assert calculate_exclusion_ratio(100, 10) == 0.1
    assert calculate_exclusion_ratio(1000, 0) == 0.0
    assert calculate_exclusion_ratio(0, 0) == 0.0

def test_enforce_exclusion_ratio_threshold():
    """Test exclusion ratio threshold enforcement."""
    assert enforce_exclusion_ratio_threshold(0.05, 0.1) is True
    assert enforce_exclusion_ratio_threshold(0.15, 0.1) is False
    assert enforce_exclusion_ratio_threshold(0.1, 0.1) is True

def test_calculate_processing_success_rate():
    """Test processing success rate calculation."""
    assert calculate_processing_success_rate(100, 95) == 0.95
    assert calculate_processing_success_rate(100, 100) == 1.0
    assert calculate_processing_success_rate(0, 0) == 0.0

def test_enforce_success_rate_threshold():
    """Test success rate threshold enforcement."""
    assert enforce_success_rate_threshold(0.95, 0.95) is True
    assert enforce_success_rate_threshold(0.90, 0.95) is False
    assert enforce_success_rate_threshold(0.96, 0.95) is True

def test_check_sample_size_power_analysis():
    """Test power analysis check."""
    assert check_sample_size_power_analysis(1000) is True
    assert check_sample_size_power_analysis(1001) is True
    assert check_sample_size_power_analysis(999) is False
    assert check_sample_size_power_analysis(500) is False