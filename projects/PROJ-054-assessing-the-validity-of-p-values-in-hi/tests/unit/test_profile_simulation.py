"""
Unit tests for profile_simulation.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from profile_simulation import get_memory_usage_mb, write_profile_report, MAX_RUNTIME_SECONDS


class TestGetMemoryUsage:
    def test_get_memory_usage_mb_returns_positive(self):
        """Test that memory usage is a positive number."""
        memory = get_memory_usage_mb()
        assert memory >= 0, "Memory usage should be non-negative"
        assert isinstance(memory, float), "Memory usage should be a float"


class TestWriteProfileReport:
    def test_write_profile_report_creates_file(self):
        """Test that write_profile_report creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "profile_test.json")
            test_results = {
                'total_params': 5,
                'completed_params': 5,
                'failed_params': 0,
                'total_runtime_seconds': 100.0,
                'max_memory_mb': 500.0,
                'status': 'completed',
                'compliant': True
            }

            write_profile_report(test_results, output_path)

            assert os.path.exists(output_path), "Output file should exist"
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == test_results, "Loaded results should match input"

    def test_write_profile_report_with_nested_data(self):
        """Test writing profile report with nested parameter results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "profile_nested.json")
            test_results = {
                'total_params': 2,
                'completed_params': 2,
                'failed_params': 0,
                'param_results': [
                    {'seed': 0, 'n': 500, 'p': 500, 'rho': 0.0, 'ks_statistic': 0.05, 'status': 'success'},
                    {'seed': 1, 'n': 1000, 'p': 500, 'rho': 0.3, 'ks_statistic': 0.08, 'status': 'success'}
                ],
                'total_runtime_seconds': 150.0,
                'max_memory_mb': 750.0,
                'status': 'completed',
                'compliant': True
            }

            write_profile_report(test_results, output_path)

            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded['param_results']) == 2
            assert loaded['param_results'][0]['seed'] == 0
            assert loaded['param_results'][1]['ks_statistic'] == 0.08


class TestMaxRuntimeConstant:
    def test_max_runtime_is_six_hours(self):
        """Verify MAX_RUNTIME_SECONDS is set to 6 hours (21600 seconds)."""
        assert MAX_RUNTIME_SECONDS == 6 * 60 * 60, \
            "MAX_RUNTIME_SECONDS should be 21600 (6 hours)"
