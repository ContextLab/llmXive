import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.save_descriptors import verify_schema, save_descriptors
from rdkit import Chem
from rdkit.Chem import Descriptors

class TestSaveDescriptors:
    def test_verify_schema_valid(self):
        """Test that a valid schema passes verification."""
        descriptor_names = ['desc_MolWt', 'desc_LogP', 'desc_NumHDonors']
        df = pd.DataFrame({
            'smiles': ['CCO', 'CCO'],
            'target': [1.0, 2.0],
            'desc_MolWt': [46.0, 46.0],
            'desc_LogP': [0.5, 0.5],
            'desc_NumHDonors': [1.0, 1.0]
        })
        assert verify_schema(df, descriptor_names) is True

    def test_verify_schema_missing_column(self):
        """Test that a missing required column raises AssertionError."""
        descriptor_names = ['desc_MolWt']
        df = pd.DataFrame({
            'smiles': ['CCO'],
            # Missing 'target'
            'desc_MolWt': [46.0]
        })
        with pytest.raises(AssertionError):
            verify_schema(df, descriptor_names)

    def test_verify_schema_forbidden_column(self):
        """Test that a forbidden column (TPSA) raises AssertionError."""
        descriptor_names = ['desc_MolWt']
        df = pd.DataFrame({
            'smiles': ['CCO'],
            'target': [1.0],
            'desc_MolWt': [46.0],
            'TPSA': [20.0]  # Forbidden
        })
        with pytest.raises(AssertionError):
            verify_schema(df, descriptor_names)

    def test_verify_schema_wrong_count(self):
        """Test that wrong column count raises AssertionError."""
        descriptor_names = ['desc_MolWt', 'desc_LogP']
        df = pd.DataFrame({
            'smiles': ['CCO'],
            'target': [1.0],
            'desc_MolWt': [46.0]
            # Missing desc_LogP
        })
        with pytest.raises(AssertionError):
            verify_schema(df, descriptor_names)

    def test_save_descriptors_integration(self):
        """Test the full save_descriptors function."""
        descriptor_names = ['desc_MolWt', 'desc_LogP']
        df = pd.DataFrame({
            'smiles': ['CCO', 'CC(=O)O'],
            'target': [1.5, 2.5],
            'desc_MolWt': [46.0, 60.0],
            'desc_LogP': [0.5, -0.5]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_descriptors.parquet"
            save_descriptors(df, output_path, descriptor_names)
            
            assert output_path.exists()
            df_loaded = pd.read_parquet(output_path)
            assert len(df_loaded) == len(df)
            assert list(df_loaded.columns) == list(df.columns)