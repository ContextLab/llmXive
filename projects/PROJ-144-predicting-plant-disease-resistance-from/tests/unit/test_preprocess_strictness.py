"""
Unit tests for T037: InChIKey alignment strictness check.
Verifies that DataQualityError is raised when < 10 common metabolites are found.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import align_metabolites_by_inchikey, DataQualityError

def test_align_with_sufficient_common_metabolites():
    """Test that alignment succeeds when >= 10 common metabolites exist."""
    # Create mock data for 2 studies
    # Study 1: 15 metabolites
    study1_cols = [f"met_{i}" for i in range(15)]
    study1_data = pd.DataFrame(np.random.rand(10, 15), columns=study1_cols)
    
    # Study 2: 15 metabolites
    study2_cols = [f"met_{i}" for i in range(15)]
    study2_data = pd.DataFrame(np.random.rand(10, 15), columns=study2_cols)
    
    # Create metadata with InChIKey mapping
    # Map all 15 metabolites to unique InChIKeys
    inchikeys = [f"INCHIKEY_{i}" for i in range(15)]
    
    meta1 = {
        'study_id': 'study1',
        'inchikey_map': {inchikeys[i]: study1_cols[i] for i in range(15)}
    }
    meta2 = {
        'study_id': 'study2',
        'inchikey_map': {inchikeys[i]: study2_cols[i] for i in range(15)}
    }
    
    data_list = [study1_data, study2_data]
    meta_list = [meta1, meta2]
    
    # Should succeed
    result_df, common_cols, stats = align_metabolites_by_inchikey(
        data_list, meta_list, min_common=10
    )
    
    assert len(common_cols) == 15
    assert stats['common_metabolites_count'] == 15

def test_align_with_insufficient_common_metabolites():
    """Test that DataQualityError is raised when < 10 common metabolites exist."""
    # Create mock data with only 5 common metabolites
    study1_cols = [f"met_{i}" for i in range(5)] + [f"unique_{i}" for i in range(10)]
    study1_data = pd.DataFrame(np.random.rand(10, 15), columns=study1_cols)
    
    study2_cols = [f"met_{i}" for i in range(5)] + [f"other_{i}" for i in range(10)]
    study2_data = pd.DataFrame(np.random.rand(10, 15), columns=study2_cols)
    
    # Map only the 5 common ones
    common_inchikeys = [f"INCHIKEY_{i}" for i in range(5)]
    
    meta1 = {
        'study_id': 'study1',
        'inchikey_map': {common_inchikeys[i]: study1_cols[i] for i in range(5)}
    }
    meta2 = {
        'study_id': 'study2',
        'inchikey_map': {common_inchikeys[i]: study2_cols[i] for i in range(5)}
    }
    
    data_list = [study1_data, study2_data]
    meta_list = [meta1, meta2]
    
    # Should raise DataQualityError
    with pytest.raises(DataQualityError) as exc_info:
        align_metabolites_by_inchikey(data_list, meta_list, min_common=10)
    
    assert "DataQualityError" in str(exc_info.value)
    assert "Insufficient common metabolites" in str(exc_info.value)
    assert "5" in str(exc_info.value)
    assert "10" in str(exc_info.value)

def test_align_with_exact_threshold():
    """Test that alignment succeeds when exactly 10 common metabolites exist."""
    study1_cols = [f"met_{i}" for i in range(10)]
    study1_data = pd.DataFrame(np.random.rand(10, 10), columns=study1_cols)
    
    study2_cols = [f"met_{i}" for i in range(10)]
    study2_data = pd.DataFrame(np.random.rand(10, 10), columns=study2_cols)
    
    inchikeys = [f"INCHIKEY_{i}" for i in range(10)]
    
    meta1 = {
        'study_id': 'study1',
        'inchikey_map': {inchikeys[i]: study1_cols[i] for i in range(10)}
    }
    meta2 = {
        'study_id': 'study2',
        'inchikey_map': {inchikeys[i]: study2_cols[i] for i in range(10)}
    }
    
    data_list = [study1_data, study2_data]
    meta_list = [meta1, meta2]
    
    # Should succeed (>= 10)
    result_df, common_cols, stats = align_metabolites_by_inchikey(
        data_list, meta_list, min_common=10
    )
    
    assert len(common_cols) == 10
    assert stats['common_metabolites_count'] == 10