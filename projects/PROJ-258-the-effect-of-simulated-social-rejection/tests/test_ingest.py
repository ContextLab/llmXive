import os
import sys
import pytest
import pandas as pd
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest import validate_composite_datasets, log_design_switch
from data_model import DesignType

class TestValidateCompositeDatasets:
    """Tests for T017: validate_composite_datasets function."""

    def test_matching_ids_returns_between_subjects(self):
        """Test that matching participant IDs result in Between-Subjects design."""
        # Create mock dataframes with matching IDs
        df_rejection = pd.DataFrame({
            'Participant_ID': ['P01', 'P02', 'P03'],
            'Condition': ['Cyberball', 'Cyberball', 'Cyberball'],
            'Reaction_Time': [200, 210, 190],
            'Mood': [2, 3, 1]
        })
        
        df_reward = pd.DataFrame({
            'Participant_ID': ['P01', 'P02', 'P04'],
            'Condition': ['Reward', 'Reward', 'Reward'],
            'Reaction_Time': [300, 310, 320],
            'Mood': [4, 5, 4]
        })
        
        is_valid, design_type = validate_composite_datasets(df_rejection, df_reward)
        
        assert is_valid is True
        assert design_type == DesignType.BETWEEN_SUBJECTS.value

    def test_no_matching_ids_fails(self):
        """Test that non-matching participant IDs result in failure."""
        df_rejection = pd.DataFrame({
            'Participant_ID': ['P01', 'P02'],
            'Condition': ['Cyberball', 'Cyberball'],
            'Reaction_Time': [200, 210],
            'Mood': [2, 3]
        })
        
        df_reward = pd.DataFrame({
            'Participant_ID': ['P03', 'P04'],
            'Condition': ['Reward', 'Reward'],
            'Reaction_Time': [300, 310],
            'Mood': [4, 5]
        })
        
        is_valid, design_type = validate_composite_datasets(df_rejection, df_reward)
        
        assert is_valid is False
        assert design_type is None

    def test_missing_participant_id_column_fails(self):
        """Test that missing Participant_ID column results in failure."""
        df_rejection = pd.DataFrame({
            'Subject': ['P01', 'P02'],
            'Condition': ['Cyberball', 'Cyberball'],
            'Reaction_Time': [200, 210],
            'Mood': [2, 3]
        })
        
        df_reward = pd.DataFrame({
            'Subject': ['P01', 'P02'],
            'Condition': ['Reward', 'Reward'],
            'Reaction_Time': [300, 310],
            'Mood': [4, 5]
        })
        
        is_valid, design_type = validate_composite_datasets(df_rejection, df_reward)
        
        assert is_valid is False
        assert design_type is None

    def test_partial_overlap_works(self):
        """Test that partial overlap of IDs is sufficient."""
        df_rejection = pd.DataFrame({
            'Participant_ID': ['P01', 'P02', 'P03', 'P04'],
            'Condition': ['Cyberball'] * 4,
            'Reaction_Time': [200, 210, 190, 220],
            'Mood': [2, 3, 1, 4]
        })
        
        df_reward = pd.DataFrame({
            'Participant_ID': ['P02', 'P04', 'P05'],
            'Condition': ['Reward'] * 3,
            'Reaction_Time': [300, 310, 320],
            'Mood': [4, 5, 4]
        })
        
        is_valid, design_type = validate_composite_datasets(df_rejection, df_reward)
        
        assert is_valid is True
        assert design_type == DesignType.BETWEEN_SUBJECTS.value

class TestLogDesignSwitch:
    """Tests for log_design_switch function."""

    def test_log_design_switch_executes(self, caplog):
        """Test that log_design_switch runs without error."""
        # This should not raise any exceptions
        log_design_switch("Single-Cohort", "Between-Subjects")
        # Verify it logs (caplog would capture this in a real test suite)
        assert True  # If we get here, no exception was raised

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
