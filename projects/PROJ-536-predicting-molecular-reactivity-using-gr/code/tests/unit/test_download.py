import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch, mock_open

# Add code directory to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.download import validate_schema, download_uspto_subset

class TestSchemaValidation:
    """Tests for the schema validation logic in download.py"""

    def test_missing_required_columns(self):
        """Test that validation fails if required columns are missing."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CC=O']
            # Missing 'yield' and 'reaction_class'
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(df)

    def test_yield_column_missing(self):
        """Test that validation fails specifically if 'yield' is missing."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO'],
            'product_smiles': ['CC=O'],
            'reaction_class': ['Oxidation']
        })
        
        with pytest.raises(ValueError, match="Missing required 'yield' column"):
            validate_schema(df)

    def test_yield_categorical_string(self):
        """Test that validation fails if 'yield' is categorical (e.g., 'High', 'Low')."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO', 'CCO'],
            'product_smiles': ['CC=O', 'CC=O'],
            'yield': ['High', 'Low'],  # Categorical
            'reaction_class': ['Oxidation', 'Oxidation']
        })
        
        with pytest.raises(ValueError, match="appears to be categorical"):
            validate_schema(df)

    def test_yield_numeric_string(self):
        """Test that validation passes if 'yield' is numeric strings (e.g., '85', '90')."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO', 'CCO'],
            'product_smiles': ['CC=O', 'CC=O'],
            'yield': ['85', '90'],  # Numeric strings
            'reaction_class': ['Oxidation', 'Oxidation']
        })
        
        # This should pass (or at least not raise the categorical error)
        # The function should handle numeric strings
        result = validate_schema(df)
        assert result is True

    def test_yield_mixed_numeric(self):
        """Test that validation passes if 'yield' is mostly numeric with some NaN."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO', 'CCO', 'CCO'],
            'product_smiles': ['CC=O', 'CC=O', 'CC=O'],
            'yield': [85.0, 90.0, np.nan],
            'reaction_class': ['Oxidation', 'Oxidation', 'Oxidation']
        })
        
        result = validate_schema(df)
        assert result is True

    def test_empty_dataframe(self):
        """Test that validation fails on an empty dataframe."""
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        with pytest.raises(ValueError, match="Dataset is empty"):
            validate_schema(df)

    def test_valid_schema(self):
        """Test that a valid schema passes."""
        df = pd.DataFrame({
            'reactants_smiles': ['CCO', 'CCO'],
            'product_smiles': ['CC=O', 'CC=O'],
            'yield': [85.0, 90.0],
            'reaction_class': ['Oxidation', 'Oxidation']
        })
        
        result = validate_schema(df)
        assert result is True

    def test_download_uspto_subset_file_not_found(self):
        """Test that download_uspto_subset raises FileNotFoundError if file missing."""
        with pytest.raises(FileNotFoundError):
            download_uspto_subset("/nonexistent/path.csv")

    def test_download_uspto_subset_success(self, tmp_path):
        """Test that download_uspto_subset works with a valid file."""
        # Create a temporary valid CSV
        csv_path = tmp_path / "valid_data.csv"
        df = pd.DataFrame({
            'reactants_smiles': ['CCO', 'CCO'],
            'product_smiles': ['CC=O', 'CC=O'],
            'yield': [85.0, 90.0],
            'reaction_class': ['Oxidation', 'Oxidation']
        })
        df.to_csv(csv_path, index=False)
        
        loaded_df = download_uspto_subset(str(csv_path))
        assert len(loaded_df) == 2
        assert 'yield' in loaded_df.columns
        assert loaded_df['yield'].dtype in [np.float64, np.float32]