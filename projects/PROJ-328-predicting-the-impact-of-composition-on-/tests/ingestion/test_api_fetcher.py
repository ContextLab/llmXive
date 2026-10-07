"""
Unit tests for code/ingestion/api_fetcher.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.api_fetcher import APIFetcher, ConfigurationError, DataFetchError

class TestAPIFetcher:
    def test_init_missing_sources(self):
        """Test that init raises ConfigurationError if sources.yaml is missing."""
        with pytest.raises(ConfigurationError):
            APIFetcher(sources_config_path=Path("non_existent.yaml"))

    @patch('ingestion.api_fetcher.requests.get')
    def test_fetch_materials_project_success(self, mock_get):
        """Test successful fetch from Materials Project."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'material_id': 'mp-123',
                    'pretty_formula': 'SnCu',
                    'composition': {'Sn': 0.9, 'Cu': 0.1},
                    'properties': {}
                }
            ]
        }
        mock_get.return_value = mock_response

        # Create a temporary sources.yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            materials_project:
              name: Materials Project
              type: api
              url: https://api.materialsproject.org
              api_key_env: MP_API_KEY
              endpoint: /materials
              verified: true
            """)
            temp_path = f.name

        try:
            # Set env var
            os.environ['MP_API_KEY'] = 'test_key'
            fetcher = APIFetcher(sources_config_path=Path(temp_path))
            
            # Mock the _load_yaml to return our temp config
            with patch.object(fetcher, '_load_yaml', return_value={'materials_project': {'verified': True, 'url': 'https://api.materialsproject.org', 'api_key_env': 'MP_API_KEY', 'endpoint': '/materials'}}):
                result = fetcher._fetch_materials_project()
                
                assert len(result) == 1
                assert result[0]['material_id'] == 'mp-123'
                assert result[0]['source'] == 'materials_project'
        finally:
            os.unlink(temp_path)
            if 'MP_API_KEY' in os.environ:
                del os.environ['MP_API_KEY']

    @patch('ingestion.api_fetcher.requests.get')
    def test_fetch_openalloy_success(self, mock_get):
        """Test successful fetch from OpenAlloy."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 'oa-456',
                'name': 'SnAgCu',
                'composition': {'Sn': 0.96, 'Ag': 0.03, 'Cu': 0.01},
                'hardness_hv': 50.0
            }
        ]
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            openalloy:
              name: OpenAlloy Database
              type: api
              url: https://openalloy.org/api/v1
              endpoint: /compositions
              verified: true
            """)
            temp_path = f.name

        try:
            fetcher = APIFetcher(sources_config_path=Path(temp_path))
            
            with patch.object(fetcher, '_load_yaml', return_value={'openalloy': {'verified': True, 'url': 'https://openalloy.org/api/v1', 'endpoint': '/compositions'}}):
                result = fetcher._fetch_openalloy()
                
                assert len(result) == 1
                assert result[0]['alloy_id'] == 'oa-456'
                assert result[0]['hardness_hv'] == 50.0
        finally:
            os.unlink(temp_path)

    def test_fetch_nist_uci_skipped(self):
        """Test that NIST/UCI fetch returns empty if no URL."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            nist_uci:
              name: NIST/UCI Repository
              type: repository
              url: https://archive.ics.uci.edu/ml/datasets.php
              dataset_id: solder_alloys
              verified: true
            """)
            temp_path = f.name

        try:
            fetcher = APIFetcher(sources_config_path=Path(temp_path))
            result = fetcher._fetch_nist_uci()
            assert result == []
        finally:
            os.unlink(temp_path)