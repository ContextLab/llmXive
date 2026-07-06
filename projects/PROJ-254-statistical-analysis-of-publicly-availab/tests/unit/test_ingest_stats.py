import pytest
import logging
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import tempfile
from pathlib import Path

# Mock dependencies before importing
import sys
sys.modules['models'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['memory_utils'] = MagicMock()

from ingest import join_mpd_mb, get_logger, setup_logging

class TestIngestionStatsLogging:
    """Tests for T015: Logging ingestion stats and warnings."""

    def setup_method(self):
        """Setup temporary log file and mock data."""
        self.log_file = "test_pipeline_log.txt"
        setup_logging(self.log_file)
        self.logger = get_logger()
        
        # Clear log file
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_logging_match_rates(self, caplog):
        """Verify that match rates and exclusion rates are logged."""
        # Mock tracks
        tracks = [
            {"track_id": "1", "artist": "A", "title": "T1", "year": 2020, "playlist_id": "p1"},
            {"track_id": "2", "artist": "B", "title": "T2", "year": 2021, "playlist_id": "p1"},
            {"track_id": "3", "artist": "C", "title": "T3", "year": None, "playlist_id": "p1"}, # Missing year
            {"track_id": "4", "artist": "D", "title": "T4", "year": 2022, "playlist_id": "p1"},
        ]
        
        # Mock session
        mock_session = MagicMock()
        
        # Mock fetch_musicbrainz to return data for all valid tracks
        # We need to patch the function inside ingest.py
        with patch('ingest.fetch_musicbrainz') as mock_fetch, \
             patch('ingest.monitor_and_maybe_gc'), \
             patch('ingest.DERIVED_DATA_DIR', Path(tempfile.gettempdir())):
             
            mock_fetch.return_value = {
                "genres": [{"name": "rock"}], 
                "date": "2020-01-01",
                "title": "T1",
                "artists": [{"name": "A"}]
            }

            # Run join
            with caplog.at_level(logging.INFO):
                join_mpd_mb(tracks, mock_session)

            # Check logs
            assert "Ingestion Stats" in caplog.text
            assert "Match Rate" in caplog.text
            assert "Exclusion Rate" in caplog.text

    def test_warning_high_missing_genre_rate(self, caplog):
        """Verify warning is logged if missing genre rate > 0.2."""
        # Construct tracks where 50% have no genres after join
        tracks = [
            {"track_id": "1", "artist": "A", "title": "T1", "year": 2020, "playlist_id": "p1"},
            {"track_id": "2", "artist": "B", "title": "T2", "year": 2020, "playlist_id": "p1"},
        ]
        
        mock_session = MagicMock()
        
        # First track gets genres, second does not
        call_count = 0
        def mock_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "genres": [{"name": "rock"}], 
                    "date": "2020-01-01",
                    "title": "T1",
                    "artists": [{"name": "A"}]
                }
            else:
                return {
                    "genres": [], # No genres
                    "date": "2020-01-01",
                    "title": "T2",
                    "artists": [{"name": "B"}]
                }

        with patch('ingest.fetch_musicbrainz', side_effect=mock_fetch), \
             patch('ingest.monitor_and_maybe_gc'), \
             patch('ingest.DERIVED_DATA_DIR', Path(tempfile.gettempdir())):

            with caplog.at_level(logging.WARNING):
                join_mpd_mb(tracks, mock_session)

            # 1 out of 2 matched tracks has no genre -> 50% rate > 20%
            assert "High missing genre rate detected" in caplog.text
            assert "WARNING" in caplog.text