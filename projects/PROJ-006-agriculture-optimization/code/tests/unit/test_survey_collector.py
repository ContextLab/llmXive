import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from src.data.collectors.survey_collector import SurveyCollector, COUNTRY_CONFIG
from src.utils.io_helpers import FatalError, IntegrityError


class TestSurveyCollectorRegionSelection:
    """Tests for region selection and configuration integrity."""

    def test_supported_countries(self):
        """Verify that expected countries are in the configuration."""
        assert "malawi" in COUNTRY_CONFIG
        assert "tanzania" in COUNTRY_CONFIG
        assert COUNTRY_CONFIG["malawi"]["survey_code"] == "MWI"
        assert COUNTRY_CONFIG["tanzania"]["survey_code"] == "TZA"

    def test_unsupported_country_raises_fatal_error(self):
        """Ensure unsupported country raises FatalError."""
        collector = SurveyCollector()
        with pytest.raises(FatalError, match="Unsupported country"):
            collector.fetch_survey_data("kenya")


class TestSurveyCollectorConfigIntegrity:
    """Tests for configuration and manifest handling."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_manifest_initialization(self, temp_cache_dir):
        """Test that manifest is initialized correctly."""
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        assert "files" in collector.manifest
        assert collector.manifest["files"] == {}

    def test_manifest_persistence(self, temp_cache_dir):
        """Test that manifest is saved and loaded correctly."""
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        collector._update_manifest("test.csv", "abc123", "http://example.com/test.csv")
        
        # Create a new instance to simulate reload
        collector2 = SurveyCollector(cache_dir=temp_cache_dir)
        assert "test.csv" in collector2.manifest["files"]
        assert collector2.manifest["files"]["test.csv"]["checksum"] == "abc123"


class TestSurveyCollectorCaching:
    """Tests for caching and checksum verification logic."""

    @pytest.fixture
    def temp_cache_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_response(self):
        """Mock a successful HTTP response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [b"test,data\n1,2"]
        mock_resp.raw = MagicMock()
        # Simulate file-like object for copyfileobj
        mock_content = b"test,data\n1,2"
        mock_resp.raw.read = MagicMock(side_effect=[mock_content, b""])
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_cache_hit(self, temp_cache_dir, mock_response):
        """Test that existing cached file is used."""
        # Pre-populate cache
        file_path = temp_cache_dir / "test.csv"
        file_path.write_text("test,data\n1,2")
        
        # Create a fake manifest entry
        manifest_path = temp_cache_dir / "cache_manifest.json"
        manifest_path.write_text(json.dumps({"files": {"test.csv": {"checksum": "fake_checksum", "url": "http://test.com"}}}))

        collector = SurveyCollector(cache_dir=temp_cache_dir)
        
        # Mock _compute_file_checksum to return the stored checksum to simulate match
        with patch.object(collector, '_compute_file_checksum', return_value="fake_checksum"):
            result_path = collector.fetch_survey_data("malawi") # Malawi config used for URL, but file name might differ. 
            # Actually, fetch_survey_data uses COUNTRY_CONFIG to get filename.
            # We need to ensure the filename matches the one in cache.
            # Let's adjust: The cache check uses the filename from COUNTRY_CONFIG.
            # So we must put the file with the correct name.
            
        # Re-doing with correct filename
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        correct_file_path = temp_cache_dir / correct_filename
        correct_file_path.write_text("test,data\n1,2")
        
        manifest_path.write_text(json.dumps({"files": {correct_filename: {"checksum": "fake_checksum", "url": "http://test.com"}}}))
        
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        
        with patch.object(collector, '_compute_file_checksum', return_value="fake_checksum"):
            with patch('src.data.collectors.survey_collector.requests.get', return_value=mock_response):
                result_path = collector.fetch_survey_data("malawi")
        
        assert result_path == correct_file_path
        # Verify download was NOT called
        # requests.get is mocked, but we can check if the logic path avoided download
        # The _verify_cached_file returned True, so _download_file should not be called.
        # We can't easily assert requests.get wasn't called if we patched it globally, 
        # but the logic flow ensures it.
        # A better way: check that the file content is the pre-existing one, not downloaded one.
        # Since we mocked download, it's hard to distinguish. 
        # Instead, we assert that _download_file was not called by patching it.
        
        with patch.object(collector, '_download_file') as mock_download:
             with patch.object(collector, '_compute_file_checksum', return_value="fake_checksum"):
                  collector.fetch_survey_data("malawi")
             mock_download.assert_not_called()

    def test_cache_miss_triggers_download(self, temp_cache_dir, mock_response):
        """Test that missing cache triggers download."""
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        
        # Ensure file doesn't exist
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        assert not (temp_cache_dir / correct_filename).exists()
        
        with patch('src.data.collectors.survey_collector.requests.get', return_value=mock_response):
            with patch.object(collector, '_compute_file_checksum', return_value="new_checksum") as mock_checksum:
                result_path = collector.fetch_survey_data("malawi")
        
        assert result_path.exists()
        mock_checksum.assert_called()
        
        # Verify manifest was updated
        assert correct_filename in collector.manifest["files"]

    def test_checksum_mismatch_triggers_redownload(self, temp_cache_dir, mock_response):
        """Test that checksum mismatch triggers re-download."""
        # Pre-populate cache with a file
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        correct_file_path = temp_cache_dir / correct_filename
        correct_file_path.write_text("old,data")
        
        # Create manifest with a DIFFERENT checksum
        manifest_path = temp_cache_dir / "cache_manifest.json"
        manifest_path.write_text(json.dumps({"files": {correct_filename: {"checksum": "old_checksum", "url": "http://test.com"}}}))

        collector = SurveyCollector(cache_dir=temp_cache_dir)
        
        # Mock _compute_file_checksum to return a NEW checksum (mismatch)
        with patch.object(collector, '_compute_file_checksum', return_value="new_checksum"):
            with patch('src.data.collectors.survey_collector.requests.get', return_value=mock_response):
                with patch.object(collector, '_download_file') as mock_download:
                    collector.fetch_survey_data("malawi")
                    
        # Verify download was called
        mock_download.assert_called_once()

    def test_download_failure_raises_fatal_error(self, temp_cache_dir):
        """Test that download failure raises FatalError."""
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        
        with patch('src.data.collectors.survey_collector.requests.get', side_effect=Exception("Network error")):
            with pytest.raises(FatalError, match="Failed to download"):
                collector.fetch_survey_data("malawi")

    def test_verify_cached_file_returns_false_if_missing(self, temp_cache_dir):
        """Test _verify_cached_file returns False if file missing."""
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        assert not collector._verify_cached_file("nonexistent.csv")

    def test_verify_cached_file_returns_true_if_exists_no_checksum(self, temp_cache_dir):
        """Test _verify_cached_file returns True if file exists and no checksum stored."""
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        (temp_cache_dir / correct_filename).write_text("data")
        
        collector = SurveyCollector(cache_dir=temp_cache_dir)
        # Manifest is empty initially
        assert collector._verify_cached_file(correct_filename) is True

    def test_verify_cached_file_returns_true_if_checksum_matches(self, temp_cache_dir):
        """Test _verify_cached_file returns True if checksum matches."""
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        file_path = temp_cache_dir / correct_filename
        file_path.write_text("data")
        
        # Compute actual checksum
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()

        # Create manifest with correct checksum
        manifest_path = temp_cache_dir / "cache_manifest.json"
        manifest_path.write_text(json.dumps({"files": {correct_filename: {"checksum": actual_checksum, "url": "http://test.com"}}}))

        collector = SurveyCollector(cache_dir=temp_cache_dir)
        assert collector._verify_cached_file(correct_filename) is True

    def test_verify_cached_file_returns_false_if_checksum_mismatch(self, temp_cache_dir):
        """Test _verify_cached_file returns False if checksum mismatches."""
        correct_filename = COUNTRY_CONFIG["malawi"]["local_filename"]
        (temp_cache_dir / correct_filename).write_text("data")
        
        # Create manifest with WRONG checksum
        manifest_path = temp_cache_dir / "cache_manifest.json"
        manifest_path.write_text(json.dumps({"files": {correct_filename: {"checksum": "wrong_checksum", "url": "http://test.com"}}}))

        collector = SurveyCollector(cache_dir=temp_cache_dir)
        assert collector._verify_cached_file(correct_filename) is False
