"""
Tests for data acquisition module.
"""
import pytest
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from code import data_acquisition
from src.config import get_config

class TestMaterialsProjectClient:
    """Tests for MaterialsProjectClient."""

    def test_init(self):
        """Test client initialization."""
        client = data_acquisition.MaterialsProjectClient("test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.materialsproject.org"
        assert client.retries == 3

    @patch('code.data_acquisition.MaterialsProjectClient._get_session')
    def test_fetch_materials_success(self, mock_session):
        """Test successful material fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "material_id": "mp-123",
                    "formula": "C",
                    "structure": {"sites": [], "lattice": {}},
                    "nsites": 2,
                    "space_group": "P6/mmm",
                    "energy_per_atom": -5.0,
                    "formation_energy_per_atom": -0.1,
                    "band_gap": 0.0,
                    "is_metal": False
                }
            ]
        }
        mock_session.return_value.get.return_value = mock_response

        client = data_acquisition.MaterialsProjectClient("test_key")
        materials = client.fetch_materials("C", limit=10)

        assert len(materials) == 1
        assert materials[0]["material_id"] == "mp-123"
        assert materials[0]["formula"] == "C"

    @patch('code.data_acquisition.MaterialsProjectClient._get_session')
    def test_fetch_materials_rate_limit(self, mock_session):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_session.return_value.get.return_value = mock_response

        client = data_acquisition.MaterialsProjectClient("test_key")

        with pytest.raises(Exception):
            client.fetch_materials("C", limit=10)

class TestSerializeStructure:
    """Tests for structure serialization."""

    def test_serialize_valid_structure(self):
        """Test serialization of valid structure."""
        structure = {
            "sites": [{"species": "C", "coords": [0, 0, 0]}],
            "lattice": {"a": 2.5, "b": 2.5, "c": 10.0}
        }
        result = data_acquisition.serialize_structure(structure)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["sites"][0]["species"] == "C"

    def test_serialize_none_structure(self):
        """Test serialization of None structure."""
        result = data_acquisition.serialize_structure(None)
        assert result == ""

class TestEnsureOutputDirectories:
    """Tests for output directory creation."""

    def test_ensure_directories(self, tmp_path):
        """Test directory creation."""
        # Change to temp directory for testing
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            
            # Create a subdirectory structure similar to project
            output_dir = tmp_path / "data" / "raw"
            output_dir.mkdir(parents=True, exist_ok=False)
            
            result = data_acquisition.ensure_output_directories()
            assert result.exists()
            assert result.is_dir()
        finally:
            os.chdir(original_cwd)

class TestRunAcquisition:
    """Tests for main acquisition function."""

    @patch('code.data_acquisition.MaterialsProjectClient')
    def test_run_acquisition_success(self, mock_client_class, tmp_path):
        """Test successful acquisition run."""
        import os
        os.chdir(tmp_path)
        
        # Mock client instance
        mock_client = Mock()
        mock_client.fetch_materials.return_value = [
            {
                "material_id": "mp-123",
                "formula": "C",
                "structure": {"sites": [], "lattice": {}},
                "nsites": 2,
                "space_group": "P6/mmm",
                "energy_per_atom": -5.0,
                "formation_energy_per_atom": -0.1,
                "band_gap": 0.0,
                "is_metal": False
            }
        ]
        mock_client_class.return_value = mock_client

        output_path = str(tmp_path / "data" / "raw" / "test_output.csv")
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        data_acquisition.run_acquisition("test_key", output_path)
        
        # Verify file was created
        assert Path(output_path).exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 1

    @patch('code.data_acquisition.MaterialsProjectClient')
    def test_run_acquisition_empty_result(self, mock_client_class):
        """Test acquisition with no results."""
        mock_client = Mock()
        mock_client.fetch_materials.return_value = []
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to fetch any materials"):
            data_acquisition.run_acquisition("test_key", "/tmp/empty.csv")

class TestMain:
    """Tests for main entry point."""

    @patch('code.data_acquisition.run_acquisition')
    @patch('code.data_acquisition.ensure_output_directories')
    @patch('code.data_acquisition.get_config')
    def test_main_success(self, mock_get_config, mock_ensure_dirs, mock_run):
        """Test successful main execution."""
        mock_config = Mock()
        mock_config.get.return_value = "test_api_key"
        mock_get_config.return_value = mock_config
        mock_ensure_dirs.return_value = Path("/tmp")
        
        data_acquisition.main()
        
        mock_run.assert_called_once()

    @patch('code.data_acquisition.get_config')
    def test_main_no_api_key(self, mock_get_config):
        """Test main execution without API key."""
        mock_config = Mock()
        mock_config.get.return_value = None
        mock_get_config.return_value = mock_config

        with pytest.raises(ValueError, match="Materials Project API key not found"):
            data_acquisition.main()