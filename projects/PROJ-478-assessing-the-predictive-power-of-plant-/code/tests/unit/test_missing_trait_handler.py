import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.data.missing_trait_handler import (
    identify_species_missing_traits,
    save_exclusion_report,
    run_missing_trait_check,
    REQUIRED_TRAIT_COLUMNS
)


@pytest.fixture
def complete_trait_df():
    """DataFrame with all required traits present."""
    return pd.DataFrame({
        'species_name': ['Species_A', 'Species_B', 'Species_C'],
        'sla': [15.0, 20.0, 18.0],
        'seed_mass': [0.5, 1.2, 0.8],
        'plant_height': [50.0, 120.0, 80.0]
    })


@pytest.fixture
def incomplete_trait_df():
    """DataFrame with missing traits."""
    return pd.DataFrame({
        'species_name': ['Species_A', 'Species_B', 'Species_C', 'Species_D'],
        'sla': [15.0, np.nan, 18.0, 22.0],  # Species_B missing SLA
        'seed_mass': [0.5, 1.2, np.nan, 0.9],  # Species_C missing seed_mass
        'plant_height': [50.0, 120.0, 80.0, np.nan]  # Species_D missing height
    })


@pytest.fixture
def empty_string_trait_df():
    """DataFrame with empty string traits."""
    return pd.DataFrame({
        'species_name': ['Species_A', 'Species_B'],
        'sla': [15.0, ''],
        'seed_mass': [0.5, ''],
        'plant_height': [50.0, '']
    })


def test_identify_species_missing_traits_no_missing(complete_trait_df):
    """Test that no species are excluded when all data is present."""
    filtered, log = identify_species_missing_traits(complete_trait_df)
    
    assert len(filtered) == len(complete_trait_df)
    assert len(log) == 0
    assert list(filtered['species_name']) == ['Species_A', 'Species_B', 'Species_C']


def test_identify_species_missing_traits_with_nan(incomplete_trait_df):
    """Test that species with NaN values are correctly identified and excluded."""
    filtered, log = identify_species_missing_traits(incomplete_trait_df)
    
    # Species_B, Species_C, Species_D should be excluded
    assert len(filtered) == 1
    assert filtered.iloc[0]['species_name'] == 'Species_A'
    
    assert len(log) == 3
    
    # Check specific reasons
    species_excluded = {entry['species']: entry['reason'] for entry in log}
    
    assert 'Species_B' in species_excluded
    assert 'sla' in species_excluded['Species_B']
    
    assert 'Species_C' in species_excluded
    assert 'seed_mass' in species_excluded['Species_C']
    
    assert 'Species_D' in species_excluded
    assert 'plant_height' in species_excluded['Species_D']


def test_identify_species_missing_traits_empty_strings(empty_string_trait_df):
    """Test that empty strings are treated as missing."""
    filtered, log = identify_species_missing_traits(empty_string_trait_df)
    
    assert len(filtered) == 1
    assert filtered.iloc[0]['species_name'] == 'Species_A'
    
    assert len(log) == 1
    assert 'Species_B' in log[0]['species']


def test_save_exclusion_report():
    """Test that exclusion report is saved correctly."""
    log = [
        {'species': 'Test_Species', 'reason': 'Missing traits: sla'},
        {'species': 'Test_Species_2', 'reason': 'Missing traits: seed_mass'}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "exclusions.csv"
        save_exclusion_report(log, str(output_path))
        
        assert output_path.exists()
        
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'species' in df.columns
        assert 'reason' in df.columns


def test_run_missing_trait_check_integration(incomplete_trait_df):
    """Test the full pipeline including report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.csv"
        
        filtered, log = run_missing_trait_check(
            incomplete_trait_df,
            output_report_path=str(report_path)
        )
        
        assert len(filtered) == 1
        assert len(log) == 3
        assert report_path.exists()
        
        report_df = pd.read_csv(report_path)
        assert len(report_df) == 3


def test_missing_required_columns():
    """Test behavior when required columns are missing from dataframe."""
    df = pd.DataFrame({
        'species_name': ['A'],
        'other_col': [1.0]
    })
    
    filtered, log = identify_species_missing_traits(df)
    
    assert len(filtered) == 0
    assert len(log) == 1
    assert 'No required trait columns found' in log[0]['reason']


def test_custom_species_column():
    """Test using a custom species column name."""
    df = pd.DataFrame({
        'taxon_id': ['A', 'B'],
        'sla': [10.0, np.nan],
        'seed_mass': [1.0, 2.0],
        'plant_height': [50.0, 60.0]
    })
    
    filtered, log = identify_species_missing_traits(df, species_col='taxon_id')
    
    assert len(filtered) == 1
    assert filtered.iloc[0]['taxon_id'] == 'A'
    assert len(log) == 1
    assert log[0]['species'] == 'B'