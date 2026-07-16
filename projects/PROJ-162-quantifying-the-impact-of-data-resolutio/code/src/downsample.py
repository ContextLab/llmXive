"""
Downsample module for gravitational wave waveforms.

Implements FIR low-pass filtering with anti-aliasing and amplitude correction
to isolate resolution loss from filter attenuation (Filter Confound Control).
"""
import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any, Optional
import json
from pathlib import Path
import os

# Ensure src is in path for imports if running as script
if __name__ == "__main__" and os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys

from src.config import ensure_directories, get_contract_path
from src.schema_validator import validate_and_save, SchemaValidationError
from src.data_hygiene import update_checksum, calculate_sha256
from src.profiler import profile_function, ResourceMetrics


def design_fir_filter(
    original_fs: int,
    target_fs: int,
    num_taps: int = 101,
    passband_ripple: float = 0.01,
    stopband_attenuation: float = 60
) -> np.ndarray:
    """
    Design a linear-phase FIR low-pass filter for anti-aliasing.
    
    Args:
        original_fs: Original sampling frequency (Hz).
        target_fs: Target sampling frequency (Hz).
        num_taps: Number of filter taps (must be odd for Type I).
        passband_ripple: Passband ripple in dB (not used directly in firwin but kept for API).
        stopband_attenuation: Stopband attenuation in dB (not used directly but kept for API).
        
    Returns:
        np.ndarray: Filter coefficients (taps).
    """
    if target_fs >= original_fs:
        raise ValueError("Target sampling rate must be lower than original rate.")
    
    # Nyquist frequency of the target rate
    nyquist_target = target_fs / 2.0
    # Normalized cutoff frequency relative to original Nyquist
    # The filter must cut off at the new Nyquist to prevent aliasing
    normalized_cutoff = nyquist_target / (original_fs / 2.0)
    
    # Ensure normalized cutoff is < 1.0
    if normalized_cutoff >= 1.0:
        normalized_cutoff = 0.999
    
    # Design FIR filter using window method
    # firwin creates a low-pass filter by default
    taps = signal.firwin(
        num_taps,
        normalized_cutoff,
        window='hamming',
        pass_zero='lowpass'
    )
    
    return taps


