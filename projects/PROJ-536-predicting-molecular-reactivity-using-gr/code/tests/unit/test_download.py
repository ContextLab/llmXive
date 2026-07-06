"""
Unit tests for the data download and validation module.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.data.download import validate_schema, REQUIRED_COLUMNS

class TestSchemaValidation:
    
    def test_missing_required_columns(self):
        """Test that validation fails when required columns are missing."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CCO']
            # 'yield' is missing
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(df)
    
    def test_categorical_yield_fails(self):
        """Test that validation fails when yield is categorical."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CCO'],
            'yield': ['high', 'low', 'medium']
        })
        
        with pytest.raises(ValueError, match="categorical"):
            validate_schema(df)
    
    def test_numeric_yield_passes(self):
        """Test that validation passes with numeric yield."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CCO'],
            'yield': [0.85, 0.92, 0.76]
        })
        
        result = validate_schema(df)
        assert result is True
    
    def test_float_yield_passes(self):
        """Test that validation passes with float yield."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CCO'],
            'yield': [85.5, 92.0, 76.2]
        })
        
        result = validate_schema(df)
        assert result is True
    
    def test_non_numeric_yield_fails(self):
        """Test that validation fails with non-numeric yield that isn't the specific categorical list."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CCO'],
            'yield': ['unknown', 'N/A', 'NaN']
        })
        
        # This should fail because it's not numeric
        with pytest.raises(ValueError):
            validate_schema(df)