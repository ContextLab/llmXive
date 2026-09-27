"""Unit tests for verify_runtime.py (T028)."""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from verify_runtime import load_resource_usage, verify_runtime


class TestLoadResourceUsage:
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing resource usage file."""
        resource_file = tmp_path / "resource_usage.json"
        expected_data = {
            "peak_rss_gb": 3.5,
            "total_runtime_hours": 4.2
        }
        
        with open(resource_file, "w") as f:
            json.dump(expected_data, f)
        
        result = load_resource_usage(str(resource_file))
        assert result == expected_data
        assert result["total_runtime_hours"] == 4.2

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_resource_usage(str(missing_file))

    def test_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_resource_usage(str(invalid_file))


class TestVerifyRuntime:
    def test_runtime_within_limit(self):
        """Test verification passes when runtime is within limit."""
        resource_data = {
            "peak_rss_gb": 3.5,
            "total_runtime_hours": 5.5
        }
        
        result = verify_runtime(resource_data, max_hours=6.0)
        assert result is True

    def test_runtime_exactly_at_limit(self):
        """Test verification passes when runtime is exactly at limit."""
        resource_data = {
            "peak_rss_gb": 3.5,
            "total_runtime_hours": 6.0
        }
        
        result = verify_runtime(resource_data, max_hours=6.0)
        assert result is True

    def test_runtime_exceeds_limit(self):
        """Test verification fails when runtime exceeds limit."""
        resource_data = {
            "peak_rss_gb": 3.5,
            "total_runtime_hours": 6.5
        }
        
        result = verify_runtime(resource_data, max_hours=6.0)
        assert result is False

    def test_missing_runtime_key(self):
        """Test that ValueError is raised when runtime key is missing."""
        resource_data = {
            "peak_rss_gb": 3.5
            # missing total_runtime_hours
        }
        
        with pytest.raises(ValueError):
            verify_runtime(resource_data)

    def test_zero_runtime(self):
        """Test verification passes with zero runtime."""
        resource_data = {
            "peak_rss_gb": 0.0,
            "total_runtime_hours": 0.0
        }
        
        result = verify_runtime(resource_data, max_hours=6.0)
        assert result is True

    def test_very_large_runtime(self):
        """Test verification fails with very large runtime."""
        resource_data = {
            "peak_rss_gb": 10.0,
            "total_runtime_hours": 24.0
        }
        
        result = verify_runtime(resource_data, max_hours=6.0)
        assert result is False
