"""
Unit tests for configuration management.
"""

import pytest
from code.utils.config import (
    CONFIG,
    SPLIT_SEED,
    DEFAULT_TRAIN_SEED,
    IMAGE_SIZE,
    BATCH_SIZE,
    STABILITY_IOU_THRESHOLD,
    set_seed,
    get_split_seed,
    get_training_seed,
    init_random_state,
    get_config_dict,
)


class TestConfigValues:
    """Test that configuration values are correctly defined."""

    def test_split_seed_is_int(self):
        """Verify split_seed is an integer."""
        assert isinstance(CONFIG['split_seed'], int)

    def test_stability_iou_threshold_is_float(self):
        """Verify stability_iou_threshold is a float."""
        assert isinstance(CONFIG['stability_iou_threshold'], float)

    def test_image_size_is_tuple(self):
        """Verify image_size is a tuple."""
        assert isinstance(CONFIG['image_size'], tuple)
        assert len(CONFIG['image_size']) == 2

    def test_batch_size_is_int(self):
        """Verify batch_size is an integer."""
        assert isinstance(CONFIG['batch_size'], int)

    def test_train_seed_is_int(self):
        """Verify train_seed is an integer."""
        assert isinstance(CONFIG['train_seed'], int)

class TestSeedFunctions:
    """Test seed management functions."""

    def test_get_split_seed_returns_42(self):
        """Verify get_split_seed returns the fixed value 42."""
        assert get_split_seed() == 42

    def test_get_training_seed_default(self):
        """Verify get_training_seed returns default when None provided."""
        assert get_training_seed(None) == DEFAULT_TRAIN_SEED

    def test_get_training_seed_custom(self):
        """Verify get_training_seed uses provided seed."""
        custom_seed = 123
        assert get_training_seed(custom_seed) == custom_seed

    def test_init_random_state_split(self):
        """Verify init_random_state with split=True uses split seed."""
        result = init_random_state(split=True)
        assert result['seed'] == SPLIT_SEED

    def test_init_random_state_train(self):
        """Verify init_random_state with split=False uses training seed."""
        result = init_random_state(split=False)
        assert result['seed'] == DEFAULT_TRAIN_SEED

class TestConfigDict:
    """Test get_config_dict function."""

    def test_config_dict_keys(self):
        """Verify all expected keys are present."""
        config = get_config_dict()
        expected_keys = {
            'split_seed',
            'train_seed',
            'image_size',
            'batch_size',
            'stability_iou_threshold',
        }
        assert set(config.keys()) == expected_keys

    def test_config_dict_values(self):
        """Verify config values match constants."""
        config = get_config_dict()
        assert config['split_seed'] == SPLIT_SEED
        assert config['train_seed'] == DEFAULT_TRAIN_SEED
        assert config['image_size'] == IMAGE_SIZE
        assert config['batch_size'] == BATCH_SIZE
        assert config['stability_iou_threshold'] == STABILITY_IOU_THRESHOLD