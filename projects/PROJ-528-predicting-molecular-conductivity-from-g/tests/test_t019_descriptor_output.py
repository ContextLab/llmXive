"""
Unit tests for T019: Descriptor computation output validation.

Tests that the descriptor pipeline produces a CSV with the EXACT required columns
and no NaN values.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from descriptors import compute_descriptors_batch
from run_descriptor_pipeline import clean_dataframe, OUTPUT_COLUMNS

class TestT019DescriptorOutput:
    """Tests for T019 descriptor output validation."""
    
    def test_output_columns_exact_match(self):
        """Verify the output columns match the T019 specification exactly."""
        expected_cols = [
            'smiles', 'status', 
            'degree_mean', 'degree_std', 'degree_max', 'degree_min',
            'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
            'aromaticity_index', 'conjugation_length', 'ring_count', 
            'bond_polarity', 'resonance_energy'
        ]
        assert OUTPUT_COLUMNS == expected_cols, f"Output columns mismatch: {OUTPUT_COLUMNS}"
    
    def test_clean_dataframe_removes_nan(self):
        """Verify clean_dataframe replaces NaN values."""
        data = {
            'smiles': ['CC', None],
            'status': ['ok', np.nan],
            'degree_mean': [1.0, np.nan],
            'degree_std': [0.5, np.nan],
            'degree_max': [2, np.nan],
            'degree_min': [1, np.nan],
            'path_length_mean': [1.0, np.nan],
            'path_length_std': [0.0, np.nan],
            'path_length_max': [1, np.nan],
            'path_length_min': [1, np.nan],
            'aromaticity_index': [0.0, np.nan],
            'conjugation_length': [0, np.nan],
            'ring_count': [0, np.nan],
            'bond_polarity': [0.0, np.nan],
            'resonance_energy': [0.0, np.nan],
        }
        df = pd.DataFrame(data)
        cleaned = clean_dataframe(df)
        
        assert not cleaned.isna().any().any(), "NaN values remain after cleaning"
        assert cleaned['status'].iloc[1] == 'unknown'
        assert cleaned['degree_mean'].iloc[1] == 0.0
    
    def test_clean_dataframe_reorders_columns(self):
        """Verify clean_dataframe reorders columns to match OUTPUT_COLUMNS."""
        # Create DF with columns in wrong order
        data = {
            'resonance_energy': [0.0],
            'smiles': ['CC'],
            'status': ['ok'],
            'degree_mean': [1.0],
            'degree_std': [0.5],
            'degree_max': [2],
            'degree_min': [1],
            'path_length_mean': [1.0],
            'path_length_std': [0.0],
            'path_length_max': [1],
            'path_length_min': [1],
            'aromaticity_index': [0.0],
            'conjugation_length': [0],
            'ring_count': [0],
            'bond_polarity': [0.0],
        }
        df = pd.DataFrame(data)
        cleaned = clean_dataframe(df)
        
        assert list(cleaned.columns) == OUTPUT_COLUMNS
    
    def test_compute_descriptors_batch_produces_required_columns(self):
        """Verify compute_descriptors_batch produces all required columns."""
        # Test with a simple valid SMILES
        smiles_list = ['CC', 'c1ccccc1']
        result = compute_descriptors_batch(smiles_list)
        
        for col in OUTPUT_COLUMNS:
            assert col in result.columns, f"Missing column: {col}"
        
        assert len(result) == len(smiles_list)
    
    def test_compute_descriptors_batch_no_nan_on_valid_input(self):
        """Verify compute_descriptors_batch produces no NaN on valid input."""
        smiles_list = ['CC', 'c1ccccc1', 'C=CC=C']
        result = compute_descriptors_batch(smiles_list)
        
        assert not result.isna().any().any(), "NaN values in descriptor output"
    
    def test_invalid_smiles_handled_gracefully(self):
        """Verify invalid SMILES are handled with status='invalid' and zeros."""
        smiles_list = ['INVALID_SMILES', 'CC']
        result = compute_descriptors_batch(smiles_list)
        
        assert len(result) == 2
        assert result.iloc[0]['status'] == 'invalid'
        assert result.iloc[1]['status'] == 'ok'
        
        # Check that invalid molecules have numeric zeros (not NaN)
        numeric_cols = [c for c in result.columns if c != 'smiles' and c != 'status']
        for col in numeric_cols:
            assert not pd.isna(result.iloc[0][col]), f"NaN in {col} for invalid SMILES"