"""
Unit tests for retrieval_output module (T020).
Tests the CSV output generation for retrieval results.
"""
import os
import tempfile
import pytest
from pathlib import Path
import csv

from retrieval_output import process_retrieval_results
from data_models import RetrievalResult, CensorshipStatus, PlanetCategory


def test_process_retrieval_results_creates_csv():
    """Test that process_retrieval_results creates a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_results.csv"
        
        # Create a simple test result
        result = RetrievalResult(
            planet_name="TestPlanet",
            equilibrium_temperature=1500.0,
            water_mixing_ratio=-4.5,
            water_std_dev=0.3,
            is_censored=False,
            censorship_status=CensorshipStatus.UNCENSORED,
            planet_category=PlanetCategory.HOT_JUPITER,
            spectral_resolution=1000,
            snr=25.0,
            host_metallicity=0.1
        )
        
        output_file = process_retrieval_results([result], str(output_path))
        
        assert output_file.exists()
        assert output_file.suffix == ".csv"
        
        # Verify CSV content
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['planet_name'] == "TestPlanet"
            assert float(rows[0]['water_mixing_ratio_log10']) == -4.5
            assert rows[0]['is_censored'] == 'False'


def test_process_retrieval_results_empty_list():
    """Test that an empty list creates a CSV with headers only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty_results.csv"
        
        output_file = process_retrieval_results([], str(output_path))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert len(headers) > 0
            rows = list(reader)
            assert len(rows) == 0


def test_process_retrieval_results_censored_data():
    """Test that censored results are properly flagged in CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "censored_results.csv"
        
        result = RetrievalResult(
            planet_name="LowSNRPlanet",
            equilibrium_temperature=800.0,
            water_mixing_ratio=-6.0,
            water_std_dev=None,  # No std dev for upper limit
            is_censored=True,
            censorship_status=CensorshipStatus.UPPER_LIMIT,
            planet_category=PlanetCategory.SUPER_EARTH,
            spectral_resolution=500,
            snr=5.0,
            host_metallicity=-0.2
        )
        
        output_file = process_retrieval_results([result], str(output_path))
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['is_censored'] == 'True'
            assert rows[0]['censorship_status'] == 'UPPER_LIMIT'


def test_process_retrieval_results_multiple_rows():
    """Test processing multiple results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "multi_results.csv"
        
        results = [
            RetrievalResult(
                planet_name=f"Planet{i}",
                equilibrium_temperature=1000.0 + i * 100,
                water_mixing_ratio=-4.0 - i * 0.5,
                water_std_dev=0.2,
                is_censored=False,
                censorship_status=CensorshipStatus.UNCENSORED,
                planet_category=PlanetCategory.HOT_JUPITER,
                spectral_resolution=1000,
                snr=20.0 + i,
                host_metallicity=0.0
            )
            for i in range(5)
        ]
        
        output_file = process_retrieval_results(results, str(output_path))
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
            for i, row in enumerate(rows):
                assert row['planet_name'] == f"Planet{i}"
                assert float(row['water_mixing_ratio_log10']) == -4.0 - i * 0.5
