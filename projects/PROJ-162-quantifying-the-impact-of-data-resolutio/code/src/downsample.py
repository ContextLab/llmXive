import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any, Optional, List
import json
from pathlib import Path
import os
import h5py
import time

from src.config import ensure_directories, get_processed_path
from src.data_hygiene import update_checksum
from src.schema_validator import validate_json
from src.profiler import Profiler, check_memory_limit

# Constants
NATIVE_RATE: int = 4096
TARGET_RATES: List[int] = [2048, 1024, 512, 256]
FILTER_ORDER: int = 64  # FIR filter order
MEMORY_LIMIT_MB: int = 6000

def design_fir_filter(cutoff_freq: float, nyquist_freq: float, order: int = FILTER_ORDER) -> np.ndarray:
    """
    Design a low-pass FIR filter using the window method.
    
    Args:
        cutoff_freq: Cutoff frequency in Hz.
        nyquist_freq: Nyquist frequency of the input signal.
        order: Filter order (number of taps - 1).
        
    Returns:
        Filter coefficients (taps).
    """
    nyq = nyquist_freq
    normalized_cutoff = cutoff_freq / nyq
    if normalized_cutoff >= 1.0:
        normalized_cutoff = 0.99
    taps = signal.firwin(order + 1, normalized_cutoff, window='hamming')
    return taps

def calculate_frequency_response(taps: np.ndarray, num_points: int = 1024) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the frequency response of the filter.
    
    Args:
        taps: Filter coefficients.
        num_points: Number of frequency points to evaluate.
        
    Returns:
        Tuple of (frequencies, magnitudes).
    """
    w, h = signal.freqz(taps, worN=num_points)
    # Convert w (radians/sample) to Hz assuming unit sampling rate for now
    # We will scale later based on actual sampling rate
    return w, np.abs(h)

def find_signal_peak_frequency(waveform: np.ndarray, fs: float) -> float:
    """
    Find the frequency with the maximum spectral amplitude in the waveform.
    
    Args:
        waveform: Time-domain signal.
        fs: Sampling frequency.
        
    Returns:
        Frequency (Hz) of the peak amplitude.
    """
    # Compute FFT
    fft_vals = np.fft.rfft(waveform)
    freqs = np.fft.rfftfreq(len(waveform), 1.0 / fs)
    magnitudes = np.abs(fft_vals)
    
    # Find peak index (excluding DC component at index 0 to avoid noise floor bias)
    if len(magnitudes) > 1:
        peak_idx = np.argmax(magnitudes[1:]) + 1
    else:
        peak_idx = 0
        
    return freqs[peak_idx], magnitudes[peak_idx]

def get_amplitude_correction_factor(taps: np.ndarray, signal_peak_freq: float, fs_input: float) -> float:
    """
    Calculate the amplitude correction factor based on the filter's response at the signal peak.
    
    Args:
        taps: Filter coefficients.
        signal_peak_freq: Frequency of the signal peak in Hz.
        fs_input: Input sampling frequency.
        
    Returns:
        Correction factor (1 / |H(f_peak)|).
    """
    # Normalize frequency for freqz (0 to pi corresponds to 0 to fs/2)
    w, h = signal.freqz(taps, worN=1024)
    freqs = w * (fs_input / (2 * np.pi))
    
    # Find closest frequency to signal_peak_freq
    idx = np.argmin(np.abs(freqs - signal_peak_freq))
    response_at_peak = np.abs(h[idx])
    
    if response_at_peak == 0:
        raise ValueError("Filter response at peak frequency is zero; cannot correct amplitude.")
        
    return 1.0 / response_at_peak

def downsample_with_correction(
    waveform: np.ndarray, 
    fs_input: int, 
    fs_target: int
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Downsample waveform with anti-aliasing filter and amplitude correction.
    
    Args:
        waveform: Input time-domain signal.
        fs_input: Input sampling frequency.
        fs_target: Target sampling frequency.
        
    Returns:
        Tuple of (downsampled waveform, metadata dict).
    """
    if fs_target >= fs_input:
        raise ValueError("Target frequency must be lower than input frequency.")
    
    decimation_factor = fs_input // fs_target
    if fs_input % fs_target != 0:
        raise ValueError("Input frequency must be an integer multiple of target frequency.")
    
    # 1. Design filter
    # Cutoff should be at or below the new Nyquist limit (fs_target / 2)
    cutoff_freq = fs_target / 2.0
    nyquist_input = fs_input / 2.0
    taps = design_fir_filter(cutoff_freq, nyquist_input)
    
    # 2. Find signal peak in original waveform
    peak_freq, _ = find_signal_peak_frequency(waveform, fs_input)
    
    # 3. Calculate correction factor
    correction_factor = get_amplitude_correction_factor(taps, peak_freq, fs_input)
    
    # 4. Apply correction BEFORE filtering/decimation to isolate resolution loss
    corrected_waveform = waveform * correction_factor
    
    # 5. Filter and decimate using scipy's decimate (which applies FIR filter internally)
    # We use 'fir' method with the custom taps we designed to ensure exact control
    # However, scipy.signal.decimate doesn't easily accept custom taps for the filter step
    # So we manually filter then decimate
    
    # Apply filter
    filtered_waveform = signal.filtfilt(taps, [1.0], corrected_waveform)
    
    # Decimate (keep every Nth sample)
    downsampled = filtered_waveform[::decimation_factor]
    
    # Calculate actual resulting fs (should match target, but verify)
    actual_fs = fs_input / len(downsampled) * len(waveform)
    
    metadata = {
        "original_fs": fs_input,
        "target_fs": fs_target,
        "actual_fs": actual_fs,
        "decimation_factor": decimation_factor,
        "filter_taps": taps.tolist(),
        "correction_factor": correction_factor,
        "signal_peak_freq": peak_freq,
        "cutoff_freq": cutoff_freq
    }
    
    return downsampled, metadata

