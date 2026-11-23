import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from code.data_ingestion import engineer_features
from code.utils import compute_tpsa, compute_morgan_fp, compute_hbond_count

class TestEngineerFeatures:
    """Test suite for the engineer_features function."""
    
    def test_basic_feature_engineering(self):
        """Test that basic features are computed correctly."""
        # Create a simple test dataframe
        df = pd.DataFrame({
            'cation_smiles': ['CCO', 'CC'],
            'anion_smiles': ['[O-]c1ccccc1', '[Cl-]'],
            'partial_charge': [0.1, 0.2]  # This should be dropped
        })
        
        # Run feature engineering
        result = engineer_features(df)
        
        # Check that required columns exist
        expected_cols = [
            'cation_tpsa', 'anion_tpsa', 'total_tpsa',
            'cation_surface_area', 'anion_surface_area', 'total_surface_area',
            'cation_hbond_count', 'anion_hbond_count', 'total_hbond_count',
            'cation_polarizability', 'anion_polarizability', 'total_polarizability',
            'morgan_fp', 'charge_reliability'
        ]
        
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"
        
        # Check that partial_charge was dropped
        assert 'partial_charge' not in result.columns, "partial_charge should be dropped"
        
        # Check that TPSA values are reasonable (positive numbers)
        assert all(result['total_tpsa'] >= 0), "TPSA should be non-negative"
        
        # Check that surface areas are positive
        assert all(result['total_surface_area'] > 0), "Surface area should be positive"
        
        # Check that H-bond counts are non-negative integers
        assert all(result['total_hbond_count'] >= 0), "H-bond count should be non-negative"
        assert all(result['total_hbond_count'].apply(lambda x: isinstance(x, (int, np.integer)))), "H-bond count should be integer"
        
        # Check that polarizability values are positive
        assert all(result['total_polarizability'] > 0), "Polarizability should be positive"
        
        # Check that Morgan fingerprints are arrays of correct length
        assert all(len(fp) == 4096 for fp in result['morgan_fp']), "Morgan fingerprint should be length 4096"
        
        # Check that charge_reliability column exists and has default value
        assert all(result['charge_reliability'] == 'reliable'), "Default reliability should be 'reliable'"
    
    def test_unreliable_charges_marked(self):
        """Test that rows with unreliable charges are marked correctly."""
        df = pd.DataFrame({
            'cation_smiles': ['CCO', 'invalid_smiles'],
            'anion_smiles': ['[O-]c1ccccc1', '[Cl-]'],
            'charge_reliability': ['reliable', 'unreliable']
        })
        
        result = engineer_features(df)
        
        assert result['charge_reliability'].iloc[0] == 'reliable'
        assert result['charge_reliability'].iloc[1] == 'unreliable'
    
    def test_output_file_created(self):
        """Test that the output parquet file is created."""
        df = pd.DataFrame({
            'cation_smiles': ['CCO'],
            'anion_smiles': ['[O-]c1ccccc1']
        })
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the output path
            original_path = 'data/processed/unified_dataset.parquet'
            test_path = os.path.join(tmpdir, 'test_output.parquet')
            
            # We can't easily mock the path in the function, so we'll just check
            # that the function runs without error and creates the file in the default location
            # For this test, we'll just verify the function doesn't crash
            result = engineer_features(df)
            
            # Check that the default output file exists
            assert os.path.exists('data/processed/unified_dataset.parquet'), "Output file should be created"
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['cation_smiles', 'anion_smiles'])
        
        result = engineer_features(df)
        
        # Should not crash and should return empty dataframe with correct columns
        assert len(result) == 0
        assert 'total_tpsa' in result.columns
        assert 'total_polarizability' in result.columns
    
    def test_missing_smiles(self):
        """Test handling of missing SMILES values."""
        df = pd.DataFrame({
            'cation_smiles': ['CCO', None],
            'anion_smiles': ['[O-]c1ccccc1', '[Cl-]']
        })
        
        result = engineer_features(df)
        
        # Should handle missing values gracefully
        assert len(result) == 2
        # Second row should have 0 or NaN for computed features
        assert result['total_tpsa'].iloc[1] == 0.0  # Default for failed calculation
        assert result['total_polarizability'].iloc[1] == 0.0