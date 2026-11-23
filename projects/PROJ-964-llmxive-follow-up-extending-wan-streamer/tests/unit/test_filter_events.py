import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.preprocess import filter_events

class TestFilterEvents:
    def setup_method(self):
        # Create a test dataframe with various conditions
        self.df = pd.DataFrame({
            'timestamp': [1, 2, 3, 4, 5, 6],
            'semantic_feature': [
                "valid text",       # Valid
                None,               # Null
                "",                 # Empty string
                "   ",              # Whitespace only (should be treated as empty)
                "another valid",    # Valid
                " "                  # Single space
            ],
            'prosodic_feature': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'turn_label': ['A', 'B', 'A', 'B', 'A', 'B']
        })

    def test_filters_null_and_empty(self):
        """Test that null and empty string semantic_features are removed."""
        result = filter_events(self.df)
        
        # Expected rows: 0 ("valid text"), 4 ("another valid")
        # Row 2 is empty string, Row 3 is whitespace (stripped to empty), Row 5 is space.
        # Note: "   " stripped is "", so it should be removed.
        # " " stripped is "", so it should be removed.
        
        assert len(result) == 2
        assert list(result['semantic_feature']) == ["valid text", "another valid"]

    def test_adds_audio_energy_if_missing(self):
        """Test that audio_energy column is added if missing."""
        result = filter_events(self.df)
        assert 'audio_energy' in result.columns

    def test_audio_energy_is_nan_when_missing(self):
        """Test that audio_energy is NaN when source data lacks it."""
        result = filter_events(self.df)
        assert result['audio_energy'].isna().all()

    def test_preserves_audio_energy_if_present(self):
        """Test that existing audio_energy is preserved."""
        df_with_energy = self.df.copy()
        df_with_energy['audio_energy'] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        
        result = filter_events(df_with_energy)
        
        # Should have 2 rows
        assert len(result) == 2
        # Values should be preserved for the valid rows (indices 0 and 4)
        assert result['audio_energy'].tolist() == [0.1, 0.5]

    def test_output_path_creation(self):
        """Test that the function can be called and returns a valid dataframe."""
        result = filter_events(self.df)
        assert isinstance(result, pd.DataFrame)
        assert 'semantic_feature' in result.columns
        assert 'audio_energy' in result.columns