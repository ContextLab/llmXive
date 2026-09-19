"""
Unit tests for T021: Behavioral Binning Logic.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.align import calculate_block_accuracy, run_behavioral_binning_pipeline
from src.utils.config import config

class TestT021BehavioralBinning:
    
    @pytest.fixture
    def sample_trials(self):
        """Create a sample DataFrame with trial data."""
        data = []
        # Subject 001: 50 trials
        for i in range(1, 51):
            # 80% accuracy
            correct = 1 if i % 5 != 0 else 0
            data.append({'subject_id': '001', 'trial_id': i, 'correct': correct})
        
        # Subject 002: 30 trials
        for i in range(1, 31):
            correct = 1 if i % 3 != 0 else 0
            data.append({'subject_id': '002', 'trial_id': i, 'correct': correct})
            
        return pd.DataFrame(data)

    def test_calculate_block_accuracy_basic(self, sample_trials):
        """Test basic block accuracy calculation."""
        block_size = 10
        result = calculate_block_accuracy(sample_trials, block_size)
        
        assert not result.empty
        assert 'subject_id' in result.columns
        assert 'block_id' in result.columns
        assert 'accuracy' in result.columns
        assert 'trial_start' in result.columns
        assert 'trial_end' in result.columns
        
        # Check subject 001: 50 trials / 10 = 5 blocks
        s1_blocks = result[result['subject_id'] == '001']
        assert len(s1_blocks) == 5
        
        # Check subject 002: 30 trials / 10 = 3 blocks
        s2_blocks = result[result['subject_id'] == '002']
        assert len(s2_blocks) == 3

    def test_calculate_block_accuracy_accuracy_values(self, sample_trials):
        """Verify accuracy values are correct."""
        block_size = 10
        result = calculate_block_accuracy(sample_trials, block_size)
        
        # Subject 001, Block 1 (Trials 1-10): 8 correct (1,2,3,4, 6,7,8,9) -> 0.8
        # Logic: i % 5 == 0 is 0 (incorrect). So 5, 10 are wrong. 1,2,3,4,6,7,8,9 are correct.
        # 8 correct out of 10 -> 0.8
        s1_b1 = result[(result['subject_id'] == '001') & (result['block_id'] == 1)]
        assert len(s1_b1) == 1
        assert np.isclose(s1_b1.iloc[0]['accuracy'], 0.8)

    def test_run_behavioral_binning_pipeline_writes_file(self, sample_trials, tmp_path):
        """Test that the pipeline writes the correct CSV file."""
        # Mock the config data dir
        original_data_dir = config.get_data_dir()
        config.set("data_dir", str(tmp_path))
        
        try:
            output_df = run_behavioral_binning_pipeline(sample_trials)
            
            expected_path = tmp_path / "accuracy_blocks.csv"
            assert expected_path.exists()
            
            # Verify content
            loaded_df = pd.read_csv(expected_path)
            assert len(loaded_df) == len(output_df)
            assert 'accuracy' in loaded_df.columns
        finally:
            # Restore config
            config.set("data_dir", str(original_data_dir))

    def test_empty_dataframe(self):
        """Test handling of empty input."""
        empty_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'correct'])
        result = calculate_block_accuracy(empty_df, 10)
        assert result.empty
        assert list(result.columns) == ['subject_id', 'block_id', 'accuracy', 'trial_start', 'trial_end']

    def test_partial_block(self, sample_trials):
        """Test handling of trials that don't fill a complete block."""
        # Create data with 25 trials (2 full blocks of 10, 1 partial of 5)
        data = []
        for i in range(1, 26):
            data.append({'subject_id': '003', 'trial_id': i, 'correct': 1})
        df = pd.DataFrame(data)
        
        result = calculate_block_accuracy(df, 10)
        assert len(result) == 3
        
        # Check partial block (block 3)
        b3 = result[result['block_id'] == 3]
        assert b3.iloc[0]['trial_start'] == 21
        assert b3.iloc[0]['trial_end'] == 25
        assert b3.iloc[0]['accuracy'] == 1.0