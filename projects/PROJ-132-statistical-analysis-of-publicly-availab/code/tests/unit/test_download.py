"""
Unit tests for the download module.

Tests cover:
- Synthetic data generation
- Checksum computation
- State file writing
- Production vs development mode behavior
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.download import (
    compute_sha256,
    generate_synthetic_ebird_data,
    generate_synthetic_climate_data,
    ensure_data_available,
    EBIRD_COLUMNS,
    CLIMATE_COLUMNS
)
import pandas as pd
import numpy as np


class TestDownloadModule:
    """Test suite for download module functions."""

    def test_compute_sha256(self):
        """Test SHA-256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            checksum = compute_sha256(temp_path)
            assert len(checksum) == 64, "SHA-256 should be 64 hex characters"
            assert checksum.isalnum(), "Checksum should be alphanumeric"
        finally:
            temp_path.unlink()

    def test_synthetic_ebird_data_generation(self):
        """Test synthetic eBird data generation."""
        df = generate_synthetic_ebird_data(seed=42, num_records=100)

        # Check columns
        assert list(df.columns) == EBIRD_COLUMNS, f"Expected columns {EBIRD_COLUMNS}, got {list(df.columns)}"

        # Check data types
        assert df["species"].dtype == object
        assert df["lat"].dtype in [np.float64, np.float32]
        assert df["lon"].dtype in [np.float64, np.float32]
        assert pd.api.types.is_datetime64_any_dtype(df["date"])
        assert df["count"].dtype in [np.int64, np.int32]
        assert df["checklist_id"].dtype == object

        # Check value ranges
        assert df["lat"].between(25.0, 49.0).all()
        assert df["lon"].between(-125.0, -70.0).all()
        assert df["count"].ge(0).all()
        assert len(df) == 100

    def test_synthetic_climate_data_generation(self):
        """Test synthetic climate data generation."""
        df = generate_synthetic_climate_data(seed=42, num_records=100)

        # Check columns
        assert list(df.columns) == CLIMATE_COLUMNS, f"Expected columns {CLIMATE_COLUMNS}, got {list(df.columns)}"

        # Check data types
        assert df["lat"].dtype in [np.float64, np.float32]
        assert df["lon"].dtype in [np.float64, np.float32]
        assert df["temp"].dtype in [np.float64, np.float32]
        assert df["week"].dtype in [np.int64, np.int32]
        assert df["precip"].dtype in [np.float64, np.float32]

        # Check value ranges
        assert df["lat"].between(25.0, 49.0).all()
        assert df["lon"].between(-125.0, -70.0).all()
        assert df["week"].between(1, 53).all()
        assert df["precip"].ge(0).all()
        assert len(df) == 100

    def test_synthetic_data_reproducibility(self):
        """Test that synthetic data is reproducible with same seed."""
        df1 = generate_synthetic_ebird_data(seed=42, num_records=100)
        df2 = generate_synthetic_ebird_data(seed=42, num_records=100)

        pd.testing.assert_frame_equal(df1, df2)

    def test_ensure_data_available_development_mode(self):
        """Test ensure_data_available in development mode creates synthetic data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the data directories
            original_data_raw = Path("data/raw")
            temp_data_raw = Path(tmpdir) / "data" / "raw"
            temp_data_raw.mkdir(parents=True)

            # Temporarily override the constants
            import src.data.download as download_module
            original_data_raw_dir = download_module.DATA_RAW_DIR
            original_state_dir = download_module.STATE_DIR

            download_module.DATA_RAW_DIR = temp_data_raw
            download_module.STATE_DIR = Path(tmpdir) / "state" / "projects"

            try:
                # This should generate synthetic data
                data_paths = ensure_data_available(mode="development")

                assert "ebird" in data_paths
                assert "climate" in data_paths
                assert data_paths["ebird"].exists()
                assert data_paths["climate"].exists()
            finally:
                # Restore original paths
                download_module.DATA_RAW_DIR = original_data_raw_dir
                download_module.STATE_DIR = original_state_dir

    def test_schema_compliance(self):
        """Test that generated data complies with expected schema."""
        ebird_df = generate_synthetic_ebird_data(seed=42, num_records=1000)
        climate_df = generate_synthetic_climate_data(seed=42, num_records=1000)

        # Check for required columns
        assert set(EBIRD_COLUMNS).issubset(set(ebird_df.columns))
        assert set(CLIMATE_COLUMNS).issubset(set(climate_df.columns))

        # Check for no missing values in critical fields
        assert ebird_df["species"].notna().all()
        assert ebird_df["lat"].notna().all()
        assert ebird_df["lon"].notna().all()
        assert ebird_df["date"].notna().all()
        assert ebird_df["count"].notna().all()
        assert ebird_df["checklist_id"].notna().all()

        assert climate_df["lat"].notna().all()
        assert climate_df["lon"].notna().all()
        assert climate_df["temp"].notna().all()
        assert climate_df["week"].notna().all()
        assert climate_df["precip"].notna().all()