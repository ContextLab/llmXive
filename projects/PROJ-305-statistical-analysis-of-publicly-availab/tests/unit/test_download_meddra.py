import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path if necessary
# Assuming the test is run from the project root or code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.download_meddra import (
    check_meddra_package,
    extract_soc_mapping_from_package,
    save_mapping_to_csv,
    main
)

class TestMeddraDownload:
    def test_check_meddra_package_installed(self, monkeypatch):
        """Test that check_meddra_package returns True when package is installed."""
        # Mock the import to succeed
        mock_module = MagicMock()
        monkeypatch.setitem(sys.modules, 'meddra', mock_module)
        
        result = check_meddra_package()
        assert result is True

    def test_check_meddra_package_not_installed(self, monkeypatch):
        """Test that check_meddra_package returns False when package is missing."""
        # Ensure 'meddra' is not in modules
        if 'meddra' in sys.modules:
            del sys.modules['meddra']
        
        with patch.dict(sys.modules, {'meddra': None}):
            # Simulate ImportError
            with patch('builtins.__import__', side_effect=ImportError("No module named 'meddra'")):
                result = check_meddra_package()
                assert result is False

    def test_save_mapping_to_csv(self, tmp_path):
        """Test that save_mapping_to_csv creates a valid CSV file."""
        mapping = {
            '10000001': 'Soc code 1',
            '10000002': 'Soc code 2'
        }
        output_file = tmp_path / "test_mapping.csv"
        
        save_mapping_to_csv(mapping, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'SOC_CODE' in content
            assert 'SOC_NAME' in content
            assert '10000001' in content
            assert 'Soc code 1' in content

    @patch('src.data.download_meddra.extract_soc_mapping_from_package')
    @patch('src.data.download_meddra.check_meddra_package')
    def test_main_with_package_success(self, mock_check, mock_extract, tmp_path, monkeypatch):
        """Test main function when package extraction succeeds."""
        mock_check.return_value = True
        mock_extract.return_value = {'10000001': 'Test SOC'}
        
        # Temporarily change the output path for the test
        original_output = Path(__file__).resolve().parent.parent.parent.parent / "data" / "meddra_soc_mapping.csv"
        test_output = tmp_path / "meddra_soc_mapping.csv"
        
        with patch('src.data.download_meddra.OUTPUT_FILE', test_output):
            main()
        
        assert test_output.exists()

    @patch('src.data.download_meddra.check_meddra_package')
    def test_main_fails_loudly_no_source(self, mock_check, caplog):
        """Test that main fails loudly if no source is available."""
        mock_check.return_value = False
        
        # Ensure no fallback file exists
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock the PROJECT_ROOT to use a temp dir without the fallback file
            with patch('src.data.download_meddra.PROJECT_ROOT', Path(tmp_dir)):
                with patch('src.data.download_meddra.OUTPUT_FILE', Path(tmp_dir) / "output.csv"):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 1
                    assert "No verified source" in caplog.text