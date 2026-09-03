import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from preprocess import (
    calculate_coefficient_of_variation,
    define_housekeeping_genes,
    define_cell_type_specific_genes,
    load_data,
    save_data
)

def test_calculate_coefficient_of_variation():
    """Test CV calculation logic."""
    data = {
        'gene_id': ['g1', 'g2', 'g3'],
        'cell_line_1': [10.0, 100.0, 5.0],
        'cell_line_2': [10.0, 150.0, 5.0],
        'cell_line_3': [10.0, 50.0, 5.0]
    }
    df = pd.DataFrame(data)
    cv_df = calculate_coefficient_of_variation(df)

    assert 'cv' in cv_df.columns
    assert 'mean' in cv_df.columns
    assert 'std' in cv_df.columns

    # g1: mean=10, std=0 -> cv=0
    # g2: mean=100, std=50 -> cv=0.5
    # g3: mean=5, std=0 -> cv=0
    
    g1_cv = cv_df[cv_df['gene_id'] == 'g1']['cv'].values[0]
    g2_cv = cv_df[cv_df['gene_id'] == 'g2']['cv'].values[0]
    g3_cv = cv_df[cv_df['gene_id'] == 'g3']['cv'].values[0]

    assert np.isclose(g1_cv, 0.0)
    assert np.isclose(g2_cv, 0.5)
    assert np.isclose(g3_cv, 0.0)

def test_define_housekeeping_genes():
    """Test housekeeping gene selection."""
    data = {
        'gene_id': ['g1', 'g2', 'g3'],
        'cell_line_1': [10.0, 100.0, 5.0],
        'cell_line_2': [10.0, 150.0, 5.0],
        'cell_line_3': [10.0, 50.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    # Threshold 0.2: g1 and g3 should be selected (CV=0)
    housekeeping_df = define_housekeeping_genes(df, cv_threshold=0.2)
    
    assert len(housekeeping_df) == 2
    assert 'g2' not in housekeeping_df['gene_id'].values
    assert 'g1' in housekeeping_df['gene_id'].values
    assert 'g3' in housekeeping_df['gene_id'].values

def test_define_cell_type_specific_genes():
    """Test cell-type-specific gene selection."""
    data = {
        'gene_id': ['g1', 'g2', 'g3'],
        'cell_line_1': [10.0, 100.0, 5.0],
        'cell_line_2': [10.0, 150.0, 5.0],
        'cell_line_3': [10.0, 50.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    # Threshold 0.5: g2 should be selected (CV=0.5, strictly > 0.5? Task says > 0.5)
    # Let's adjust data to ensure g2 > 0.5
    data['cell_line_1'] = [10.0, 10.0, 5.0]
    data['cell_line_2'] = [10.0, 200.0, 5.0]
    data['cell_line_3'] = [10.0, 0.0, 5.0] # Mean 66.6, Std ~100 -> CV > 1
    df = pd.DataFrame(data)
    
    specific_df = define_cell_type_specific_genes(df, cv_threshold=0.5)
    
    assert len(specific_df) == 1
    assert specific_df['gene_id'].values[0] == 'g2'

def test_save_and_load_data(tmp_path):
    """Test saving and loading data roundtrip."""
    data = {
        'gene_id': ['g1', 'g2'],
        'val1': [1.0, 2.0],
        'val2': [3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    output_path = os.path.join(tmp_path, "test.csv")
    save_data(df, output_path)
    
    loaded_df = load_data(output_path)
    
    assert loaded_df.shape == df.shape
    assert list(loaded_df.columns) == list(df.columns)
    assert np.allclose(loaded_df['val1'], df['val1'])
    assert np.allclose(loaded_df['val2'], df['val2'])