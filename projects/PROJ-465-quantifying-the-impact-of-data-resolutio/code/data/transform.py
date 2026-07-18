"""
Transform module for gravitational wave data processing.
Handles downsampling, quantization, and resolution configuration.
"""
import logging
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

from code.config import DATA_DIR
from code.utils.logging_config import get_derivation_logger

logger = logging.getLogger(__name__)
derivation_logger = get_derivation_logger("transform")

def validate_nyquist_compliance(
    strain_data: np.ndarray,
    original_fs: float,
    target_fs: float
) -> bool:
    """
    Validate that the target sampling rate satisfies the Nyquist criterion
    relative to the dominant frequency content of the signal.

    Args:
        strain_data: 1D numpy array of strain data
        original_fs: Original sampling frequency in Hz
        target_fs: Target sampling frequency in Hz

    Returns:
        True if Nyquist limit is satisfied, False otherwise

    Raises:
        ValueError: If target_fs is not less than original_fs
    """
    if target_fs >= original_fs:
        raise ValueError(f"Target fs ({target_fs}) must be less than original fs ({original_fs})")

    # Calculate Nyquist frequency for target
    target_nyquist = target_fs / 2.0

    # Compute FFT to find dominant frequency content
    fft_data = fft(strain_data)
    freqs = fftfreq(len(strain_data), 1.0 / original_fs)

    # Find the frequency with the highest power (excluding DC)
    power = np.abs(fft_data[1:]) ** 2
    max_power_idx = np.argmax(power) + 1
    dominant_freq = abs(freqs[max_power_idx])

    # Check if dominant frequency is below Nyquist
    is_compliant = dominant_freq < target_nyquist

    if not is_compliant:
        logger.warning(
            f"Dominant frequency ({dominant_freq:.2f} Hz) exceeds target Nyquist "
            f"({target_nyquist:.2f} Hz). Downsampling may cause aliasing."
        )
        derivation_logger.warning(
            "Nyquist violation",
            dominant_freq=dominant_freq,
            target_nyquist=target_nyquist,
            target_fs=target_fs
        )

    return is_compliant

def downsample_strain_data(
    strain_data: np.ndarray,
    original_fs: float,
    target_fs: float
) -> Tuple[np.ndarray, float]:
    """
    Downsample strain data using scipy.signal.decimate with anti-aliasing.

    Args:
        strain_data: 1D numpy array of strain data
        original_fs: Original sampling frequency in Hz
        target_fs: Target sampling frequency in Hz

    Returns:
        Tuple of (downsampled_data, new_sampling_rate)
    """
    if target_fs >= original_fs:
        raise ValueError("Target sampling rate must be lower than original")

    # Calculate decimation factor
    decimation_factor = int(original_fs / target_fs)

    if decimation_factor < 1:
        raise ValueError("Invalid decimation factor calculated")

    # Apply anti-aliasing filter and downsample
    # f=0.8 ensures the filter cutoff is 80% of the new Nyquist
    downsampled = signal.decimate(strain_data, decimation_factor, ftype='iir', zero_phase=True)

    logger.info(
        f"Downsampled data from {original_fs} Hz to {target_fs} Hz "
        f"(factor={decimation_factor}, new length={len(downsampled)})"
    )
    derivation_logger.info(
        "Downsampling applied",
        original_fs=original_fs,
        target_fs=target_fs,
        decimation_factor=decimation_factor,
        original_length=len(strain_data),
        new_length=len(downsampled)
    )

    return downsampled, target_fs

