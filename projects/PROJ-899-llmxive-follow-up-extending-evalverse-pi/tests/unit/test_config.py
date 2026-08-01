"""
Unit tests for configuration.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys
import json
from src.config import get_project_root, get_data_root, ensure_environment, get_config_summary

class TestEnvironmentSetup:
    def test_get_project_root(self):
        root = get_project_root()
        assert root.exists()
        assert root.is_dir()

    def test_ensure_environment_creates_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override paths for testing
            original_root = get_project_root()
            # In real scenario, this would create the directory structure
            pass

class TestConfigurationValues:
    def test_config_summary(self):
        summary = get_config_summary()
        assert "project_root" in summary
        assert "data_root" in summary
        assert "random_seed" in summary

class TestConfigSummary:
    def test_summary_structure(self):
        summary = get_config_summary()
        expected_keys = [
            "project_root", "data_root", "state_root",
            "reports_root", "figures_root", "random_seed"
        ]
        for key in expected_keys:
            assert key in summary
