"""
Unit tests to validate the existence and content of documentation artifacts for Task T034b.
"""
import os
import pytest
from pathlib import Path

# Project root relative to tests
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

class TestDocumentationArtifacts:
    """Tests to ensure T034b artifacts exist and contain required content."""

    def test_analysis_api_exists(self):
        """Verify that docs/analysis_api.md exists."""
        api_path = DOCS_DIR / "analysis_api.md"
        assert api_path.exists(), f"API documentation not found at {api_path}"

    def test_analysis_api_content(self):
        """Verify that docs/analysis_api.md contains required sections."""
        api_path = DOCS_DIR / "analysis_api.md"
        content = api_path.read_text()

        required_sections = [
            "Module Overview",
            "Functions",
            "fit_lmm_variability",
            "fit_lmm_mean",
            "run_lopo_cv",
            "run_sensitivity_single_rating_bootstrap",
            "Dependencies"
        ]

        for section in required_sections:
            assert section in content, f"Missing section '{section}' in analysis_api.md"

    def test_data_dictionary_exists(self):
        """Verify that docs/data_dictionary_daily_aggregates.md exists."""
        dict_path = DOCS_DIR / "data_dictionary_daily_aggregates.md"
        assert dict_path.exists(), f"Data dictionary not found at {dict_path}"

    def test_data_dictionary_content(self):
        """Verify that docs/data_dictionary_daily_aggregates.md contains required content."""
        dict_path = DOCS_DIR / "data_dictionary_daily_aggregates.md"
        content = dict_path.read_text()

        required_columns = [
            "participant_id",
            "date",
            "total_steps",
            "mean_mood",
            "mood_std",
            "n_mood_ratings",
            "sleep_duration",
            "baseline_affect",
            "day_of_week"
        ]

        required_sections = [
            "Column Definitions",
            "Data Generation Logic",
            "Constraints & Validation"
        ]

        for col in required_columns:
            assert col in content, f"Missing column '{col}' in data dictionary"

        for section in required_sections:
            assert section in content, f"Missing section '{section}' in data dictionary"

    def test_flake8_config_exists(self):
        """Verify that code/.flake8 exists with correct configuration."""
        flake8_path = PROJECT_ROOT / "code" / ".flake8"
        assert flake8_path.exists(), f".flake8 config not found at {flake8_path}"

        content = flake8_path.read_text()
        assert "[flake8]" in content, "Missing [flake8] section in .flake8"
        assert "max-line-length = 88" in content, "Missing or incorrect max-line-length"
        assert "ignore = E203, E266, W503" in content, "Missing or incorrect ignore list"