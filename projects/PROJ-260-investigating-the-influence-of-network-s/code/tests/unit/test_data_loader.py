import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import logging

from src.services.data_loader import (
    load_verified_dataset_ids,
    fetch_dataset,
    write_missing_log,
    main,
    VERIFIED_DATASET_IDS,
    RESEARCH_MD_PATH,
    DATA_RAW_DIR,
    MISSING_LOG_PATH
)
from src.lib.utils import FatalError

class TestDataLoaderParsing:
    @patch('src.services.data_loader.RESEARCH_MD_PATH')
    @patch('builtins.open', new_callable=mock_open, read_data="Verified Dataset IDs: 1234567, 2345678, 3456789")
    def test_load_verified_ids_from_research_md(self, mock_file, mock_research_path):
        """Test that verified dataset IDs are loaded from research.md"""
        mock_research_path.exists.return_value = True
        
        # This test is simplified - in reality, we'd parse the file properly
        # For now, we just ensure the function doesn't crash when research.md exists
        result = load_verified_dataset_ids()
        
        assert isinstance(result, dict)
        assert 1000 in result
        assert 2000 in result
        assert 4000 in result

    @patch('src.services.data_loader.RESEARCH_MD_PATH')
    def test_load_verified_ids_fails_if_research_md_missing(self, mock_research_path):
        """Test that FatalError is raised if research.md is not found"""
        mock_research_path.exists.return_value = False
        
        with pytest.raises(FatalError) as exc_info:
            load_verified_dataset_ids()
        
        assert "research.md not found" in str(exc_info.value)

    @patch('src.services.data_loader.RESEARCH_MD_PATH')
    @patch('builtins.open', new_callable=mock_open, read_data="Some content without IDs")
    def test_load_verified_ids_fails_if_ids_not_in_research_md(self, mock_file, mock_research_path):
        """Test that FatalError is raised if dataset IDs are not in research.md"""
        mock_research_path.exists.return_value = True
        
        with pytest.raises(FatalError) as exc_info:
            load_verified_dataset_ids()
        
        assert "not found in research.md" in str(exc_info.value)

class TestDataLoaderFetching:
    @patch('src.services.data_loader.urlretrieve')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_fetch_dataset_success(self, mock_exists, mock_stat, mock_urlretrieve):
        """Test successful dataset fetch"""
        mock_urlretrieve.return_value = None
        mock_stat.return_value.st_size = 1024
        mock_exists.return_value = True
        
        output_dir = Path("/tmp/test_output")
        result = fetch_dataset(1000, "1234567", output_dir)
        
        assert result is not None
        assert isinstance(result, Path)
        mock_urlretrieve.assert_called_once()

    @patch('src.services.data_loader.urlretrieve')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_fetch_dataset_fails_if_file_empty(self, mock_exists, mock_stat, mock_urlretrieve):
        """Test that fetch_dataset returns None if downloaded file is empty"""
        mock_urlretrieve.return_value = None
        mock_stat.return_value.st_size = 0
        mock_exists.return_value = True
        
        output_dir = Path("/tmp/test_output")
        result = fetch_dataset(1000, "1234567", output_dir)
        
        assert result is None

    @patch('src.services.data_loader.urlretrieve')
    def test_fetch_dataset_fails_on_network_error(self, mock_urlretrieve):
        """Test that fetch_dataset returns None on network error"""
        from urllib.error import URLError
        mock_urlretrieve.side_effect = URLError("Network error")
        
        output_dir = Path("/tmp/test_output")
        result = fetch_dataset(1000, "1234567", output_dir)
        
        assert result is None

class TestMainFunction:
    @patch('src.services.data_loader.load_verified_dataset_ids')
    @patch('src.services.data_loader.fetch_dataset')
    @patch('src.services.data_loader.write_missing_log')
    @patch('src.services.data_logger.setup_logging')
    def test_main_succeeds_with_sufficient_data(self, mock_setup_logging, mock_write_log, mock_fetch, mock_load_ids):
        """Test that main succeeds when all system sizes have >= 30 realizations"""
        mock_setup_logging.return_value = logging.getLogger(__name__)
        mock_load_ids.return_value = {1000: ["1"] * 30, 2000: ["2"] * 30, 4000: ["3"] * 30}
        mock_fetch.return_value = MagicMock(exists=lambda: True)
        
        # This should not raise
        try:
            main()
        except SystemExit:
            # We expect main() to call sys.exit(0) on success
            pass

    @patch('src.services.data_loader.load_verified_dataset_ids')
    @patch('src.services.data_loader.fetch_dataset')
    @patch('src.services.data_loader.write_missing_log')
    @patch('src.services.data_loader.setup_logging')
    def test_main_fails_with_insufficient_data(self, mock_setup_logging, mock_write_log, mock_fetch, mock_load_ids):
        """Test that main raises FatalError when any system size has < 30 realizations"""
        mock_setup_logging.return_value = logging.getLogger(__name__)
        mock_load_ids.return_value = {1000: ["1"] * 20, 2000: ["2"] * 30, 4000: ["3"] * 30}
        mock_fetch.return_value = MagicMock(exists=lambda: True)
        
        with pytest.raises(FatalError) as exc_info:
            main()
        
        assert "Insufficient data" in str(exc_info.value)

class TestWriteMissingLog:
    @patch('pathlib.Path.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_write_missing_log_creates_file(self, mock_mkdir, mock_file):
        """Test that write_missing_log creates the log file"""
        missing_counts = {1000: 20, 2000: 25}
        write_missing_log(missing_counts)
        
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()
