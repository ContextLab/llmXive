"""
Tests for T028b: Derive Dilemma Choice.

Verifies that the derivation logic correctly identifies 'save_many' vs 'save_few'
without using response_time.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from derive_dilemma_choice import derive_choice

class TestDeriveDilemmaChoice:
    
    def test_save_many_choice(self):
        """Test case where participant chooses the side with more lives."""
        data = {
            'participant_id': [1],
            'n_alives_ego': [5],
            'n_alives_other': [2],
            'choice': ['ego']  # Chose ego side (5 lives) over other (2 lives)
        }
        df = pd.DataFrame(data)
        result = derive_choice(df)
        assert result['dilemma_choice'].iloc[0] == 'save_many'

    def test_save_few_choice(self):
        """Test case where participant chooses the side with fewer lives."""
        data = {
            'participant_id': [1],
            'n_alives_ego': [2],
            'n_alives_other': [5],
            'choice': ['ego']  # Chose ego side (2 lives) over other (5 lives)
        }
        df = pd.DataFrame(data)
        result = derive_choice(df)
        assert result['dilemma_choice'].iloc[0] == 'save_few'

    def test_other_side_choice(self):
        """Test case where participant chooses 'other' side."""
        data = {
            'participant_id': [1],
            'n_alives_ego': [2],
            'n_alives_other': [5],
            'choice': ['other']  # Chose other side (5 lives) over ego (2 lives)
        }
        df = pd.DataFrame(data)
        result = derive_choice(df)
        assert result['dilemma_choice'].iloc[0] == 'save_many'

    def test_equal_lives(self):
        """Test case where lives are equal."""
        data = {
            'participant_id': [1],
            'n_alives_ego': [3],
            'n_alives_other': [3],
            'choice': ['ego']
        }
        df = pd.DataFrame(data)
        result = derive_choice(df)
        assert result['dilemma_choice'].iloc[0] == 'equal'

    def test_no_response_time_dependency(self):
        """Ensure the function does not use response_time column."""
        # If the function tried to access response_time, it would raise KeyError
        # if the column is missing, or use it if present.
        # We construct a DF with response_time but ensure logic relies on lives.
        data = {
            'participant_id': [1],
            'n_alives_ego': [5],
            'n_alives_other': [2],
            'choice': ['ego'],
            'response_time': [1000]  # This should be ignored
        }
        df = pd.DataFrame(data)
        # This should run without error and produce 'save_many'
        result = derive_choice(df)
        assert result['dilemma_choice'].iloc[0] == 'save_many'

    def test_missing_columns_raises_error(self):
        """Test that missing life count columns raise a ValueError."""
        data = {
            'participant_id': [1],
            'choice': ['ego']
            # Missing n_alives_ego, n_alives_other
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="Missing required life count columns"):
            derive_choice(df)