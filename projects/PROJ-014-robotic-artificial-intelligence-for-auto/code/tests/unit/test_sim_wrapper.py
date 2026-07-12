"""
Unit tests for SimWrapper.

Tests noise injection logic and wrapper functionality without requiring CARLA.
"""

import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.environment.sim_wrapper import SimWrapper, NoiseConfig, create_sim_wrapper


class TestNoiseConfig:
    """Tests for NoiseConfig class."""

    def test_default_config(self):
        """Test default noise configuration values."""
        config = NoiseConfig()
        assert config.enabled is True
        assert config.rgb_noise_type == "gaussian"
        assert config.rgb_noise_std == 0.05
        assert config.depth_noise_type == "dropout"
        assert config.depth_dropout_rate == 0.1
        assert config.lidar_noise_type == "range"
        assert config.lidar_noise_std == 0.1
        assert config.lidar_dropout_rate == 0.05

    def test_custom_config(self):
        """Test custom noise configuration."""
        config = NoiseConfig(
            rgb_noise_type="salt_pepper",
            rgb_noise_std=0.1,
            enabled=False
        )
        assert config.rgb_noise_type == "salt_pepper"
        assert config.rgb_noise_std == 0.1
        assert config.enabled is False

    def test_from_config_dict(self):
        """Test loading config from dictionary."""
        config_dict = {
            "rgb_noise_type": "blur",
            "rgb_noise_std": 0.2,
            "enabled": True
        }
        config = NoiseConfig.from_config(config_dict)
        assert config.rgb_noise_type == "blur"
        assert config.rgb_noise_std == 0.2


class TestNoiseInjection:
    """Tests for noise injection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = NoiseConfig(enabled=True, rgb_noise_std=0.1)
        self.wrapper = SimWrapper(env_type="dummy", noise_config=self.config)

    def test_rgb_gaussian_noise(self):
        """Test Gaussian noise injection on RGB."""
        self.config.rgb_noise_type = "gaussian"
        self.config.rgb_noise_std = 0.1
        self.wrapper.set_noise_config(self.config)
        
        # Create a uniform image
        clean_rgb = np.ones((84, 84, 3), dtype=np.uint8) * 128
        noisy_rgb = self.wrapper.inject_noise(clean_rgb, "rgb")
        
        # Check that noise was applied (values should differ)
        assert not np.array_equal(clean_rgb, noisy_rgb)
        # Check that values are still in valid range
        assert np.all(noisy_rgb >= 0) and np.all(noisy_rgb <= 255)

    def test_rgb_salt_pepper_noise(self):
        """Test salt and pepper noise injection on RGB."""
        self.config.rgb_noise_type = "salt_pepper"
        self.config.rgb_noise_std = 0.1  # Used as probability
        self.wrapper.set_noise_config(self.config)
        
        clean_rgb = np.ones((84, 84, 3), dtype=np.uint8) * 128
        noisy_rgb = self.wrapper.inject_noise(clean_rgb, "rgb")
        
        # Check that some pixels changed (salt or pepper)
        assert not np.array_equal(clean_rgb, noisy_rgb)

    def test_depth_dropout_noise(self):
        """Test dropout noise injection on Depth."""
        self.config.depth_noise_type = "dropout"
        self.config.depth_dropout_rate = 0.5
        self.wrapper.set_noise_config(self.config)
        
        clean_depth = np.ones((84, 84), dtype=np.float32) * 10.0
        noisy_depth = self.wrapper.inject_noise(clean_depth, "depth")
        
        # Check that some pixels are zeroed out
        zero_count = np.sum(noisy_depth == 0)
        expected_zeros = int(84 * 84 * 0.5)
        # Allow some variance due to randomness
        assert zero_count > 0
        assert zero_count < 84 * 84  # Not all should be zero

    def test_lidar_range_noise(self):
        """Test range noise injection on LiDAR."""
        self.config.lidar_noise_type = "range"
        self.config.lidar_noise_std = 0.1
        self.wrapper.set_noise_config(self.config)
        
        # Create a simple point cloud
        clean_lidar = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 2.0, 0.0, 1.0],
            [0.0, 0.0, 3.0, 1.0]
        ], dtype=np.float32)
        
        noisy_lidar = self.wrapper.inject_noise(clean_lidar, "lidar")
        
        # Check that points moved (distances changed)
        assert not np.array_equal(clean_lidar, noisy_lidar)
        # Check shape is preserved
        assert noisy_lidar.shape == clean_lidar.shape

    def test_lidar_dropout_noise(self):
        """Test dropout noise injection on LiDAR."""
        self.config.lidar_noise_type = "dropout"
        self.config.lidar_dropout_rate = 0.5
        self.wrapper.set_noise_config(self.config)
        
        clean_lidar = np.random.rand(100, 4).astype(np.float32)
        noisy_lidar = self.wrapper.inject_noise(clean_lidar, "lidar")
        
        # Check that some points are removed
        assert noisy_lidar.shape[0] < clean_lidar.shape[0]
        assert noisy_lidar.shape[1] == 4

    def test_noise_disabled(self):
        """Test that noise is not applied when disabled."""
        self.config.enabled = False
        self.wrapper.set_noise_config(self.config)
        
        clean_rgb = np.ones((84, 84, 3), dtype=np.uint8) * 128
        noisy_rgb = self.wrapper.inject_noise(clean_rgb, "rgb")
        
        # Should be identical
        assert np.array_equal(clean_rgb, noisy_rgb)


class TestSimWrapper:
    """Tests for SimWrapper class."""

    def test_dummy_initialization(self):
        """Test dummy environment initialization."""
        wrapper = SimWrapper(env_type="dummy")
        assert wrapper.env_type == "dummy"
        assert wrapper.noise_config.enabled is True

    def test_reset_returns_observation(self):
        """Test that reset returns a valid observation dictionary."""
        wrapper = SimWrapper(env_type="dummy")
        obs = wrapper.reset()
        
        assert isinstance(obs, dict)
        assert "rgb" in obs
        assert "depth" in obs
        assert "lidar" in obs
        assert obs["rgb"].shape == (84, 84, 3)
        assert obs["depth"].shape == (84, 84)
        assert obs["lidar"].shape[1] == 4  # x, y, z, intensity

    def test_step_returns_tuple(self):
        """Test that step returns correct tuple structure."""
        wrapper = SimWrapper(env_type="dummy")
        obs, reward, done, info = wrapper.step(action=0)
        
        assert isinstance(obs, dict)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_get_status(self):
        """Test get_status returns valid dictionary."""
        wrapper = SimWrapper(env_type="dummy")
        status = wrapper.get_status()
        
        assert "env_type" in status
        assert "noise_enabled" in status
        assert "noise_config" in status
        assert status["env_type"] == "dummy"

    def test_create_sim_wrapper_factory(self):
        """Test factory function."""
        noise_dict = {"rgb_noise_type": "gaussian", "rgb_noise_std": 0.1}
        wrapper = create_sim_wrapper(
            env_type="dummy",
            noise_config_dict=noise_dict,
            seed=42
        )
        
        assert wrapper.env_type == "dummy"
        assert wrapper.noise_config.rgb_noise_type == "gaussian"
        assert wrapper.noise_config.rgb_noise_std == 0.1

    def test_close(self):
        """Test close method doesn't raise errors."""
        wrapper = SimWrapper(env_type="dummy")
        wrapper.close()
        # Should complete without error