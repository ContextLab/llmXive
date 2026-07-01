"""
Integration tests for the data cleaning pipeline (T017).
Ensures the script runs end-to-end and produces the expected output file.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.cleaning import clean_and_save, convert_units, filter_missing_values, map_alloy_composition

@pytest.fixture
def sample_raw_data(tmp_path):
    """Create a temporary raw CSV file for testing."""
    input_file = tmp_path / "raw_combined_builds.csv"
    data = {
        'laser_power': [200, 300, 400, 500, None], # 400 is kW? Let's assume W for now, or add unit col
        'scan_speed': [500, 600, 700, 800, 900],
        'hatch_spacing': [80, 90, 100, 110, 120],
        'layer_thickness': [30, 35, 40, 45, 50],
        'ductility': [10.5, 12.0, 8.5, 15.0, None], # Last one missing
        'alloy_family': ['Inconel 718', 'Inconel 625', 'Inconel 718', 'Hastelloy X', 'Inconel 718'],
        'alloy_name': ['Inconel 718', 'Inconel 625', 'Inconel 718', 'Hastelloy X', 'Inconel 718'],
        'energy_density': [50.0, 60.0, 70.0, 80.0, 90.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(input_file, index=False)
    return input_file

def test_clean_and_save_creates_file(sample_raw_data, tmp_path):
    """Test that clean_and_save creates the output CSV file."""
    output_file = tmp_path / "curated_builds.csv"
    
    # Run cleaning
    df_clean = clean_and_save(sample_raw_data, output_file)
    
    # Assertions
    assert output_file.exists(), "Output file was not created."
    assert isinstance(df_clean, pd.DataFrame), "Function did not return a DataFrame."
    assert len(df_clean) == 4, f"Expected 4 rows (1 missing), got {len(df_clean)}."
    
    # Check columns
    assert 'laser_power' in df_clean.columns
    assert 'ductility' in df_clean.columns
    assert 'Cr' in df_clean.columns or 'Al' in df_clean.columns # At least one flag should exist

def test_convert_units_logic():
    """Test unit conversion logic with explicit unit columns."""
    data = {
        'laser_power': [1.0, 2.0, 3.0], # kW
        'power_unit': ['kW', 'kW', 'W'],
        'scan_speed': [1.0, 2.0, 3.0], # m/s
        'speed_unit': ['m/s', 'm/s', 'mm/s'],
        'hatch_spacing': [1.0, 2.0, 3.0], # mm
        'hatch_unit': ['mm', 'mm', 'µm'],
        'layer_thickness': [1.0, 2.0, 3.0], # mm
        'thickness_unit': ['mm', 'mm', 'µm'],
        'ductility': [10.0, 11.0, 12.0]
    }
    df = pd.DataFrame(data)
    
    df_converted = convert_units(df)
    
    # Power: 1kW->1000W, 2kW->2000W, 3W->3W
    assert df_converted.loc[0, 'laser_power'] == 1000.0
    assert df_converted.loc[1, 'laser_power'] == 2000.0
    assert df_converted.loc[2, 'laser_power'] == 3.0
    
    # Speed: 1m/s->1000mm/s, 2m/s->2000mm/s, 3mm/s->3mm/s
    assert df_converted.loc[0, 'scan_speed'] == 1000.0
    assert df_converted.loc[1, 'scan_speed'] == 2000.0
    assert df_converted.loc[2, 'scan_speed'] == 3.0

def test_filter_missing_values_logic():
    """Test filtering logic for missing values."""
    data = {
        'laser_power': [200, None, 400],
        'scan_speed': [500, 600, None],
        'hatch_spacing': [80, 90, 100],
        'layer_thickness': [30, 35, 40],
        'ductility': [10.0, 11.0, None],
        'alloy_family': ['A', 'B', 'C']
    }
    df = pd.DataFrame(data)
    
    df_filtered = filter_missing_values(df)
    
    # Only the first row should remain (no missing values in critical cols)
    assert len(df_filtered) == 1
    assert df_filtered.iloc[0]['laser_power'] == 200

def test_map_alloy_composition_logic():
    """Test binary flag creation for alloy elements."""
    data = {
        'alloy_name': ['Inconel 718', 'Inconel 625', 'Hastelloy X', 'Stainless Steel'],
        'laser_power': [200, 200, 200, 200],
        'scan_speed': [500, 500, 500, 500],
        'hatch_spacing': [80, 80, 80, 80],
        'layer_thickness': [30, 30, 30, 30],
        'ductility': [10.0, 11.0, 12.0, 13.0],
        'alloy_family': ['A', 'B', 'C', 'D']
    }
    df = pd.DataFrame(data)
    
    df_mapped = map_alloy_composition(df)
    
    # Inconel 718 -> Ni, Cr, Fe, Mo, Nb (Cr, Mo present)
    # Inconel 625 -> Ni, Cr, Mo, Nb (Cr, Mo present)
    # Hastelloy X -> Ni, Cr, Fe, Mo (Cr, Mo present)
    # Stainless Steel -> Cr, Ni (Cr present)
    
    # Check Cr column (should be 1 for all in this heuristic)
    assert all(df_mapped['Cr'] == 1)
    
    # Check Mo column (should be 1 for first 3, maybe 0 for Stainless Steel depending on string)
    # 'Stainless Steel' doesn't contain 'Mo' explicitly in the name string usually
    assert df_mapped.loc[0, 'Mo'] == 1 # Inconel 718
    assert df_mapped.loc[3, 'Mo'] == 0 # Stainless Steel (no Mo in name)