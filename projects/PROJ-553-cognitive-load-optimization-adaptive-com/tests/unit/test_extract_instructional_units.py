"""
Unit tests for extract_instructional_units.py
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.extract_instructional_units import fetch_assistments_instructional_units

class TestFetchInstructionalUnits:
    def test_fetch_returns_dataframe(self):
        """Test that the function returns a DataFrame with expected columns."""
        # Mock the load_dataset to avoid network calls in unit test
        mock_item = {
            'skill': 'Algebra: Solve for x',
            'problem_text': None
        }
        
        mock_ds = [mock_item] * 100
        
        with patch('code.extract_instructional_units.load_dataset') as mock_load:
            mock_load.return_value = mock_ds
            
            df = fetch_assistments_instructional_units(max_samples=100)
            
            assert isinstance(df, pd.DataFrame)
            assert 'interaction_id' in df.columns
            assert 'instructional_unit_text' in df.columns
            assert 'source_dataset' in df.columns
            assert len(df) > 0

    def test_fetch_filters_duplicates(self):
        """Test that duplicate skills are not added."""
        mock_item = {'skill': 'Same Skill'}
        mock_ds = [mock_item] * 50
        
        with patch('code.extract_instructional_units.load_dataset') as mock_load:
            mock_load.return_value = mock_ds
            
            df = fetch_assistments_instructional_units(max_samples=50)
            
            # Should only have 1 unique entry
            assert len(df) == 1

    def test_fetch_filters_short_texts(self):
        """Test that very short texts are filtered out."""
        mock_items = [
            {'skill': 'A'}, # Too short
            {'skill': 'Algebra: Solve for x'}, # Valid
            {'skill': ''}, # Empty
        ]
        
        with patch('code.extract_instructional_units.load_dataset') as mock_load:
            mock_load.return_value = mock_items
            
            df = fetch_assistments_instructional_units(max_samples=10)
            
            # Only the valid one should remain
            assert len(df) == 1
            assert df.iloc[0]['instructional_unit_text'] == 'Algebra: Solve for x'

    def test_fetch_raises_on_empty_result(self):
        """Test that ValueError is raised if no valid units are found."""
        mock_items = [{'skill': 'A'}, {'skill': 'B'}] # All too short
        
        with patch('code.extract_instructional_units.load_dataset') as mock_load:
            mock_load.return_value = mock_items
            
            with pytest.raises(ValueError, match="No valid instructional units found"):
                fetch_assistments_instructional_units(max_samples=10)
