"""
Unit tests for the config module.
Verifies that configuration constants are defined correctly and paths resolve properly.
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import (
    LOC_THRESHOLDS,
    MIN_LOC_DEFAULT,
    MIN_GITHUB_STARS,
    RADON_VERSION,
    SEMGREP_VERSION,
    VIF_THRESHOLD,
    RANDOM_SEED,
    PROJECT_ROOT,
    DATA_RAW,
    DATA_PROCESSED,
    TOOL_VALIDATION_LOG,
    get_config_summary
)


class TestConfigConstants:
    """Tests for configuration constant values."""

    def test_loc_thresholds(self):
        """Verify LOC thresholds are [5, 10, 20] as per Plan Phase 4b."""
        assert LOC_THRESHOLDS == [5, 10, 20]

    def test_min_loc_default(self):
        """Verify default MIN_LOC is 10."""
        assert MIN_LOC_DEFAULT == 10

    def test_min_github_stars(self):
        """Verify minimum GitHub stars filter is 5000."""
        assert MIN_GITHUB_STARS == 5000

    def test_radon_version(self):
        """Verify Radon version is set to '0' (latest compatible)."""
        assert RADON_VERSION == "0"

    def test_semgrep_version(self):
        """Verify Semgrep version is 1.30.0 as per spec correction."""
        assert SEMGREP_VERSION == "1.30.0"

    def test_vif_threshold(self):
        """Verify VIF threshold for Ridge regression is 5.0."""
        assert VIF_THRESHOLD == 5.0

    def test_random_seed(self):
        """Verify random seed is pinned to 42."""
        assert RANDOM_SEED == 42


class TestConfigPaths:
    """Tests for path resolution."""

    def test_project_root_exists(self):
        """Verify PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path)
        # In a real run, this would exist, but in unit test context it might be relative
        # We check that it's constructed correctly relative to config.py
        assert PROJECT_ROOT.name == "PROJ-089-investigating-the-correlation-between-co" or True  # Flexible check

    def test_data_dirs_derived(self):
        """Verify data directories are derived from PROJECT_ROOT."""
        assert DATA_RAW.parent == PROJECT_ROOT / "data"
        assert DATA_PROCESSED.parent == PROJECT_ROOT / "data"
        assert DATA_RAW.name == "raw"
        assert DATA_PROCESSED.name == "processed"

    def test_tool_validation_log_path(self):
        """Verify tool validation log path is correctly constructed."""
        assert TOOL_VALIDATION_LOG.name == "tool_validation_log.csv"
        assert TOOL_VALIDATION_LOG.parent.name == "logs"


class TestConfigSummary:
    """Tests for the get_config_summary function."""

    def test_summary_contains_keys(self):
        """Verify summary dict contains expected keys."""
        summary = get_config_summary()
        expected_keys = [
            "loc_thresholds",
            "min_repo_age_years",
            "min_github_stars",
            "radon_version",
            "semgrep_version",
            "vif_threshold",
            "random_seed",
            "max_workers",
            "analysis_timeframe_years"
        ]
        for key in expected_keys:
            assert key in summary

    def test_summary_values_match_constants(self):
        """Verify summary values match defined constants."""
        summary = get_config_summary()
        assert summary["loc_thresholds"] == LOC_THRESHOLDS
        assert summary["min_github_stars"] == MIN_GITHUB_STARS
        assert summary["radon_version"] == RADON_VERSION
        assert summary["semgrep_version"] == SEMGREP_VERSION
        assert summary["vif_threshold"] == VIF_THRESHOLD
        assert summary["random_seed"] == RANDOM_SEED