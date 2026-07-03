"""
Unit tests for the download module.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download import (
    compute_sha256,
    generate_synthetic_ebird,
    generate_synthetic_climate,
    run_download_pipeline
)


class TestDownloadModule:
    """Tests for data download functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Save original paths
        self.original_root = Path(__file__).resolve().parent.parent.parent
        
        # Create a temporary directory structure
        self.test_root = tmp_path
        self.test_data_raw = self.test_root / "data" / "raw"
        self.test_ebird = self.test_data_raw / "ebird"
        self.test_climate = self.test_data_raw / "climate"
        self.test_archive = self.test_data_raw / "archive"
        self.test_state = self.test_root / "state"
        
        for d in [self.test_data_raw, self.test_ebird, self.test_climate, 
                  self.test_archive, self.test_state]:
            d.mkdir(parents=True)

        # Patch the module's paths
        import src.data.download as download_mod
        self.orig_data_raw = download_mod.DATA_RAW_DIR
        self.orig_ebird = download_mod.DATA_RAW_EBIRD
        self.orig_climate = download_mod.DATA_RAW_CLIMATE
        self.orig_archive = download_mod.ARCHIVE_DIR
        self.orig_state = download_mod.STATE_DIR
        self.orig_project_id = download_mod.PROJECT_ID

        download_mod.DATA_RAW_DIR = self.test_data_raw
        download_mod.DATA_RAW_EBIRD = self.test_ebird
        download_mod.DATA_RAW_CLIMATE = self.test_climate
        download_mod.ARCHIVE_DIR = self.test_archive
        download_mod.STATE_DIR = self.test_state
        download_mod.PROJECT_ID = "TEST-PROJECT"

        yield

        # Restore original paths
        download_mod.DATA_RAW_DIR = self.orig_data_raw
        download_mod.DATA_RAW_EBIRD = self.orig_ebird
        download_mod.DATA_RAW_CLIMATE = self.orig_climate
        download_mod.ARCHIVE_DIR = self.orig_archive
        download_mod.STATE_DIR = self.orig_state
        download_mod.PROJECT_ID = self.orig_project_id

    def test_compute_sha256(self):
        """Test SHA-256 checksum computation."""
        test_file = self.test_data_raw / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

    def test_generate_synthetic_ebird(self):
        """Test synthetic eBird data generation."""
        output_path = generate_synthetic_ebird(seed=42)
        
        assert output_path.exists()
        
        df = pd.read_csv(output_path)
        
        # Check columns
        expected_cols = ["species", "lat", "lon", "date", "count", "checklist_id"]
        assert list(df.columns) == expected_cols
        
        # Check dtypes
        assert df["lat"].dtype in ["float64", "float32"]
        assert df["lon"].dtype in ["float64", "float32"]
        assert df["count"].dtype in ["int64", "int32"]
        
        # Check data ranges
        assert df["lat"].between(25.0, 48.0).all()
        assert df["lon"].between(-125.0, -70.0).all()
        assert (df["count"] >= 0).all()

    def test_generate_synthetic_climate(self):
        """Test synthetic climate data generation."""
        output_path = generate_synthetic_climate(seed=42)
        
        assert output_path.exists()
        
        df = pd.read_parquet(output_path)
        
        # Check columns
        expected_cols = ["lat", "lon", "temp", "week", "precip"]
        assert list(df.columns) == expected_cols
        
        # Check dtypes
        assert df["lat"].dtype in ["float64", "float32"]
        assert df["lon"].dtype in ["float64", "float32"]
        assert df["temp"].dtype in ["float64", "float32"]
        assert df["week"].dtype in ["int64", "int32"]
        assert df["precip"].dtype in ["float64", "float32"]

    def test_run_download_pipeline_production_missing(self):
        """Test production mode aborts when data is missing."""
        # Ensure directories are empty
        for f in list(self.test_ebird.iterdir()):
            f.unlink()
        for f in list(self.test_climate.iterdir()):
            f.unlink()

        with pytest.raises(SystemExit) as exc_info:
            run_download_pipeline(production_mode=True)
        
        assert exc_info.value.code == 1

    def test_run_download_pipeline_development_missing(self):
        """Test development mode generates synthetic data when missing."""
        # Ensure directories are empty
        for f in list(self.test_ebird.iterdir()):
            f.unlink()
        for f in list(self.test_climate.iterdir()):
            f.unlink()

        # Should not raise
        run_download_pipeline(production_mode=False)

        # Check synthetic files were created
        assert (self.test_data_raw / "synthetic_ebird.csv").exists()
        assert (self.test_data_raw / "synthetic_climate.parquet").exists()

    def test_run_download_pipeline_production_with_data(self, tmp_path):
        """Test production mode succeeds when data exists."""
        # Create dummy real data
        ebird_file = self.test_ebird / "real_ebird.csv"
        ebird_file.write_text("species,lat,lon,date,count,checklist_id\nTurdus,40.0,-100.0,2023-01-01,5,CL001")
        
        climate_file = self.test_climate / "real_climate.parquet"
        pd.DataFrame({"lat": [40.0], "lon": [-100.0], "temp": [10.0], "week": [1], "precip": [5.0]}).to_parquet(climate_file)

        # Should not raise
        run_download_pipeline(production_mode=True)

        # Check state file was created
        state_file = self.test_state / "TEST-PROJECT.yaml"
        assert state_file.exists()

        # Check archive was created
        assert len(list(self.test_archive.iterdir())) > 0
