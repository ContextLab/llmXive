"""
Unit tests for the config module.
Verifies path existence and constant values.
"""
import pytest
import os
from pathlib import Path
import sys

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from config import (
    DATA_RAW_PATH,
    DATA_INTERIM_PATH,
    DATA_PROCESSED_PATH,
    DATA_FINAL_PATH,
    DATASET_HF_ID,
    DATASET_COMMIT_HASH,
    GLOBAL_SEED,
    PLANNING_TIMEOUT_SECONDS,
    MAX_RAM_USAGE_GB,
    get_config_summary
)


class TestConfigConstants:
    """Test that configuration constants are set correctly."""

    def test_dataset_hf_id(self):
        assert DATASET_HF_ID == "RoboDojo/RoboDojo-v1"

    def test_dataset_commit_hash(self):
        assert DATASET_COMMIT_HASH == "v.1"

    def test_global_seed(self):
        assert GLOBAL_SEED == 42

    def test_planning_timeout(self):
        assert PLANNING_TIMEOUT_SECONDS == 60

    def test_max_ram_usage(self):
        assert MAX_RAM_USAGE_GB == 6

    def test_config_summary_structure(self):
        summary = get_config_summary()
        assert isinstance(summary, dict)
        assert "dataset_id" in summary
        assert "commit_hash" in summary
        assert "global_seed" in summary
        assert summary["dataset_id"] == DATASET_HF_ID
        assert summary["commit_hash"] == DATASET_COMMIT_HASH


class TestPathHelpers:
    """Test that path constants resolve to valid Path objects and directories exist."""

    def test_data_raw_path_exists(self):
        assert DATA_RAW_PATH.exists()
        assert DATA_RAW_PATH.is_dir()

    def test_data_interim_path_exists(self):
        assert DATA_INTERIM_PATH.exists()
        assert DATA_INTERIM_PATH.is_dir()

    def test_data_processed_path_exists(self):
        assert DATA_PROCESSED_PATH.exists()
        assert DATA_PROCESSED_PATH.is_dir()

    def test_data_final_path_exists(self):
        assert DATA_FINAL_PATH.exists()
        assert DATA_FINAL_PATH.is_dir()

    def test_paths_are_absolute(self):
        assert DATA_RAW_PATH.is_absolute()
        assert DATA_INTERIM_PATH.is_absolute()
        assert DATA_PROCESSED_PATH.is_absolute()
        assert DATA_FINAL_PATH.is_absolute()


class TestValidation:
    """Test validation logic if any is added to config."""

    def test_seed_is_integer(self):
        assert isinstance(GLOBAL_SEED, int)

    def test_timeout_is_positive(self):
        assert PLANNING_TIMEOUT_SECONDS > 0

    def test_ram_limit_is_positive(self):
        assert MAX_RAM_USAGE_GB > 0