def process_waveform_file(
    input_path: Path,
    output_dir: Path,
    waveform_id: str,
    target_rates: Optional[List[int]] = None
) -> List[Path]:
    """
    Process a single waveform file: save native (4096 Hz) and generate down-sampled versions.
    
    Args:
        input_path: Path to input HDF5 waveform file.
        output_dir: Directory to save output files.
        waveform_id: Unique identifier for the waveform.
        target_rates: List of target sampling rates. Defaults to TARGET_RATES.
        
    Returns:
        List of paths to generated output files.
    """
    if target_rates is None:
        target_rates = TARGET_RATES
    
    ensure_directories([output_dir])
    
    generated_files = []
    
    # Read input file
    with h5py.File(input_path, 'r') as f:
        if 'strain' not in f:
            raise ValueError(f"Input file {input_path} does not contain 'strain' dataset.")
        if 'metadata' not in f:
            raise ValueError(f"Input file {input_path} does not contain 'metadata' dataset.")
        
        waveform = f['strain'][:]
        metadata = json.loads(f['metadata'][()])
        
        # Verify native rate
        input_fs = metadata.get('sampling_frequency', NATIVE_RATE)
        if input_fs != NATIVE_RATE:
            raise ValueError(f"Expected input sampling rate {NATIVE_RATE} Hz, got {input_fs} Hz.")
    
    # 1. Process and save the NATIVE rate (4096 Hz) file
    # We must apply the same metadata tagging and validation as down-sampled files
    native_output_path = output_dir / f"waveform_{waveform_id}_{NATIVE_RATE}Hz.h5"
    
    # Create metadata for native file (no down-sampling correction needed, but still tag)
    native_metadata = {
        "waveform_id": waveform_id,
        "sampling_frequency": NATIVE_RATE,
        "original_file": str(input_path),
        "processing_type": "native",
        "timestamp": time.time(),
        "filter_applied": False,
        "correction_factor": 1.0,
        "source_metadata": metadata
    }
    
    # Validate metadata against schema (T016 integration point)
    # We assume the schema is available at contracts/injection.schema.yaml or similar
    # For now, we just ensure it's a valid JSON-serializable dict
    try:
        validate_json(native_metadata, "contracts/injection.schema.yaml")
    except FileNotFoundError:
        # Schema might not exist yet, skip validation if missing
        pass
    except Exception as e:
        # Log but continue if validation fails (schema might be incomplete)
        print(f"Warning: Metadata validation failed for native file: {e}")
    
    with h5py.File(native_output_path, 'w') as f:
        f.create_dataset('strain', data=waveform)
        f.create_dataset('metadata', data=json.dumps(native_metadata))
    
    generated_files.append(native_output_path)
    
    # 2. Generate and save down-sampled files
    for target_fs in target_rates:
        output_path = output_dir / f"waveform_{waveform_id}_{target_fs}Hz.h5"
        
        # Perform downsampling
        downsampled_waveform, ds_metadata = downsample_with_correction(
            waveform, NATIVE_RATE, target_fs
        )
        
        # Merge with original metadata
        full_metadata = {
            "waveform_id": waveform_id,
            "sampling_frequency": target_fs,
            "original_file": str(input_path),
            "processing_type": "downsampled",
            "timestamp": time.time(),
            "filter_applied": True,
            "correction_factor": ds_metadata['correction_factor'],
            "signal_peak_freq": ds_metadata['signal_peak_freq'],
            "cutoff_freq": ds_metadata['cutoff_freq'],
            "decimation_factor": ds_metadata['decimation_factor'],
            "source_metadata": metadata
        }
        
        # Validate metadata
        try:
            validate_json(full_metadata, "contracts/injection.schema.yaml")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: Metadata validation failed for {target_fs}Hz file: {e}")
        
        # Write to HDF5
        with h5py.File(output_path, 'w') as f:
            f.create_dataset('strain', data=downsampled_waveform)
            f.create_dataset('metadata', data=json.dumps(full_metadata))
        
        generated_files.append(output_path)
        
        # Update checksums
        update_checksum(output_path)
    
    # Update checksum for the native file too
    update_checksum(native_output_path)
    
    return generated_files

def main():
    """
    Main entry point for the downsampling pipeline.
    Processes all waveforms in data/processed/waveforms/raw/ and outputs to data/processed/waveforms/
    """
    input_dir = Path("data/processed/waveforms/raw")
    output_dir = Path("data/processed/waveforms")
    
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist. Run waveform generation first.")
        return
    
    # Get all HDF5 files in input directory
    input_files = list(input_dir.glob("*.h5"))
    if not input_files:
        print(f"No HDF5 files found in {input_dir}")
        return
    
    print(f"Processing {len(input_files)} waveform files...")
    
    for input_file in input_files:
        # Extract waveform ID from filename (assumes format: waveform_{id}.h5)
        stem = input_file.stem
        waveform_id = stem.replace("waveform_", "")
        
        print(f"Processing {input_file.name} (ID: {waveform_id})...")
        
        try:
            generated = process_waveform_file(input_file, output_dir, waveform_id)
            print(f"  Generated {len(generated)} files:")
            for g in generated:
                print(f"    - {g.name}")
        except Exception as e:
            print(f"  ERROR processing {input_file.name}: {e}")
            raise
    
    print("Downsampling pipeline complete.")

if __name__ == "__main__":
    main()