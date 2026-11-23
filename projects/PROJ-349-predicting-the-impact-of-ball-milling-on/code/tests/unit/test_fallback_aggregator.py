"""
Unit tests for fallback aggregation logic (T013c).
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.exceptions import DataIngestionError, InsufficientDataError
from src.ingest.fallback_aggregator import (
    load_fallback_data,
    append_fallback_if_needed,
    run_fallback_aggregation,
    MIN_ROWS
)


@pytest.fixture
def temp_fallback_dir():
    """Create a temporary directory for fallback data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_fallback_csv(temp_fallback_dir):
    """Create a valid fallback CSV with >150 rows."""
    fallback_path = temp_fallback_dir / "verified_static_subset.csv"
    # Create a dataframe with 200 rows
    data = {
        "experiment_id": [f"EXP_{i}" for i in range(200)],
        "source": ["fallback"] * 200,
        "material_type": ["Al"] * 200,
        "milling_speed": [300] * 200,
        "milling_time": [2.0] * 200,
        "ball_to_powder_ratio": [5.0] * 200,
        "youngs_modulus": [70.0] * 200,
        "density": [2.7] * 200,
        "d10": [10.0] * 200,
        "d50": [50.0] * 200,
        "d90": [90.0] * 200,
        "process_duration": [4.0] * 200
    }
    df = pd.DataFrame(data)
    df.to_csv(fallback_path, index=False)
    return fallback_path


@pytest.fixture
def small_fallback_csv(temp_fallback_dir):
    """Create a fallback CSV with <150 rows (should raise InsufficientDataError)."""
    fallback_path = temp_fallback_dir / "small_subset.csv"
    data = {
        "experiment_id": [f"EXP_{i}" for i in range(50)],
        "source": ["fallback"] * 50,
        "material_type": ["Al"] * 50,
        "milling_speed": [300] * 50,
        "milling_time": [2.0] * 50,
        "ball_to_powder_ratio": [5.0] * 50,
        "youngs_modulus": [70.0] * 50,
        "density": [2.7] * 50,
        "d10": [10.0] * 50,
        "d50": [50.0] * 50,
        "d90": [90.0] * 50,
        "process_duration": [4.0] * 50
    }
    df = pd.DataFrame(data)
    df.to_csv(fallback_path, index=False)
    return fallback_path


class TestLoadFallbackData:
    def test_load_valid_fallback(self, valid_fallback_csv):
        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", valid_fallback_csv):
            df = load_fallback_data()
            assert len(df) == 200
            assert "experiment_id" in df.columns

    def test_load_missing_file(self, temp_fallback_dir):
        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", temp_fallback_dir / "nonexistent.csv"):
            with pytest.raises(DataIngestionError, match="Fallback file not found"):
                load_fallback_data()

    def test_load_empty_file(self, temp_fallback_dir):
        empty_path = temp_fallback_dir / "empty.csv"
        pd.DataFrame().to_csv(empty_path, index=False)
        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", empty_path):
            with pytest.raises(DataIngestionError, match="is empty"):
                load_fallback_data()

    def test_load_insufficient_rows(self, small_fallback_csv):
        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", small_fallback_csv):
            with pytest.raises(InsufficientDataError, match="minimum viable threshold"):
                load_fallback_data()


class TestAppendFallbackIfNeeded:
    def test_no_fallback_needed(self):
        # Current has >150 rows
        current_df = pd.DataFrame({"experiment_id": [f"EXP_{i}" for i in range(200)]})
        result = append_fallback_if_needed(current_df)
        assert len(result) == 200

    def test_fallback_needed_and_successful(self, valid_fallback_csv):
        # Current has <150 rows
        current_df = pd.DataFrame({
            "experiment_id": [f"EXP_{i}" for i in range(50)],
            "source": ["primary"] * 50,
            "material_type": ["Al"] * 50,
            "milling_speed": [300] * 50,
            "milling_time": [2.0] * 50,
            "ball_to_powder_ratio": [5.0] * 50,
            "youngs_modulus": [70.0] * 50,
            "density": [2.7] * 50,
            "d10": [10.0] * 50,
            "d50": [50.0] * 50,
            "d90": [90.0] * 50,
            "process_duration": [4.0] * 50
        })

        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", valid_fallback_csv):
            result = append_fallback_if_needed(current_df)
            assert len(result) == 250  # 50 + 200

    def test_fallback_still_insufficient(self, small_fallback_csv):
        current_df = pd.DataFrame({
            "experiment_id": [f"EXP_{i}" for i in range(50)],
            "source": ["primary"] * 50,
            "material_type": ["Al"] * 50,
            "milling_speed": [300] * 50,
            "milling_time": [2.0] * 50,
            "ball_to_powder_ratio": [5.0] * 50,
            "youngs_modulus": [70.0] * 50,
            "density": [2.7] * 50,
            "d10": [10.0] * 50,
            "d50": [50.0] * 50,
            "d90": [90.0] * 50,
            "process_duration": [4.0] * 50
        })

        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", small_fallback_csv):
            with pytest.raises(InsufficientDataError, match="still below the minimum"):
                append_fallback_if_needed(current_df)

    def test_schema_mismatch_no_common_cols(self, temp_fallback_dir):
        # Create fallback with completely different columns
        fallback_path = temp_fallback_dir / "bad_schema.csv"
        bad_data = {
            "col_a": [1, 2, 3],
            "col_b": [4, 5, 6]
        }
        pd.DataFrame(bad_data).to_csv(fallback_path, index=False)

        current_df = pd.DataFrame({
            "experiment_id": [1, 2],
            "source": ["primary"] * 2
        })

        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", fallback_path):
            with pytest.raises(DataIngestionError, match="No common columns"):
                append_fallback_if_needed(current_df)

class TestRunFallbackAggregation:
    def test_run_and_write_output(self, valid_fallback_csv, temp_fallback_dir):
        current_df = pd.DataFrame({
            "experiment_id": [f"EXP_{i}" for i in range(50)],
            "source": ["primary"] * 50,
            "material_type": ["Al"] * 50,
            "milling_speed": [300] * 50,
            "milling_time": [2.0] * 50,
            "ball_to_powder_ratio": [5.0] * 50,
            "youngs_modulus": [70.0] * 50,
            "density": [2.7] * 50,
            "d10": [10.0] * 50,
            "d50": [50.0] * 50,
            "d90": [90.0] * 50,
            "process_duration": [4.0] * 50
        })

        output_path = temp_fallback_dir / "output.parquet"

        with patch("src.ingest.fallback_aggregator.FALLBACK_PATH", valid_fallback_csv):
            result = run_fallback_aggregation(current_df, output_path)

            assert len(result) == 250
            assert output_path.exists()
            loaded = pd.read_parquet(output_path)
            assert len(loaded) == 250