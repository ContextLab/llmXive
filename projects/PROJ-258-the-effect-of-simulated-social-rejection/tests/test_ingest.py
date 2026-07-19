import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import validate_separate_datasets, setup_paths

class TestValidateSeparateDatasets:
    """Tests for validate_separate_datasets function."""
    
    def test_both_datasets_valid(self):
        """Test when both datasets are valid."""
        # Create valid DataFrames
        df_rejection = pd.DataFrame({
            'participant_id': ['sub-01', 'sub-02', 'sub-03'],
            'condition': ['rejection', 'rejection', 'rejection'],
            'mood': [3, 2, 4]
        })
        
        df_reward = pd.DataFrame({
            'participant_id': ['sub-04', 'sub-05', 'sub-06'],
            'condition': ['reward', 'reward', 'reward'],
            'reaction_time': [250, 300, 280]
        })
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        assert result['status'] == 'valid'
        assert result['rejection_valid'] == True
        assert result['reward_valid'] == True
        assert 'Both datasets are valid' in result['reason']
        
        # Verify report file was created
        paths = setup_paths()
        report_path = paths['interim'] / 'separate_validation_report.json'
        assert report_path.exists()
        
        # Verify report content
        with open(report_path, 'r') as f:
            report = json.load(f)
        assert report['status'] == 'valid'
    
    def test_rejection_dataset_invalid(self):
        """Test when rejection dataset is invalid."""
        # Create invalid rejection DataFrame (missing columns)
        df_rejection = pd.DataFrame({
            'participant_id': ['sub-01', 'sub-02'],
            'condition': ['rejection', 'rejection']
            # Missing 'mood' column
        })
        
        df_reward = pd.DataFrame({
            'participant_id': ['sub-03', 'sub-04'],
            'condition': ['reward', 'reward'],
            'reaction_time': [250, 300]
        })
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        assert result['status'] == 'invalid'
        assert result['rejection_valid'] == False
        assert result['reward_valid'] == True
        assert 'Missing columns' in result['reason']
    
    def test_reward_dataset_invalid(self):
        """Test when reward dataset is invalid."""
        df_rejection = pd.DataFrame({
            'participant_id': ['sub-01', 'sub-02'],
            'condition': ['rejection', 'rejection'],
            'mood': [3, 4]
        })
        
        # Create invalid reward DataFrame (missing columns)
        df_reward = pd.DataFrame({
            'participant_id': ['sub-03', 'sub-04'],
            'condition': ['reward', 'reward']
            # Missing 'reaction_time' column
        })
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        assert result['status'] == 'invalid'
        assert result['rejection_valid'] == True
        assert result['reward_valid'] == False
        assert 'Missing columns' in result['reason']
    
    def test_both_datasets_invalid(self):
        """Test when both datasets are invalid."""
        df_rejection = pd.DataFrame({
            'participant_id': ['sub-01'],
            # Missing required columns
        })
        
        df_reward = pd.DataFrame({
            'participant_id': ['sub-02'],
            # Missing required columns
        })
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        assert result['status'] == 'invalid'
        assert result['rejection_valid'] == False
        assert result['reward_valid'] == False
    
    def test_empty_datasets(self):
        """Test with empty DataFrames."""
        df_rejection = pd.DataFrame()
        df_reward = pd.DataFrame()
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        assert result['status'] == 'invalid'
        assert result['rejection_valid'] == False
        assert result['reward_valid'] == False
    
    def test_none_datasets(self):
        """Test with None values."""
        result = validate_separate_datasets(None, None)
        
        assert result['status'] == 'invalid'
        assert result['rejection_valid'] == False
        assert result['reward_valid'] == False
    
    def test_report_schema(self):
        """Test that the report follows the required schema."""
        df_rejection = pd.DataFrame({
            'participant_id': ['sub-01'],
            'condition': ['rejection'],
            'mood': [3]
        })
        
        df_reward = pd.DataFrame({
            'participant_id': ['sub-02'],
            'condition': ['reward'],
            'reaction_time': [250]
        })
        
        result = validate_separate_datasets(df_rejection, df_reward)
        
        # Check required keys
        assert 'status' in result
        assert 'reason' in result
        assert result['status'] in ['valid', 'invalid']
        assert isinstance(result['reason'], str)
        assert len(result['reason']) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
