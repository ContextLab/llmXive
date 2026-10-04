import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust imports based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion.tng_loader import (
    calculate_sha256,
    get_api_key,
    fetch_halos_list,
    load_galaxy_properties_from_tng,
    load_galaxy_properties
)
from utils.config import get_data_processed_path

class TestTNGLoader:
    """Tests for the TNG loader module."""

    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(str(test_file))
        expected_checksum = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected_checksum

    def test_get_api_key_missing(self, monkeypatch):
        """Test that get_api_key raises error when key is missing."""
        monkeypatch.delenv("TNG_API_KEY", raising=False)
        assert get_api_key() is None

    @patch('code.ingestion.tng_loader.requests.get')
    def test_fetch_halos_list_success(self, mock_get, monkeypatch):
        """Test successful fetching of halos list."""
        monkeypatch.setenv("TNG_API_KEY", "fake_key")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": 1}, {"id": 2}],
            "count": 2
        }
        mock_get.return_value = mock_response
        
        halos = fetch_halos_list()
        assert len(halos) == 2
        assert halos[0]["id"] == 1

    @patch('code.ingestion.tng_loader.requests.get')
    def test_fetch_halos_list_failure(self, mock_get, monkeypatch):
        """Test failure in fetching halos list."""
        monkeypatch.setenv("TNG_API_KEY", "fake_key")
        
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            fetch_halos_list()

    @patch('code.ingestion.tng_loader.fetch_halos_list')
    @patch('code.ingestion.tng_loader.fetch_tng_halo_data')
    def test_load_galaxy_properties_from_tng(self, mock_fetch_halo, mock_fetch_list, tmp_path):
        """Test extraction of galaxy properties."""
        # Mock halo list
        mock_fetch_list.return_value = [{"id": 123}]
        
        # Mock halo data with a central subhalo
        mock_halo_data = {
            "subhalos": [
                {
                    "subhalo_id": 0,
                    "stellar_mass": 1.0e10,
                    "sfr": 5.0,
                    "half_mass_rad": 2.5,
                    "mass": [0, 0, 1.0e10, 0, 0, 0]
                },
                {
                    "subhalo_id": 1,
                    "stellar_mass": 1.0e9,
                    "sfr": 0.1,
                    "half_mass_rad": 1.0,
                    "mass": [0, 0, 1.0e9, 0, 0, 0]
                }
            ]
        }
        mock_fetch_halo.return_value = mock_halo_data
        
        output_path = str(tmp_path / "galaxy_properties.csv")
        properties = load_galaxy_properties_from_tng(output_path)
        
        assert len(properties) == 1
        assert properties[0]["halo_id"] == 123
        assert properties[0]["galaxy_id"] == 0
        assert properties[0]["stellar_mass"] == 1.0e10
        assert properties[0]["sfr"] == 5.0
        assert properties[0]["effective_radius"] == 2.5

    def test_load_galaxy_properties_creates_file(self, tmp_path, monkeypatch):
        """Test that load_galaxy_properties creates the output file."""
        # Mock the API calls to avoid network requests
        with patch('code.ingestion.tng_loader.fetch_halos_list') as mock_list, \
             patch('code.ingestion.tng_loader.fetch_tng_halo_data') as mock_halo:
            
            monkeypatch.setenv("TNG_API_KEY", "fake_key")
            
            mock_list.return_value = [{"id": 999}]
            mock_halo.return_value = {
                "subhalos": [{
                    "subhalo_id": 0,
                    "stellar_mass": 5.0e10,
                    "sfr": 2.0,
                    "half_mass_rad": 3.0,
                    "mass": [0, 0, 5.0e10, 0, 0, 0]
                }]
            }
            
            output_path = str(tmp_path / "test_galaxy.csv")
            load_galaxy_properties(output_path)
            
            assert os.path.exists(output_path)
            # Verify associational flag is present
            with open(output_path, 'r') as f:
                first_line = f.readline()
                assert "# associational_only=true" in first_line