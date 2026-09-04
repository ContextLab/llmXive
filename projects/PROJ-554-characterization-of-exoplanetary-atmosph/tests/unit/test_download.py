import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from download import classify_planet_category, process_metadata, count_unique_planets

class TestClassifyPlanetCategory:
    def test_hot_jupiter(self):
        # Hot Jupiter: T > 1000K, R > 0.8 Rj
        row = pd.Series({'temperature': 1500, 'radius': 1.2})
        assert classify_planet_category(row) == "Hot Jupiter"

    def test_temperate_super_earth(self):
        # Temperate Super-Earth: T <= 1000K, 0.1 < R < 0.14 Rj (approx 1-1.6 Re)
        row = pd.Series({'temperature': 800, 'radius': 0.12})
        assert classify_planet_category(row) == "Temperate Super-Earth"

    def test_unclassified(self):
        # Does not fit criteria
        row = pd.Series({'temperature': 1200, 'radius': 0.5})
        assert classify_planet_category(row) == "Unclassified"

class TestProcessMetadata:
    def test_process_metadata_columns(self):
        # Mock raw data
        raw_data = {
            'pl_name': ['Planet A', 'Planet B'],
            'pl_radj': [1.2, 0.12],
            'pl_eqt': [1500, 800],
            'st_met': [0.1, -0.2]
        }
        df = pd.DataFrame(raw_data)
        result = process_metadata(df)
        
        assert 'planet_name' in result.columns
        assert 'planet_category' in result.columns
        assert 'temperature' in result.columns
        assert 'radius' in result.columns

class TestCountUniquePlanets:
    def test_count_unique(self):
        df = pd.DataFrame({
            'planet_name': ['A', 'B', 'A', 'C']
        })
        assert count_unique_planets(df) == 3
    
    def test_count_empty(self):
        df = pd.DataFrame()
        assert count_unique_planets(df) == 0