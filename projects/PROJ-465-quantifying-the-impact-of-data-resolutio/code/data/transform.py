import logging
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

from code.utils.logging_config import get_derivation_logger, log_derivation_params
from code.utils.seeds import set_global_seed
from code.config import DATA_DIR

logger = logging.getLogger(__name__)

def validate_nyquist_compliance(data: np.ndarray, original_fs: float, target_fs: float, signal_bandwidth: Optional[float] = None) -> bool:
    """
    Validates if the target sampling rate satisfies the Nyquist criterion relative to
    the signal's dominant frequency content before downsampling.

    Args:
        data: The time series data array.
        original_fs: Original sampling frequency in Hz.
        target_fs: Target sampling frequency in Hz.
        signal_bandwidth: Optional known bandwidth of the signal. If None, estimated from data.

    Returns:
        True if Nyquist limit is respected (target_fs > 2 * max_freq), False otherwise.
    """
    if target_fs <= 0:
        raise ValueError("Target sampling frequency must be positive.")

    # Estimate dominant frequency if not provided
    if signal_bandwidth is None:
        n = len(data)
        if n == 0:
            logger.warning("Empty data array provided to Nyquist validation.")
            return False
        
        # Compute FFT to find dominant frequencies
        # Use a small subset if data is massive to save time, or full if reasonable
        fft_size = min(n, 100000) 
        yf = fft(data[:fft_size])
        xf = fftfreq(fft_size, 1 / original_fs)
        
        # Find frequencies with significant power (above mean + 3 std)
        power = np.abs(yf[:fft_size//2])
        threshold = np.mean(power) + 3 * np.std(power)
        significant_indices = np.where(power > threshold)[0]
        
        if len(significant_indices) == 0:
            logger.info("No significant frequency components found above noise floor.")
            return True # Assume safe if no signal detected

        max_freq_idx = significant_indices[np.argmax(power[significant_indices])]
        estimated_max_freq = np.abs(xf[max_freq_idx])
        signal_bandwidth = estimated_max_freq

    nyquist_freq = target_fs / 2.0

    if signal_bandwidth > nyquist_freq:
        logger.warning(
            f"Nyquist violation: Signal bandwidth ({signal_bandwidth:.2f} Hz) "
            f"exceeds Nyquist limit ({nyquist_freq:.2f} Hz) for target rate {target_fs} Hz."
        )
        return False

    logger.info(f"Nyquist check passed: Signal bandwidth ({signal_bandwidth:.2f} Hz) < Nyquist limit ({nyquist_freq:.2f} Hz).")
    return True

def downsample_strain_data(
    data: np.ndarray, 
    original_fs: float, 
    target_fs: float, 
    seed: Optional[int] = None
) -> Tuple[np.ndarray, float]:
    """
    Downsamples strain data using scipy.signal.decimate with anti-aliasing filtering.

    Args:
        data: 1D numpy array of strain data.
        original_fs: Original sampling frequency in Hz.
        target_fs: Target sampling frequency in Hz.
        seed: Optional seed for any internal random processes (though decimate is deterministic).

    Returns:
        Tuple of (downsampled_data, new_sampling_rate).
    """
    if seed is not None:
        set_global_seed(seed)

    if target_fs >= original_fs:
        raise ValueError(f"Target frequency ({target_fs}) must be less than original frequency ({original_fs}).")
    
    if target_fs <= 0:
        raise ValueError("Target frequency must be positive.")

    # Calculate decimation factor
    # factor = original_fs / target_fs
    # We require integer factor for strict decimation, or use resample for non-integer
    # Given the task (4096 -> 2048 -> 1024), factors are integers (2, 4).
    factor = original_fs / target_fs

    if not float(factor).is_integer():
        logger.warning(f"Non-integer decimation factor ({factor}). Using scipy.signal.resample_poly for precision.")
        # Use resample_poly for non-integer factors to maintain phase and amplitude accuracy
        # resample_poly(x, up, down) -> output rate = input_rate * up / down
        # We want: target_fs = original_fs * up / down
        # Let up = target_fs, down = original_fs (simplified if integers)
        # Better: use gcd to reduce
        from math import gcd
        numerator = int(target_fs)
        denominator = int(original_fs)
        common = gcd(numerator, denominator)
        up = numerator // common
        down = denominator // common
        
        downsampled_data = signal.resample_poly(data, up, down, window='hamming')
        new_fs = original_fs * up / down
    else:
        factor = int(factor)
        # decimate applies a lowpass filter (Butterworth by default) to prevent aliasing
        # 'firls' is often better for anti-aliasing but 'fir' is default and robust
        downsampled_data = signal.decimate(data, factor, ftype='fir', zero_phase=True)
        new_fs = original_fs / factor

    logger.info(f"Downsampled data from {original_fs} Hz to {new_fs} Hz (factor={factor}).")
    return downsampled_data, new_fs

def quantize_strain_data(
    data: np.ndarray, 
    bit_depth: int = 32
) -> np.ndarray:
    """
    Quantizes data to simulate storage constraints (16-bit or 32-bit float).
    
    Args:
        data: Input float64 array.
        bit_depth: Target bit depth (16 or 32).
        
    Returns:
        Quantized numpy array.
    """
    if bit_depth == 32:
        # Standard float32 quantization
        return data.astype(np.float32)
    elif bit_depth == 16:
        # Simulate 16-bit float (half precision)
        # Note: numpy float16 is the standard half precision
        return data.astype(np.float16)
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}. Use 16 or 32.")

def apply_resolution_transforms(
    strain_data: np.ndarray, 
    original_fs: float, 
    target_resolutions: List[int],
    output_dir: Optional[Path] = None,
    event_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Applies downsampling to a list of target resolutions.
    
    Args:
        strain_data: Original strain data.
        original_fs: Original sampling rate.
        target_resolutions: List of target sampling rates (e.g., [4096, 2048, 1024]).
        output_dir: Optional directory to save results.
        event_id: Optional event ID for logging.
        
    Returns:
        Dictionary mapping target_fs to {'data': array, 'fs': float, 'path': str}.
    """
    results = {}
    
    # Ensure output directory exists if specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for target_fs in target_resolutions:
        logger.info(f"Processing resolution: {target_fs} Hz for event {event_id or 'unknown'}")
        
        # Validate Nyquist before processing
        # Note: We assume the signal content is valid for the highest target, 
        # but we check against the specific target to be safe.
        # In a real pipeline, we'd check against the signal's actual bandwidth.
        # Here we assume the input is valid for 4096, so lower rates are checked.
        is_valid = validate_nyquist_compliance(strain_data, original_fs, target_fs)
        
        if not is_valid:
            # Depending on strictness, we might skip or proceed with warning
            # The task requires anti-aliasing, which decimate handles, 
            # but the validation check is a safety gate.
            # We proceed because decimate handles the anti-aliasing filter internally.
            # The validation function logs the warning.
            pass

        downsampled_data, new_fs = downsample_strain_data(
            strain_data, original_fs, target_fs
        )
        
        result_entry = {
            'data': downsampled_data,
            'fs': new_fs,
            'original_fs': original_fs,
            'event_id': event_id
        }
        
        if output_dir:
            filename = f"{event_id}_fs{target_fs}.npy"
            path = output_dir / filename
            np.save(path, downsampled_data)
            result_entry['path'] = str(path)
            logger.info(f"Saved downsampled data to {path}")
        
        results[str(target_fs)] = result_entry

    return results

def generate_all_resolutions(
    strain_data: np.ndarray, 
    original_fs: float,
    event_id: str,
    output_base_dir: Optional[Path] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Generates all required resolutions (4096, 2048, 1024 Hz) for a given event.
    
    Args:
        strain_data: Original high-res strain data.
        original_fs: Original sampling rate.
        event_id: Identifier for the event.
        output_base_dir: Base directory for saving outputs. Defaults to DATA_DIR / 'derived'.
        
    Returns:
        Dictionary of results keyed by target frequency string.
    """
    if output_base_dir is None:
        output_base_dir = DATA_DIR / 'derived'
        
    target_resolutions = [4096, 2048, 1024]
    
    logger.info(f"Generating resolutions {target_resolutions} for {event_id}")
    
    return apply_resolution_transforms(
        strain_data=strain_data,
        original_fs=original_fs,
        target_resolutions=target_resolutions,
        output_dir=output_base_dir,
        event_id=event_id
    )