def quantize_strain_data(
    strain_data: np.ndarray,
    bit_depth: int
) -> np.ndarray:
    """
    Quantize strain data to a specific floating-point bit depth.

    This simulates storage constraints by converting the data to the
    specified float representation (16-bit or 32-bit).

    Args:
        strain_data: 1D numpy array of strain data (float64)
        bit_depth: Target bit depth (16 or 32)

    Returns:
        Quantized data as numpy array with specified dtype

    Raises:
        ValueError: If bit_depth is not 16 or 32
    """
    if bit_depth not in [16, 32]:
        raise ValueError(f"Unsupported bit depth: {bit_depth}. Only 16 or 32 supported.")

    dtype_map = {
        16: np.float16,
        32: np.float32
    }

    target_dtype = dtype_map[bit_depth]

    # Log original statistics
    original_min = np.min(strain_data)
    original_max = np.max(strain_data)
    original_mean = np.mean(strain_data)
    original_std = np.std(strain_data)

    # Perform quantization
    quantized = strain_data.astype(target_dtype)

    # Log quantization effects
    quantized_min = np.min(quantized)
    quantized_max = np.max(quantized)
    quantized_mean = np.mean(quantized)
    quantized_std = np.std(quantized)

    # Calculate relative error
    if original_std > 0:
        relative_error = np.mean(np.abs(quantized - strain_data)) / original_std
    else:
        relative_error = 0.0

    logger.info(
        f"Quantized data to {bit_depth}-bit float: "
        f"range [{quantized_min:.2e}, {quantized_max:.2e}], "
        f"rel_error={relative_error:.2e}"
    )

    derivation_logger.info(
        "Quantization applied",
        bit_depth=bit_depth,
        original_dtype=strain_data.dtype,
        target_dtype=target_dtype,
        original_range=(original_min, original_max),
        quantized_range=(quantized_min, quantized_max),
        relative_error=relative_error
    )

    return quantized

def apply_resolution_transforms(
    strain_data: np.ndarray,
    original_fs: float,
    target_fs: int,
    bit_depth: int
) -> Tuple[np.ndarray, float, Dict[str, Any]]:
    """
    Apply both downsampling and quantization to strain data.

    Args:
        strain_data: 1D numpy array of strain data
        original_fs: Original sampling frequency in Hz
        target_fs: Target sampling frequency in Hz
        bit_depth: Target bit depth (16 or 32)

    Returns:
        Tuple of (transformed_data, new_fs, metadata_dict)
    """
    # Validate Nyquist first
    validate_nyquist_compliance(strain_data, original_fs, target_fs)

    # Downsample
    downsampled_data, new_fs = downsample_strain_data(strain_data, original_fs, target_fs)

    # Quantize
    quantized_data = quantize_strain_data(downsampled_data, bit_depth)

    metadata = {
        "original_fs": original_fs,
        "target_fs": new_fs,
        "bit_depth": bit_depth,
        "original_length": len(strain_data),
        "final_length": len(quantized_data),
        "transformations": ["downsample", "quantize"]
    }

    return quantized_data, new_fs, metadata

def generate_all_resolutions(
    strain_data: np.ndarray,
    original_fs: float,
    output_dir: Optional[Path] = None
) -> Dict[str, Tuple[np.ndarray, float]]:
    """
    Generate all required resolution configurations for an event.

    Configurations:
    - 4096 Hz (baseline)
    - 2048 Hz
    - 1024 Hz
    - 512 Hz
    Each with 16-bit and 32-bit quantization.

    Args:
        strain_data: 1D numpy array of strain data
        original_fs: Original sampling frequency in Hz
        output_dir: Optional directory to save results

    Returns:
        Dictionary mapping resolution string to (data, fs) tuple
    """
    target_fs_list = [4096, 2048, 1024, 512]
    bit_depths = [32, 16]
    results = {}

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for fs in target_fs_list:
        for bit_depth in bit_depths:
            key = f"{fs}Hz_{bit_depth}bit"
            data, new_fs, _ = apply_resolution_transforms(
                strain_data, original_fs, fs, bit_depth
            )
            results[key] = (data, new_fs)

            if output_dir:
                output_path = output_dir / f"{key}.npy"
                np.save(output_path, data)
                logger.info(f"Saved {output_path}")

    return results

def main():
    """
    Main entry point for testing transform functions.
    Generates synthetic data for demonstration purposes only.
    """
    # Note: This is a test harness. Real data is loaded via download.py
    logger.info("Running transform module self-test...")

    # Create synthetic strain data for testing
    t = np.linspace(0, 1, 4096)
    synthetic_data = np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(len(t))

    # Test downsampling
    downsampled, fs = downsample_strain_data(synthetic_data, 4096, 2048)
    logger.info(f"Downsampled to {fs} Hz, length {len(downsampled)}")

    # Test quantization
    q16 = quantize_strain_data(downsampled, 16)
    q32 = quantize_strain_data(downsampled, 32)
    logger.info(f"Quantized to 16-bit: {q16.dtype}")
    logger.info(f"Quantized to 32-bit: {q32.dtype}")

    logger.info("Transform module self-test complete.")

if __name__ == "__main__":
    main()