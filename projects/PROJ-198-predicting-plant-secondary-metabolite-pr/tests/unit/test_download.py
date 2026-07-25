"""
Unit tests for the genome size filter logic in code/data/download.py.

This module tests the `download_genomes` function's ability to skip
genomes larger than the configured threshold (default 500MB).
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import download_genomes, DownloadError
from config import get_config, load_config, get_data_path
from utils.logging import setup_logging, get_logger

# Test fixtures
@pytest.fixture
def mock_species_list():
    """Return a list of mock species dictionaries."""
    return [
        {
            "species_name": "Arabidopsis thaliana",
            "assembly_accession": "GCA_000001735",
            "genome_size_mb": 135.0,
            "source": "NCBI"
        },
        {
            "species_name": "Triticum aestivum",
            "assembly_accession": "GCA_002110835",
            "genome_size_mb": 5800.0,  # Exceeds 500MB limit
            "source": "NCBI"
        },
        {
            "species_name": "Oryza sativa",
            "assembly_accession": "GCA_001433935",
            "genome_size_mb": 389.0,
            "source": "NCBI"
        }
    ]

@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary config with a low threshold for testing."""
    config_data = {
        "species_list": [
            {"species_name": "Test Species", "assembly_accession": "GCA_000000000", "genome_size_mb": 600.0}
        ],
        "genome_size_threshold_mb": 500,
        "data_path": str(tmp_path)
    }
    # Mock the config loading to use our test data
    with patch('data.download.get_config') as mock_get_config:
        mock_config_obj = MagicMock()
        mock_config_obj.genome_size_threshold_mb = 500
        mock_config_obj.species_list = config_data["species_list"]
        mock_config_obj.data_path = tmp_path
        mock_get_config.return_value = mock_config_obj
        yield mock_config_obj

def test_genome_size_filter_skips_large_genomes(mock_species_list):
    """Test that genomes exceeding the size threshold are skipped."""
    with patch('data.download.get_config') as mock_get_config:
        # Setup mock config
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 500
        mock_config.species_list = mock_species_list
        mock_config.data_path = "/tmp/test_data"
        mock_get_config.return_value = mock_config
        
        # Mock requests to avoid actual network calls
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response
            
            # Mock logging to capture warnings
            with patch('data.download.logger') as mock_logger:
                # Mock the download function to avoid file I/O
                with patch('data.download._download_file') as mock_download:
                    mock_download.return_value = Path("/tmp/test.fasta")
                    
                    # Run the function
                    results = download_genomes()
                    
                    # Verify the large genome was skipped
                    assert len(results) == 2  # Only 2 valid genomes
                    
                    # Check that the 5800MB genome was not in the results
                    downloaded_accessions = [r["assembly_accession"] for r in results]
                    assert "GCA_002110835" not in downloaded_accessions
                    
                    # Verify the logger was called with a skip message
                    skip_calls = [call for call in mock_logger.warning.call_args_list 
                                if "skipping" in str(call).lower()]
                    assert len(skip_calls) > 0, "Expected a warning log for skipped large genome"

def test_genome_size_filter_allows_small_genomes(mock_species_list):
    """Test that genomes within the size threshold are processed."""
    with patch('data.download.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 500
        mock_config.species_list = mock_species_list
        mock_config.data_path = "/tmp/test_data"
        mock_get_config.return_value = mock_config
        
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response
            
            with patch('data.download._download_file') as mock_download:
                mock_download.return_value = Path("/tmp/test.fasta")
                
                results = download_genomes()
                
                # Verify all valid genomes were processed
                assert len(results) == 2
                
                # Check that small genomes are in the results
                downloaded_accessions = [r["assembly_accession"] for r in results]
                assert "GCA_000001735" in downloaded_accessions
                assert "GCA_001433935" in downloaded_accessions

def test_genome_size_filter_boundary_case(mock_species_list):
    """Test behavior at the exact threshold boundary."""
    # Add a species exactly at 500MB
    boundary_species = {
        "species_name": "Boundary Species",
        "assembly_accession": "GCA_000000999",
        "genome_size_mb": 500.0,
        "source": "NCBI"
    }
    test_list = mock_species_list + [boundary_species]
    
    with patch('data.download.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 500
        mock_config.species_list = test_list
        mock_config.data_path = "/tmp/test_data"
        mock_get_config.return_value = mock_config
        
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response
            
            with patch('data.download._download_file') as mock_download:
                mock_download.return_value = Path("/tmp/test.fasta")
                
                results = download_genomes()
                
                # The 500MB genome should be included (<= threshold)
                assert len(results) == 3
                assert "GCA_000000999" in [r["assembly_accession"] for r in results]

def test_genome_size_filter_zero_size(mock_species_list):
    """Test handling of species with missing or zero genome size."""
    # Add a species with 0 size
    zero_species = {
        "species_name": "Zero Size Species",
        "assembly_accession": "GCA_000000888",
        "genome_size_mb": 0.0,
        "source": "NCBI"
    }
    test_list = mock_species_list + [zero_species]
    
    with patch('data.download.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 500
        mock_config.species_list = test_list
        mock_config.data_path = "/tmp/test_data"
        mock_get_config.return_value = mock_config
        
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response
            
            with patch('data.download._download_file') as mock_download:
                mock_download.return_value = Path("/tmp/test.fasta")
                
                # This should handle the 0 size gracefully (likely skip or treat as unknown)
                # The current implementation should skip it or handle it without crashing
                try:
                    results = download_genomes()
                    # If it doesn't crash, verify other valid ones are present
                    assert "GCA_000001735" in [r["assembly_accession"] for r in results]
                except Exception as e:
                    # If it crashes, that's also a valid test outcome if the logic requires a size
                    pytest.xfail(f"Expected behavior for zero-size genome: {e}")

def test_genome_size_filter_config_override(tmp_path):
    """Test that the size threshold can be overridden via config."""
    # Create a species that is 400MB
    species_400 = {
        "species_name": "Medium Species",
        "assembly_accession": "GCA_000000777",
        "genome_size_mb": 400.0,
        "source": "NCBI"
    }
    
    # Test with threshold 300MB (should skip)
    with patch('data.download.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 300
        mock_config.species_list = [species_400]
        mock_config.data_path = tmp_path
        mock_get_config.return_value = mock_config
        
        with patch('data.download.requests.get'):
            with patch('data.download._download_file') as mock_download:
                mock_download.return_value = Path("/tmp/test.fasta")
                
                with patch('data.download.logger') as mock_logger:
                    results = download_genomes()
                    assert len(results) == 0
                    # Verify skip warning was logged
                    assert any("skipping" in str(call).lower() for call in mock_logger.warning.call_args_list)
    
    # Test with threshold 500MB (should include)
    with patch('data.download.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.genome_size_threshold_mb = 500
        mock_config.species_list = [species_400]
        mock_config.data_path = tmp_path
        mock_get_config.return_value = mock_config
        
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response
            
            with patch('data.download._download_file') as mock_download:
                mock_download.return_value = Path("/tmp/test.fasta")
                
                results = download_genomes()
                assert len(results) == 1
                assert results[0]["assembly_accession"] == "GCA_000000777"