import pytest
import os
import sys
import logging
from pathlib import Path
import tempfile
import shutil

# Adjust path to allow imports from code/
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging import log_counterbalance_strategy, get_log_path
from config import get_project_root, ensure_directories

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for testing log files."""
    temp_dir = tempfile.mkdtemp()
    original_root = os.environ.get("PROJECT_ROOT")
    os.environ["PROJECT_ROOT"] = temp_dir
    yield temp_dir
    if original_root:
        os.environ["PROJECT_ROOT"] = original_root
    else:
        os.environ.pop("PROJECT_ROOT", None)
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_log_counterbalance_strategy_creates_file(temp_log_dir):
    """Test that log_counterbalance_strategy creates the log file with correct content."""
    seed = 42
    split_ratio = 0.5
    log_filename = "test_strategy.log"
    
    log_counterbalance_strategy(seed, split_ratio, output_file=log_filename)
    
    log_path = Path(temp_log_dir) / "logs" / log_filename
    assert log_path.exists(), f"Log file {log_path} was not created."
    
    content = log_path.read_text()
    assert f"Random Seed: {seed}" in content, "Seed not found in log content."
    assert f"Split Ratio: {split_ratio:.4f}" in content, "Split ratio not found in log content."
    assert "Counterbalancing Strategy Log" in content, "Header not found in log content."
    assert "Seeded random shuffle" in content, "Method description not found in log content."

def test_log_counterbalance_strategy_default_file(temp_log_dir):
    """Test that log_counterbalance_strategy creates the default log file."""
    seed = 123
    split_ratio = 0.5
    
    log_counterbalance_strategy(seed, split_ratio)
    
    # Default file is counterbalance_strategy.log
    log_path = Path(temp_log_dir) / "logs" / "counterbalance_strategy.log"
    assert log_path.exists(), f"Default log file {log_path} was not created."
    
    content = log_path.read_text()
    assert f"Random Seed: {seed}" in content

def test_log_counterbalance_strategy_format(temp_log_dir):
    """Test that the log file contains the expected format."""
    seed = 999
    split_ratio = 0.49
    log_filename = "format_test.log"
    
    log_counterbalance_strategy(seed, split_ratio, output_file=log_filename)
    
    log_path = Path(temp_log_dir) / "logs" / log_filename
    content = log_path.read_text()
    
    # Check for key sections
    assert "Random Seed:" in content
    assert "Split Ratio:" in content
    assert "Method:" in content
    assert "Assignment File:" in content
    
    # Check that the ratio is formatted to 4 decimal places
    assert f"Split Ratio: {split_ratio:.4f}" in content