def calculate_frequency_response(
    taps: np.ndarray,
    original_fs: int,
    frequencies: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the complex frequency response H(f) of the FIR filter.
    
    Args:
        taps: Filter coefficients.
        original_fs: Original sampling frequency.
        frequencies: Array of frequencies to evaluate. If None, defaults to 0 to fs/2.
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (frequencies, complex_response)
    """
    if frequencies is None:
        # Evaluate at sufficient resolution to find peak
        n_points = 4096
        frequencies = np.linspace(0, original_fs / 2, n_points)
    
    w, h = signal.freqz(taps, worN=frequencies, fs=original_fs)
    return w, h


def get_amplitude_correction_factor(
    taps: np.ndarray,
    original_fs: int,
    signal_peak_freq: float
) -> float:
    """
    Calculate the theoretical amplitude correction factor 1/|H(f_peak)|.
    
    This implements the "Filter Confound Control" strategy:
    Pre-scale the waveform amplitude to compensate for filter attenuation
    at the signal's peak frequency, isolating resolution effects from filter effects.
    
    Args:
        taps: Filter coefficients.
        original_fs: Original sampling frequency.
        signal_peak_freq: Frequency (Hz) where the signal has its peak amplitude.
        
    Returns:
        float: Correction factor (>= 1.0).
    """
    # Get frequency response
    freqs, h_response = calculate_frequency_response(taps, original_fs)
    
    # Find the index closest to the signal peak frequency
    idx = np.argmin(np.abs(freqs - signal_peak_freq))
    
    # Get magnitude of response at that frequency
    magnitude_at_peak = np.abs(h_response[idx])
    
    # Avoid division by zero
    if magnitude_at_peak < 1e-10:
        raise ValueError(
            f"Filter response at peak frequency {signal_peak_freq} Hz is effectively zero. "
            "Cannot compute correction factor. Check filter design or peak frequency."
        )
    
    # Return correction factor
    return 1.0 / magnitude_at_peak


def downsample_with_correction(
    waveform: np.ndarray,
    original_fs: int,
    target_fs: int,
    signal_peak_freq: float,
    num_taps: int = 101
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Downsample a waveform with anti-aliasing FIR filtering and amplitude correction.
    
    This function:
    1. Designs an FIR low-pass filter with cutoff at target_fs/2.
    2. Calculates the theoretical frequency response H(f).
    3. Computes the correction factor 1/|H(f_peak)|.
    4. Pre-scales the waveform amplitude.
    5. Applies the filter and decimates.
    
    Args:
        waveform: 1D numpy array of waveform strain.
        original_fs: Original sampling frequency (Hz).
        target_fs: Target sampling frequency (Hz).
        signal_peak_freq: Frequency (Hz) of the signal's peak amplitude.
        num_taps: Number of FIR filter taps.
        
    Returns:
        Tuple[np.ndarray, Dict]: (downsampled_waveform, metadata_dict)
    """
    if target_fs >= original_fs:
        raise ValueError("Target sampling rate must be lower than original rate.")
    
    if target_fs <= 0 or original_fs <= 0:
        raise ValueError("Sampling rates must be positive.")
        
    if len(waveform) == 0:
        raise ValueError("Waveform cannot be empty.")
    
    # Step 1: Design FIR filter
    taps = design_fir_filter(original_fs, target_fs, num_taps)
    
    # Step 2: Calculate correction factor
    correction_factor = get_amplitude_correction_factor(taps, original_fs, signal_peak_freq)
    
    # Step 3: Pre-scale waveform amplitude
    corrected_waveform = waveform * correction_factor
    
    # Step 4: Apply filter and decimate
    # decimate applies a low-pass filter (by default FIR) and then downsamples
    # We use the custom taps we designed, so we apply them explicitly
    # Use filtfilt for zero-phase filtering to avoid phase distortion
    # But for decimation, we need to handle the downsampling ratio
    
    decimation_factor = original_fs // target_fs
    
    if decimation_factor < 2:
        # If factor is 1, no downsampling needed (should be caught earlier)
        raise ValueError("Decimation factor must be at least 2.")
    
    # Apply the filter using filtfilt for zero-phase distortion
    # Ensure the number of taps is odd for filtfilt (it is by design)
    filtered_waveform = signal.filtfilt(taps, [1.0], corrected_waveform)
    
    # Decimate by taking every decimation_factor-th sample
    # We start from the center to align with the filter delay compensation of filtfilt
    # Actually, filtfilt has zero delay, so we can just take every Nth sample
    # But we need to be careful about the length
    downsampled = filtered_waveform[::decimation_factor]
    
    # Prepare metadata
    metadata = {
        "original_fs": original_fs,
        "target_fs": target_fs,
        "decimation_factor": decimation_factor,
        "num_taps": num_taps,
        "correction_factor": correction_factor,
        "signal_peak_freq": signal_peak_freq,
        "filter_response_magnitude_at_peak": 1.0 / correction_factor,
        "original_length": len(waveform),
        "downsampled_length": len(downsampled),
        "method": "FIR_lowpass_with_amplitude_correction"
    }
    
    return downsampled, metadata


def find_signal_peak_frequency(
    waveform: np.ndarray,
    fs: int,
    f_min: float = 20.0,
    f_max: Optional[float] = None
) -> float:
    """
    Find the frequency of the peak amplitude in the waveform's power spectrum.
    
    Args:
        waveform: 1D numpy array of waveform strain.
        fs: Sampling frequency.
        f_min: Minimum frequency to consider (Hz).
        f_max: Maximum frequency to consider (Hz). Defaults to Nyquist.
        
    Returns:
        float: Frequency (Hz) of the peak amplitude.
    """
    if f_max is None:
        f_max = fs / 2.0
        
    # Compute FFT
    n = len(waveform)
    fft_result = np.fft.rfft(waveform)
    freqs = np.fft.rfftfreq(n, 1.0/fs)
    
    # Power spectrum
    power = np.abs(fft_result) ** 2
    
    # Mask frequencies outside range
    mask = (freqs >= f_min) & (freqs <= f_max)
    
    if not np.any(mask):
        raise ValueError(f"No frequencies in range [{f_min}, {f_max}] found.")
    
    # Find peak in valid range
    peak_idx = np.argmax(power[mask])
    peak_freq = freqs[mask][peak_idx]
    
    return peak_freq


@profile_function
def process_waveform_file(
    input_path: str,
    output_dir: str,
    target_rates: Tuple[int, ...] = (4096, 2048, 1024, 512, 256),
    num_taps: int = 101
) -> Dict[str, Any]:
    """
    Process a single waveform file, downsample to multiple target rates, and save.
    
    Args:
        input_path: Path to input waveform file (JSON or NPZ).
        output_dir: Directory to save processed waveforms.
        target_rates: Tuple of target sampling rates (Hz).
        num_taps: Number of FIR filter taps.
        
    Returns:
        Dict: Summary of processing results.
    """
    # Load waveform
    if input_path.endswith('.npz'):
        data = np.load(input_path)
        waveform = data['waveform']
        meta = dict(data) if hasattr(data, 'keys') else {}
        # Extract metadata if stored in separate keys
        if 'metadata' in meta:
            meta = meta['metadata']
        fs = int(meta.get('fs', 4096))
        # Try to get peak frequency from metadata or compute it
        peak_freq = float(meta.get('peak_freq', find_signal_peak_frequency(waveform, fs)))
    elif input_path.endswith('.json'):
        with open(input_path, 'r') as f:
            data = json.load(f)
        waveform = np.array(data['waveform'])
        meta = data.get('metadata', {})
        fs = int(meta.get('fs', 4096))
        peak_freq = float(meta.get('peak_freq', find_signal_peak_frequency(waveform, fs)))
    else:
        raise ValueError(f"Unsupported input format: {input_path}")
    
    # Ensure output directory exists
    ensure_directories(output_dir)
    
    base_name = Path(input_path).stem
    results = {
        "input_file": input_path,
        "original_fs": fs,
        "signal_peak_freq": peak_freq,
        "processed_files": []
    }
    
    for target_fs in target_rates:
        if target_fs >= fs:
            # Skip if target is not lower
            continue
        
        try:
            # Downsample
            downsampled, metadata = downsample_with_correction(
                waveform, fs, target_fs, peak_freq, num_taps
            )
            
            # Save downsampled waveform
            output_filename = f"{base_name}_fs{target_fs}.npz"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save with metadata
            np.savez(
                output_path,
                waveform=downsampled,
                fs=target_fs,
                metadata=metadata
            )
            
            # Update checksum
            checksum = calculate_sha256(output_path)
            update_checksum(output_path, checksum)
            
            results["processed_files"].append({
                "output_file": output_path,
                "target_fs": target_fs,
                "output_length": len(downsampled),
                "checksum": checksum
            })
            
        except Exception as e:
            results["errors"].append({
                "target_fs": target_fs,
                "error": str(e)
            })
    
    return results


def main():
    """
    Main entry point for command-line execution.
    
    Usage:
        python -m src.downsample --input data/raw/waveform_001.npz --output data/processed/
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Downsample GW waveforms with anti-aliasing and amplitude correction.")
    parser.add_argument("--input", type=str, required=True, help="Path to input waveform file (.npz or .json)")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--rates", type=int, nargs="+", default=[2048, 1024, 512, 256], help="Target sampling rates")
    parser.add_argument("--taps", type=int, default=101, help="Number of FIR filter taps")
    
    args = parser.parse_args()
    
    print(f"Processing {args.input}...")
    results = process_waveform_file(
        args.input,
        args.output,
        tuple(args.rates),
        args.taps
    )
    
    print(f"Processing complete. Results: {json.dumps(results, indent=2)}")
    
    # Write results summary
    summary_path = os.path.join(args.output, f"{Path(args.input).stem}_downsample_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
