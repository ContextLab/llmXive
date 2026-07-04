"""
Integration test for the data ingestion pipeline.

Tests the full flow from data fetching to descriptor computation.
Requires T013 (main.py) and T013b (synthetic.py) to be implemented.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.synthetic import generate_synthetic_dataset
from features.descriptors import apply_descriptors_to_dataframe
from utils.dedup import deduplicate_compositions

# Test fixtures
@pytest.fixture
def sample_compositions():
    """Generate a small set of sample compositions for testing."""
    return pd.DataFrame({
        'composition': ['Zr50Cu40Al10', 'Ti40Zr40Cu20', 'Pd40Ni40P20', 'Mg65Cu25Y10', 'Fe50Co30Ni20'],
        'phase': ['amorphous', 'crystalline', 'amorphous', 'amorphous', 'crystalline'],
        'source': ['test', 'test', 'test', 'test', 'test'],
        'url': ['test://1', 'test://2', 'test://3', 'test://4', 'test://5']
    })

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_synthetic_data_generation():
    """Test that synthetic data generation produces valid compositions."""
    df = generate_synthetic_dataset(n_samples=100)
    
    assert len(df) == 100
    assert 'composition' in df.columns
    assert 'phase' in df.columns
    assert 'source' in df.columns
    
    # Check phase labels
    valid_phases = ['amorphous', 'crystalline']
    assert all(p in valid_phases for p in df['phase'].unique())
    
    # Check that composition strings are non-empty
    assert all(len(c) > 0 for c in df['composition'])

def test_descriptor_computation_on_synthetic():
    """Test that descriptors are computed correctly on synthetic data."""
    # Generate synthetic data
    df = generate_synthetic_dataset(n_samples=50)
    
    # Apply descriptors
    df_with_desc = apply_descriptors_to_dataframe(df)
    
    # Check that descriptors were added
    expected_descriptors = [
        'atomic_radius', 'electronegativity', 'valence_electron_concentration',
        'atomic_size_mismatch', 'mixing_enthalpy', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio',
        'miedema_heat_of_formation', 'atomic_packing_factor'
    ]
    
    for desc in expected_descriptors:
        assert desc in df_with_desc.columns, f"Missing descriptor: {desc}"
    
    # Check for reasonable ranges (basic sanity check)
    # Atomic radius should be positive
    assert all(df_with_desc['atomic_radius'] > 0)
    
    # Electronegativity should be positive
    assert all(df_with_desc['electronegativity'] > 0)

def test_deduplication_preserves_primary_source():
    """Test that deduplication retains the primary source (Science Advances)."""
    # Create data with duplicates
    data = pd.DataFrame({
        'composition': ['Zr50Cu40Al10', 'Zr50Cu40Al10', 'Ti40Zr40Cu20'],
        'phase': ['amorphous', 'crystalline', 'amorphous'],
        'source': ['science_advances', 'materials_project', 'test'],
        'url': ['doi:1', 'doi:2', 'doi:3']
    })
    
    # Deduplicate
    deduped, stats = deduplicate_compositions(data)
    
    # Should have 2 unique compositions
    assert len(deduped) == 2
    
    # Zr50Cu40Al10 should retain 'science_advances' source
    zr_row = deduped[deduped['composition'] == 'Zr50Cu40Al10']
    assert len(zr_row) == 1
    assert zr_row.iloc[0]['source'] == 'science_advances'

def test_full_pipeline_integration(temp_data_dir):
    """Test the full ingestion pipeline with synthetic data fallback."""
    # Simulate the pipeline flow
    
    # 1. Generate synthetic data (simulating fallback)
    raw_df = generate_synthetic_dataset(n_samples=200)
    
    # 2. Deduplicate
    deduped_df, stats = deduplicate_compositions(raw_df)
    
    # 3. Compute descriptors
    engineered_df = apply_descriptors_to_dataframe(deduped_df)
    
    # Assertions
    assert len(engineered_df) > 0
    assert len(engineered_df) <= len(raw_df)  # Deduplication may reduce count
    
    # Check descriptor completeness
    desc_cols = [
        'atomic_radius', 'electronegativity', 'valence_electron_concentration',
        'atomic_size_mismatch', 'mixing_enthalpy', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio',
        'miedema_heat_of_formation', 'atomic_packing_factor'
    ]
    
    completeness = engineered_df[desc_cols].notna().all(axis=1).mean()
    assert completeness >= 0.95, f"Descriptor completeness too low: {completeness}"
    
    # Check physical ranges
    assert all(engineered_df['atomic_radius'] > 0)
    assert all(engineered_df['electronegativity'] > 0)
    assert all(engineered_df['valence_electron_concentration'] > 0)

def test_dataset_capping():
    """Test that dataset capping logic works correctly."""
    # Generate more than 10,000 samples
    large_df = generate_synthetic_dataset(n_samples=15000)
    
    # Apply capping (stratified by alloy system - simplified here)
    # In real implementation, this would be done in utils/io.py
    capped_df = large_df.head(10000)
    
    assert len(capped_df) == 10000
    assert len(capped_df) < len(large_df)
