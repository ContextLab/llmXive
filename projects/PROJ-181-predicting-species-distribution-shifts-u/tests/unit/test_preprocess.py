"""
Unit tests for the preprocess module.
"""

import os
import sys
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.preprocess import check_historical_data_sufficiency, thin_occurrences
from code.config import DATA_DIR, METRICS_DIR

class TestDataSufficiencyCheck:
    def test_insufficient_data_flag(self, tmp_path):
        """Test that species with <100 records are flagged."""
        # Create a mock CSV
        input_file = tmp_path / "occurrence.csv"
        output_file = tmp_path / "insufficient.json"
        
        # Create data with one species having 50 records, another 150
        data = {
            'species': ['SpeciesA'] * 50 + ['SpeciesB'] * 150,
            'decimalLatitude': [40.0] * 200,
            'decimalLongitude': [-75.0] * 200,
            'eventDate': ['2000-06-01'] * 200
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        result = check_historical_data_sufficiency(
            input_path=str(input_file),
            output_path=str(output_file),
            threshold=100
        )
        
        assert result['insufficient_species_count'] == 1
        assert result['sufficient_species_count'] == 1
        assert any(r['species'] == 'SpeciesA' for r in result['records'])
        
        # Verify JSON file exists
        assert os.path.exists(output_file)

class TestSpatialThinning:
    def test_thinning_logic(self, tmp_path):
        """Test that thinning enforces minimum distance."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        # Create data with points very close together (within 1km)
        # Species A: 3 points at same location
        # Species B: 2 points 100km apart
        data = {
            'species': ['SpeciesA', 'SpeciesA', 'SpeciesA', 'SpeciesB', 'SpeciesB'],
            'decimalLatitude': [40.0, 40.001, 40.002, 40.0, 50.0], # ~0.1 deg ~ 11km
            'decimalLongitude': [-75.0, -75.001, -75.002, -75.0, -75.0],
            'eventDate': ['2000-06-01', '2000-06-01', '2000-06-01', '2000-06-01', '2000-06-01']
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        result = thin_occurrences(
            input_path=str(input_file),
            output_path=str(output_file),
            distance_km=10.0
        )
        
        # Load output
        output_df = pd.read_csv(output_file)
        
        # SpeciesA should have 1 point (others too close)
        # SpeciesB should have 2 points (far apart)
        species_a_count = len(output_df[output_df['species'] == 'SpeciesA'])
        species_b_count = len(output_df[output_df['species'] == 'SpeciesB'])
        
        assert species_a_count == 1
        assert species_b_count == 2
        assert result['after_count'] == 3

    def test_breeding_season_filter(self, tmp_path):
        """Test that non-breeding season records are removed."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        data = {
            'species': ['SpeciesA', 'SpeciesA', 'SpeciesA'],
            'decimalLatitude': [40.0, 40.0, 40.0],
            'decimalLongitude': [-75.0, -75.0, -75.0],
            'eventDate': ['2000-01-01', '2000-06-01', '2000-12-01'] # Jan, June, Dec
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        thin_occurrences(
            input_path=str(input_file),
            output_path=str(output_file),
            distance_km=10.0
        )
        
        output_df = pd.read_csv(output_file)
        # Only June (month 6) should remain
        assert len(output_df) == 1
        assert output_df.iloc[0]['species'] == 'SpeciesA'