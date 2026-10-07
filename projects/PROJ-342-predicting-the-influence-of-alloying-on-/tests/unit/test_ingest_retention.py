"""
Unit tests for T014: Retention rate logging and cleaned data saving.
"""
import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import clean_data, save_cleaned_data, write_ingestion_stats, get_project_root

class TestRetentionRateLogging:
    """Tests for retention rate calculation and logging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_df = pd.DataFrame({
            'Tg': [450.0, 500.0, 550.0, 600.0, 650.0],
            'composition': ['Fe40', 'Fe40', 'Fe40', 'Fe40', 'Fe40'],
            'other_col': [1, 2, 3, 4, 5]
        })
        
        # Create a mock logger
        import logging
        self.logger = logging.getLogger("test_ingest")
        self.logger.setLevel(logging.INFO)
        
        # Create temp directory for test outputs
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_data_retention_calculation(self):
        """Test that clean_data correctly calculates retention rate."""
        # Create a dataset with some nulls
        df_with_nulls = pd.DataFrame({
            'Tg': [450.0, None, 550.0, 600.0, None],
            'composition': ['Fe40', 'Fe40', None, 'Fe40', 'Fe40'],
            'other': [1, 2, 3, 4, 5]
        })
        
        df_cleaned, raw_count, cleaned_count, retention_rate = clean_data(
            df_with_nulls, self.logger
        )
        
        assert raw_count == 5
        assert cleaned_count == 1  # Only one row has both Tg and composition
        assert retention_rate == 0.2
        assert len(df_cleaned) == 1

    def test_save_cleaned_data_creates_file(self):
        """Test that save_cleaned_data writes the CSV file."""
        output_path = Path(self.temp_dir) / "test_cleaned.csv"
        save_cleaned_data(self.test_df, output_path, self.logger)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 5
        assert 'Tg' in loaded_df.columns
        assert 'composition' in loaded_df.columns

    def test_write_ingestion_stats_creates_json(self):
        """Test that write_ingestion_stats writes the JSON file."""
        stats = {
            "source_doi": "10.5281/zenodo.10043838",
            "raw_count": 100,
            "cleaned_count": 90,
            "retention_rate": 0.9
        }
        output_path = Path(self.temp_dir) / "test_stats.json"
        write_ingestion_stats(stats, output_path, self.logger)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify content
        with open(output_path, 'r') as f:
            loaded_stats = json.load(f)
        
        assert loaded_stats["source_doi"] == "10.5281/zenodo.10043838"
        assert loaded_stats["raw_count"] == 100
        assert loaded_stats["cleaned_count"] == 90
        assert loaded_stats["retention_rate"] == 0.9

    def test_ingestion_stats_schema(self):
        """Test that ingestion stats JSON has required keys."""
        stats = {
            "source_doi": "10.5281/zenodo.10043838",
            "raw_count": 100,
            "cleaned_count": 90,
            "retention_rate": 0.9
        }
        output_path = Path(self.temp_dir) / "test_stats.json"
        write_ingestion_stats(stats, output_path, self.logger)
        
        with open(output_path, 'r') as f:
            loaded_stats = json.load(f)
        
        # Verify all required keys exist
        required_keys = ["source_doi", "raw_count", "cleaned_count", "retention_rate"]
        for key in required_keys:
            assert key in loaded_stats, f"Missing required key: {key}"
        
        # Verify types
        assert isinstance(loaded_stats["source_doi"], str)
        assert isinstance(loaded_stats["raw_count"], int)
        assert isinstance(loaded_stats["cleaned_count"], int)
        assert isinstance(loaded_stats["retention_rate"], float)
        assert loaded_stats["retention_rate"] > 0

    def test_retention_rate_less_than_one(self):
        """Test that retention rate is correctly calculated when data is dropped."""
        df_partial = pd.DataFrame({
            'Tg': [450.0, None, 550.0],
            'composition': ['Fe40', 'Fe40', 'Fe40']
        })
        
        _, raw_count, cleaned_count, retention_rate = clean_data(
            df_partial, self.logger
        )
        
        assert raw_count == 3
        assert cleaned_count == 2
        assert retention_rate == 2/3

    def test_retention_rate_one_when_no_drop(self):
        """Test that retention rate is 1.0 when no data is dropped."""
        df_clean = pd.DataFrame({
            'Tg': [450.0, 500.0, 550.0],
            'composition': ['Fe40', 'Fe40', 'Fe40']
        })
        
        _, raw_count, cleaned_count, retention_rate = clean_data(
            df_clean, self.logger
        )
        
        assert raw_count == 3
        assert cleaned_count == 3
        assert retention_rate == 1.0