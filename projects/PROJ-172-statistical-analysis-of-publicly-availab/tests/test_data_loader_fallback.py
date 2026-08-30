"""
Unit tests for Data Loader Fallback Protocol.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import Timeout, HTTPError

# Import the module to test
from code.data_loader import fetch_retrosheet_data, generate_synthetic_data, load_data
from code.config import ensure_directories

class TestDataLoaderFallback:
    
    def test_generate_synthetic_data_structure(self):
        """Test that synthetic data has the correct columns."""
        years = [2020, 2021]
        df = generate_synthetic_data(years)
        
        expected_cols = [
            "game_id", "year", "date", "home_team", "away_team",
            "home_score", "away_score", "home_win", "attendance", "venue"
        ]
        
        assert list(df.columns) == expected_cols
        assert len(df) > 0
        assert df["year"].unique().tolist() == years

    def test_generate_synthetic_data_distribution(self):
        """Test that synthetic data mimics reasonable distributions."""
        df = generate_synthetic_data([2020], seed=42)
        
        # Check scores are non-negative
        assert (df["home_score"] >= 0).all()
        assert (df["away_score"] >= 0).all()
        
        # Check home_win is binary
        assert df["home_win"].isin([0, 1]).all()

    @patch('code.data_loader.requests.get')
    def test_fetch_real_data_success(self, mock_get):
        """Test successful real data fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"game_id,year,home_team,away_team,home_score,away_score,home_win\n1,2020,NYY,BOS,5,3,1"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        df = fetch_retrosheet_data([2020])
        
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]["year"] == 2020

    @patch('code.data_loader.requests.get')
    def test_fetch_real_data_timeout_triggers_fallback_logic(self, mock_get):
        """Test that timeout triggers the fallback path in load_data."""
        mock_get.side_effect = Timeout("Connection timed out")
        
        # We test load_data here because it orchestrates the fallback
        # We mock fetch_retrosheet_data to return None to simulate failure
        with patch('code.data_loader.fetch_retrosheet_data', return_value=None):
            df, is_real = load_data(years=[2020])
            
            assert is_real is False
            assert df is not None
            assert len(df) > 0  # Should have synthetic data

    @patch('code.data_loader.requests.get')
    def test_fetch_real_data_403_triggers_fallback_logic(self, mock_get):
        """Test that 403 triggers the fallback path."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("403 Client Error")
        mock_get.return_value = mock_response
        
        with patch('code.data_loader.fetch_retrosheet_data', return_value=None):
            df, is_real = load_data(years=[2020])
            
            assert is_real is False
            assert df is not None
            assert len(df) > 0

    def test_load_data_creates_metadata(self):
        """Test that load_data creates the status report."""
        import os
        from pathlib import Path
        
        # Force synthetic mode
        with patch('code.data_loader.fetch_retrosheet_data', return_value=None):
            load_data(years=[2020])
        
        meta_path = Path("artifacts/reports/data_load_status.json")
        assert meta_path.exists()
        
        import json
        with open(meta_path, "r") as f:
            data = json.load(f)
        
        assert "is_real_data" in data
        assert data["is_real_data"] is False
        assert "record_count" in data
        assert "timestamp" in data
