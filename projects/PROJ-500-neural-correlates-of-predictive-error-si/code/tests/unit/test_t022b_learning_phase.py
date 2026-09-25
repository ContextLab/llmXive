"""
Unit tests for T022b: Learning Phase feature generation.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.align import add_learning_phase, run_learning_phase_pipeline
from src.utils.config import get_data_dir

class TestT022bLearningPhase:
    """Tests for learning phase generation logic"""

    def test_learning_phase_assignment_basic(self):
        """Test basic early/late phase assignment"""
        # Create mock data with 4 blocks per subject
        data = {
            'subject_id': ['S1', 'S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S2'],
            'block_id': [0, 1, 2, 3, 0, 1, 2, 3],
            'mmn_amplitude': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            'source_window_start_trial': [0, 10, 20, 30, 0, 10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        result = add_learning_phase(df)
        
        # Check that learning_phase column exists
        assert 'learning_phase' in result.columns
        
        # Check phase assignments (first 2 blocks = Early, last 2 = Late)
        assert result.loc[result['block_id'] == 0, 'learning_phase'].iloc[0] == 'Early'
        assert result.loc[result['block_id'] == 1, 'learning_phase'].iloc[1] == 'Early'
        assert result.loc[result['block_id'] == 2, 'learning_phase'].iloc[2] == 'Late'
        assert result.loc[result['block_id'] == 3, 'learning_phase'].iloc[3] == 'Late'

    def test_learning_phase_assignment_odd_blocks(self):
        """Test phase assignment with odd number of blocks"""
        # Create mock data with 5 blocks per subject
        data = {
            'subject_id': ['S1'] * 5,
            'block_id': [0, 1, 2, 3, 4],
            'mmn_amplitude': [0.1, 0.2, 0.3, 0.4, 0.5],
            'source_window_start_trial': [0, 10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        
        result = add_learning_phase(df)
        
        # With 5 blocks, split at 5//2 = 2, so blocks 0,1 = Early, 2,3,4 = Late
        assert result.loc[result['block_id'] == 0, 'learning_phase'].iloc[0] == 'Early'
        assert result.loc[result['block_id'] == 1, 'learning_phase'].iloc[1] == 'Early'
        assert result.loc[result['block_id'] == 2, 'learning_phase'].iloc[2] == 'Late'
        assert result.loc[result['block_id'] == 3, 'learning_phase'].iloc[3] == 'Late'
        assert result.loc[result['block_id'] == 4, 'learning_phase'].iloc[4] == 'Late'

    def test_learning_phase_per_subject(self):
        """Test that phase assignment is done per subject independently"""
        # Create mock data with different block counts per subject
        data = {
            'subject_id': ['S1', 'S1', 'S1', 'S2', 'S2'],
            'block_id': [0, 1, 2, 0, 1],
            'mmn_amplitude': [0.1, 0.2, 0.3, 0.4, 0.5],
            'source_window_start_trial': [0, 10, 20, 0, 10]
        }
        df = pd.DataFrame(data)
        
        result = add_learning_phase(df)
        
        # S1 has 3 blocks: 0,1 = Early, 2 = Late
        assert result.loc[(result['subject_id'] == 'S1') & (result['block_id'] == 0), 'learning_phase'].iloc[0] == 'Early'
        assert result.loc[(result['subject_id'] == 'S1') & (result['block_id'] == 1), 'learning_phase'].iloc[1] == 'Early'
        assert result.loc[(result['subject_id'] == 'S1') & (result['block_id'] == 2), 'learning_phase'].iloc[2] == 'Late'
        
        # S2 has 2 blocks: 0 = Early, 1 = Late
        assert result.loc[(result['subject_id'] == 'S2') & (result['block_id'] == 0), 'learning_phase'].iloc[3] == 'Early'
        assert result.loc[(result['subject_id'] == 'S2') & (result['block_id'] == 1), 'learning_phase'].iloc[4] == 'Late'

    def test_learning_phase_output_format(self):
        """Test that output contains required columns"""
        data = {
            'subject_id': ['S1', 'S1'],
            'block_id': [0, 1],
            'mmn_amplitude': [0.1, 0.2],
            'source_window_start_trial': [0, 10]
        }
        df = pd.DataFrame(data)
        
        result = add_learning_phase(df)
        
        # Check required columns
        required_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial', 'learning_phase']
        for col in required_cols:
            assert col in result.columns, f"Missing required column: {col}"
        
        # Check that learning_phase is categorical
        assert result['learning_phase'].dtype == 'object'
        assert set(result['learning_phase'].unique()).issubset({'Early', 'Late', 'Unknown'})

    def test_learning_phase_with_single_block(self):
        """Test phase assignment with only one block per subject"""
        data = {
            'subject_id': ['S1', 'S2'],
            'block_id': [0, 0],
            'mmn_amplitude': [0.1, 0.2],
            'source_window_start_trial': [0, 0]
        }
        df = pd.DataFrame(data)
        
        result = add_learning_phase(df)
        
        # With 1 block, split at 1//2 = 0, so block 0 = Late (since 0 >= 0)
        # Actually, our logic: if block_id < split_point (0), then Early, else Late
        # So block 0 >= 0 -> Late
        assert result.loc[result['block_id'] == 0, 'learning_phase'].iloc[0] == 'Late'
        assert result.loc[result['block_id'] == 0, 'learning_phase'].iloc[1] == 'Late'

    def test_learning_phase_file_generation(self, tmp_path):
        """Test that learning phase generation creates the required files"""
        # Setup temporary directory
        original_data_dir = get_data_dir()
        
        # Mock the data directory
        import src.utils.config as config_module
        original_get_data_dir = config_module.get_data_dir
        config_module.get_data_dir = lambda: tmp_path
        
        try:
            # Create mock interim_lagged_mmns.csv
            data = {
                'subject_id': ['S1', 'S1', 'S1', 'S1'],
                'block_id': [0, 1, 2, 3],
                'mmn_amplitude': [0.1, 0.2, 0.3, 0.4],
                'source_window_start_trial': [0, 10, 20, 30]
            }
            mock_df = pd.DataFrame(data)
            mock_df.to_csv(tmp_path / "interim_lagged_mmns.csv", index=False)
            
            # Run pipeline
            result = run_learning_phase_pipeline()
            
            # Check that files were created
            assert (tmp_path / "interim_lagged_mmns.csv").exists()
            assert (tmp_path / "learning_phases.csv").exists()
            
            # Check content of learning_phases.csv
            phases_df = pd.read_csv(tmp_path / "learning_phases.csv")
            assert 'learning_phase' in phases_df.columns
            assert len(phases_df) == 4
            assert set(phases_df['learning_phase'].unique()) == {'Early', 'Late'}
            
        finally:
            # Restore original function
            config_module.get_data_dir = original_get_data_dir

    def test_learning_phase_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame(columns=['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial'])
        
        result = add_learning_phase(df)
        
        # Should return empty dataframe with learning_phase column
        assert 'learning_phase' in result.columns
        assert len(result) == 0
