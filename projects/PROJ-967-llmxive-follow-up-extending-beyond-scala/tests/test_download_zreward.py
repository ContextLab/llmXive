"""
Tests for download_zreward.py

These tests verify the dataset download logic and schema validation.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Import the module functions
import sys
sys.path.insert(0, 'projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code')
from download_zreward import (
    validate_columns,
    download_dataset,
    download_from_local_archive,
    REQUIRED_COLUMNS,
    REQUIRED_RUBRIC_KEYS,
)


class TestValidateColumns:
    """Tests for the validate_columns function."""

    def test_valid_columns(self, caplog):
        """Test that valid columns pass validation."""
        # Create a mock DataFrame with all required columns
        df = pd.DataFrame({
            "prompt": ["test prompt"],
            "image_url": ["http://example.com/img.jpg"],
            "teacher_scores": [
                {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85}
            ],
            "student_scalar": [0.75],
            "human_annotations": [
                {"Alignment": 0.88, "Realism": 0.79, "Aesthetics": 0.68, "Plausibility": 0.82}
            ],
            "primary_dimension": ["Alignment"],
        })

        # This should not raise
        validate_columns(df, MagicMock())

    def test_missing_top_level_columns(self, caplog):
        """Test that missing top-level columns raise an error."""
        df = pd.DataFrame({
            "prompt": ["test"],
            "teacher_scores": [{}],
        })

        with pytest.raises(RuntimeError) as exc_info:
            validate_columns(df, MagicMock())

        assert "missing required columns" in str(exc_info.value).lower()

    def test_missing_teacher_scores_keys(self, caplog):
        """Test that missing teacher_scores keys raise an error."""
        df = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": [{"Alignment": 0.9}],  # Missing other keys
            "student_scalar": [0.75],
            "human_annotations": [
                {"Alignment": 0.88, "Realism": 0.79, "Aesthetics": 0.68, "Plausibility": 0.82}
            ],
            "primary_dimension": ["Alignment"],
        })

        with pytest.raises(RuntimeError) as exc_info:
            validate_columns(df, MagicMock())

        assert "teacher_scores missing required keys" in str(exc_info.value)

    def test_missing_human_annotations_keys(self, caplog):
        """Test that missing human_annotations keys raise an error."""
        df = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": [
                {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85}
            ],
            "student_scalar": [0.75],
            "human_annotations": [{"Alignment": 0.88}],  # Missing other keys
            "primary_dimension": ["Alignment"],
        })

        with pytest.raises(RuntimeError) as exc_info:
            validate_columns(df, MagicMock())

        assert "human_annotations missing required keys" in str(exc_info.value)

    def test_non_dict_teacher_scores(self, caplog):
        """Test that non-dict teacher_scores raise an error."""
        df = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": ["not a dict"],
            "student_scalar": [0.75],
            "human_annotations": [
                {"Alignment": 0.88, "Realism": 0.79, "Aesthetics": 0.68, "Plausibility": 0.82}
            ],
            "primary_dimension": ["Alignment"],
        })

        with pytest.raises(RuntimeError) as exc_info:
            validate_columns(df, MagicMock())

        assert "teacher_scores column contains non-dict values" in str(exc_info.value)

    def test_non_dict_human_annotations(self, caplog):
        """Test that non-dict human_annotations raise an error."""
        df = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": [
                {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85}
            ],
            "student_scalar": [0.75],
            "human_annotations": ["not a dict"],
            "primary_dimension": ["Alignment"],
        })

        with pytest.raises(RuntimeError) as exc_info:
            validate_columns(df, MagicMock())

        assert "human_annotations column contains non-dict values" in str(exc_info.value)


class TestDownloadDataset:
    """Tests for the download_dataset function."""

    @patch("download_zreward.load_dataset")
    @patch("download_zreward.calculate_sha256")
    @patch("download_zreward.save_checksum")
    def test_download_success(self, mock_save_checksum, mock_calc_sha, mock_load_dataset, tmp_path):
        """Test successful dataset download."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": [
                {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85}
            ],
            "student_scalar": [0.75],
            "human_annotations": [
                {"Alignment": 0.88, "Realism": 0.79, "Aesthetics": 0.68, "Plausibility": 0.82}
            ],
            "primary_dimension": ["Alignment"],
        })
        mock_load_dataset.return_value = mock_dataset
        mock_calc_sha.return_value = "abc123"

        logger = MagicMock()

        result = download_dataset("test/dataset", str(tmp_path), logger)

        # Verify the file was created
        assert result.exists()
        assert result.name == "zreward_raw.parquet"

        # Verify calls
        mock_load_dataset.assert_called_once_with("test/dataset", split="train")
        mock_calc_sha.assert_called_once()
        mock_save_checksum.assert_called_once()

    @patch("download_zreward.load_dataset")
    def test_download_failure(self, mock_load_dataset, tmp_path):
        """Test that download failure raises an error."""
        mock_load_dataset.side_effect = Exception("Network error")

        logger = MagicMock()

        with pytest.raises(Exception):
            download_dataset("test/dataset", str(tmp_path), logger)


class TestDownloadFromLocalArchive:
    """Tests for the download_from_local_archive function."""

    def test_download_from_parquet(self, tmp_path):
        """Test loading from a local parquet file."""
        # Create a test parquet file
        test_df = pd.DataFrame({
            "prompt": ["test"],
            "image_url": ["http://example.com"],
            "teacher_scores": [
                {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85}
            ],
            "student_scalar": [0.75],
            "human_annotations": [
                {"Alignment": 0.88, "Realism": 0.79, "Aesthetics": 0.68, "Plausibility": 0.82}
            ],
            "primary_dimension": ["Alignment"],
        })

        input_path = tmp_path / "input.parquet"
        test_df.to_parquet(input_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        logger = MagicMock()

        result = download_from_local_archive(str(input_path), str(output_dir), logger)

        # Verify the file was created
        assert result.exists()
        assert result.name == "zreward_raw.parquet"

    def test_file_not_found(self, tmp_path):
        """Test that missing file raises an error."""
        logger = MagicMock()

        with pytest.raises(FileNotFoundError):
            download_from_local_archive(
                str(tmp_path / "nonexistent.parquet"),
                str(tmp_path / "output"),
                logger
            )

    def test_unsupported_format(self, tmp_path):
        """Test that unsupported file format raises an error."""
        # Create a dummy file with unsupported extension
        input_path = tmp_path / "input.txt"
        input_path.write_text("dummy content")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        logger = MagicMock()

        with pytest.raises(ValueError):
            download_from_local_archive(str(input_path), str(output_dir), logger)