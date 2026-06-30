"""
Unit tests for code cleanup and linting utilities (T034).
"""
import pytest
from pathlib import Path
import tempfile
import os

# Import the module under test
# Assuming it's in code/utils/linting_config.py
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.linting_config import (
    check_seed_consistency,
    check_debug_prints,
    REQUIRED_SEED
)

def test_seed_consistency_missing():
    """Test detection of missing seeds in main scripts."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("import random\n# No seed set\n")
        f.flush()
        path = Path(f.name)

    warnings = check_seed_consistency(path)
    assert len(warnings) > 0
    assert any("Missing" in w for w in warnings)
    path.unlink()

def test_seed_consistency_incorrect():
    """Test detection of incorrect seeds."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(f"import random\nrandom.seed(123)\n")
        f.flush()
        path = Path(f.name)

    warnings = check_seed_consistency(path)
    assert len(warnings) > 0
    assert any("Incorrect seed 123" in w for w in warnings)
    path.unlink()

def test_seed_consistency_correct():
    """Test that correct seed passes."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(f"import random\nrandom.seed({REQUIRED_SEED})\n")
        f.flush()
        path = Path(f.name)

    warnings = check_seed_consistency(path)
    # Should not have warnings for correct seed
    assert len(warnings) == 0
    path.unlink()

def test_debug_prints_detected():
    """Test detection of debug prints."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('DEBUG: something')\nprint('Hello')\n")
        f.flush()
        path = Path(f.name)

    issues = check_debug_prints(path)
    assert len(issues) == 1
    assert "DEBUG" in issues[0][1]
    path.unlink()

def test_debug_prints_none():
    """Test that normal prints are not flagged."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello World')\n")
        f.flush()
        path = Path(f.name)

    issues = check_debug_prints(path)
    assert len(issues) == 0
    path.unlink()