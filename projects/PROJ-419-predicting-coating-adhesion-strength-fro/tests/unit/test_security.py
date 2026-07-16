import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ingestion import (
    validate_url_parameter,
    fetch_materials_project_data,
    fetch_nist_surface_metrology_data,
    fetch_open_access_literature_data
)

class TestURLValidation:
    """Test cases for URL parameter validation."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs pass validation."""
        url = "https://api.materialsproject.org/v2/materials?api_key=test123"
        assert validate_url_parameter(url) is True

    def test_valid_http_url(self):
        """Test that valid HTTP URLs pass validation."""
        url = "http://srdata.nist.gov/surface-metrology/api/v1/datasets"
        assert validate_url_parameter(url) is True

    def test_invalid_scheme(self):
        """Test that invalid schemes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            validate_url_parameter("ftp://api.materialsproject.org/data")

    def test_unauthorized_host(self):
        """Test that unauthorized hosts raise ValueError."""
        with pytest.raises(ValueError, match="Unauthorized host"):
            validate_url_parameter("https://evil.com/api/data")

    def test_sql_injection_in_query(self):
        """Test that SQL injection patterns in query params are detected."""
        urls = [
            "https://api.materialsproject.org/data?id=1; drop table materials",
            "https://api.materialsproject.org/data?id=1' OR '1'='1",
            "https://api.materialsproject.org/data?id=1--",
        ]
        for url in urls:
            with pytest.raises(ValueError, match="Potential SQL injection"):
                validate_url_parameter(url)

    def test_path_traversal(self):
        """Test that path traversal is detected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_url_parameter("https://api.materialsproject.org/../../../etc/passwd")

    def test_empty_url(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            validate_url_parameter("")

    def test_none_url(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            validate_url_parameter(None)

class TestMaterialsProjectAPI:
    """Test cases for Materials Project API interaction."""

    @patch('ingestion.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch from Materials Project."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'material_id': 'mp-123'}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_materials_project_data("valid_api_key")
        
        assert len(result) == 1
        assert result[0]['material_id'] == 'mp-123'
        mock_get.assert_called_once()

    def test_invalid_api_key_format(self):
        """Test that short API keys raise ValueError."""
        with pytest.raises(ValueError, match="Invalid API key format"):
            fetch_materials_project_data("short")

    def test_invalid_formula_format(self):
        """Test that invalid formula formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid chemical formula format"):
            fetch_materials_project_data("valid_key", formula="TiO2; DROP TABLE materials")

class TestNISTAPI:
    """Test cases for NIST API interaction."""

    @patch('ingestion.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch from NIST."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'dataset_id': 'nist-001'}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_nist_surface_metrology_data("nist-001")
        
        assert len(result) == 1
        assert result[0]['dataset_id'] == 'nist-001'

    def test_invalid_dataset_id(self):
        """Test that invalid dataset IDs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid dataset ID format"):
            fetch_nist_surface_metrology_data("id; DROP TABLE datasets")

    def test_empty_dataset_id(self):
        """Test that empty dataset ID raises ValueError."""
        with pytest.raises(ValueError, match="Dataset ID must be a non-empty string"):
            fetch_nist_surface_metrology_data("")

class TestLiteratureAPI:
    """Test cases for open-access literature API interaction."""

    @patch('ingestion.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch from literature source."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [{'title': 'Paper 1'}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_open_access_literature_data("https://example.com/api", {"q": "adhesion"})
        
        assert len(result) == 1
        assert result[0]['title'] == 'Paper 1'

    def test_sql_injection_in_params(self):
        """Test that SQL injection in query params is detected."""
        with pytest.raises(ValueError, match="Potential injection"):
            fetch_open_access_literature_data("https://example.com/api", {"q": "adhesion; DROP TABLE papers"})

    def test_invalid_base_url(self):
        """Test that invalid base URLs raise ValueError."""
        with pytest.raises(ValueError, match="Unauthorized host"):
            fetch_open_access_literature_data("https://malicious-site.com/api")

class TestInputSanitization:
    """Test cases for input sanitization across all functions."""

    def test_null_input_handling(self):
        """Test that None inputs are handled gracefully."""
        with pytest.raises(ValueError):
            validate_url_parameter(None)

        with pytest.raises(ValueError):
            fetch_materials_project_data(None)

        with pytest.raises(ValueError):
            fetch_nist_surface_metrology_data(None)

    def test_non_string_input(self):
        """Test that non-string inputs are rejected."""
        with pytest.raises(ValueError):
            validate_url_parameter(123)

        with pytest.raises(ValueError):
            fetch_materials_project_data(123)

        with pytest.raises(ValueError):
            fetch_nist_surface_metrology_data(123)