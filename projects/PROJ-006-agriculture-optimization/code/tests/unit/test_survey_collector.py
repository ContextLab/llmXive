import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.data.collectors.survey_collector import SurveyCollector, FatalError

class TestSurveyCollectorRegionSelection:
    def test_supported_countries(self):
        """Test that only supported countries are accepted."""
        # Valid countries
        collector_mw = SurveyCollector(country="malawi")
        assert collector_mw.country == "malawi"
        
        collector_tz = SurveyCollector(country="tanzania")
        assert collector_tz.country == "tanzania"

    def test_unsupported_country_raises_fatal_error(self):
        """Test that unsupported countries raise FatalError."""
        with pytest.raises(FatalError) as excinfo:
            SurveyCollector(country="kenya")
        assert "Unsupported country" in str(excinfo.value)

class TestSurveyCollectorConfigIntegrity:
    def test_initialization_creates_output_dir(self):
        """Test that initialization creates the output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_output"
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            assert output_dir.exists()

    def test_cache_manifest_initialization(self):
        """Test that cache manifest is initialized correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            assert collector.cache_manifest_path.exists()
            assert "files" in collector.cache_manifest

class TestSurveyCollectorCaching:
    def test_is_cache_valid_false_when_file_missing(self):
        """Test that cache is invalid when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            # File doesn't exist
            assert not collector._is_cache_valid()

    def test_is_cache_valid_false_when_hash_mismatch(self):
        """Test that cache is invalid when hash doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            
            # Create a fake data file
            fake_data_path = collector.raw_data_path
            fake_data_path.write_text("fake data")
            
            # Set wrong hash in manifest
            collector.cache_manifest["files"][str(fake_data_path)] = "wrong_hash"
            collector._save_cache_manifest()
            
            assert not collector._is_cache_valid()

    def test_is_cache_valid_true_when_hash_matches(self):
        """Test that cache is valid when hash matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            
            # Create a fake data file
            fake_data_path = collector.raw_data_path
            fake_data_path.write_text("fake data")
            
            # Set correct hash in manifest
            correct_hash = collector._compute_file_hash(fake_data_path)
            collector.cache_manifest["files"][str(fake_data_path)] = correct_hash
            collector._save_cache_manifest()
            
            assert collector._is_cache_valid()

    def test_collect_uses_cache_when_valid(self):
        """Test that collect() uses cache when valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            
            # Create a fake data file
            fake_data_path = collector.raw_data_path
            fake_data_path.write_text("fake data")
            
            # Set correct hash in manifest
            correct_hash = collector._compute_file_hash(fake_data_path)
            collector.cache_manifest["files"][str(fake_data_path)] = correct_hash
            collector._save_cache_manifest()
            
            # Mock authenticate to avoid actual auth attempt
            with patch.object(collector, '_authenticate'):
                result_path = collector.collect()
                assert result_path == fake_data_path

    def test_collect_downloads_when_cache_invalid(self):
        """Test that collect() downloads when cache is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            
            # Mock authenticate
            with patch.object(collector, '_authenticate'):
                # Mock download to return a fake file
                with patch.object(collector, '_download_data') as mock_download:
                    mock_download.return_value = collector.raw_data_path
                    collector.raw_data_path.write_text("downloaded data")
                    
                    # Set wrong hash to force download
                    collector.cache_manifest["files"][str(collector.raw_data_path)] = "wrong_hash"
                    collector._save_cache_manifest()
                    
                    result_path = collector.collect()
                    assert result_path == collector.raw_data_path
                    mock_download.assert_called_once()

    def test_collect_fails_loudly_without_credentials(self):
        """Test that collect() fails loudly when credentials are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            collector = SurveyCollector(country="malawi", output_dir=output_dir)
            
            # Ensure no credentials are set
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(FatalError) as excinfo:
                    collector.collect()
                assert "World Bank API credentials" in str(excinfo.value)
