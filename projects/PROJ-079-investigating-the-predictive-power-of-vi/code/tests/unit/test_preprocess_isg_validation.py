import pytest
import pandas as pd
import numpy as np
from src.preprocess import validate_isg_mapping

def test_validate_isg_mapping_success():
    """Test that validation passes when overlap >= 80%."""
    mappings = ['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5']
    counts_matrix = pd.DataFrame(
        np.random.rand(10, 5),
        columns=['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5']
    )
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is True

def test_validate_isg_mapping_failure():
    """Test that validation fails when overlap < 80%."""
    mappings = ['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5']
    # Only GENE1 and GENE2 are present (40% overlap)
    counts_matrix = pd.DataFrame(
        np.random.rand(10, 2),
        columns=['GENE1', 'GENE2']
    )
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is False

def test_validate_isg_mapping_empty_mappings():
    """Test that validation fails with empty mappings."""
    mappings = []
    counts_matrix = pd.DataFrame(
        np.random.rand(10, 5),
        columns=['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5']
    )
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is False

def test_validate_isg_mapping_empty_matrix():
    """Test that validation fails with empty counts matrix."""
    mappings = ['GENE1', 'GENE2', 'GENE3']
    counts_matrix = pd.DataFrame()
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is False

def test_validate_isg_mapping_no_overlap():
    """Test that validation fails when there is no overlap."""
    mappings = ['GENE_A', 'GENE_B', 'GENE_C']
    counts_matrix = pd.DataFrame(
        np.random.rand(10, 3),
        columns=['GENE_X', 'GENE_Y', 'GENE_Z']
    )
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is False

def test_validate_isg_mapping_exactly_80_percent():
    """Test that validation passes exactly at 80% threshold."""
    mappings = ['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5']
    # 4 out of 5 genes present (80%)
    counts_matrix = pd.DataFrame(
        np.random.rand(10, 4),
        columns=['GENE1', 'GENE2', 'GENE3', 'GENE4']
    )
    
    result = validate_isg_mapping(mappings, counts_matrix)
    assert result is True