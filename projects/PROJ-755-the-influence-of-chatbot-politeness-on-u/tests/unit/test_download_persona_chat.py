"""
Unit tests for code/01_download_persona_chat.py

These tests verify the logic of the download script without actually downloading
the full dataset. They mock the HuggingFace datasets library.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import code_01_download_persona_chat as download_script

class TestPersonaChatDownload:
    
    @patch('code.code_01_download_persona_chat.load_skip_flag')
    @patch('code.code_01_download_persona_chat.load_dataset_with_check')
    @patch('code.code_01_download_persona_chat.save_raw_data')
    @patch('code.code_01_download_persona_chat.save_validation_report')
    def test_skip_if_hci_p2_valid(
        self, mock_save_report, mock_save_raw, mock_load_check, mock_load_skip
    ):
        """Test that the script skips if HCI_P2 is valid."""
        mock_load_skip.return_value = True
        
        download_script.main()
        
        mock_load_skip.assert_called_once()
        mock_load_check.assert_not_called()
        mock_save_raw.assert_not_called()
        mock_save_report.assert_called_once()
        
        # Verify the report content
        call_args = mock_save_report.call_args[0][0]
        assert call_args["status"] == "skipped"
        assert "HCI_P2 was valid" in call_args["reason"]

    @patch('code.code_01_download_persona_chat.load_skip_flag')
    @patch('code.code_01_download_persona_chat.load_dataset_with_check')
    @patch('code.code_01_download_persona_chat.save_validation_report')
    def test_skip_if_missing_quality_rating(
        self, mock_save_report, mock_load_check, mock_load_skip
    ):
        """Test that the script skips if quality_rating is missing."""
        mock_load_skip.return_value = False
        mock_load_check.return_value = (
            None, 
            {"status": "skipped", "reason": "missing_required_field", "missing_field": "quality_rating"}
        )
        
        download_script.main()
        
        mock_load_check.assert_called_once()
        mock_save_report.assert_called_once()
        
        call_args = mock_save_report.call_args[0][0]
        assert call_args["status"] == "skipped"
        assert call_args["reason"] == "missing_required_field"

    @patch('code.code_01_download_persona_chat.load_skip_flag')
    @patch('code.code_01_download_persona_chat.load_dataset_with_check')
    @patch('code.code_01_download_persona_chat.save_raw_data')
    @patch('code.code_01_download_persona_chat.generate_checksums_and_manifest')
    @patch('code.code_01_download_persona_chat.save_validation_report')
    def test_success_path(
        self, mock_save_report, mock_gen_manifest, mock_save_raw, mock_load_check, mock_load_skip
    ):
        """Test the successful download and storage path."""
        mock_load_skip.return_value = False
        
        mock_dataset = MagicMock()
        mock_report = {"status": "loaded", "num_rows": 100}
        mock_load_check.return_value = (mock_dataset, mock_report)
        
        mock_save_raw.return_value = "data/raw/persona_chat/persona_chat_raw.parquet"
        mock_gen_manifest.return_value = ({"manifest": "data"}, {"checksum": "abc123"})
        
        download_script.main()
        
        mock_load_check.assert_called_once()
        mock_save_raw.assert_called_once()
        mock_gen_manifest.assert_called_once()
        mock_save_report.assert_called_once()
        
        # Verify success status in report
        call_args = mock_save_report.call_args[0][0]
        assert call_args["status"] == "success"
        
class TestHelperFunctions:
    
    def test_load_skip_flag_file_not_exists(self):
        """Test load_skip_flag when flag file does not exist."""
        # Mock Path.exists to return False
        with patch('code.code_01_download_persona_chat.FLAG_FILE') as mock_flag:
            mock_flag.exists.return_value = False
            result = download_script.load_skip_flag()
            assert result is False
    
    def test_load_skip_flag_file_exists_true(self):
        """Test load_skip_flag when flag file exists and is 'true'."""
        with patch('code.code_01_download_persona_chat.FLAG_FILE') as mock_flag:
            mock_flag.exists.return_value = True
            mock_flag.read_text.return_value = "true"
            result = download_script.load_skip_flag()
            assert result is True

    def test_load_skip_flag_file_exists_false(self):
        """Test load_skip_flag when flag file exists and is 'false'."""
        with patch('code.code_01_download_persona_chat.FLAG_FILE') as mock_flag:
            mock_flag.exists.return_value = True
            mock_flag.read_text.return_value = "false"
            result = download_script.load_skip_flag()
            assert result is False