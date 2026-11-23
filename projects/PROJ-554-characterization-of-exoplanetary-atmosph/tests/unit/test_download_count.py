import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Import the function to test
from download import count_unique_planets

def test_count_unique_planets():
    """
    Test that count_unique_planets correctly counts unique planets 
    and writes the JSON report.
    """
    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        metadata_file = tmpdir_path / "metadata.csv"
        
        # Create mock data
        data = {
            'planet_name': ['Planet A', 'Planet B', 'Planet A', 'Planet C'],
            'equilibrium_temperature': [100, 200, 100, 300],
            'metallicity': [0.1, 0.2, 0.1, 0.3],
            'snr': [10, 20, 10, 30],
            'resolution': [50, 60, 50, 70],
            'instrument': ['HST', 'Spitzer', 'HST', 'JWST'],
            'wavelength_range': ['1-5', '1-5', '1-5', '1-5'],
            'planet_category': ['Hot Jupiter', 'Super Earth', 'Hot Jupiter', 'Super Earth']
        }
        df = pd.DataFrame(data)
        df.to_csv(metadata_file, index=False)
        
        # Run the function
        result = count_unique_planets(metadata_file)
        
        # Verify result
        assert result == {"count": 3}, f"Expected count 3, got {result['count']}"
        
        # Verify file creation
        report_file = tmpdir_path / "count_report.json"
        assert report_file.exists(), "count_report.json was not created"
        
        with open(report_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == {"count": 3}, f"Saved report mismatch: {saved_data}"

def test_count_unique_planets_empty():
    """
    Test behavior with a file containing only headers (0 unique planets).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        metadata_file = tmpdir_path / "metadata.csv"
        
        # Create mock data with only headers
        data = {
            'planet_name': [],
            'equilibrium_temperature': [],
            'metallicity': [],
            'snr': [],
            'resolution': [],
            'instrument': [],
            'wavelength_range': [],
            'planet_category': []
        }
        df = pd.DataFrame(data)
        df.to_csv(metadata_file, index=False)
        
        result = count_unique_planets(metadata_file)
        assert result == {"count": 0}