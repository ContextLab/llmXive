import pytest
import tempfile
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.acquisition import (
    interpolate_noise_nearest_neighbor,
    save_interpolated_records,
    get_interpolation_max_km,
)
from src.utils.config import get_interim_data_dir


class TestInterpolation:
    def test_interpolate_within_max_km(self):
        """Test that records within max_km are interpolated."""
        missing = [
            {
                "recording_id": "m1",
                "species_id": "s1",
                "latitude": 40.0,
                "longitude": -74.0,
            }
        ]
        existing = [
            {
                "recording_id": "e1",
                "species_id": "s2",
                "latitude": 40.01,  # ~1.1 km away
                "longitude": -74.01,
                "noise_level_db": 55.0,
            }
        ]

        interpolated, failed = interpolate_noise_nearest_neighbor(
            missing, existing, max_km=50.0
        )

        assert len(interpolated) == 1
        assert len(failed) == 0
        assert interpolated[0]["noise_level_db"] == 55.0
        assert interpolated[0]["noise_source"] == "interpolated"

    def test_interpolate_outside_max_km(self):
        """Test that records outside max_km are not interpolated."""
        missing = [
            {
                "recording_id": "m1",
                "species_id": "s1",
                "latitude": 40.0,
                "longitude": -74.0,
            }
        ]
        existing = [
            {
                "recording_id": "e1",
                "species_id": "s2",
                "latitude": 45.0,  # ~555 km away
                "longitude": -74.0,
                "noise_level_db": 55.0,
            }
        ]

        interpolated, failed = interpolate_noise_nearest_neighbor(
            missing, existing, max_km=50.0
        )

        assert len(interpolated) == 0
        assert len(failed) == 1

    def test_save_interpolated_records(self):
        """Test saving interpolated records to CSV."""
        interpolated = [
            {
                "recording_id": "i1",
                "species_id": "s1",
                "latitude": 40.0,
                "longitude": -74.0,
                "noise_level_db": 55.0,
                "noise_source": "interpolated",
                "interpolation_source_lat": 40.01,
                "interpolation_source_lon": -74.01,
                "interpolation_distance_km": 1.1,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_interpolated.csv"
            save_interpolated_records(interpolated, output_path)

            assert output_path.exists()
            with open(output_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["recording_id"] == "i1"
                assert float(rows[0]["noise_level_db"]) == 55.0

    def test_save_empty_interpolated_records(self):
        """Test saving empty list creates file with headers."""
        interpolated = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_empty.csv"
            save_interpolated_records(interpolated, output_path)

            assert output_path.exists()
            with open(output_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0

    def test_no_valid_sources(self):
        """Test interpolation fails when no valid sources exist."""
        missing = [
            {
                "recording_id": "m1",
                "species_id": "s1",
                "latitude": 40.0,
                "longitude": -74.0,
            }
        ]
        existing = []  # No valid sources

        interpolated, failed = interpolate_noise_nearest_neighbor(
            missing, existing, max_km=50.0
        )

        assert len(interpolated) == 0
        assert len(failed) == 1