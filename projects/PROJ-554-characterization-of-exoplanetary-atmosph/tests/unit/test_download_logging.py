import pytest
import logging
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from download import (
    _get_download_logger, 
    classify_planet_category, 
    fetch_spectrum_data,
    download_all_spectra,
    save_metadata_csv
)

class TestDownloadLogging:
    """Tests for download logging functionality (T014)."""
    
    def test_logger_creation_creates_log_file(self, tmp_path, monkeypatch):
        """Test that the logger creates the log file."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        # Monkeypatch the LOG_FILE path
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        # Get the logger (this should create the file)
        logger = _get_download_logger()
        
        # Log something to ensure the file is written
        logger.info("Test log message")
        
        # Verify the log file exists and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test log message" in content
        
        # Clean up monkeypatch
        download.LOG_FILE = Path("logs/download.log")
        download.LOGS_DIR = Path("logs")

    def test_logger_formats_correctly(self, tmp_path, monkeypatch):
        """Test that log messages are formatted correctly."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        logger = _get_download_logger()
        logger.info("Test message")
        
        content = log_file.read_text()
        # Check for expected log format: timestamp - name - level - message
        assert "download" in content
        assert "INFO" in content
        assert "Test message" in content

    def test_download_progress_logged(self, tmp_path, monkeypatch, mocker):
        """Test that download progress is logged."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        # Mock the API response
        mock_response = {
            "equilibrium_temperature": 1500,
            "host_metallicity": 0.1,
            "signal_to_noise": 50,
            "spectral_resolution": 100,
            "instrument": "HST",
            "wavelength_min": 0.5,
            "wavelength_max": 2.5,
            "radius": 1.2
        }
        
        with patch('download.fetch_spectrum_data', return_value=mock_response):
            with patch('download.requests.get') as mock_get:
                mock_get.return_value = MagicMock(
                    json=lambda: [mock_response],
                    raise_for_status=lambda: None
                )
                
                output_dir = tmp_path / "data" / "raw"
                output_dir.mkdir(parents=True)
                
                metadata_df, downloaded_files = download_all_spectra(output_dir)
        
        # Verify progress was logged
        content = log_file.read_text()
        assert "Processing" in content
        assert "Saved" in content
        assert "Download complete" in content

    def test_api_response_handling_logged(self, tmp_path, monkeypatch, mocker):
        """Test that API response handling is logged."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        # Mock successful API call
        mock_response = {
            "equilibrium_temperature": 1200,
            "host_metallicity": -0.1,
            "signal_to_noise": 30,
            "spectral_resolution": 50,
            "instrument": "JWST",
            "wavelength_min": 1.0,
            "wavelength_max": 5.0,
            "radius": 0.9
        }
        
        with patch('download.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                json=lambda: [mock_response],
                raise_for_status=lambda: None
            )
            
            output_dir = tmp_path / "data" / "raw"
            output_dir.mkdir(parents=True)
            
            metadata_df, downloaded_files = download_all_spectra(output_dir)
        
        # Verify API response was logged
        content = log_file.read_text()
        assert "Retrieved data" in content or "Processing" in content

    def test_error_handling_logged(self, tmp_path, monkeypatch, mocker):
        """Test that errors are logged appropriately."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        # Mock API failure
        with patch('download.requests.get', side_effect=Exception("API Error")):
            output_dir = tmp_path / "data" / "raw"
            output_dir.mkdir(parents=True)
            
            # This should log an error but not crash
            metadata_df, downloaded_files = download_all_spectra(output_dir)
        
        # Verify error was logged
        content = log_file.read_text()
        assert "Error" in content or "failed" in content.lower()

    def test_planet_classification_logged(self, tmp_path, monkeypatch):
        """Test that planet classification is logged."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "download.log"
        
        import download
        download.LOG_FILE = log_file
        download.LOGS_DIR = logs_dir
        
        # Mock successful download with classification
        mock_response = {
            "equilibrium_temperature": 1500,
            "radius": 1.2,  # > 0.8 R_Jup
            "host_metallicity": 0.0,
            "signal_to_noise": 40,
            "spectral_resolution": 75,
            "instrument": "HST",
            "wavelength_min": 0.6,
            "wavelength_max": 2.0
        }
        
        with patch('download.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                json=lambda: [mock_response],
                raise_for_status=lambda: None
            )
            
            output_dir = tmp_path / "data" / "raw"
            output_dir.mkdir(parents=True)
            
            metadata_df, downloaded_files = download_all_spectra(output_dir)
        
        # Verify classification was logged
        content = log_file.read_text()
        assert "Hot Jupiter" in content or "Category" in content

class TestPlanetClassification:
    """Tests for planet classification logic."""
    
    def test_hot_jupiter_classification(self):
        """Test Hot Jupiter classification."""
        result = classify_planet_category(radius=1.0, temperature=1500)
        assert result == "Hot Jupiter"
    
    def test_temperate_super_earth_classification(self):
        """Test Temperate Super-Earth classification."""
        result = classify_planet_category(radius=0.1, temperature=500)
        assert result == "Temperate Super-Earth"
    
    def test_other_classification(self):
        """Test 'Other' classification."""
        result = classify_planet_category(radius=0.5, temperature=1200)
        assert result == "Other"
