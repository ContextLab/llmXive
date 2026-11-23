"""
Integration tests for GEO acquisition.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.data_acquisition import get_valid_geo_count, fetch_geo_dataset, parse_geo_samples
from src.config import GEO_IDS

class TestGEOAcquisition:
    @pytest.fixture
    def mock_geo_data(self):
        """Mock GEO data with response labels."""
        return {
            "sample_id": ["sample1", "sample2"],
            "tumor_type": ["Breast", "Breast"],
            "response_label": ["CR", "PD"],
            "gene1": [1.0, 2.0],
            "gene2": [3.0, 4.0]
        }

    @pytest.fixture
    def mock_geo_data_no_labels(self):
        """Mock GEO data without response labels."""
        return {
            "sample_id": ["sample1", "sample2"],
            "tumor_type": ["Breast", "Breast"],
            "gene1": [1.0, 2.0],
            "gene2": [3.0, 4.0]
        }

    def test_fetch_geo_dataset_found(self, tmp_path):
        """Test that fetch_geo_dataset returns a valid result for a found dataset."""
        # Mock the requests.get to return a valid response
        with patch('src.data_acquisition.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content.return_value = [b"test content"]
            mock_get.return_value = mock_response

            # Create a fake SOFT file
            soft_file = tmp_path / "GSE12345_family.soft.gz"
            with gzip.open(soft_file, 'wt') as f:
                f.write("!Series_title = Test")
            
            # Mock the tempfile.NamedTemporaryFile to return our fake file
            with patch('src.data_acquisition.tempfile.NamedTemporaryFile') as mock_tmp:
                mock_tmp.return_value.__enter__.return_value.name = str(soft_file)
                mock_tmp.return_value.__enter__.return_value.write = MagicMock()
                
                result = fetch_geo_dataset("GSE12345")
                assert result is not None
                assert result["id"] == "GSE12345"
                assert result["status"] == "found"

    def test_parse_geo_samples_with_labels(self, mock_geo_data, tmp_path):
        """Test that parse_geo_samples correctly parses samples with response labels."""
        # Create a temporary CSV file
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame(mock_geo_data)
        df.to_csv(csv_file, index=False)

        samples = parse_geo_samples("GSE12345", str(csv_file))
        assert len(samples) == 2
        assert all("response_label" in s for s in samples)

    def test_parse_geo_samples_without_labels(self, mock_geo_data_no_labels, tmp_path):
        """Test that parse_geo_samples raises an error for samples without response labels."""
        # Create a temporary CSV file
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame(mock_geo_data_no_labels)
        df.to_csv(csv_file, index=False)

        with pytest.raises(ValueError):
            parse_geo_samples("GSE12345", str(csv_file))

    def test_get_valid_geo_count(self, tmp_path):
        """Test that get_valid_geo_count returns the correct count of valid datasets."""
        # Mock the fetch_geo_dataset and parse_geo_samples functions
        with patch('src.data_acquisition.fetch_geo_dataset') as mock_fetch, \
             patch('src.data_acquisition.parse_geo_samples') as mock_parse, \
             patch('src.data_acquisition.GEO_IDS', ["GSE12345", "GSE67890"]):
            
            mock_fetch.return_value = {"id": "GSE12345", "status": "found", "path": str(tmp_path / "test.soft.gz")}
            mock_parse.return_value = [
                {"sample_id": "s1", "response_label": "CR", "tumor_type": "Breast", "expression_vector": []},
                {"sample_id": "s2", "response_label": "PD", "tumor_type": "Breast", "expression_vector": []}
            ]

            count = get_valid_geo_count()
            assert count == 2

    def test_get_valid_geo_count_insufficient(self, tmp_path):
        """Test that get_valid_geo_count handles insufficient datasets."""
        # Mock the fetch_geo_dataset and parse_geo_samples functions to return only one valid dataset
        with patch('src.data_acquisition.fetch_geo_dataset') as mock_fetch, \
             patch('src.data_acquisition.parse_geo_samples') as mock_parse, \
             patch('src.data_acquisition.GEO_IDS', ["GSE12345", "GSE67890"]):
            
            mock_fetch.return_value = {"id": "GSE12345", "status": "found", "path": str(tmp_path / "test.soft.gz")}
            mock_parse.return_value = [
                {"sample_id": "s1", "response_label": "CR", "tumor_type": "Breast", "expression_vector": []}
            ]

            count = get_valid_geo_count()
            assert count == 1
