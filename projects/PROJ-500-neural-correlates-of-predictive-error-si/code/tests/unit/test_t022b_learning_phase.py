import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.align import add_learning_phase

class TestT022bLearningPhase:
    @pytest.fixture
    def sample_lagged_data(self):
        """Create sample lagged data for testing."""
        data = {
            'subject_id': ['S1', 'S1', 'S1', 'S1', 'S2', 'S2', 'S2'],
            'block_id': [0, 1, 2, 3, 0, 1, 2],
            'mmn_amplitude': [0.1, 0.2, 0.3, 0.4, 0.15, 0.25, 0.35],
            'source_window_start_trial': [0, 10, 20, 30, 0, 10, 20]
        }
        return pd.DataFrame(data)

    def test_learning_phase_assignment(self, sample_lagged_data):
        """Test that learning_phase column is correctly added."""
        result = add_learning_phase(sample_lagged_data)
        
        assert 'learning_phase' in result.columns
        assert result['learning_phase'].notna().all()
        
        # Check specific assignments
        # S1 has 4 blocks (0,1,2,3). Threshold = 2. Blocks 0,1 -> Early; 2,3 -> Late
        s1_data = result[result['subject_id'] == 'S1']
        assert s1_data[s1_data['block_id'] == 0]['learning_phase'].values[0] == 'Early'
        assert s1_data[s1_data['block_id'] == 1]['learning_phase'].values[0] == 'Early'
        assert s1_data[s1_data['block_id'] == 2]['learning_phase'].values[0] == 'Late'
        assert s1_data[s1_data['block_id'] == 3]['learning_phase'].values[0] == 'Late'
        
        # S2 has 3 blocks (0,1,2). Threshold = 1. Block 0 -> Early; 1,2 -> Late
        s2_data = result[result['subject_id'] == 'S2']
        assert s2_data[s2_data['block_id'] == 0]['learning_phase'].values[0] == 'Early'
        assert s2_data[s2_data['block_id'] == 1]['learning_phase'].values[0] == 'Late'
        assert s2_data[s2_data['block_id'] == 2]['learning_phase'].values[0] == 'Late'

    def test_output_file_creation(self, sample_lagged_data):
        """Test that output files are created."""
        # Temporarily override get_data_dir to use a temp directory
        import src.data.align as align_module
        original_get_data_dir = align_module.get_data_dir
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            align_module.get_data_dir = lambda: temp_path
            
            try:
                result = add_learning_phase(sample_lagged_data)
                
                assert (temp_path / "interim_lagged_mmns.csv").exists()
                assert (temp_path / "learning_phases.csv").exists()
                
                # Verify content of learning_phases.csv
                phases_df = pd.read_csv(temp_path / "learning_phases.csv")
                assert 'learning_phase' in phases_df.columns
            finally:
                align_module.get_data_dir = original_get_data_dir

    def test_empty_input(self):
        """Test behavior with empty input."""
        empty_df = pd.DataFrame(columns=['subject_id', 'block_id', 'mmn_amplitude'])
        result = add_learning_phase(empty_df)
        assert result.empty
        
        none_result = add_learning_phase(None)
        assert none_result.empty