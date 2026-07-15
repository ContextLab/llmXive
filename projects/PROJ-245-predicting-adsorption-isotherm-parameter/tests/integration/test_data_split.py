"""
Integration test for material-level data splitting.
"""
import pytest
import pandas as pd
import numpy as np
from code.models.train import material_level_split

@pytest.fixture
def sample_data():
    """Create sample data with known material_id distribution."""
    data = {
        'material_id': ['M1', 'M1', 'M2', 'M2', 'M3', 'M3', 'M4', 'M5', 'M5', 'M6'],
        'polarizability': [1.0, 1.1, 2.0, 2.1, 3.0, 3.1, 4.0, 5.0, 5.1, 6.0],
        'surface_area': [100, 105, 200, 205, 300, 305, 400, 500, 505, 600],
        'langmuir_capacity': [10, 11, 20, 21, 30, 31, 40, 50, 51, 60],
        'henry_constant': [0.1, 0.11, 0.2, 0.21, 0.3, 0.31, 0.4, 0.5, 0.51, 0.6]
    }
    return pd.DataFrame(data)

def test_material_level_split_no_overlap(sample_data):
    """Test that train and test sets have no material_id overlap."""
    train_df, test_df = material_level_split(sample_data, test_size=0.3, random_state=42)
    
    train_materials = set(train_df['material_id'].unique())
    test_materials = set(test_df['material_id'].unique())
    
    # Check for no overlap
    overlap = train_materials.intersection(test_materials)
    assert len(overlap) == 0, f"Found overlapping material IDs: {overlap}"
    
    # Check that all materials are accounted for
    all_materials = set(sample_data['material_id'].unique())
    assert train_materials.union(test_materials) == all_materials

def test_material_level_split_proportions(sample_data):
    """Test that the split approximates the requested test_size."""
    train_df, test_df = material_level_split(sample_data, test_size=0.3, random_state=42)
    
    total_materials = len(sample_data['material_id'].unique())
    test_materials = len(test_df['material_id'].unique())
    
    # The test set should contain approximately 30% of materials
    # Allow some tolerance due to the discrete nature of material splitting
    expected_test_ratio = 0.3
    actual_test_ratio = test_materials / total_materials
    
    # Allow 20% tolerance
    assert abs(actual_test_ratio - expected_test_ratio) < 0.2, \
        f"Test material ratio {actual_test_ratio} deviates significantly from expected {expected_test_ratio}"

def test_material_level_split_deterministic(sample_data):
    """Test that the split is deterministic with the same random_state."""
    train_df1, test_df1 = material_level_split(sample_data, test_size=0.3, random_state=42)
    train_df2, test_df2 = material_level_split(sample_data, test_size=0.3, random_state=42)
    
    # Check that the splits are identical
    pd.testing.assert_frame_equal(train_df1.sort_values('material_id').reset_index(drop=True),
                                 train_df2.sort_values('material_id').reset_index(drop=True))
    pd.testing.assert_frame_equal(test_df1.sort_values('material_id').reset_index(drop=True),
                                 test_df2.sort_values('material_id').reset_index(drop=True))
