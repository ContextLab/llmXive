"""
Tests for T019: Descriptor Pipeline Runner
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.run_descriptor_pipeline import load_smiles_from_file, clean_dataframe, compute_all_descriptors
from code.descriptors import compute_all_descriptors as compute_desc_func

class TestDescriptorPipeline:
    """Test suite for T019 descriptor pipeline."""
    
    def test_load_smiles_from_file_valid(self):
        """Test loading valid SMILES from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("smiles\n")
            f.write("c1ccccc1\n")  # Benzene
            f.write("CCO\n")       # Ethanol
            temp_path = f.name
        
        try:
            df = load_smiles_from_file(temp_path)
            assert len(df) == 2
            assert 'smiles' in df.columns
            assert 'valid' in df.columns
            assert df['valid'].sum() == 2  # Both valid
        finally:
            os.unlink(temp_path)
    
    def test_load_smiles_from_file_invalid(self):
        """Test loading invalid SMILES from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("smiles\n")
            f.write("invalid_smiles\n")
            f.write("c1ccccc1\n")
            temp_path = f.name
        
        try:
            df = load_smiles_from_file(temp_path)
            assert len(df) == 2
            assert df['valid'].sum() == 1  # Only benzene valid
        finally:
            os.unlink(temp_path)
    
    def test_clean_dataframe(self):
        """Test cleaning dataframe removes invalid rows."""
        data = {
            'smiles': ['c1ccccc1', 'invalid', 'CCO'],
            'valid': [True, False, True],
            'error_msg': ['', 'Invalid SMILES', '']
        }
        df = pd.DataFrame(data)
        
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 2
        assert 'error_msg' not in cleaned.columns
    
    def test_compute_all_descriptors_benzene(self):
        """Test descriptor computation on benzene."""
        smiles_list = ['c1ccccc1']
        results = compute_desc_func(smiles_list)
        
        assert len(results) == 1
        result = results[0]
        
        # Check all expected columns exist
        expected_cols = [
            'degree_mean', 'degree_std', 'degree_max', 'degree_min',
            'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
            'aromaticity_index', 'ring_count',
            'conjugation_length', 'num_conjugated_bonds', 'conjugation_density',
            'aromatic_ring_count', 'conjugated_ring_count'
        ]
        
        for col in expected_cols:
            assert col in result, f"Missing column: {col}"
            assert not np.isnan(result[col]), f"NaN value in {col} for benzene"
        
        # Benzene specific checks
        assert result['aromaticity_index'] > 0.5  # High aromaticity
        assert result['aromatic_ring_count'] == 1
    
    def test_compute_all_descriptors_ethanol(self):
        """Test descriptor computation on ethanol (non-aromatic)."""
        smiles_list = ['CCO']
        results = compute_desc_func(smiles_list)
        
        assert len(results) == 1
        result = results[0]
        
        # Check all expected columns exist
        expected_cols = [
            'degree_mean', 'degree_std', 'degree_max', 'degree_min',
            'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
            'aromaticity_index', 'ring_count',
            'conjugation_length', 'num_conjugated_bonds', 'conjugation_density',
            'aromatic_ring_count', 'conjugated_ring_count'
        ]
        
        for col in expected_cols:
            assert col in result, f"Missing column: {col}"
            assert not np.isnan(result[col]), f"NaN value in {col} for ethanol"
        
        # Ethanol specific checks
        assert result['aromaticity_index'] == 0.0
        assert result['aromatic_ring_count'] == 0
    
    def test_compute_all_descriptors_mixed(self):
        """Test descriptor computation on mixed valid/invalid input."""
        smiles_list = ['c1ccccc1', 'invalid_smiles', 'CCO']
        results = compute_desc_func(smiles_list)
        
        assert len(results) == 3
        
        # First and third should be valid
        assert not np.isnan(results[0]['aromaticity_index'])
        assert not np.isnan(results[2]['aromaticity_index'])
        
        # Second should be NaN
        assert np.isnan(results[1]['aromaticity_index'])
    
    def test_compute_all_descriptors_empty(self):
        """Test descriptor computation on empty list."""
        results = compute_desc_func([])
        assert len(results) == 0
    
    def test_compute_all_descriptors_all_nan(self):
        """Test descriptor computation when all inputs are invalid."""
        smiles_list = ['invalid1', 'invalid2']
        results = compute_desc_func(smiles_list)
        
        assert len(results) == 2
        for result in results:
            assert np.isnan(result['aromaticity_index'])
            assert np.isnan(result['degree_mean'])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
