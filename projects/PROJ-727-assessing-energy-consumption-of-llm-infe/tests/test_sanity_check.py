"""
Tests for the sanity check module (T031).
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.sanity_check import check_plot_content


def test_check_plot_content_file_not_found():
    """Test that check_plot_content returns False for missing file."""
    result = check_plot_content("/nonexistent/path/plot.png")
    assert result is False


def test_check_plot_content_empty_file():
    """Test that check_plot_content returns False for empty file."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
        # File is created empty
    
    try:
        result = check_plot_content(tmp_path)
        assert result is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_check_plot_content_valid_file():
    """Test that check_plot_content returns True for a valid non-empty file."""
    # Create a dummy valid PNG (minimal valid PNG header + some data)
    # A real minimal PNG is complex, so we just write a non-empty file
    # and trust the size check.
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(b'\x89PNG\r\n\x1a\n') # PNG header
        tmp.write(b'fake png data')
        tmp_path = tmp.name
    
    try:
        result = check_plot_content(tmp_path)
        assert result is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)