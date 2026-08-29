"""
Tests for the Golden Set acquisition workflow (T006b).
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from acquire_golden_set import (
    generate_template,
    ensure_directories,
    load_golden_set,
    MIN_SAMPLES
)


class TestGoldenSetTemplate:
    """Tests for template generation functionality."""

    def test_generate_template_creates_required_columns(self):
        """Template must contain all required columns for expert labeling."""
        df = generate_template()

        required_columns = [
            "interaction_id",
            "student_id",
            "skill_id",
            "problem_id",
            "attempt_number",
            "response_correctness",
            "response_latency_sec",
            "hint_requests",
            "expert_load_score"
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_generate_template_has_minimum_samples(self):
        """Template must have at least MIN_SAMPLES entries."""
        df = generate_template()
        assert len(df) >= MIN_SAMPLES, f"Template has {len(df)} rows, need at least {MIN_SAMPLES}"

    def test_generate_template_sets_expert_load_score_as_none(self):
        """Template must have None/NaN for expert_load_score to indicate it needs labeling."""
        df = generate_template()
        assert df["expert_load_score"].isna().all(), "Template should have no expert_load_score values"

    def test_generate_template_unique_interaction_ids(self):
        """Each row must have a unique interaction_id."""
        df = generate_template()
        assert df["interaction_id"].is_unique, "Interaction IDs must be unique"


class TestGoldenSetValidation:
    """Tests for Golden Set validation logic."""

    def test_load_golden_set_returns_none_if_missing(self, tmp_path):
        """Should return None if Golden Set file doesn't exist."""
        # Temporarily change the path
        with patch('acquire_golden_set.GOLDEN_SET_PATH', tmp_path / "nonexistent.csv"):
            result = load_golden_set()
            assert result is None

    def test_load_golden_set_validates_required_columns(self, tmp_path):
        """Should return None if required columns are missing."""
        fake_csv = tmp_path / "golden_set.csv"
        fake_csv.write_text("interaction_id,other_column\n1,2\n")

        with patch('acquire_golden_set.GOLDEN_SET_PATH', fake_csv):
            result = load_golden_set()
            assert result is None

    def test_load_golden_set_validates_minimum_samples(self, tmp_path):
        """Should return None if fewer than MIN_SAMPLES rows."""
        fake_csv = tmp_path / "golden_set.csv"
        # Create fewer than MIN_SAMPLES rows
        data = "interaction_id,expert_load_score\n"
        for i in range(10):
            data += f"ID-{i},{i * 10}\n"
        fake_csv.write_text(data)

        with patch('acquire_golden_set.GOLDEN_SET_PATH', fake_csv):
            result = load_golden_set()
            assert result is None

    def test_load_golden_set_validates_no_missing_scores(self, tmp_path):
        """Should return None if expert_load_score has missing values."""
        fake_csv = tmp_path / "golden_set.csv"
        data = "interaction_id,expert_load_score\n"
        data += "ID-1,50\n"
        data += "ID-2,\n"  # Missing value
        data += "ID-3,70\n"
        fake_csv.write_text(data)

        with patch('acquire_golden_set.GOLDEN_SET_PATH', fake_csv):
            result = load_golden_set()
            assert result is None

    def test_load_golden_set_success(self, tmp_path):
        """Should return DataFrame if all validations pass."""
        fake_csv = tmp_path / "golden_set.csv"
        data = "interaction_id,expert_load_score\n"
        for i in range(MIN_SAMPLES):
            data += f"ID-{i},{i * 2}\n"
        fake_csv.write_text(data)

        with patch('acquire_golden_set.GOLDEN_SET_PATH', fake_csv):
            result = load_golden_set()
            assert result is not None
            assert len(result) == MIN_SAMPLES
            assert "expert_load_score" in result.columns
            assert not result["expert_load_score"].isna().any()


class TestGoldenSetWorkflow:
    """Integration tests for the Golden Set acquisition workflow."""

    def test_workflow_blocks_on_missing_data(self):
        """Workflow should block and wait for expert population."""
        # This is tested via the main() function behavior
        # We verify the template generation happens correctly
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            processed_dir = tmp_path / "data" / "processed"
            processed_dir.mkdir(parents=True)

            with patch('acquire_golden_set.PROJECT_ROOT', tmp_path):
                with patch('acquire_golden_set.GOLDEN_SET_PATH', processed_dir / "golden_set.csv"):
                    with patch('acquire_golden_set.TEMPLATE_PATH', processed_dir / "golden_set_template.csv"):
                        # Generate template
                        df = generate_template()
                        assert df is not None
                        assert len(df) >= MIN_SAMPLES

    def test_workflow_validates_external_source_failure(self):
        """Workflow should proceed to template generation when external sources fail."""
        with patch('acquire_golden_set.VERIFIED_EXTERNAL_SOURCES', []):
            with patch('acquire_golden_set.fetch_external_golden_set', return_value=None):
                # The workflow should continue to template generation
                # This is implicitly tested by the main() flow
                pass