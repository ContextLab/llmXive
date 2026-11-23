"""
Unit tests for the export_scores module.
"""
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.export_scores import export_scores_to_csv
from code.stratification import load_scores_from_csv


class TestExportScores:
    """Tests for the export_scores_to_csv function."""

    def test_export_creates_valid_csv(self, tmp_path):
        """Test that export creates a valid CSV with correct headers."""
        scores = [
            {"repo_id": "repo_a", "regularity_score": 0.95},
            {"repo_id": "repo_b", "regularity_score": 0.42}
        ]
        output_file = tmp_path / "test_scores.csv"

        result_path = export_scores_to_csv(scores, output_path=output_file)

        assert result_path == output_file
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["repo_id"] == "repo_a"
        assert float(rows[0]["regularity_score"]) == 0.95
        assert rows[1]["repo_id"] == "repo_b"
        assert float(rows[1]["regularity_score"]) == 0.42

    def test_export_empty_list_raises(self, tmp_path):
        """Test that exporting an empty list raises ValueError."""
        with pytest.raises(ValueError, match="empty scores list"):
            export_scores_to_csv([], output_path=tmp_path / "empty.csv")

    def test_export_missing_required_field_raises(self, tmp_path):
        """Test that missing required fields raise ValueError."""
        scores = [
            {"repo_id": "repo_a"}  # Missing regularity_score
        ]
        with pytest.raises(ValueError, match="must contain 'repo_id' and 'regularity_score'"):
            export_scores_to_csv(scores, output_path=tmp_path / "invalid.csv")

    def test_export_writes_to_default_path_if_not_provided(self):
        """Test that default path is used when output_path is None."""
        scores = [{"repo_id": "repo_a", "regularity_score": 0.8}]

        with patch("code.export_scores.get_path") as mock_get_path, \
             patch("code.export_scores.ensure_directories") as mock_ensure, \
             patch("builtins.open", MagicMock()) as mock_open:

            mock_get_path.return_value = Path("/default/path/scores.csv")
            export_scores_to_csv(scores)

            mock_get_path.assert_called_once_with("data/processed/regularity_scores.csv")
            mock_ensure.assert_called_once()
            mock_open.assert_called()