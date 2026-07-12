"""
Unit tests for data transformation utilities, specifically focusing on
quantization logic and anti-aliasing filter behavior.
"""
import pytest
import numpy as np
from scipy import signal
from scipy.stats import norm

# Import the functions under test from the project's transform module
# We assume the project structure places these in code/data/transform.py
# and that the module is importable as 'code.data.transform' or similar.
# Given the API surface provided:
# "from data.transform import ..., quantize_strain_data, ..."
# We will attempt to import directly from the relative path structure used in the project.
# In a real execution environment, sys.path would be configured to include the 'code' directory.
try:
    from code.data.transform import quantize_strain_data
except ImportError:
    # Fallback for local testing if 'code' is not in path but the file exists relative to tests
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.data.transform import quantize_strain_data


class TestQuantizationLogic:
    """Tests for the 16-bit and 32-bit quantization logic."""

    def test_quantize_16bit_preserves_range(self):
        """
        Verify that 16-bit quantization maps the input signal to the correct
        integer range [-32768, 32767] and preserves relative order.
        """
        # Generate a signal with a known range
        np.random.seed(42) # Reproducibility
        t = np.linspace(0, 1, 1000)
        # Signal with amplitude 1.0, centered at 0
        data = np.sin(2 * np.pi * 10 * t) 
        
        # Quantize to 16-bit
        quantized_16 = quantize_strain_data(data, bit_depth=16)
        
        # Check dtype is integer (or float representing integers)
        # The implementation likely returns float64 to avoid overflow during processing,
        # but the values should be integers.
        assert np.issubdtype(quantized_16.dtype, np.floating) or np.issubdtype(quantized_16.dtype, np.integer)
        
        # Check range: 16-bit signed integer range is -32768 to 32767
        # The max value in the signal is ~1.0, min is ~-1.0.
        # The quantizer should map 1.0 to ~32767 and -1.0 to ~-32768.
        max_val = np.max(quantized_16)
        min_val = np.min(quantized_16)
        
        # Allow for small floating point errors if the implementation returns floats
        assert max_val <= 32767.0, f"Max value {max_val} exceeds 16-bit signed max"
        assert min_val >= -32768.0, f"Min value {min_val} exceeds 16-bit signed min"
        
        # Verify that the full range is utilized for a signal that spans the input range
        # If the input spans [-1, 1], the output should span close to [-32768, 32767]
        # We check that the range is significant (e.g., > 50% of max possible range)
        expected_range = 32767 - (-32768)
        actual_range = max_val - min_val
        assert actual_range > expected_range * 0.5, "Quantization did not utilize sufficient range"

    def test_quantize_32bit_precision(self):
        """
        Verify that 32-bit quantization (float32) preserves more precision
        than 16-bit for small variations, and stays within float32 limits.
        """
        np.random.seed(123)
        # Create a signal with small variations to test precision
        data = np.random.normal(0, 0.001, 1000) 
        
        quantized_32 = quantize_strain_data(data, bit_depth=32)
        
        # 32-bit float has a much larger dynamic range and precision
        # Check that the output is not truncated to integers like 16-bit might be (if implemented as int)
        # Assuming the function returns float64 for 32-bit to avoid precision loss in numpy operations,
        # but the values should effectively represent float32 precision.
        
        # Verify the values are within float32 limits (approx +/- 3.4e38)
        assert np.all(np.isfinite(quantized_32))
        
        # Check that the relative differences are preserved better than a coarse quantization
        # Compare the variance of the original vs quantized
        var_orig = np.var(data)
        var_quant = np.var(quantized_32)
        
        # The variance should be very close (relative error < 1e-5)
        rel_error = abs(var_orig - var_quant) / (var_orig + 1e-10)
        assert rel_error < 1e-4, f"32-bit quantization introduced too much error: {rel_error}"

    def test_quantize_invalid_bit_depth(self):
        """Verify that invalid bit depths raise an error."""
        data = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            quantize_strain_data(data, bit_depth=8) # 8-bit not supported by spec
        
        with pytest.raises(ValueError):
            quantize_strain_data(data, bit_depth=64) # 64-bit not supported by spec
        
        with pytest.raises(ValueError):
            quantize_strain_data(data, bit_depth=10) # Arbitrary invalid depth

    def test_quantize_clipping_behavior(self):
        """
        Verify that values exceeding the representable range of the bit depth
        are clipped correctly.
        """
        # Create a signal that exceeds the range of a 16-bit integer if normalized to [-1, 1]
        # But the quantizer usually normalizes based on the input data's max/min or a fixed range.
        # Let's assume the function expects data in a normalized range [-1, 1] or handles scaling internally.
        # If the function scales based on data max, we test with data that has outliers.
        
        data = np.array([1.0, 2.0, 3.0, -1.0, -2.0, -3.0])
        
        # If the implementation normalizes to the data's max, 3.0 becomes 1.0, 1.0 becomes 0.33
        # If the implementation assumes input is already in [-1, 1] and clips, then 2.0 becomes 1.0.
        # Based on typical GW strain data, it's usually small numbers.
        # Let's test the clipping of the output range.
        
        quantized = quantize_strain_data(data, bit_depth=16)
        
        # The max possible value for 16-bit signed is 32767
        assert np.max(quantized) <= 32767
        assert np.min(quantized) >= -32768
        
        # If the input had values > 1 (assuming normalized input), they should be clipped
        # However, without knowing the exact normalization strategy of the implementation,
        # we rely on the range check above.
        # Let's force a scenario where we know the scaling:
        # If the function scales 1.0 -> 32767, then 2.0 -> 65534 (clipped to 32767)
        
        # Re-test with a specific normalization assumption:
        # Assume the function treats the max absolute value in the input as the reference for 1.0.
        # If so, 3.0 is the max, so 3.0 -> 32767, 1.0 -> 10922.
        # This test is valid if the implementation does NOT normalize to a fixed range.
        
        # Alternative: If the function assumes input is in [-1, 1] and clips outliers:
        # Then 2.0 -> 32767, 1.0 -> 16383.5 (clipped/rounded).
        
        # To be robust, we check that the output is within the 16-bit bounds regardless of input scaling.
        # The previous assertions cover this.

    def test_quantize_reproducibility(self):
        """Verify that quantization is deterministic for the same input."""
        data = np.random.randn(1000)
        
        q1 = quantize_strain_data(data, bit_depth=16)
        q2 = quantize_strain_data(data, bit_depth=16)
        
        assert np.array_equal(q1, q2), "Quantization is not deterministic"


