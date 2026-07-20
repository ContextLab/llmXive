"""
Unit tests for src/data/fetch_traits.py

Tests:
- Source validation logic (Handbook 2013 vs others)
- Trait filtering
- Aggregation logic
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.fetch_traits import (
    validate_source_metadata,
    filter_required_traits,
    aggregate_species_traits,
    HANDBOOK_2013_SOURCE,
    UNVERIFIED_PROTOCOL_FLAG
)

@pytest.fixture
def sample_trait_df():
    """Create a sample DataFrame for testing."""
    data = {
        'species': ['Helianthus annuus', 'Helianthus annuus', 'Zea mays', 'Arabidopsis thaliana'],
        'trait_name': ['SLA', 'seed mass', 'Plant Height', 'SLA'],
        'value': [15.5, 2.3, 180.0, 20.1],
        'source': ['Handbook 2013', 'Handbook 2013', 'Other Source', '']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_trait_df_with_variations():
    """Create a sample DataFrame with trait name variations."""
    data = {
        'species': ['Species A', 'Species A', 'Species B', 'Species B'],
        'trait_name': ['specific leaf area', 'Seed_Mass', 'height', 'plant height'],
        'value': [10.0, 5.0, 100.0, 120.0],
        'source': ['Handbook 2013', 'Handbook 2013', 'Handbook 2013', 'Handbook 2013']
    }
    return pd.DataFrame(data)

def test_validate_source_metadata_handbook_2013(sample_trait_df):
    """Test that 'Handbook 2013' sources are marked as verified."""
    result = validate_source_metadata(sample_trait_df)
    
    # Check column existence
    assert 'protocol_status' in result.columns
    
    # Check specific rows
    assert result.loc[0, 'protocol_status'] == 'verified protocol'
    assert result.loc[1, 'protocol_status'] == 'verified protocol'
    assert result.loc[2, 'protocol_status'] == UNVERIFIED_PROTOCOL_FLAG
    assert result.loc[3, 'protocol_status'] == UNVERIFIED_PROTOCOL_FLAG

def test_validate_source_metadata_empty_source(sample_trait_df):
    """Test that empty sources are marked as unverified."""
    # Modify source to be empty string
    sample_trait_df.loc[3, 'source'] = ''
    result = validate_source_metadata(sample_trait_df)
    assert result.loc[3, 'protocol_status'] == UNVERIFIED_PROTOCOL_FLAG

def test_validate_source_metadata_nan_source():
    """Test that NaN sources are marked as unverified."""
    data = {
        'species': ['Species A'],
        'trait_name': ['SLA'],
        'value': [10.0],
        'source': [np.nan]
    }
    df = pd.DataFrame(data)
    result = validate_source_metadata(df)
    assert result.loc[0, 'protocol_status'] == UNVERIFIED_PROTOCOL_FLAG

def test_filter_required_traits_basic(sample_trait_df):
    """Test filtering for SLA, seed mass, plant height."""
    result = filter_required_traits(sample_trait_df)
    
    # All rows should be kept in this specific case as they map to required traits
    assert len(result) == 4
    assert 'canonical_trait' in result.columns
    assert all(result['canonical_trait'].isin(['sla', 'seed_mass', 'plant_height']))

def test_filter_required_traits_with_variations(sample_trait_df_with_variations):
    """Test filtering with various trait name formats."""
    result = filter_required_traits(sample_trait_df_with_variations)
    
    assert len(result) == 4
    assert 'canonical_trait' in result.columns
    # Check mapping
    assert result.loc[0, 'canonical_trait'] == 'sla'
    assert result.loc[1, 'canonical_trait'] == 'seed_mass'
    assert result.loc[2, 'canonical_trait'] == 'plant_height'
    assert result.loc[3, 'canonical_trait'] == 'plant_height'

def test_filter_required_traits_excludes_unwanted():
    """Test that non-required traits are excluded."""
    data = {
        'species': ['Species A'],
        'trait_name': ['Leaf Nitrogen'], # Not in required list
        'value': [2.0],
        'source': ['Handbook 2013']
    }
    df = pd.DataFrame(data)
    result = filter_required_traits(df)
    assert len(result) == 0

def test_aggregate_species_traits(sample_trait_df):
    """Test aggregation of traits by species."""
    # Ensure canonical_trait is present (it should be after filter_required_traits)
    filtered_df = filter_required_traits(sample_trait_df)
    result = aggregate_species_traits(filtered_df)
    
    assert 'species' in result.columns
    assert 'sla' in result.columns
    assert 'seed_mass' in result.columns
    assert 'plant_height' in result.columns
    
    # Check specific species
    # Helianthus annuus has SLA=15.5
    helianthus = result[result['species'] == 'Helianthus annuus']
    assert len(helianthus) == 1
    assert helianthus['sla'].values[0] == 15.5

def test_aggregate_species_traits_multiple_values():
    """Test aggregation with multiple values for the same trait."""
    data = {
        'species': ['Species A', 'Species A', 'Species A'],
        'trait_name': ['SLA', 'SLA', 'SLA'],
        'value': [10.0, 20.0, 30.0],
        'source': ['Handbook 2013', 'Handbook 2013', 'Handbook 2013']
    }
    df = pd.DataFrame(data)
    filtered_df = filter_required_traits(df)
    result = aggregate_species_traits(filtered_df)
    
    assert len(result) == 1
    assert result['sla'].values[0] == 20.0 # Mean of 10, 20, 30

def test_aggregate_species_traits_missing_trait():
    """Test aggregation when a species is missing a required trait."""
    data = {
        'species': ['Species A', 'Species B'],
        'trait_name': ['SLA', 'SLA'],
        'value': [10.0, 15.0],
        'source': ['Handbook 2013', 'Handbook 2013']
    }
    df = pd.DataFrame(data)
    filtered_df = filter_required_traits(df)
    result = aggregate_species_traits(filtered_df)
    
    assert len(result) == 2
    # Species A should have seed_mass and plant_height as NaN
    assert pd.isna(result.loc[result['species'] == 'Species A', 'seed_mass'].values[0])
    assert pd.isna(result.loc[result['species'] == 'Species B', 'seed_mass'].values[0])
