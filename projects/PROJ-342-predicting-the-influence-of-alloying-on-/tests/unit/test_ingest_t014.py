import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingest import clean_data, write_ingestion_stats, save_cleaned_data

class TestT014IngestionStats:
    """Tests for T014: Retention rate logging and saving cleaned data."""

    @patch('ingest.logging.getLogger')
    def test_clean_data_retention_calculation(self, mock_logger):
        """Verify that clean_data correctly calculates counts and drops nulls."""
        # Create a mock dataframe
        data = {
            'Tg': [100.0, 200.0, None, 400.0, 500.0],
            'composition': ['A', 'B', 'C', None, 'E'],
            'other': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, raw_count, cleaned_count = clean_data(df, mock_logger)
        
        assert raw_count == 5
        assert cleaned_count == 2  # Only 'A' and 'E' rows remain
        assert len(cleaned_df) == 2
        assert 'Tg' not in cleaned_df[cleaned_df['Tg'].isna()].index

    @patch('ingest.logging.getLogger')
    def test_write_ingestion_stats_format(self, mock_logger, tmp_path):
        """Verify that write_ingestion_stats creates a valid JSON with required keys."""
        stats = {
            "source_doi": "10.5281/zenodo.10043838",
            "raw_count": 100,
            "cleaned_count": 90,
            "retention_rate": 0.9
        }
        output_path = tmp_path / "ingestion_stats.json"
        
        write_ingestion_stats(stats, output_path, mock_logger)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_stats = json.load(f)
        
        assert "source_doi" in loaded_stats
        assert "retention_rate" in loaded_stats
        assert "raw_count" in loaded_stats
        assert "cleaned_count" in loaded_stats
        
        assert isinstance(loaded_stats["retention_rate"], float)
        assert loaded_stats["retention_rate"] > 0

    @patch('ingest.logging.getLogger')
    def test_save_cleaned_data_creates_file(self, mock_logger, tmp_path):
        """Verify that save_cleaned_data writes a CSV file."""
        data = {
            'Tg': [100.0, 200.0],
            'composition': ['A', 'B']
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "cleaned_mg.csv"
        
        save_cleaned_data(df, output_path, mock_logger)
        
        assert output_path.exists()
        
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert 'Tg' in loaded_df.columns
        assert 'composition' in loaded_df.columns