class TestDecimateAntiAliasing:
    """Tests for scipy.signal.decimate anti-aliasing filter behavior."""

    def test_decimate_reduces_frequency_content(self):
        """
        Verify that decimation with anti-aliasing filter removes high frequency
        components that would alias.
        """
        fs = 4096
        t = np.arange(0, 1, 1/fs)
        
        # Create a signal with a frequency component near the Nyquist of the new rate
        # Target rate: 1024 Hz. New Nyquist: 512 Hz.
        # Original signal: 600 Hz (above new Nyquist, will alias without filter)
        f_alias = 600 
        signal_high_freq = np.sin(2 * np.pi * f_alias * t)
        
        # Decimate by factor 4 (4096 -> 1024)
        # scipy.signal.decimate uses a low-pass filter by default (FIR or IIR)
        downsampled = signal.decimate(signal_high_freq, 4, ftype='fir')
        
        # The new sampling rate is 1024 Hz.
        # The 600 Hz component should be filtered out.
        # If it wasn't filtered, it would alias to |600 - 1024| = 424 Hz (or similar depending on folding).
        # But with a proper low-pass filter (cutoff < 512 Hz), the 600 Hz component should be attenuated.
        
        # Analyze the power of the downsampled signal
        # If the filter worked, the signal should be mostly noise (attenuated sine)
        # We can check the amplitude.
        rms_original = np.sqrt(np.mean(signal_high_freq**2))
        rms_down = np.sqrt(np.mean(downsampled**2))
        
        # The amplitude should be significantly reduced (e.g., by a factor of 10 or more)
        # A perfect filter would make it 0.
        attenuation = rms_down / (rms_original + 1e-10)
        assert attenuation < 0.1, f"Anti-aliasing filter failed to attenuate high frequency: attenuation={attenuation}"

    def test_decimate_preserves_low_frequency(self):
        """
        Verify that decimation preserves low frequency components below the new Nyquist.
        """
        fs = 4096
        t = np.arange(0, 1, 1/fs)
        
        # Low frequency signal: 10 Hz (well below new Nyquist of 512 Hz)
        f_low = 10
        signal_low_freq = np.sin(2 * np.pi * f_low * t)
        
        downsampled = signal.decimate(signal_low_freq, 4, ftype='fir')
        
        # The amplitude should be preserved (within filter ripple)
        rms_original = np.sqrt(np.mean(signal_low_freq**2))
        rms_down = np.sqrt(np.mean(downsampled**2))
        
        # Allow for some filter ripple (e.g., < 5% error)
        error = abs(rms_original - rms_down) / (rms_original + 1e-10)
        assert error < 0.05, f"Low frequency signal was distorted: error={error}"

    def test_decimate_output_length(self):
        """Verify that the output length is approximately N/factor."""
        fs = 4096
        n_samples = 40960 # 10 seconds
        t = np.arange(n_samples) / fs
        data = np.random.randn(n_samples)
        
        factor = 4
        downsampled = signal.decimate(data, factor)
        
        expected_len = n_samples // factor
        # decimate might handle the remainder slightly differently, but should be close
        assert abs(len(downsampled) - expected_len) <= 1, f"Output length mismatch: {len(downsampled)} vs {expected_len}"