"""
Unit tests for RGB preprocessing pipeline (T020).
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from data.pipeline import RGBPreprocessor, RGBPreprocessingConfig, create_rgb_preprocessor


class TestRGBPreprocessingConfig:
    def test_default_values(self):
        config = RGBPreprocessingConfig()
        assert config.target_height == 84
        assert config.target_width == 84
        assert config.normalize is True
        assert len(config.mean) == 3
        assert len(config.std) == 3

    def test_custom_values(self):
        config = RGBPreprocessingConfig(target_height=128, target_width=128, normalize=False)
        assert config.target_height == 128
        assert config.target_width == 128
        assert config.normalize is False

    def test_invalid_dimensions(self):
        with pytest.raises(ValueError):
            RGBPreprocessingConfig(target_height=0)
        with pytest.raises(ValueError):
            RGBPreprocessingConfig(target_width=-10)


class TestRGBPreprocessor:
    @pytest.fixture
    def preprocessor(self):
        return create_rgb_preprocessor()

    @pytest.fixture
    def dummy_rgb_image(self):
        """Create a dummy RGB image (64x64x3)."""
        return np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)

    @pytest.fixture
    def dummy_grayscale_image(self):
        """Create a dummy grayscale image (64x64)."""
        return np.random.randint(0, 256, (64, 64), dtype=np.uint8)

    def test_initialization(self, preprocessor):
        assert preprocessor.config.target_height == 84
        assert preprocessor.config.target_width == 84

    def test_preprocess_rgb_image(self, preprocessor, dummy_rgb_image):
        result = preprocessor.preprocess(dummy_rgb_image)
        assert result.shape == (84, 84, 3)
        assert result.dtype == np.float32
        # Check normalization (mean should be close to 0, std close to 1 after normalization)
        # Note: Exact values depend on input, but we check range
        assert result.min() < 0  # Normalized data can be negative
        assert result.max() > 0

    def test_preprocess_grayscale_image(self, preprocessor, dummy_grayscale_image):
        result = preprocessor.preprocess(dummy_grayscale_image)
        # Grayscale should be converted to 3 channels
        assert result.shape == (84, 84, 3)
        assert result.dtype == np.float32

    def test_preprocess_larger_image(self, preprocessor):
        """Test with image larger than target size."""
        large_img = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        result = preprocessor.preprocess(large_img)
        assert result.shape == (84, 84, 3)

    def test_preprocess_rectangular_image(self, preprocessor):
        """Test with rectangular image to verify center crop logic."""
        rect_img = np.random.randint(0, 256, (100, 200, 3), dtype=np.uint8)
        result = preprocessor.preprocess(rect_img)
        assert result.shape == (84, 84, 3)

    def test_preprocess_empty_image(self, preprocessor):
        """Test that empty image raises error."""
        empty_img = np.array([]).reshape(0, 0, 3)
        with pytest.raises(ValueError):
            preprocessor.preprocess(empty_img)

    def test_preprocess_invalid_type(self, preprocessor):
        """Test that non-numpy input raises error."""
        with pytest.raises(TypeError):
            preprocessor.preprocess("not an image")

    def test_preprocess_already_target_size(self, preprocessor):
        """Test image already at target size."""
        target_img = np.random.randint(0, 256, (84, 84, 3), dtype=np.uint8)
        result = preprocessor.preprocess(target_img)
        assert result.shape == (84, 84, 3)

    def test_custom_config_preprocessor(self):
        """Test preprocessor with custom config."""
        config = RGBPreprocessingConfig(target_height=32, target_width=32, normalize=False)
        preprocessor = create_rgb_preprocessor(config)
        
        img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        result = preprocessor.preprocess(img)
        
        assert result.shape == (32, 32, 3)
        # If normalize=False, values should be in 0-1 range (since we divide by 255 in resize logic fallback)
        assert result.max() <= 1.0

class TestCreateRGBPreprocessor:
    def test_factory_function(self):
        preprocessor = create_rgb_preprocessor()
        assert isinstance(preprocessor, RGBPreprocessor)

    def test_factory_with_config(self):
        config = RGBPreprocessingConfig(target_height=64, target_width=64)
        preprocessor = create_rgb_preprocessor(config)
        assert preprocessor.config.target_height == 64