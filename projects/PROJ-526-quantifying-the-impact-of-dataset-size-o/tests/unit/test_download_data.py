"""
Unit tests for download_data.py functionality.

Tests the download logic, retry mechanisms, and data processing
without requiring actual network access.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download_data import (
    exponential_backoff,
    DownloadError,
    process_property_files,
    DATASET_CONFIGS
)
from config import Config


class TestExponentialBackoff:
    """Tests for exponential backoff calculation."""

    def test_backoff_increases(self):
        """Backoff delay should increase with attempt number."""
        delay0 = exponential_backoff(0)
        delay1 = exponential_backoff(1)
        delay2 = exponential_backoff(2)
        
        assert delay1 > delay0
        assert delay2 > delay1

    def test_backoff_has_jitter(self):
        """Backoff should include jitter."""
        delays = [exponential_backoff(1) for _ in range(10)]
        # With jitter, not all delays should be identical
        assert len(set([round(d, 2) for d in delays])) > 1

    def test_backoff_max_limit(self):
        """Backoff should not exceed maximum limit."""
        # Large attempt number should still respect max
        delay = exponential_backoff(100)
        assert delay <= 60.0 + 6.0  # max_backoff + 10% jitter

    def test_backoff_min_limit(self):
        """Backoff should not be less than initial."""
        delay = exponential_backoff(0)
        assert delay >= 1.0


class TestProcessPropertyFiles:
    """Tests for property file processing."""

    def test_csv_processing(self):
        """Test CSV file processing with standard columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Create test data
            data = """material_id,value,units,source
            mp-123,1.5,eV,MaterialsProject
            mp-456,2.3,eV,MaterialsProject"""
            
            csv_path.write_text(data)
            
            df = process_property_files(Path(tmpdir), "test_prop", csv_path)
            
            assert len(df) == 2
            assert "material_id" in df.columns
            assert "value" in df.columns
            assert "units" in df.columns
            assert "source" in df.columns
            assert "property_name" in df.columns
            assert df["property_name"].iloc[0] == "test_prop"

    def test_parquet_processing(self):
        """Test Parquet file processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"
            
            # Create test DataFrame and save
            test_df = pd.DataFrame({
                'material_id': ['mp-123', 'mp-456'],
                'value': [1.5, 2.3],
                'units': ['eV', 'eV'],
                'source': ['MP', 'MP']
            })
            test_df.to_parquet(parquet_path)
            
            df = process_property_files(Path(tmpdir), "test_prop", parquet_path)
            
            assert len(df) == 2
            assert df["property_name"].iloc[0] == "test_prop"

    def test_missing_units_column(self):
        """Test handling of missing units column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Data without units column
            data = """material_id,value,source
            mp-123,1.5,MaterialsProject
            mp-456,2.3,MaterialsProject"""
            
            csv_path.write_text(data)
            
            df = process_property_files(Path(tmpdir), "test_prop", csv_path)
            
            assert "units" in df.columns
            assert all(df["units"] == "unknown")

    def test_missing_source_column(self):
        """Test handling of missing source column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Data without source column
            data = """material_id,value,units
            mp-123,1.5,eV
            mp-456,2.3,eV"""
            
            csv_path.write_text(data)
            
            df = process_property_files(Path(tmpdir), "test_prop", csv_path)
            
            assert "source" in df.columns
            assert all(df["source"] == "unknown")

    def test_infer_value_column(self):
        """Test inference of value column when not explicitly named."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Data with non-standard column names
            data = """id,energy,units,src
            mp-123,1.5,eV,MP
            mp-456,2.3,eV,MP"""
            
            csv_path.write_text(data)
            
            df = process_property_files(Path(tmpdir), "test_prop", csv_path)
            
            assert "value" in df.columns
            assert df["value"].iloc[0] == 1.5
            assert df["value"].iloc[1] == 2.3

    def test_empty_dataframe(self):
        """Test processing of empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            csv_path.write_text("material_id,value,units,source\n")
            
            df = process_property_files(Path(tmpdir), "test_prop", csv_path)
            
            assert len(df) == 0
            assert "property_name" in df.columns

    def test_unsupported_format(self):
        """Test handling of unsupported file format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "test.txt"
            txt_path.write_text("some data")
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                process_property_files(Path(tmpdir), "test_prop", txt_path)


class TestDatasetConfigs:
    """Tests for dataset configuration structure."""

    def test_configs_exist(self):
        """Verify dataset configurations are defined."""
        assert len(DATASET_CONFIGS) > 0

    def test_config_structure(self):
        """Verify each config has required fields."""
        required_fields = ["repo_id", "subsets", "description"]
        
        for config in DATASET_CONFIGS:
            for field in required_fields:
                assert field in config, f"Missing {field} in config"
                assert isinstance(config[field], str) or isinstance(config[field], list)

    def test_subsets_are_lists(self):
        """Verify subsets are lists."""
        for config in DATASET_CONFIGS:
            assert isinstance(config["subsets"], list)
            assert len(config["subsets"]) > 0

    def test_repo_ids_are_valid_format(self):
        """Verify repo IDs follow HuggingFace format."""
        for config in DATASET_CONFIGS:
            repo_id = config["repo_id"]
            assert "/" in repo_id, f"Invalid repo_id format: {repo_id}"
            assert len(repo_id.split("/")) == 2
