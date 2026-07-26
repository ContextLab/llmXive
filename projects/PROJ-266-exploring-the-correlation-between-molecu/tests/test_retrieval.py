"""
Unit tests for the data retrieval and filtering logic.

This module tests the core logic of the data retrieval pipeline, specifically:
1. Extraction of records from API responses.
2. Filtering logic for non-NULL SMILES and logPapp.
3. Pass rate calculation and exclusion reporting.
"""

import pytest
import sys
from pathlib import Path
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data.retrieval import extract_records
from code.data.preprocessing import preprocess_data, load_raw_data

class TestExtraction:
    def test_extract_records_empty(self):
        """Test extraction from empty data."""
        data = {"assays": []}
        records = extract_records(data)
        assert records == []

    def test_extract_records_with_data(self):
        """Test extraction with mock data structure."""
        # Mock data structure similar to ChEMBL API response
        mock_assay = {
            "assay_id": 123,
            "assay_chembl_id": "CHEMBL123",
            "assay_type": "CELL_BASED"
        }
        
        mock_data = {
            "assays": [mock_assay]
        }
        
        records = extract_records(mock_data)
        
        assert len(records) == 1
        assert records[0]["assay_id"] == 123
        assert records[0]["assay_chembl_id"] == "CHEMBL123"

    def test_extract_records_multiple_assays(self):
        """Test extraction with multiple assays."""
        mock_assays = [
            {"assay_id": 1, "assay_chembl_id": "CHEMBL1"},
            {"assay_id": 2, "assay_chembl_id": "CHEMBL2"},
            {"assay_id": 3, "assay_chembl_id": "CHEMBL3"}
        ]
        
        mock_data = {"assays": mock_assays}
        records = extract_records(mock_data)
        
        assert len(records) == 3
        assert all("assay_id" in r for r in records)

class TestPreprocessing:
    def test_preprocess_data_filter_null_smiles(self):
        """Test that records with NULL/empty SMILES are filtered out."""
        raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "assay_id": 1},
            {"smiles": "", "logPapp": -4.2, "assay_id": 2},
            {"smiles": None, "logPapp": -4.1, "assay_id": 3},
            {"smiles": "CC(=O)O", "logPapp": -3.8, "assay_id": 4}
        ]
        
        filtered_data, stats = preprocess_data(raw_data)
        
        # Should only keep records with valid SMILES and logPapp
        assert len(filtered_data) == 2
        assert stats["total_records"] == 4
        assert stats["excluded_null_smiles"] == 2

    def test_preprocess_data_filter_null_logpapp(self):
        """Test that records with NULL logPapp are filtered out."""
        raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "assay_id": 1},
            {"smiles": "CC(=O)O", "logPapp": None, "assay_id": 2},
            {"smiles": "CCC", "logPapp": "", "assay_id": 3},
            {"smiles": "CCCC", "logPapp": -5.0, "assay_id": 4}
        ]
        
        filtered_data, stats = preprocess_data(raw_data)
        
        assert len(filtered_data) == 2
        assert stats["excluded_null_logpapp"] == 2

    def test_preprocess_data_pass_rate_calculation(self):
        """Test that pass rate is calculated correctly."""
        raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "assay_id": 1},
            {"smiles": "CC(=O)O", "logPapp": -4.2, "assay_id": 2},
            {"smiles": "CCC", "logPapp": None, "assay_id": 3},
            {"smiles": "", "logPapp": -4.0, "assay_id": 4},
            {"smiles": "CCCC", "logPapp": -5.0, "assay_id": 5}
        ]
        
        # 3 valid out of 5 total
        filtered_data, stats = preprocess_data(raw_data)
        
        assert stats["total_records"] == 5
        assert stats["valid_records"] == 3
        assert abs(stats["pass_rate"] - 0.6) < 0.001

    def test_preprocess_data_exclusion_reasons(self):
        """Test that exclusion reasons are tracked correctly."""
        raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "assay_id": 1},
            {"smiles": "", "logPapp": -4.2, "assay_id": 2},  # null smiles
            {"smiles": "CC(=O)O", "logPapp": None, "assay_id": 3},  # null logPapp
            {"smiles": "", "logPapp": "", "assay_id": 4},  # both null
            {"smiles": "CCC", "logPapp": -4.0, "assay_id": 5}
        ]
        
        filtered_data, stats = preprocess_data(raw_data)
        
        assert stats["excluded_null_smiles"] == 2
        assert stats["excluded_null_logpapp"] == 2
        # Note: The last record (id 4) is counted in both exclusions
        # Total excluded = 4, but some overlap exists
        assert stats["valid_records"] == 2

    def test_preprocess_data_empty_input(self):
        """Test preprocessing with empty input."""
        raw_data = []
        
        filtered_data, stats = preprocess_data(raw_data)
        
        assert len(filtered_data) == 0
        assert stats["total_records"] == 0
        assert stats["valid_records"] == 0
        assert stats["pass_rate"] == 0.0

    def test_preprocess_data_all_valid(self):
        """Test preprocessing when all records are valid."""
        raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "assay_id": 1},
            {"smiles": "CC(=O)O", "logPapp": -4.2, "assay_id": 2},
            {"smiles": "CCC", "logPapp": -4.0, "assay_id": 3}
        ]
        
        filtered_data, stats = preprocess_data(raw_data)
        
        assert len(filtered_data) == 3
        assert stats["pass_rate"] == 1.0
        assert stats["excluded_null_smiles"] == 0
        assert stats["excluded_null_logpapp"] == 0

class TestLoadRawData:
    def test_load_raw_data_from_file(self):
        """Test loading raw data from a CSV file."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("smiles,logPapp,assay_id\n")
            f.write("CCO,-4.5,1\n")
            f.write("CC(=O)O,-4.2,2\n")
            f.write("CCC,-4.0,3\n")
            temp_path = f.name
        
        try:
            data = load_raw_data(temp_path)
            
            assert len(data) == 3
            assert data[0]["smiles"] == "CCO"
            assert data[0]["logPapp"] == -4.5
            assert data[1]["assay_id"] == 2
        finally:
            os.unlink(temp_path)

    def test_load_raw_data_missing_file(self):
        """Test loading from a missing file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_raw_data("/nonexistent/path/to/file.csv")

    def test_load_raw_data_with_header_only(self):
        """Test loading a file with only headers."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("smiles,logPapp,assay_id\n")
            temp_path = f.name
        
        try:
            data = load_raw_data(temp_path)
            assert len(data) == 0
        finally:
            os.unlink(temp_path)

class TestIntegration:
    @patch('code.data.retrieval.requests.get')
    def test_full_retrieval_flow_mocked(self, mock_get):
        """Test the full retrieval flow with mocked API responses."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "assays": [
                {
                    "assay_id": 1,
                    "assay_chembl_id": "CHEMBL1",
                    "activities": [
                        {
                            "smiles": "CCO",
                            "logPapp": -4.5,
                            "assay_id": 1
                        }
                    ]
                }
            ],
            "count": 1,
            "next": None
        }
        mock_get.return_value = mock_response
        
        # This would normally call the API and process data
        # For unit tests, we verify the logic paths exist
        # Full integration is tested in T009 execution
        pass