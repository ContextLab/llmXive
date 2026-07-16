import pytest
import numpy as np
from code.noise import get_noise_injection_function, inject_gaussian_noise, inject_quantization_noise
from code.utils.data_models import Trajectory
from code.config import NoiseType

class TestNoiseErrorHandling:
    """Tests for error handling of unsupported noise types."""

    def test_unsupported_noise_type_raises_value_error(self):
        """Test that get_noise_injection_function raises ValueError for unsupported types."""
        # Create a mock unsupported noise type
        class UnsupportedNoiseType:
            pass

        unsupported = UnsupportedNoiseType()
        
        with pytest.raises(ValueError) as exc_info:
            get_noise_injection_function(unsupported)
        
        assert "Unsupported noise type" in str(exc_info.value)
        assert "Only" in str(exc_info.value)

    def test_unsupported_noise_type_in_enum_raises_value_error(self):
        """Test that get_noise_injection_function raises ValueError for invalid enum values."""
        # Try to create a NoiseType that doesn't exist in the enum
        # This simulates a potential misconfiguration
        try:
            invalid_type = NoiseType("INVALID_TYPE_NAME")
        except ValueError:
            # If the enum doesn't allow arbitrary strings, we test the function directly
            # by passing a string that isn't in the enum
            with pytest.raises(ValueError) as exc_info:
                get_noise_injection_function("INVALID_NOISE_TYPE")
            
            assert "Unsupported noise type" in str(exc_info.value)
            return

        # If the enum allows it (unlikely), test the function
        with pytest.raises(ValueError) as exc_info:
            get_noise_injection_function(invalid_type)
        
        assert "Unsupported noise type" in str(exc_info.value)

    def test_gaussian_noise_injection_valid(self):
        """Test that Gaussian noise injection works correctly."""
        clean_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        trajectory = Trajectory(data=clean_data, system_type="lorenz", seed=42)
        
        noisy = inject_gaussian_noise(trajectory, target_snr_db=20.0, seed=123)
        
        assert noisy.noise_type == NoiseType.GAUSSIAN
        assert noisy.actual_snr_db <= 20.5  # Allow some tolerance
        assert np.allclose(noisy.clean_data, clean_data)

    def test_quantization_noise_injection_valid(self):
        """Test that quantization noise injection works correctly."""
        clean_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        trajectory = Trajectory(data=clean_data, system_type="rossler", seed=42)
        
        noisy = inject_quantization_noise(trajectory, bit_resolution=8, seed=123)
        
        assert noisy.noise_type == NoiseType.QUANTIZATION
        assert noisy.bit_resolution == 8
        assert np.allclose(noisy.clean_data, clean_data)

    def test_invalid_bit_resolution_raises_error(self):
        """Test that invalid bit resolution raises ValueError."""
        clean_data = np.array([1.0, 2.0, 3.0])
        trajectory = Trajectory(data=clean_data, system_type="lorenz", seed=42)
        
        with pytest.raises(ValueError) as exc_info:
            inject_quantization_noise(trajectory, bit_resolution=-1)
        
        assert "positive integer" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            inject_quantization_noise(trajectory, bit_resolution=0)
        
        assert "positive integer" in str(exc_info.value)

    def test_invalid_snr_raises_error(self):
        """Test that invalid SNR values raise ValueError."""
        clean_data = np.array([1.0, 2.0, 3.0])
        trajectory = Trajectory(data=clean_data, system_type="lorenz", seed=42)
        
        with pytest.raises(ValueError) as exc_info:
            inject_gaussian_noise(trajectory, target_snr_db=float('inf'))
        
        assert "finite number" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            inject_gaussian_noise(trajectory, target_snr_db=float('nan'))
        
        assert "finite number" in str(exc_info.value)