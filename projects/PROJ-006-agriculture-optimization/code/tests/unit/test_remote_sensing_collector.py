import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

import pandas as pd
import numpy as np

# Import the collector
from src.data.collectors.remote_sensing_collector import RemoteSensingCollector, FatalError

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_survey_df():
    """Create a sample survey dataframe."""
    data = {
        'household_id': [1, 2, 3],
        'latitude': [-13.24, -13.25, -13.26],
        'longitude': [34.31, 34.32, 34.33],
        'other_col': ['A', 'B', 'C']
    }
    return pd.DataFrame(data)

class TestRemoteSensingCollector:
    def test_initialization(self, temp_output_dir):
        """Test collector initialization and directory creation."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        assert collector.output_dir == Path(temp_output_dir)
        assert collector.output_dir.exists()
        assert collector.cache_manifest_path.exists()

    def test_load_manifest_empty(self, temp_output_dir):
        """Test loading an empty/missing manifest."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        # Should initialize empty manifest
        assert collector.manifest == {"files": {}}

    def test_load_manifest_corrupt(self, temp_output_dir):
        """Test handling of a corrupt manifest."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        # Write corrupt JSON
        with open(collector.cache_manifest_path, 'w') as f:
            f.write("not json")
        
        # Reload should reset
        collector.manifest = collector._load_manifest()
        assert collector.manifest == {"files": {}}

    @patch('src.data.collectors.remote_sensing_collector.requests.get')
    def test_search_granules_success(self, mock_get, temp_output_dir):
        """Test successful granule search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "Id": "test-id-1",
                    "Name": "S2A_MSIL2A_20230101...",
                    "CreationDate": "2023-01-01T00:00:00Z",
                    "CloudCover": 0.5,
                    "ProductType": "S2MSI2A"
                }
            ]
        }
        mock_get.return_value = mock_response

        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"

        granules = collector._search_granules(
            latitude=-13.24,
            longitude=34.31,
            cloud_cover_max=0.9
        )

        assert len(granules) == 1
        assert granules[0]["id"] == "test-id-1"
        assert granules[0]["cloud_cover"] == 0.5

    @patch('src.data.collectors.remote_sensing_collector.requests.get')
    def test_search_granules_pagination(self, mock_get, temp_output_dir):
        """Test pagination in granule search."""
        # First call returns page 1 with next link
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "value": [{"Id": "id1", "Name": "S2...", "CreationDate": "2023-01-01", "CloudCover": 0.5, "ProductType": "S2MSI2A"}],
            "@odata.nextLink": "https://next.page"
        }
        
        # Second call returns page 2 with no next link
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "value": [{"Id": "id2", "Name": "S2...", "CreationDate": "2023-01-02", "CloudCover": 0.5, "ProductType": "S2MSI2A"}]
        }
        
        mock_get.side_effect = [mock_response1, mock_response2]

        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"

        granules = collector._search_granules(
            latitude=-13.24,
            longitude=34.31,
            cloud_cover_max=0.9
        )

        assert len(granules) == 2
        assert mock_get.call_count == 2

    @patch('src.data.collectors.remote_sensing_collector.requests.get')
    def test_download_granule_new(self, mock_get, temp_output_dir):
        """Test downloading a new granule."""
        # Mock search
        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.json.return_value = {
            "value": [{"Id": "test-id", "Name": "S2...", "CreationDate": "2023-01-01", "CloudCover": 0.5, "ProductType": "S2MSI2A"}]
        }
        
        # Mock download
        mock_download = MagicMock()
        mock_download.status_code = 200
        mock_download.headers = {"content-length": "100"}
        mock_download.iter_content.return_value = [b"chunk1", b"chunk2"]
        
        # Mock requests.get to return search then download
        def side_effect(*args, **kwargs):
            if "Products" in args[0] and "$value" not in args[0]:
                return mock_search
            else:
                return mock_download

        mock_get.side_effect = side_effect

        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"

        granules = collector._search_granules(-13.24, 34.31)
        path = collector._download_granule(granules[0])

        assert path.exists()
        assert path.suffix == ".zip"
        # Check manifest updated
        assert "test-id" in collector.manifest["files"]

    @patch('src.data.collectors.remote_sensing_collector.requests.get')
    def test_download_granule_cached(self, mock_get, temp_output_dir, sample_survey_df):
        """Test that cached granules are not re-downloaded."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"
        
        # Create a fake cached file
        cached_file = collector.output_dir / "S2_test.zip"
        cached_file.write_text("fake content")
        
        # Pre-populate manifest
        collector.manifest["files"]["test-id"] = {
            "path": str(cached_file),
            "hash": collector._compute_file_hash(cached_file),
            "cloud_cover": 0.5,
            "downloaded_at": "2023-01-01"
        }
        collector._save_manifest()

        # Mock search to return the same ID
        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.json.return_value = {
            "value": [{"Id": "test-id", "Name": "S2_test", "CreationDate": "2023-01-01", "CloudCover": 0.5, "ProductType": "S2MSI2A"}]
        }
        mock_get.return_value = mock_search

        # Should use cached file and not call download logic
        path = collector._download_granule({
            "id": "test-id",
            "name": "S2_test",
            "url": "fake_url"
        })

        assert path == cached_file
        # Ensure no extra requests were made for download
        assert mock_get.call_count == 1 # Only search

    def test_collect_for_household_integration(self, temp_output_dir):
        """Integration test for household collection (mocked network)."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"
        
        # Mock search to return empty list
        with patch.object(collector, '_search_granules', return_value=[]):
            paths = collector.collect_for_household(
                household_id=1,
                latitude=-13.24,
                longitude=34.31
            )
            assert paths == []

    def test_collect_for_survey_integration(self, temp_output_dir, sample_survey_df):
        """Integration test for survey collection."""
        collector = RemoteSensingCollector(output_dir=temp_output_dir)
        collector.access_token = "fake_token"
        
        # Mock collect_for_household
        with patch.object(collector, 'collect_for_household', return_value=[Path("fake.zip")]) as mock_method:
            results = collector.collect_for_survey(sample_survey_df, cloud_cover_max=0.9)
            
            assert len(results) == 3
            assert all(len(v) == 1 for v in results.values())
            assert mock_method.call_count == 3

    def test_missing_credentials(self, temp_output_dir):
        """Test that missing credentials raise FatalError."""
        # Temporarily unset env vars if they exist
        old_user = os.environ.pop("CDS_USERNAME", None)
        old_pass = os.environ.pop("CDS_PASSWORD", None)
        
        try:
            collector = RemoteSensingCollector(output_dir=temp_output_dir)
            # Force auth attempt
            with patch.object(collector, '_authenticate', side_effect=FatalError("Auth failed")):
                try:
                    collector._search_granules(-13.24, 34.31)
                    assert False, "Should have raised FatalError"
                except FatalError:
                    pass # Expected
        finally:
            if old_user: os.environ["CDS_USERNAME"] = old_user
            if old_pass: os.environ["CDS_PASSWORD"] = old_pass
