import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add code root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.align import calculate_block_accuracy, run_behavioral_binning_pipeline
from src.utils.config import get_accuracy_block_size

class TestT021BehavioralBinning:
    @pytest.fixture
    def mock_trials(self):
        """Create mock trial data for testing."""
        data = {
            'trial_id': list(range(100)),
            'accuracy': [1] * 50 + [0] * 50, # First 50 correct, next 50 incorrect
            'subject_id': ['S001'] * 100
        }
        return pd.DataFrame(data)

    def test_calculate_block_accuracy_full_blocks(self, mock_trials):
        """Test accuracy calculation with exact block size fit."""
        block_size = 50
        result = calculate_block_accuracy(mock_trials, block_size)
        
        assert len(result) == 2
        assert result.iloc[0]['accuracy'] == 1.0
        assert result.iloc[0]['trial_start'] == 0
        assert result.iloc[0]['trial_end'] == 49
        assert result.iloc[1]['accuracy'] == 0.0
        assert result.iloc[1]['trial_start'] == 50
        assert result.iloc[1]['trial_end'] == 99

    def test_calculate_block_accuracy_partial_block(self):
        """Test accuracy calculation with remainder trials."""
        data = {
            'trial_id': list(range(60)),
            'accuracy': [1] * 60,
            'subject_id': ['S001'] * 60
        }
        df = pd.DataFrame(data)
        block_size = 50
        result = calculate_block_accuracy(df, block_size)
        
        assert len(result) == 2
        assert result.iloc[0]['accuracy'] == 1.0
        assert result.iloc[1]['accuracy'] == 1.0
        assert result.iloc[1]['trial_start'] == 50
        assert result.iloc[1]['trial_end'] == 59

    def test_run_behavioral_binning_pipeline_creates_file(self, tmp_path):
        """Test that the pipeline creates the expected CSV file."""
        # Setup mock data directory structure
        preprocessed_dir = tmp_path / "preprocessed"
        preprocessed_dir.mkdir()
        
        # Create mock epochs file
        epochs_data = {
            'trial_id': list(range(100)),
            'condition': ['standard'] * 50 + ['deviant'] * 50,
            'accuracy': [1] * 50 + [0] * 50,
            'signal_CP3': [0.0] * 100,
            'signal_CP4': [0.0] * 100,
            'signal_C3': [0.0] * 100,
            'signal_C4': [0.0] * 100,
            'subject_id': ['S001'] * 100
        }
        epochs_df = pd.DataFrame(epochs_data)
        epochs_df.to_csv(preprocessed_dir / "S001_epochs.csv", index=False)
        
        # Run pipeline
        output_path = run_behavioral_binning_pipeline(data_dir=tmp_path)
        
        assert output_path.exists()
        assert output_path.name == "accuracy_blocks.csv"
        
        # Verify content
        result_df = pd.read_csv(output_path)
        assert 'subject_id' in result_df.columns
        assert 'block_id' in result_df.columns
        assert 'accuracy' in result_df.columns
        assert 'trial_start' in result_df.columns
        assert 'trial_end' in result_df.columns
        assert len(result_df) == 2 # 100 trials / 50 block size