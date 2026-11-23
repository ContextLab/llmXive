import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.utils.deduplicator import handle_duplicates

class TestHandleDuplicates:
    def test_basic_deduplication(self):
        """Test basic duplicate handling with mean aggregation."""
        data = {
            'smiles': ['CCO', 'CCO', 'CCO', 'CCO', 'CCO'],
            'target': [1.0, 2.0, 3.0, 4.0, 5.0],
            'source_id': ['A', 'B', 'A', 'C', 'B']
        }
        df = pd.DataFrame(data)
        
        result = handle_duplicates(df)
        
        assert len(result) == 1
        assert result['smiles'].iloc[0] == 'CCO'
        assert result['target_mean'].iloc[0] == 3.0  # Mean of 1,2,3,4,5
        assert result['count'].iloc[0] == 5
        assert 'A' in result['source_id'].iloc[0]
        assert 'B' in result['source_id'].iloc[0]
        assert 'C' in result['source_id'].iloc[0]

    def test_no_duplicates(self):
        """Test that unique SMILES remain unchanged."""
        data = {
            'smiles': ['CCO', 'CCCO', 'CCCCO'],
            'target': [1.0, 2.0, 3.0],
            'source_id': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        
        result = handle_duplicates(df)
        
        assert len(result) == 3
        assert list(result['smiles']) == ['CCO', 'CCCO', 'CCCCO']
        assert list(result['target_mean']) == [1.0, 2.0, 3.0]
        assert list(result['count']) == [1, 1, 1]

    def test_empty_dataframe(self):
        """Test handling of empty input."""
        df = pd.DataFrame(columns=['smiles', 'target', 'source_id'])
        
        result = handle_duplicates(df)
        
        assert len(result) == 0
        assert list(result.columns) == ['smiles', 'target_mean', 'count', 'source_id']

    def test_missing_columns(self):
        """Test that missing columns raise an error."""
        data = {
            'smiles': ['CCO'],
            'wrong_col': [1.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError):
            handle_duplicates(df)

    def test_schema_compliance(self):
        """Test that output schema matches requirements."""
        data = {
            'smiles': ['CCO', 'CCO'],
            'target': [1.0, 2.0],
            'source_id': ['A', 'B']
        }
        df = pd.DataFrame(data)
        
        result = handle_duplicates(df)
        
        expected_cols = ['smiles', 'target_mean', 'count', 'source_id']
        assert list(result.columns) == expected_cols
        assert result['target_mean'].dtype in [np.float64, np.float32]
        assert result['count'].dtype in [np.int64, np.int32]
