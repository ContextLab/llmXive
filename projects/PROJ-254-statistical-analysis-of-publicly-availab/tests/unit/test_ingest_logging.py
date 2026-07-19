import pytest
import pandas as pd
import logging
import io
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import ingest_mpd
from utils import setup_logging, get_logger

def test_ingestion_logging_missing_genre_warning(tmp_path):
    """
    Test that ingest_mpd logs a warning when missing_genre_rate > 0.2
    """
    # Setup logger to capture output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    
    # Ensure the logger used by ingest module captures this
    logger = logging.getLogger('pipeline_logger')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    raw_dir = tmp_path / "raw"
    derived_dir = tmp_path / "derived"
    raw_dir.mkdir()
    derived_dir.mkdir()

    # Call ingestion (which uses mock data in the current implementation for T015)
    # The mock data in ingest.py has 2 missing genres out of 5 -> 0.4 rate > 0.2
    try:
        ingest_mpd(raw_dir, derived_dir)
    except Exception:
        pass # Ignore potential execution errors in mock, we only care about logging

    log_contents = log_stream.getvalue()
    
    # Verify warning was logged
    assert "WARNING" in log_contents, "Expected a WARNING log entry for missing genre rate"
    assert "Missing genre rate" in log_contents, "Expected log to mention missing genre rate"
    assert "exceeds threshold" in log_contents, "Expected log to mention threshold exceedance"

def test_ingestion_logging_stats(tmp_path):
    """
    Test that ingestion stats (match rates, exclusion rates) are logged
    """
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    
    logger = logging.getLogger('pipeline_logger')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    raw_dir = tmp_path / "raw"
    derived_dir = tmp_path / "derived"
    raw_dir.mkdir()
    derived_dir.mkdir()

    try:
        ingest_mpd(raw_dir, derived_dir)
    except Exception:
        pass

    log_contents = log_stream.getvalue()
    
    assert "Ingestion Stats" in log_contents, "Expected 'Ingestion Stats' in log"
    assert "Total tracks processed" in log_contents
    assert "Missing genre rate" in log_contents