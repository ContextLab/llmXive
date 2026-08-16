"""
Unit tests for T018: save_descriptors.py

Tests:
1. verify_schema: Checks for forbidden columns (TPSA, SMARTS, 3D).
2. verify_schema: Checks column count mismatch (filtering detection).
3. verify_schema: Checks required columns ('smiles', 'target').
4. save_descriptors: Validates file creation and schema.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.save_descriptors import verify_schema, save_descriptors, FORBIDDEN_COLUMNS

class TestVerifySchema:
    def test_missing_smiles_column(self):
        df = pd.DataFrame({'target': [1.0, 2.0], 'desc1': [0.1, 0.2]})
        with pytest.raises(AssertionError, match="Missing required column: 'smiles'"):
            verify_schema(df, ['target', 'desc1'])
    
    def test_missing_target_column(self):
        df = pd.DataFrame({'smiles': ['C', 'CC'], 'desc1': [0.1, 0.2]})
        with pytest.raises(AssertionError, match="Missing required column: 'target'"):
            verify_schema(df, ['smiles', 'desc1'])
    
    def test_forbidden_tpsa_column(self):
        df = pd.DataFrame({
            'smiles': ['C', 'CC'], 
            'target': [1.0, 2.0], 
            'TPSA': [50.0, 60.0],
            'desc1': [0.1, 0.2]
        })
        with pytest.raises(AssertionError, match="Forbidden columns found"):
            verify_schema(df, ['smiles', 'target', 'TPSA', 'desc1'])
    
    def test_forbidden_3d_prefix(self):
        df = pd.DataFrame({
            'smiles': ['C', 'CC'], 
            'target': [1.0, 2.0], 
            'MolWt_3D': [12.0, 24.0],
            'desc1': [0.1, 0.2]
        })
        with pytest.raises(AssertionError, match="Forbidden 3D prefix columns found"):
            verify_schema(df, ['smiles', 'target', 'MolWt_3D', 'desc1'])
    
    def test_column_count_mismatch(self):
        # Input had 4 columns, output has 3 (one removed -> filtering happened)
        input_cols = ['smiles', 'target', 'desc1', 'desc2']
        df = pd.DataFrame({
            'smiles': ['C', 'CC'], 
            'target': [1.0, 2.0], 
            'desc1': [0.1, 0.2]
            # desc2 is missing
        })
        with pytest.raises(AssertionError, match="Column count mismatch"):
            verify_schema(df, input_cols)
    
    def test_valid_schema(self):
        df = pd.DataFrame({
            'smiles': ['C', 'CC'], 
            'target': [1.0, 2.0], 
            'desc1': [0.1, 0.2],
            'desc2': [0.3, 0.4]
        })
        input_cols = ['smiles', 'target', 'desc1', 'desc2']
        result = verify_schema(df, input_cols)
        assert result is True

class TestSaveDescriptors:
    def test_save_and_verify(self):
        df = pd.DataFrame({
            'smiles': ['C', 'CC', 'CCC'], 
            'target': [1.0, 2.0, 3.0], 
            'desc1': [0.1, 0.2, 0.3],
            'desc2': [0.4, 0.5, 0.6]
        })
        input_cols = ['smiles', 'target', 'desc1', 'desc2']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_descriptors.parquet"
            save_descriptors(df, output_path, input_cols)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            # Reload and verify
            loaded_df = pd.read_parquet(output_path)
            assert list(loaded_df.columns) == input_cols
            assert 'TPSA' not in loaded_df.columns
            assert 'MolWt_3D' not in loaded_df.columns