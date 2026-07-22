import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.download import (
    compute_sha256,
    archive_real_data,
    generate_synthetic_ebird_data,
    generate_synthetic_climate_data,
    write_synthetic_data,
    write_state_file,
    check_real_data_available,
    ensure_data_available,
    run_download_pipeline
)

class TestDownloadModule:
    """Unit tests for the download module."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary subdirectories
        os.makedirs("data/raw/ebird", exist_ok=True)
        os.makedirs("data/raw/climate", exist_ok=True)
        os.makedirs("data/raw/archive", exist_ok=True)
        os.makedirs("state/projects", exist_ok=True)
        
        yield
        
        # Clean up
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        test_file = Path("data/raw/ebird/test.txt")
        test_file.write_text("test content")
        
        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert isinstance(checksum, str)

    def test_generate_synthetic_ebird_data(self):
        """Test synthetic eBird data generation."""
        df = generate_synthetic_ebird_data(seed=42)
        
        # Check columns
        expected_columns = ["species", "lat", "lon", "date", "count", "checklist_id"]
        assert list(df.columns) == expected_columns
        
        # Check row count
        assert len(df) == 1000
        
        # Check data types
        assert df["lat"].dtype in ["float64", "float32"]
        assert df["lon"].dtype in ["float64", "float32"]
        assert df["count"].dtype in ["int64", "int32"]

    def test_generate_synthetic_climate_data(self):
        """Test synthetic climate data generation."""
        df = generate_synthetic_climate_data(seed=42)
        
        # Check columns
        expected_columns = ["lat", "lon", "temp", "week", "precip"]
        assert list(df.columns) == expected_columns
        
        # Check row count
        assert len(df) == 500

    def test_write_synthetic_data_csv(self):
        """Test writing synthetic data to CSV."""
        df = generate_synthetic_ebird_data(seed=42)
        output_path = Path("data/raw/synthetic_ebird.csv")
        
        write_synthetic_data(df, output_path, "csv")
        
        assert output_path.exists()
        
        # Verify content can be read back
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(df)

    def test_write_synthetic_data_parquet(self):
        """Test writing synthetic data to Parquet."""
        df = generate_synthetic_climate_data(seed=42)
        output_path = Path("data/raw/synthetic_climate.parquet")
        
        write_synthetic_data(df, output_path, "parquet")
        
        assert output_path.exists()
        
        # Verify content can be read back
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == len(df)

    def test_write_state_file(self):
        """Test writing state file."""
        checksums = {
            "file1.csv": "abc123",
            "file2.parquet": "def456"
        }
        
        write_state_file(checksums)
        
        state_file = Path("state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml")
        assert state_file.exists()

    def test_check_real_data_available_empty(self):
        """Test checking for real data when none exists."""
        assert check_real_data_available() is False

    def test_check_real_data_available_with_files(self):
        """Test checking for real data when files exist."""
        # Create dummy files
        (Path("data/raw/ebird") / "test.txt").write_text("test")
        (Path("data/raw/climate") / "test.txt").write_text("test")
        
        assert check_real_data_available() is True

    def test_ensure_data_available_production_no_data(self):
        """Test production mode with no data should exit."""
        # Clear any existing data
        for f in Path("data/raw/ebird").glob("*"):
            f.unlink()
        for f in Path("data/raw/climate").glob("*"):
            f.unlink()
        
        with pytest.raises(SystemExit) as exc_info:
            ensure_data_available(mode="production")
        
        assert exc_info.value.code == 1

    def test_ensure_data_available_development_no_data(self):
        """Test development mode with no data generates synthetic."""
        # Clear any existing data
        for f in Path("data/raw/ebird").glob("*"):
            f.unlink()
        for f in Path("data/raw/climate").glob("*"):
            f.unlink()
        
        result = ensure_data_available(mode="development")
        
        assert result["mode"] == "development"
        assert result["ebird_path"] is not None
        assert result["climate_path"] is not None
        assert len(result["checksums"]) > 0
        
        # Verify files were created
        assert Path(result["ebird_path"]).exists()
        assert Path(result["climate_path"]).exists()

    def test_run_download_pipeline_development(self):
        """Test running the full download pipeline in development mode."""
        # Clear any existing data
        for f in Path("data/raw/ebird").glob("*"):
            f.unlink()
        for f in Path("data/raw/climate").glob("*"):
            f.unlink()
        
        result = run_download_pipeline(mode="development")
        
        assert result["mode"] == "development"
        assert Path(result["ebird_path"]).exists()
        assert Path(result["climate_path"]).exists()