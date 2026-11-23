import pytest
import pandas as pd
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.ingestion.load_nist import validate_url, load_nist_data, VALID_PROVENANCE_TYPES

class TestValidateUrl:
    def test_valid_nist_url(self):
        assert validate_url("https://webbook.nist.gov/cgi/cbook.cgi") is True
        assert validate_url("http://webbook.nist.gov/cgi/cbook.cgi") is True

    def test_invalid_domain(self):
        assert validate_url("https://example.com") is False
        assert validate_url("https://nist.gov.fake.com") is False

    def test_invalid_scheme(self):
        assert validate_url("ftp://webbook.nist.gov") is False

class TestLoadNistData:
    @patch('src.ingestion.load_nist.fetch_nist_spectrum')
    def test_load_data_with_valid_provenance(self, mock_fetch):
        # Mock response with valid provenance
        mock_fetch.return_value = {
            'cas_number': '74-82-8',
            'spectrum': [{'wavenumber': 1000, 'intensity': 50}],
            'provenance': 'kinetic studies',
            'source': 'NIST WebBook'
        }
        
        df = load_nist_data(['74-82-8'])
        
        assert len(df) == 1
        assert df.iloc[0]['provenance'] == 'kinetic studies'
        assert df.iloc[0]['cas_number'] == '74-82-8'

    @patch('src.ingestion.load_nist.fetch_nist_spectrum')
    def test_load_data_filters_invalid_provenance(self, mock_fetch):
        # Mock response with invalid provenance
        mock_fetch.return_value = {
            'cas_number': '75-15-0',
            'spectrum': [{'wavenumber': 1000, 'intensity': 50}],
            'provenance': 'product structure',
            'source': 'NIST WebBook'
        }
        
        df = load_nist_data(['75-15-0'])
        
        # Should be empty because provenance is invalid
        assert len(df) == 0

    @patch('src.ingestion.load_nist.fetch_nist_spectrum')
    def test_load_data_mixed_provenance(self, mock_fetch):
        # Mock responses: one valid, one invalid
        side_effects = [
            {
                'cas_number': '74-82-8',
                'spectrum': [{'wavenumber': 1000, 'intensity': 50}],
                'provenance': 'kinetic studies',
                'source': 'NIST WebBook'
            },
            {
                'cas_number': '75-15-0',
                'spectrum': [{'wavenumber': 1000, 'intensity': 50}],
                'provenance': 'product structure',
                'source': 'NIST WebBook'
            },
            {
                'cas_number': '75-13-8',
                'spectrum': [{'wavenumber': 1000, 'intensity': 50}],
                'provenance': 'validated intermediates',
                'source': 'NIST WebBook'
            }
        ]
        mock_fetch.side_effect = side_effects
        
        df = load_nist_data(['74-82-8', '75-15-0', '75-13-8'])
        
        # Should have 2 records (kinetic studies and validated intermediates)
        assert len(df) == 2
        provenances = set(df['provenance'].unique())
        assert provenances == {'kinetic studies', 'validated intermediates'}

    @patch('src.ingestion.load_nist.fetch_nist_spectrum')
    def test_load_data_handles_fetch_failure(self, mock_fetch):
        # Mock response returns None (fetch failure)
        mock_fetch.return_value = None
        
        df = load_nist_data(['74-82-8'])
        
        assert len(df) == 0