import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the functions to test
# Assuming ingest.py is in the code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import clean_data, write_ingestion_stats, save_cleaned_data, get_project_root

class TestT014RetentionLogging:
    """Tests for T014: Retention rate logging and saving cleaned data."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    def test_clean_data_calculates_retention(self, temp_dir):
        """Test that clean_data returns correct raw, cleaned counts and retention rate."""
        # Create mock data
        data = {
            'Tg': [300.0, 400.0, None, 500.0, 600.0],
            'composition': ['Fe40Ni40P20', 'Cu50Zr50', 'Fe30Co30Ni40', '', 'Al80Si20'],
            'other': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
        
        logger = MockLogger()
        
        cleaned_df, raw_count, cleaned_count, retention_rate = clean_data(df, logger)
        
        assert raw_count == 5
        # Rows dropped: row 2 (Tg null), row 3 (empty composition) -> 2 dropped
        # Expected cleaned: 3 rows
        assert cleaned_count == 3
        assert retention_rate == 3.0 / 5.0
        assert len(cleaned_df) == 3

    def test_write_ingestion_stats_schema(self, temp_dir):
        """Test that write_ingestion_stats creates valid JSON with required keys."""
        stats = {
            "source_doi": "10.5281/zenodo.10043838",
            "raw_count": 100,
            "cleaned_count": 90,
            "retention_rate": 0.90
        }
        output_path = temp_dir / "ingestion_stats.json"
        
        write_ingestion_stats(stats, output_path, MagicMock())
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_stats = json.load(f)
        
        assert "source_doi" in loaded_stats
        assert "retention_rate" in loaded_stats
        assert "raw_count" in loaded_stats
        assert "cleaned_count" in loaded_stats
        assert isinstance(loaded_stats["retention_rate"], float)
        assert loaded_stats["retention_rate"] > 0

    def test_save_cleaned_data_creates_file(self, temp_dir):
        """Test that save_cleaned_data writes a non-empty CSV."""
        data = {
            'Tg': [300.0, 400.0],
            'composition': ['Fe40Ni40P20', 'Cu50Zr50']
        }
        df = pd.DataFrame(data)
        output_path = temp_dir / "cleaned_mg.csv"
        
        save_cleaned_data(df, output_path, MagicMock())
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert 'Tg' in loaded_df.columns
        assert 'composition' in loaded_df.columns