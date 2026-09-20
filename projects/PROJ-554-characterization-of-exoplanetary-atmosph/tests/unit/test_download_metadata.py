import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import process_metadata, save_metadata_csv, classify_planet

class TestMetadataProcessing:
    """Tests for metadata processing functions."""

    def test_process_metadata_adds_wavelength_range(self):
        """Test that wavelength_range is added from min/max wavelengths."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1000],
            'metallicity': [0.0],
            'snr': [10.0],
            'resolution': [50],
            'wavelength_min': [0.5],
            'wavelength_max': [5.0],
            'instrument': ['HST']
        })
        
        result = process_metadata(df)
        
        assert 'wavelength_range' in result.columns
        assert result['wavelength_range'].iloc[0] == "0.50-5.00"

    def test_process_metadata_adds_planet_category(self):
        """Test that planet_category is added after classification."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1500],
            'metallicity': [0.0],
            'snr': [10.0],
            'resolution': [50],
            'wavelength_min': [0.5],
            'wavelength_max': [5.0],
            'instrument': ['HST'],
            'equilibrium_temperature': [1500],
            'radius': [1.5]
        })
        
        result = classify_planet(df)
        result = process_metadata(result)
        
        assert 'planet_category' in result.columns
        assert result['planet_category'].iloc[0] == "Hot Jupiter"

    def test_save_metadata_csv_creates_file(self, tmp_path):
        """Test that save_metadata_csv creates the output file."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1000],
            'metallicity': [0.0],
            'snr': [10.0],
            'resolution': [50],
            'planet_category': ['Hot Jupiter'],
            'instrument': ['HST'],
            'wavelength_range': ['0.50-5.00']
        })
        
        output_path = tmp_path / "metadata.csv"
        save_metadata_csv(df, str(output_path))
        
        assert output_path.exists()
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 1
        assert 'wavelength_range' in loaded_df.columns

    def test_save_metadata_csv_validates_columns(self, tmp_path):
        """Test that save_metadata_csv raises error if required columns missing."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1000],
            # Missing required columns
        })
        
        output_path = tmp_path / "metadata.csv"
        
        with pytest.raises(ValueError, match="Required column"):
            save_metadata_csv(df, str(output_path))

    def test_save_metadata_csv_validates_nulls(self, tmp_path):
        """Test that save_metadata_csv raises error if non-optional columns have nulls."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1000],
            'metallicity': [0.0],
            'snr': [None],  # This should cause an error
            'resolution': [50],
            'planet_category': ['Hot Jupiter'],
            'instrument': ['HST'],
            'wavelength_range': ['0.50-5.00']
        })
        
        output_path = tmp_path / "metadata.csv"
        
        with pytest.raises(ValueError, match="contains null values"):
            save_metadata_csv(df, str(output_path))

    def test_all_required_columns_present(self, tmp_path):
        """Test that all required columns are present in output."""
        df = pd.DataFrame({
            'planet_name': ['Test Planet'],
            'temperature': [1000],
            'metallicity': [0.0],
            'snr': [10.0],
            'resolution': [50],
            'planet_category': ['Hot Jupiter'],
            'instrument': ['HST'],
            'wavelength_range': ['0.50-5.00']
        })
        
        output_path = tmp_path / "metadata.csv"
        save_metadata_csv(df, str(output_path))
        
        loaded_df = pd.read_csv(output_path)
        
        required_columns = [
            'planet_name', 'temperature', 'metallicity', 'snr', 
            'resolution', 'planet_category', 'instrument', 'wavelength_range'
        ]
        
        for col in required_columns:
            assert col in loaded_df.columns, f"Missing required column: {col}"