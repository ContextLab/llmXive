"""
tests/unit/test_main_pipeline.py
Unit tests for the main pipeline orchestration.
"""
import pytest
import sys
from pathlib import Path

# Add code dir to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_imports():
    """Test that all pipeline imports resolve correctly."""
    try:
        from main_pipeline import run_pipeline, main
        from utils.logger import setup_logging, get_logger
        # If imports succeed, the skeleton is valid
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_logger_setup():
    """Test that logging setup does not crash."""
    from utils.logger import setup_logging
    # Should not raise
    setup_logging()
    assert True
