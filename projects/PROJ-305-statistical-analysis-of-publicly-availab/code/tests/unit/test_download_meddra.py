"""
Unit tests for download_meddra.py
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.download_meddra import (
    check_meddra_package,
    extract_soc_mapping_from_package,
    extract_soc_mapping_from_zip,
    save_mapping_to_csv,
    main
)

class TestMeddraDownload:
    """Tests for MedDRA download functionality"""

    def test_check_meddra_package_installed(self):
        """Test that check_meddra_package returns True when package is available"""
        # Mock the import to simulate package being installed
        with patch.dict('sys.modules', {'meddra': MagicMock()}):
            result = check_meddra_package()
            assert result is True

    def test_check_meddra_package_not_installed(self):
        """Test that check_meddra_package returns False when package is missing"""
        # Ensure meddra is not in sys.modules
        if 'meddra' in sys.modules:
            del sys.modules['meddra']
        
        # Temporarily hide the package
        original_modules = sys.modules.copy()
        sys.modules = {k: v for k, v in sys.modules.items() if not k.startswith('meddra')}
        
        try:
            result = check_meddra_package()
            assert result is False
        finally:
            sys.modules = original_modules

    def test_extract_soc_mapping_from_package(self):
        """Test extraction of SOC mapping from meddra package"""
        # Mock the meddra package
        mock_meddra = MagicMock()
        mock_meddra.__version__ = "26.1"
        mock_meddra.load_meddra.return_value = [
            {"SOC_CD": "10000001", "SOC": "Blood and lymphatic system disorders", "HLGT": "", "HLT": "", "LLT": ""},
            {"SOC_CD": "10000002", "SOC": "Cardiac disorders", "HLGT": "", "HLT": "", "LLT": ""}
        ]
        
        with patch.dict('sys.modules', {'meddra': mock_meddra}):
            mapping, source = extract_soc_mapping_from_package()
            
            assert len(mapping) == 2
            assert mapping[0]["code"] == "10000001"
            assert mapping[0]["name"] == "Blood and lymphatic system disorders"
            assert "meddra" in source

    def test_save_mapping_to_csv(self):
        """Test saving mapping to CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_mapping.csv"
            mapping = [
                {"code": "10000001", "name": "Test SOC", "hlgt": "", "hlt": "", "llt": ""}
            ]
            
            save_mapping_to_csv(mapping, output_path, "test_source")
            
            assert output_path.exists()
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "# Source: test_source" in content
            assert "10000001" in content
            assert "Test SOC" in content

    def test_save_mapping_to_csv_empty(self):
        """Test that empty mapping raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_mapping.csv"
            
            with pytest.raises(ValueError, match="Mapping list is empty"):
                save_mapping_to_csv([], output_path, "test_source")

    def test_main_success_with_package(self):
        """Test main function when meddra package is available"""
        with patch('src.data.download_meddra.check_meddra_package', return_value=True):
            with patch('src.data.download_meddra.extract_soc_mapping_from_package') as mock_extract:
                mock_extract.return_value = (
                    [{"code": "10000001", "name": "Test", "hlgt": "", "hlt": "", "llt": ""}],
                    "test_source"
                )
                
                with patch('src.data.download_meddra.save_mapping_to_csv') as mock_save:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # Temporarily change the output path
                        from src.data import download_meddra
                        original_output = download_meddra.OUTPUT_FILE
                        download_meddra.OUTPUT_FILE = Path(tmpdir) / "meddra_soc_mapping.csv"
                        
                        try:
                            result = main()
                            assert result == 0
                            mock_save.assert_called_once()
                        finally:
                            download_meddra.OUTPUT_FILE = original_output

    def test_main_failure_no_source(self):
        """Test main function when no source is available"""
        with patch('src.data.download_meddra.check_meddra_package', return_value=False):
            with patch('src.data.download_meddra.download_from_ema_mirror', return_value=None):
                with patch('src.data.download_meddra.setup_logging') as mock_log:
                    mock_logger = MagicMock()
                    mock_log.return_value = mock_logger
                    
                    result = main()
                    
                    assert result == 1
                    assert any("FATAL" in str(call) for call in mock_logger.error.call_args_list)
