import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import shutil

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from preprocess import (
    load_data,
    save_data,
    filter_genes_zero_expression,
    apply_log_pseudocount,
    impute_missing_values_median,
    calculate_coefficient_of_variation,
    define_housekeeping_genes,
    define_cell_type_specific_genes
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'gene_id': ['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5'],
        'cell_line_1': [10.0, 0.0, 5.0, 0.0, 100.0],
        'cell_line_2': [12.0, 0.0, 6.0, 0.0, 110.0],
        'cell_line_3': [8.0, 0.0, 4.0, 0.0, 90.0],
        'cell_line_4': [11.0, 0.0, 5.5, 0.0, 105.0],
        'cell_line_5': [9.0, 0.0, 4.5, 0.0, 95.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

def test_filter_genes_zero_expression(sample_data):
    """Test filtering genes with zero expression in all samples."""
    filtered = filter_genes_zero_expression(sample_data, 'gene_id')
    
    # GENE2, GENE4 should be filtered out (all zeros)
    expected_genes = ['GENE1', 'GENE3', 'GENE5']
    assert list(filtered['gene_id']) == expected_genes
    assert len(filtered) == 3

def test_apply_log_pseudocount(sample_data):
    """Test log pseudocount transformation."""
    transformed = apply_log_pseudocount(sample_data, 'gene_id', pseudocount=1.0)
    
    # Check that transformation was applied
    assert 'cell_line_1' in transformed.columns
    assert transformed['cell_line_1'].iloc[0] == np.log2(10.0 + 1.0)
    assert transformed['cell_line_1'].iloc[1] == np.log2(0.0 + 1.0)  # log2(1) = 0

def test_impute_missing_values_median(sample_data):
    """Test median imputation for missing values."""
    # Add some NaN values
    sample_data_with_nan = sample_data.copy()
    sample_data_with_nan.loc[0, 'cell_line_1'] = np.nan
    sample_data_with_nan.loc[1, 'cell_line_2'] = np.nan
    
    imputed = impute_missing_values_median(sample_data_with_nan, 'gene_id')
    
    # Check that NaN values are filled
    assert not imputed['cell_line_1'].isna().any()
    assert not imputed['cell_line_2'].isna().any()
    
    # Check that the imputed value is the median
    median_val = sample_data['cell_line_1'].median()
    assert imputed.loc[0, 'cell_line_1'] == median_val

def test_calculate_coefficient_of_variation(sample_data):
    """Test CV calculation."""
    cv_df = calculate_coefficient_of_variation(sample_data, 'gene_id')
    
    # Check that CV column exists
    assert 'cv' in cv_df.columns
    assert len(cv_df) == len(sample_data)
    
    # GENE2 and GENE4 have all zeros, so CV should be 0 (handled in implementation)
    # GENE1, GENE3, GENE5 should have non-zero CV
    g1_cv = cv_df.loc[cv_df['gene_id'] == 'GENE1', 'cv'].values[0]
    assert g1_cv > 0  # Should have some variation

def test_define_housekeeping_genes(sample_data):
    """Test housekeeping gene definition with CV threshold."""
    # With threshold 0.2, only genes with very low CV should be selected
    # GENE1, GENE3, GENE5 have low variation relative to mean
    housekeeping = define_housekeeping_genes(sample_data, cv_threshold=0.2, gene_col='gene_id')
    
    # Check that housekeeping genes have CV < 0.2
    assert all(housekeeping['cv'] < 0.2)
    
    # GENE2 and GENE4 should be filtered out (all zeros, CV=0 but might be handled differently)
    # In practice, GENE2 and GENE4 would have been filtered earlier by filter_genes_zero_expression
    assert 'GENE1' in housekeeping['gene_id'].values or 'GENE3' in housekeeping['gene_id'].values

def test_define_cell_type_specific_genes(sample_data):
    """Test cell-type-specific gene definition with CV threshold."""
    # With threshold 0.5, genes with high CV should be selected
    cell_type = define_cell_type_specific_genes(sample_data, cv_threshold=0.5, gene_col='gene_id')
    
    # Check that cell-type-specific genes have CV > 0.5
    assert all(cell_type['cv'] > 0.5)

def test_load_save_data(temp_dir, sample_data):
    """Test loading and saving data."""
    test_file = os.path.join(temp_dir, 'test.csv')
    
    # Save data
    save_data(sample_data, test_file)
    assert os.path.exists(test_file)
    
    # Load data
    loaded = load_data(test_file)
    assert len(loaded) == len(sample_data)
    assert list(loaded.columns) == list(sample_data.columns)
    
    # Check values
    pd.testing.assert_frame_equal(loaded, sample_data)