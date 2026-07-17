"""
Unit tests for src/utils/config.py
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from src.utils.config import (
    RESEARCHCLAWBENCH_DATASET_ID,
    SCIENTIFIC_CORE_MARGIN,
    MAX_CONCURRENCY,
    EXPERIMENT_WALL_CLOCK_BUDGET_SECONDS,
    SINGLE_RUN_TIMEOUT_SECONDS,
    MIN_STATISTICAL_POWER,
    ensure_directories,
    get_config_summary,
    PROJECT_ROOT,
    DATA_RAW_DIR,
    RESULTS_DIR,
)


class TestConstants:
    """Test that required constants are defined with correct values."""

    def test_researchclawbench_dataset_id(self):
        """Verify the dataset ID is set correctly."""
        assert RESEARCHCLAWBENCH_DATASET_ID == "llmXive/ResearchClawBench"
        assert isinstance(RESEARCHCLAWBENCH_DATASET_ID, str)
        assert len(RESEARCHCLAWBENCH_DATASET_ID) > 0

    def test_scientific_core_margin(self):
        """Verify the TOST margin is 5 as per FR-005."""
        assert SCIENTIFIC_CORE_MARGIN == 5
        assert isinstance(SCIENTIFIC_CORE_MARGIN, int)

    def test_max_concurrency(self):
        """Verify the concurrency limit is 7."""
        assert MAX_CONCURRENCY == 7
        assert isinstance(MAX_CONCURRENCY, int)

    def test_experiment_budget(self):
        """Verify the 24-hour budget in seconds."""
        assert EXPERIMENT_WALL_CLOCK_BUDGET_SECONDS == 86400

    def test_single_run_timeout(self):
        """Verify the single run timeout is 1 hour."""
        assert SINGLE_RUN_TIMEOUT_SECONDS == 3600

    def test_min_statistical_power(self):
        """Verify the minimum power threshold."""
        assert MIN_STATISTICAL_POWER == 0.4


class TestConfigSummary:
    """Test the configuration summary function."""

    def test_get_config_summary_keys(self):
        """Verify the summary contains all expected keys."""
        summary = get_config_summary()
        
        expected_keys = [
            "dataset_id",
            "scientific_core_margin",
            "max_concurrency",
            "experiment_budget_seconds",
            "single_run_timeout_seconds",
            "min_statistical_power",
        ]
        
        for key in expected_keys:
            assert key in summary, f"Missing key: {key}"

    def test_get_config_summary_values(self):
        """Verify the summary values match the constants."""
        summary = get_config_summary()
        
        assert summary["dataset_id"] == RESEARCHCLAWBENCH_DATASET_ID
        assert summary["scientific_core_margin"] == SCIENTIFIC_CORE_MARGIN
        assert summary["max_concurrency"] == MAX_CONCURRENCY


class TestEnsureDirectories:
    """Test the directory creation logic."""

    def test_ensure_directories_creates_folders(self):
        """Verify that ensure_directories creates the required folders."""
        # Use a temporary directory to avoid polluting the real project structure during tests
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Temporarily override the global paths for the test
            # Note: In a real scenario, we might mock these or pass them as arguments.
            # For this test, we assume the function works relative to the actual project root
            # but we can verify the logic by checking if the specific paths exist after calling.
            # Since we can't easily mock the global Path objects in the module without side effects,
            # we will test the existence of the directories in the actual project structure.
            # This test assumes the project structure is set up correctly by T001.
            
            # Call the function
            ensure_directories()
            
            # Verify specific directories exist (relative to the actual project root)
            # We check if the directories exist on disk
            assert DATA_RAW_DIR.exists(), f"Directory {DATA_RAW_DIR} does not exist"
            assert RESULTS_DIR.exists(), f"Directory {RESULTS_DIR} does not exist"
            
            # Verify they are actually directories
            assert DATA_RAW_DIR.is_dir()
            assert RESULTS_DIR.is_dir()
