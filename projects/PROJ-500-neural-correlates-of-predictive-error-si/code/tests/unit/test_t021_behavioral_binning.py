import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

from src.data.align import calculate_block_accuracy, run_behavioral_binning_pipeline

class TestT021BehavioralBinning:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_epochs_data(self):
        """Create mock epochs data for testing."""
        data = []
        for subject in ['S001', 'S002']:
            for trial in range(20):
                # Alternate correct/incorrect responses
                correctness = 1 if trial % 2 == 0 else 0
                data.append({
                    'subject_id': subject,
                    'trial_id': trial,
                    'stimulus_type': 'deviant' if trial % 3 == 0 else 'standard',
                    'response_correctness': correctness,
                    'amplitude_CP3': 0.5 + trial * 0.01,
                    'amplitude_CP4': 0.6 + trial * 0.01,
                    'amplitude_C3': 0.4 + trial * 0.01,
                    'amplitude_C4': 0.55 + trial * 0.01,
                    'time_window_start_trial': trial
                })
        return pd.DataFrame(data)

    def test_calculate_block_accuracy_basic(self, mock_epochs_data):
        """Test basic block accuracy calculation."""
        block_size = 5
        result = calculate_block_accuracy(mock_epochs_data, block_size)
        
        assert 'subject_id' in result.columns
        assert 'block_id' in result.columns
        assert 'accuracy' in result.columns
        assert 'trial_start' in result.columns
        assert 'trial_end' in result.columns
        
        # Check that we have 4 blocks per subject (20 trials / 5 block_size)
        assert len(result) == 4  # 2 subjects * 2 blocks each (20/5=4 per subject, but we have 20 trials)
        
        # Verify accuracy values are between 0 and 1
        assert (result['accuracy'] >= 0).all()
        assert (result['accuracy'] <= 1).all()

    def test_calculate_block_accuracy_variable_size(self, mock_epochs_data):
        """Test with different block sizes."""
        for block_size in [2, 4, 10]:
            result = calculate_block_accuracy(mock_epochs_data, block_size)
            
            # Verify trial ranges don't overlap within subjects
            for subject in result['subject_id'].unique():
                subject_blocks = result[result['subject_id'] == subject].sort_values('block_id')
                for i in range(len(subject_blocks) - 1):
                    current_end = subject_blocks.iloc[i]['trial_end']
                    next_start = subject_blocks.iloc[i + 1]['trial_start']
                    assert current_end < next_start, f"Overlapping blocks for subject {subject}"

    def test_calculate_block_accuracy_empty_input(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'response_correctness'])
        result = calculate_block_accuracy(empty_df, 5)
        
        assert len(result) == 0
        assert 'subject_id' in result.columns

    def test_calculate_block_accuracy_single_subject(self, mock_epochs_data):
        """Test filtering by single subject."""
        block_size = 5
        result = calculate_block_accuracy(mock_epochs_data, block_size, subject_id='S001')
        
        assert len(result) == 4  # 20 trials / 5 block_size
        assert (result['subject_id'] == 'S001').all()

    def test_run_behavioral_binning_pipeline(self, mock_epochs_data, temp_data_dir):
        """Test full pipeline execution."""
        epochs_path = temp_data_dir / 'preprocessed_epochs.csv'
        output_path = temp_data_dir / 'accuracy_blocks.csv'
        
        # Save mock data
        mock_epochs_data.to_csv(epochs_path, index=False)
        
        # Run pipeline
        result = run_behavioral_binning_pipeline(epochs_path, output_path)
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify output content
        output_df = pd.read_csv(output_path)
        assert len(output_df) == len(result)
        assert 'accuracy' in output_df.columns
        assert (output_df['accuracy'] >= 0).all()
        assert (output_df['accuracy'] <= 1).all()

    def test_block_accuracy_calculation_logic(self):
        """Test that accuracy is calculated correctly."""
        data = pd.DataFrame({
            'subject_id': ['S001'] * 10,
            'trial_id': list(range(10)),
            'response_correctness': [1, 1, 1, 0, 0, 1, 1, 1, 0, 0]
        })
        
        # Block size 5: first block should have 3/5 = 0.6 accuracy
        result = calculate_block_accuracy(data, block_size=5)
        
        assert result.iloc[0]['accuracy'] == 0.6
        assert result.iloc[1]['accuracy'] == 0.4  # Second block: 2/5
