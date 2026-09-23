import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

class TestCheckpointIntegration:
    """Integration tests for checkpoint mechanism in fetch_data and preprocess"""
    
    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create a temporary checkpoint directory"""
        temp_dir = tempfile.mkdtemp()
        # Temporarily override checkpoint directory
        original_dir = os.environ.get('CHECKPOINT_DIR')
        os.environ['CHECKPOINT_DIR'] = temp_dir
        yield temp_dir
        # Cleanup
        if original_dir:
            os.environ['CHECKPOINT_DIR'] = original_dir
        else:
            os.environ.pop('CHECKPOINT_DIR', None)
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    def test_checkpoint_save_and_load(self, temp_checkpoint_dir):
        """Test basic checkpoint save and load functionality"""
        checkpoint_path = get_checkpoint_path('test')
        
        test_data = {
            'start_index': 5,
            'processed_games': ['game1', 'game2'],
            'timestamp': 1234567890
        }
        
        save_checkpoint(test_data, checkpoint_path)
        
        assert os.path.exists(checkpoint_path)
        
        loaded_data = load_checkpoint(checkpoint_path)
        
        assert loaded_data['start_index'] == 5
        assert loaded_data['processed_games'] == ['game1', 'game2']
        assert loaded_data['timestamp'] == 1234567890
        
    def test_checkpoint_missing_file(self, temp_checkpoint_dir):
        """Test loading from non-existent checkpoint file"""
        checkpoint_path = get_checkpoint_path('nonexistent')
        
        # Should return None or raise appropriate error
        result = load_checkpoint(checkpoint_path)
        assert result is None
        
    def test_checkpoint_directory_creation(self, temp_checkpoint_dir):
        """Test that checkpoint directory is created if it doesn't exist"""
        new_dir = os.path.join(temp_checkpoint_dir, 'new_subdir')
        os.environ['CHECKPOINT_DIR'] = new_dir
        
        checkpoint_path = get_checkpoint_path('test')
        ensure_checkpoint_dir()
        
        assert os.path.exists(os.path.dirname(checkpoint_path))
        
    def test_checkpoint_update(self, temp_checkpoint_dir):
        """Test updating an existing checkpoint"""
        checkpoint_path = get_checkpoint_path('test')
        
        # Save initial state
        initial_data = {
            'start_index': 0,
            'processed_games': [],
            'timestamp': 1000
        }
        save_checkpoint(initial_data, checkpoint_path)
        
        # Update with new state
        updated_data = {
            'start_index': 3,
            'processed_games': ['game1', 'game2', 'game3'],
            'timestamp': 2000
        }
        save_checkpoint(updated_data, checkpoint_path)
        
        # Verify update
        loaded = load_checkpoint(checkpoint_path)
        assert loaded['start_index'] == 3
        assert len(loaded['processed_games']) == 3
        assert loaded['timestamp'] == 2000
        
    def test_checkpoint_with_fetch_data_simulation(self, temp_checkpoint_dir):
        """Simulate checkpoint usage in fetch_data.py"""
        checkpoint_path = get_checkpoint_path('fetch_data')
        
        # Simulate processing first game
        state = {
            'start_index': 1,
            'completed_games': ['super-mario-64'],
            'timestamp': 1234567890
        }
        save_checkpoint(state, checkpoint_path)
        
        # Simulate processing second game
        state['start_index'] = 2
        state['completed_games'].append('zelda-oot')
        state['timestamp'] = 1234567900
        save_checkpoint(state, checkpoint_path)
        
        # Verify final state
        loaded = load_checkpoint(checkpoint_path)
        assert loaded['start_index'] == 2
        assert len(loaded['completed_games']) == 2
        assert 'super-mario-64' in loaded['completed_games']
        assert 'zelda-oot' in loaded['completed_games']
        
    def test_checkpoint_with_preprocess_simulation(self, temp_checkpoint_dir):
        """Simulate checkpoint usage in preprocess.py"""
        checkpoint_path = get_checkpoint_path('preprocess')
        
        # Simulate processing
        state = {
            'start_index': 0,
            'processed_games': [],
            'total_records': 0,
            'timestamp': 1234567890
        }
        save_checkpoint(state, checkpoint_path)
        
        # After first game
        state['start_index'] = 1
        state['processed_games'] = ['super-mario-64']
        state['total_records'] = 150
        state['timestamp'] = 1234567900
        save_checkpoint(state, checkpoint_path)
        
        # After second game
        state['start_index'] = 2
        state['processed_games'].append('zelda-oot')
        state['total_records'] = 320
        state['timestamp'] = 1234568000
        save_checkpoint(state, checkpoint_path)
        
        # Verify
        loaded = load_checkpoint(checkpoint_path)
        assert loaded['start_index'] == 2
        assert loaded['total_records'] == 320
        assert len(loaded['processed_games']) == 2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])