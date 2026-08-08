import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.download import get_clo_migratory_list, check_real_data_available, compute_sha256

class TestDownloadModule:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    def test_compute_sha256_basic(self, temp_dir):
        """Test basic SHA-256 computation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

    def test_check_real_data_available_success(self):
        """Test successful URL check."""
        # This is a mock test; in real execution, we might test against a known good URL
        # For now, we verify the function handles the request correctly
        with patch('src.data.download.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            assert check_real_data_available("http://example.com") is True

    def test_check_real_data_available_failure(self):
        """Test failed URL check."""
        with patch('src.data.download.requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection error")
            assert check_real_data_available("http://invalid.url") is False

    @patch('src.data.download.pd.read_csv')
    @patch('src.data.download.check_real_data_available')
    def test_get_clo_migratory_list_success(self, mock_check, mock_read_csv, temp_dir):
        """Test successful retrieval of migratory list."""
        mock_check.return_value = True
        
        # Create a mock DataFrame
        mock_df = pd.DataFrame({
            'Common Name': ['Species A', 'Species B', 'Species C'],
            'Scientific Name': ['SpA', 'SpB', 'SpC'],
            'Species Status': ['Migratory', 'Resident', 'Migratory']
        })
        mock_read_csv.return_value = mock_df

        output_path = temp_dir / "output.csv"
        result_path = get_clo_migratory_list(output_path)

        assert result_path.exists()
        result_df = pd.read_csv(result_path)
        assert len(result_df) == 2  # Only migratory species
        assert 'Common Name' in result_df.columns

    @patch('src.data.download.check_real_data_available')
    def test_get_clo_migratory_list_unavailable(self, mock_check, temp_dir):
        """Test handling of unavailable source."""
        mock_check.return_value = False
        output_path = temp_dir / "output.csv"
        
        with pytest.raises(RuntimeError, match="CRITICAL: Real data source"):
            get_clo_migratory_list(output_path)

    @patch('src.data.download.pd.read_csv')
    @patch('src.data.download.check_real_data_available')
    def test_get_clo_migratory_list_no_migratory(self, mock_check, mock_read_csv, temp_dir):
        """Test handling of empty migratory result."""
        mock_check.return_value = True
        
        mock_df = pd.DataFrame({
            'Common Name': ['Species A'],
            'Scientific Name': ['SpA'],
            'Species Status': ['Resident']
        })
        mock_read_csv.return_value = mock_df

        output_path = temp_dir / "output.csv"
        
        with pytest.raises(RuntimeError, match="No migratory species found"):
            get_clo_migratory_list(output_path)