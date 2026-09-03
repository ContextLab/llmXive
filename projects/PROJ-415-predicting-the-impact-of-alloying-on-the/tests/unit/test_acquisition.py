import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.acquisition import fetch_real_diffusion_data_from_nist, acquire_and_save_diffusion_data
from config import DATA_DIR

class TestAcquisition:
    @patch('code.data.acquisition.requests.get')
    def test_fetch_real_data_success(self, mock_get):
        """Test successful fetch of real data."""
        # Generate 60 rows of mock data
        rows = ["solute,host,activation_energy,temperature_range"]
        for i in range(60):
            rows.append(f"Solute{i},Host{str(i%10)},0.5,300-500")
        mock_response = MagicMock()
        mock_response.text = "\n".join(rows)
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        data = fetch_real_diffusion_data_from_nist()
        assert len(data) == 60
        assert 'solute' in data[0]

    @patch('code.data.acquisition.requests.get')
    def test_fetch_real_data_insufficient(self, mock_get):
        """Test that insufficient data raises SystemExit."""
        # Generate only 10 rows of mock data
        rows = ["solute,host,activation_energy,temperature_range"]
        for i in range(10):
            rows.append(f"Solute{i},Host{str(i%10)},0.5,300-500")
        
        mock_response = MagicMock()
        mock_response.text = "\n".join(rows)
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # We test acquire_and_save_diffusion_data which calls fetch and checks count
        with pytest.raises(SystemExit, match="Data Insufficiency: N < 50"):
            # Mock the file writing to avoid actual disk writes in test
            with patch('code.data.acquisition.open', mock_open()):
                acquire_and_save_diffusion_data()

    @patch('code.data.acquisition.requests.get')
    def test_fetch_real_data_network_error(self, mock_get):
        """Test that network error raises SystemExit."""
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Network error")

        with pytest.raises(SystemExit, match="Data Fetch Failed"):
            acquire_and_save_diffusion_data()

    def test_output_file_created(self):
        """Test that the output file is created with sufficient data."""
        # Mock a large dataset
        rows = ["solute,host,activation_energy,temperature_range"]
        for i in range(100):
            rows.append(f"Solute{i},Host{str(i%10)},0.5,300-500")
        mock_data = "\n".join(rows)
        
        with patch('code.data.acquisition.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            output_path = str(DATA_DIR / "raw" / "test_fetched_diffusion.csv")
            try:
                acquire_and_save_diffusion_data(output_path)
                assert Path(output_path).exists()
                assert Path(output_path).stat().st_size > 0
            finally:
                if Path(output_path).exists():
                    os.remove(output_path)