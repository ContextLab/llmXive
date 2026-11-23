"""
Tests for T027: Verify total pipeline memory usage <= 7 GB.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.verify_memory import check_memory_usage, write_resource_usage, MEMORY_LIMIT_GB

def test_write_and_check_memory_within_limit(tmp_path):
    """Test that write_resource_usage and check_memory_usage work correctly when within limit."""
    # Mock the output path
    output_file = tmp_path / "resource_usage.json"
    with patch("code.verify_memory.RESOURCE_USAGE_PATH", output_file):
        # Write a usage within limit
        write_resource_usage(peak_rss_gb=5.0, total_runtime_hours=2.0)

        # Check it returns True
        assert check_memory_usage() is True

        # Verify file contents
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["peak_rss_gb"] == 5.0
        assert data["total_runtime_hours"] == 2.0

def test_check_memory_exceeds_limit(tmp_path):
    """Test that check_memory_usage returns False when limit is exceeded."""
    output_file = tmp_path / "resource_usage.json"
    with patch("code.verify_memory.RESOURCE_USAGE_PATH", output_file):
        write_resource_usage(peak_rss_gb=8.0, total_runtime_hours=2.0)
        assert check_memory_usage() is False

def test_check_memory_missing_file(tmp_path):
    """Test that check_memory_usage returns False if file is missing."""
    output_file = tmp_path / "nonexistent.json"
    with patch("code.verify_memory.RESOURCE_USAGE_PATH", output_file):
        assert check_memory_usage() is False

def test_memory_limit_constant():
    """Verify the memory limit constant is set to 7.0 GB."""
    assert MEMORY_LIMIT_GB == 7.0