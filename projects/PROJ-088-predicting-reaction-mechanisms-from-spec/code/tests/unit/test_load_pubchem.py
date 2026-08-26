"""
Unit tests for load_pubchem.py
"""
import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import json
import tempfile

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.load_pubchem import validate_url, fetch_pubchem_data, load_pubchem_data
from src.ingestion.provenance_filter import should_exclude_row


class TestValidateUrl:
    def test_valid_http_url(self):
        assert validate_url("http://example.com/data") is True
    
    def test_valid_https_url(self):
        assert validate_url("https://huggingface.co/datasets/test") is True
    
    def test_invalid_url_no_scheme(self):
        assert validate_url("example.com/data") is False
    
    def test_invalid_url_malformed(self):
        assert validate_url("ht!tp://example.com") is False
    
    def test_empty_url(self):
        assert validate_url("") is False


class TestLoadPubchemData:
    @patch('src.ingestion.load_pubchem.load_dataset')
    def test_fetch_data_success(self, mock_load_dataset):
        # Mock a dataset with valid provenance
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"provenance": "kinetic_studies", "chemical_shift": 12.5, "molecule_id": "M1", "mechanism_label": "SN2"},
            {"provenance": "validated_intermediate", "chemical_shift": 10.2, "molecule_id": "M2", "mechanism_label": "SN1"},
            {"provenance": "unknown_source", "chemical_shift": 5.0, "molecule_id": "M3", "mechanism_label": "E1"}
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        df = fetch_pubchem_data(streaming=True)
        
        # Should have loaded 3 rows initially
        assert len(df) == 3
        assert "provenance" in df.columns
    
    @patch('src.ingestion.load_pubchem.load_dataset')
    def test_provenance_filtering(self, mock_load_dataset):
        # Mock a dataset with mixed provenance
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"provenance": "kinetic_studies", "chemical_shift": 12.5, "molecule_id": "M1", "mechanism_label": "SN2"},
            {"provenance": "validated_intermediate", "chemical_shift": 10.2, "molecule_id": "M2", "mechanism_label": "SN1"},
            {"provenance": "unknown_source", "chemical_shift": 5.0, "molecule_id": "M3", "mechanism_label": "E1"},
            {"provenance": None, "chemical_shift": 3.0, "molecule_id": "M4", "mechanism_label": "SN2"},
            {"chemical_shift": 8.0, "molecule_id": "M5", "mechanism_label": "E1"} # Missing provenance key
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        # We can't easily test the full load_pubchem_data with mocking the file write in a unit test
        # without creating temp dirs, so we test the filtering logic directly on the DataFrame
        # or mock the internal fetch.
        # Here we simulate the result of fetch and then apply the filter logic manually to verify.
        
        df_raw = pd.DataFrame([
            {"provenance": "kinetic_studies", "chemical_shift": 12.5, "molecule_id": "M1", "mechanism_label": "SN2"},
            {"provenance": "validated_intermediate", "chemical_shift": 10.2, "molecule_id": "M2", "mechanism_label": "SN1"},
            {"provenance": "unknown_source", "chemical_shift": 5.0, "molecule_id": "M3", "mechanism_label": "E1"},
            {"provenance": None, "chemical_shift": 3.0, "molecule_id": "M4", "mechanism_label": "SN2"},
            {"chemical_shift": 8.0, "molecule_id": "M5", "mechanism_label": "E1"}
        ])
        
        valid_values = {"kinetic_studies", "validated_intermediate"}
        filtered = df_raw[df_raw.apply(lambda row: not should_exclude_row(row, valid_values), axis=1)]
        
        # Only first two rows should remain
        assert len(filtered) == 2
        assert all(filtered["provenance"].isin(valid_values))
    
    @patch('src.ingestion.load_pubchem.load_dataset')
    def test_fetch_data_empty(self, mock_load_dataset):
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(RuntimeError):
            load_pubchem_data()
    
    @patch('src.ingestion.load_pubchem.load_dataset')
    def test_missing_columns(self, mock_load_dataset):
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"chemical_shift": 12.5} # Missing provenance, molecule_id, etc.
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(ValueError):
            load_pubchem_data()
    
    def test_validate_url_integration(self):
        # Test that invalid URLs are rejected
        assert validate_url("ftp://invalid.com") is False
        assert validate_url("http://valid.com") is True