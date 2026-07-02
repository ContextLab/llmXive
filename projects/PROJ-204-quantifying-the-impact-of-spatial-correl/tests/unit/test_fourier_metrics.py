"""
Unit test for Fourier low-frequency integration (T018).

Asserts spectral power matches synthetic ground truth.
"""
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_code_dir = os.path.join(_project_root, "code")
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from analysis.fourier_metrics import (
    compute_fourier_transform, 
    compute_power_spectrum, 
    get_frequency_grid, 
    compute_low_frequency_spectral_power
)

def test_fourier_low_frequency_integration():
    """
    Create a synthetic image with a known low-frequency component (a large sine wave),
    compute the Fourier transform, integrate low-frequency power, and assert it matches
    the theoretical ground truth.
    
    Ground Truth Logic:
    - Signal: sin(x) + sin(y) with amplitude 1.
    - Theoretical power of a sine wave A*sin(kx) is A^2/2 per dimension in the continuous limit,
      but in discrete DFT, the power is concentrated in specific bins.
    - For a 64x64 image with freq=1 cycle/image, the power is concentrated in 4 bins (2 per dim).
    - Total power of the signal component (ignoring noise) should be roughly:
      2 * (N^2 * (1/2)) = N^2. (Since sin(x) has power 0.5, and we have two dimensions).
    - We verify that the calculated low-frequency power is within a tight tolerance of this theoretical value.
    """
    np.random.seed(42)
    size = 64
    
    # Create a synthetic image: a large sine wave (low frequency) + small noise
    x = np.linspace(0, 2 * np.pi, size, endpoint=False)
    y = np.linspace(0, 2 * np.pi, size, endpoint=False)
    X, Y = np.meshgrid(x, y)
    
    # Frequency k=1 (1 cycle per image length) -> very low frequency
    freq = 1
    signal = np.sin(X * freq) + np.sin(Y * freq)
    noise = np.random.normal(0, 0.01, (size, size))
    image = signal + noise
    
    # Compute Fourier Transform
    fft_result = compute_fourier_transform(image)
    
    # Compute Power Spectrum
    power_spectrum = compute_power_spectrum(fft_result)
    
    # Get frequency grid
    fx, fy = get_frequency_grid(image.shape)
    
    # Define low-frequency range. 
    # The signal has frequency 1 cycle/image. The grid spacing is 1/size = 1/64.
    # The peak is at index corresponding to 1 cycle.
    # We set a cutoff that definitely includes the signal peaks but excludes high frequencies.
    # Cutoff = 2 cycles/image is safe.
    cutoff_freq = 2.0 
    
    # Compute low-frequency spectral power
    low_freq_power = compute_low_frequency_spectral_power(
        power_spectrum, fx, fy, cutoff_freq=cutoff_freq
    )
    
    # Ground truth estimation:
    # The signal is sin(x) + sin(y).
    # In a discrete DFT of a pure sine wave of amplitude A=1 and frequency k=1:
    # The energy is split between positive and negative frequencies.
    # Total power in the signal part (excluding noise) = N^2 * (A^2 / 2) * 2 (for x and y components)
    # Wait, sin(x) + sin(y).
    # Power of sin(x) = 0.5. Power of sin(y) = 0.5. Total signal power density = 1.0.
    # Total energy = 1.0 * N^2.
    # Since the frequencies are very low (k=1), they fall well within the cutoff of 2.0.
    expected_signal_power = (0.5 + 0.5) * (size ** 2) # = 1.0 * 4096 = 4096
    
    # Allow for noise contribution and numerical precision.
    # Noise power is roughly variance * N^2 = 0.0001 * 4096 = 0.4 (negligible).
    # Tolerance: 5%
    tolerance = 0.05 
    min_expected = expected_signal_power * (1 - tolerance)
    max_expected = expected_signal_power * (1 + tolerance)
    
    assert min_expected <= low_freq_power <= max_expected, (
        f"Spectral power mismatch. Expected ~{expected_signal_power:.2f}, got {low_freq_power:.2f}. "
        f"Low-frequency integration may be incorrect. "
        f"Signal: sin(x)+sin(y), Size: {size}, Cutoff: {cutoff_freq}"
    )

if __name__ == "__main__":
    test_fourier_low_frequency_integration()
    print("Test passed: Fourier low-frequency integration matches synthetic ground truth.")