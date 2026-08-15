import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_reward import check_physics_reward_exists, main

class TestValidateReward:
    """Unit tests for reward validation functions."""

    def test_check_physics_reward_exists_with_field(self):
        """Test check_physics_reward_exists when physics_reward field exists."""
        # Mock a dataset sample with physics_reward
        sample_with_reward = {
            "actions": [0.1, 0.2, 0.3, 0.4, 0.5],
            "physics_reward": 0.8,
            "text_description": "test"
        }
        
        # Create a mock dataset iterator
        mock_dataset = [sample_with_reward]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample_with_reward)
            
            # Should return True without raising
            result = check_physics_reward_exists("mock_dataset_id", 1)
            assert result is True

    def test_check_physics_reward_exists_without_field(self):
        """Test check_physics_reward_exists when physics_reward field is missing."""
        # Mock a dataset sample without physics_reward
        sample_without_reward = {
            "actions": [0.1, 0.2, 0.3, 0.4, 0.5],
            "text_description": "test"
        }
        
        mock_dataset = [sample_without_reward]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample_without_reward)
            
            # Should return False
            result = check_physics_reward_exists("mock_dataset_id", 1)
            assert result is False

    def test_check_physics_reward_exists_with_none_value(self):
        """Test check_physics_reward_exists when physics_reward is None."""
        sample_with_none = {
            "actions": [0.1, 0.2, 0.3, 0.4, 0.5],
            "physics_reward": None,
            "text_description": "test"
        }
        
        mock_dataset = [sample_with_none]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample_with_none)
            
            result = check_physics_reward_exists("mock_dataset_id", 1)
            assert result is False

    def test_check_physics_reward_exists_with_zero(self):
        """Test check_physics_reward_exists when physics_reward is 0 (valid)."""
        sample_with_zero = {
            "actions": [0.1, 0.2, 0.3, 0.4, 0.5],
            "physics_reward": 0.0,
            "text_description": "test"
        }
        
        mock_dataset = [sample_with_zero]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample_with_zero)
            
            # 0.0 is a valid value, so should return True
            result = check_physics_reward_exists("mock_dataset_id", 1)
            assert result is True

    def test_check_physics_reward_exists_streaming(self):
        """Test that check_physics_reward_exists uses streaming mode."""
        sample = {
            "actions": [0.1, 0.2, 0.3],
            "physics_reward": 0.5,
            "text_description": "test"
        }
        
        mock_dataset = [sample]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample)
            
            check_physics_reward_exists("mock_dataset_id", 1)
            
            # Verify streaming=True was passed
            mock_load.assert_called_once()
            call_kwargs = mock_load.call_args
            assert call_kwargs.kwargs.get('streaming') is True

    def test_main_with_valid_reward(self):
        """Test main function when physics_reward exists."""
        sample = {
            "actions": [0.1, 0.2, 0.3],
            "physics_reward": 0.5,
            "text_description": "test"
        }
        
        mock_dataset = [sample]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load, \
             patch('scripts.validate_reward.get_logger') as mock_get_logger:
            
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample)
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Should complete without error
            main()
            
            # Verify logger was used
            assert mock_logger.info.called

    def test_main_with_missing_reward(self):
        """Test main function when physics_reward is missing."""
        sample = {
            "actions": [0.1, 0.2, 0.3],
            "text_description": "test"
        }
        
        mock_dataset = [sample]
        
        with patch('scripts.validate_reward.load_dataset') as mock_load, \
             patch('scripts.validate_reward.get_logger') as mock_get_logger:
            
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_dataset))
            mock_load.return_value.__getitem__ = MagicMock(return_value=sample)
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Should exit with code 1
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)