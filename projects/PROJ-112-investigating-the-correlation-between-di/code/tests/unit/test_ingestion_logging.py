import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ingestion.logging_config import (
    get_ingestion_logger, 
    log_download_status, 
    log_filter_counts, 
    log_merge_result
)

@pytest.fixture
def temp_log_dir():
    """Creates a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily patch the log path
        original_path = None
        # We can't easily patch the module-level constant INGESTION_LOG_PATH without importing it first
        # Instead, we test the logger behavior by capturing the handler
        yield Path(tmpdir)

def test_get_ingestion_logger_creates_file_handler():
    """Test that the ingestion logger creates a file handler."""
    # Reset logger cache to ensure clean state if needed
    from src.utils.logger import reset_logger_cache
    reset_logger_cache()
    
    logger = get_ingestion_logger()
    assert logger is not None
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

def test_log_download_status_success(caplog):
    """Test logging a successful download."""
    logger = get_ingestion_logger()
    with caplog.at_level(logging.INFO):
        log_download_status(logger, "AGP", "SUCCESS", "Downloaded 100MB")
    
    assert "Download AGP: SUCCESS" in caplog.text
    assert "Downloaded 100MB" in caplog.text

def test_log_download_status_fail(caplog):
    """Test logging a failed download."""
    logger = get_ingestion_logger()
    with caplog.at_level(logging.ERROR):
        log_download_status(logger, "UKBB", "FAIL", "Connection timeout")
    
    assert "Download UKBB: FAIL" in caplog.text
    assert "Connection timeout" in caplog.text

def test_log_filter_counts(caplog):
    """Test logging filter counts."""
    logger = get_ingestion_logger()
    with caplog.at_level(logging.INFO):
        log_filter_counts(logger, "Read Count", 50, "Below 5000 reads")
    
    assert "Filtered Samples (Read Count): 50" in caplog.text
    assert "Below 5000 reads" in caplog.text

def test_log_merge_result(caplog):
    """Test logging merge results."""
    logger = get_ingestion_logger()
    with caplog.at_level(logging.INFO):
        log_merge_result(logger, 1000, 600, 400)
    
    assert "Harmonized Samples: 1000" in caplog.text
    assert "AGP samples: 600" in caplog.text
    assert "UKBB samples: 400" in caplog.text

def test_run_ingestion_pipeline_logs_structure(caplog):
    """
    Integration-style test to ensure the pipeline script logs the required entries.
    We mock the actual data fetching to simulate success/failure scenarios.
    """
    # Reset logger cache
    from src.utils.logger import reset_logger_cache
    reset_logger_cache()
    
    with patch('src.ingestion.run_ingestion_pipeline.fetch_agp_data') as mock_agp, \
         patch('src.ingestion.run_ingestion_pipeline.fetch_ukbb_data') as mock_ukbb, \
         patch('src.ingestion.run_ingestion_pipeline.harmonize_and_merge') as mock_harm:
         
        mock_agp.return_value = None # fetch_agp_data usually writes to disk, return None
        mock_ukbb.return_value = None
        # Mock harmonize_and_merge to return a dummy DF and stats
        mock_harm.return_value = (MagicMock(__len__=lambda self: 5000), {'agp_count': 3000, 'ukbb_count': 2000, 'filtered_count': 100})

        from src.ingestion.run_ingestion_pipeline import main
        
        # Capture logs
        with caplog.at_level(logging.INFO):
            # We need to run the function, but it calls main() which parses args.
            # Instead, we simulate the logic inside main directly or mock sys.argv
            import sys
            sys.argv = ['run_ingestion_pipeline.py']
            
            # Re-import to get fresh state if necessary, but patching handles it
            # We call the internal functions directly to test logging logic
            logger = get_ingestion_logger()
            
            run_agp_ingestion(logger)
            run_ukbb_ingestion(logger)
            run_harmonization(logger)

        # Verify required log entries exist
        assert "Download AGP: SUCCESS" in caplog.text
        assert "Download UKBB: SUCCESS" in caplog.text
        assert "Filtered Samples" in caplog.text
        assert "Harmonized Samples: 5000" in caplog.text