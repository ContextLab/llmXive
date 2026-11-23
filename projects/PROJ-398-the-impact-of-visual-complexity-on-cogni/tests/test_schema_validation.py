"""
Tests for schema validation utilities.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pytest

from src.lib.schema_validator import (
    validate_dict_against_schema,
    validate_dataframe_schema,
    validate_background_frame,
    validate_human_rating,
    validate_session,
    validate_metrics_csv,
    validate_human_ratings_csv,
    validate_json_sidecar,
    SchemaValidationError,
    BACKGROUND_FRAME_SCHEMA,
    HUMAN_RATING_SCHEMA,
    SESSION_SCHEMA,
)


class TestBackgroundFrameSchema:
    """Tests for BackgroundFrame schema validation."""

    def test_valid_background_frame(self):
        """Test that a valid background frame passes validation."""
        valid_data = {
            "image_id": "img_001",
            "entropy": 5.23,
            "color_variance": 0.45,
            "object_count": 3,
            "width": 1920,
            "height": 1080,
            "file_path": "/data/stimuli/img_001.jpg",
        }

        is_valid, error = validate_background_frame(valid_data)
        assert is_valid is True
        assert error is None

    def test_missing_required_field(self):
        """Test validation fails when a required field is missing."""
        invalid_data = {
            "image_id": "img_001",
            "entropy": 5.23,
            # Missing color_variance and object_count
        }

        is_valid, error = validate_background_frame(invalid_data)
        assert is_valid is False
        assert "Missing required field" in error

    def test_invalid_type(self):
        """Test validation fails for incorrect types."""
        invalid_data = {
            "image_id": 12345,  # Should be string
            "entropy": 5.23,
            "color_variance": 0.45,
            "object_count": 3,
        }

        is_valid, error = validate_background_frame(invalid_data)
        assert is_valid is False
        assert "must be of type string" in error

    def test_negative_object_count(self):
        """Test validation fails for negative object_count."""
        invalid_data = {
            "image_id": "img_001",
            "entropy": 5.23,
            "color_variance": 0.45,
            "object_count": -1,  # Invalid: minimum is 0
        }

        is_valid, error = validate_background_frame(invalid_data)
        assert is_valid is False
        assert "less than minimum" in error

    def test_zero_object_count_valid(self):
        """Test that zero object_count is valid (no objects detected)."""
        valid_data = {
            "image_id": "img_001",
            "entropy": 5.23,
            "color_variance": 0.45,
            "object_count": 0,
        }

        is_valid, error = validate_background_frame(valid_data)
        assert is_valid is True
        assert error is None


class TestHumanRatingSchema:
    """Tests for HumanRating schema validation."""

    def test_valid_human_rating(self):
        """Test that a valid human rating passes validation."""
        valid_data = {
            "image_id": "img_001",
            "participant_id": "p_001",
            "complexity_score": 75.5,
        }

        is_valid, error = validate_human_rating(valid_data)
        assert is_valid is True
        assert error is None

    def test_complexity_score_out_of_range(self):
        """Test validation fails for complexity_score outside 0-100."""
        invalid_data = {
            "image_id": "img_001",
            "participant_id": "p_001",
            "complexity_score": 150.0,  # Exceeds maximum
        }

        is_valid, error = validate_human_rating(invalid_data)
        assert is_valid is False
        assert "greater than maximum" in error

    def test_missing_participant_id(self):
        """Test validation fails when participant_id is missing."""
        invalid_data = {
            "image_id": "img_001",
            "complexity_score": 75.5,
        }

        is_valid, error = validate_human_rating(invalid_data)
        assert is_valid is False
        assert "Missing required field" in error


class TestSessionSchema:
    """Tests for Session schema validation."""

    def test_valid_session(self):
        """Test that a valid session passes validation."""
        valid_data = {
            "participant_id": "p_001",
            "session_id": "s_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "stimulus_id": "img_001",
            "tlx_score": 45.0,
            "reaction_time": 350.5,
        }

        is_valid, error = validate_session(valid_data)
        assert is_valid is True
        assert error is None

    def test_negative_reaction_time(self):
        """Test validation fails for negative reaction_time."""
        invalid_data = {
            "participant_id": "p_001",
            "session_id": "s_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "stimulus_id": "img_001",
            "tlx_score": 45.0,
            "reaction_time": -10.0,
        }

        is_valid, error = validate_session(invalid_data)
        assert is_valid is False
        assert "less than minimum" in error


class TestDataFrameValidation:
    """Tests for DataFrame schema validation."""

    def test_valid_metrics_dataframe(self):
        """Test validation of a valid metrics DataFrame."""
        df = pd.DataFrame(
            [
                {
                    "image_id": "img_001",
                    "entropy": 5.23,
                    "color_variance": 0.45,
                    "object_count": 3,
                },
                {
                    "image_id": "img_002",
                    "entropy": 4.12,
                    "color_variance": 0.32,
                    "object_count": 1,
                },
            ]
        )

        is_valid, error = validate_dataframe_schema(
            df, BACKGROUND_FRAME_SCHEMA, "test_df"
        )
        assert is_valid is True
        assert error is None

    def test_missing_column_in_dataframe(self):
        """Test validation fails when a required column is missing."""
        df = pd.DataFrame(
            [
                {
                    "image_id": "img_001",
                    "entropy": 5.23,
                    # Missing color_variance and object_count
                },
            ]
        )

        is_valid, error = validate_dataframe_schema(
            df, BACKGROUND_FRAME_SCHEMA, "test_df"
        )
        assert is_valid is False
        assert "missing required columns" in error.lower()

    def test_nan_in_required_column(self):
        """Test validation fails when a required column has NaN."""
        df = pd.DataFrame(
            [
                {
                    "image_id": "img_001",
                    "entropy": 5.23,
                    "color_variance": 0.45,
                    "object_count": None,  # NaN
                },
            ]
        )

        is_valid, error = validate_dataframe_schema(
            df, BACKGROUND_FRAME_SCHEMA, "test_df"
        )
        assert is_valid is False
        assert "NaN" in error


class TestFileValidation:
    """Tests for file-based validation functions."""

    def test_validate_metrics_csv_valid(self):
        """Test validation of a valid metrics CSV file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write(
                "image_id,entropy,color_variance,object_count\n"
                "img_001,5.23,0.45,3\n"
                "img_002,4.12,0.32,1\n"
            )
            temp_path = f.name

        try:
            is_valid, error = validate_metrics_csv(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            Path(temp_path).unlink()

    def test_validate_metrics_csv_missing_file(self):
        """Test validation fails when file does not exist."""
        is_valid, error = validate_metrics_csv("/nonexistent/path.csv")
        assert is_valid is False
        assert "not found" in error.lower()

    def test_validate_human_ratings_csv_valid(self):
        """Test validation of a valid human ratings CSV file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write(
                "image_id,participant_id,complexity_score\n"
                "img_001,p_001,75.5\n"
                "img_002,p_002,60.0\n"
            )
            temp_path = f.name

        try:
            is_valid, error = validate_human_ratings_csv(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            Path(temp_path).unlink()

    def test_validate_json_sidecar_valid(self):
        """Test validation of a valid JSON sidecar file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "image_id": "img_001",
                    "entropy": 5.23,
                    "color_variance": 0.45,
                    "object_count": 3,
                },
                f,
            )
            temp_path = f.name

        try:
            is_valid, error = validate_json_sidecar(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            Path(temp_path).unlink()

    def test_validate_json_sidecar_invalid_json(self):
        """Test validation fails for invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json {{{")
            temp_path = f.name

        try:
            is_valid, error = validate_json_sidecar(temp_path)
            assert is_valid is False
            assert "Invalid JSON" in error
        finally:
            Path(temp_path).unlink()

    def test_validate_json_sidecar_missing_fields(self):
        """Test validation fails when required fields are missing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "image_id": "img_001",
                    # Missing entropy, color_variance, object_count
                },
                f,
            )
            temp_path = f.name

        try:
            is_valid, error = validate_json_sidecar(temp_path)
            assert is_valid is False
            assert "Missing required field" in error
        finally:
            Path(temp_path).unlink()