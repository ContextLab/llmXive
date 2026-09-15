"""
Unit tests for src/lib/config.py constants and paths.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure the code/src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from lib import config

class TestConfigConstants:
    """Test that resource limits and constants are defined correctly."""

    def test_memory_limit_gb_is_7(self):
        assert config.MEMORY_LIMIT_GB == 7.0

    def test_memory_limit_bytes_is_correct(self):
        expected = int(7.0 * 1024**3)
        assert config.MEMORY_LIMIT_BYTES == expected

    def test_timeout_seconds_defined(self):
        assert config.TIMEOUT_SECONDS > 0

    def test_max_records_limit(self):
        assert config.MAX_RECORDS == 500

    def test_min_sample_size(self):
        assert config.MIN_SAMPLE_SIZE == 30

    def test_model_name(self):
        assert config.MODEL_NAME == "distilbert-base-uncased"

    def test_random_seed(self):
        assert config.RANDOM_SEED == 42

class TestConfigPaths:
    """Test that path constants are valid Path objects and exist."""

    def test_project_root_exists(self):
        assert config.PROJECT_ROOT.exists()
        assert config.PROJECT_ROOT.is_dir()

    def test_data_root_exists(self):
        assert config.DATA_ROOT.exists()

    def test_results_root_exists(self):
        assert config.RESULTS_ROOT.exists()

    def test_tool_mapping_file_path(self):
        assert isinstance(config.TOOL_MAPPING_FILE, Path)
        # We don't assert it exists here as it might be generated later, 
        # but the path construction must be correct.

    def test_ensure_dirs_creates_folders(self):
        # Temporarily test creation of a new folder
        test_folder = config.PROJECT_ROOT / "test_temp_dir"
        try:
            if test_folder.exists():
                test_folder.rmdir()
            config.ensure_dirs()
            # ensure_dirs should create standard folders
            assert config.DATA_ROOT.exists()
        finally:
            if test_folder.exists():
                test_folder.rmdir()

class TestConfigFunctions:
    """Test helper functions in config."""

    def test_get_path_resolves_correctly(self):
        relative = "data/raw"
        resolved = config.get_path(relative)
        expected = config.PROJECT_ROOT / relative
        assert resolved == expected

    def test_ensure_dirs_no_error(self):
        # Should not raise
        config.ensure_dirs()