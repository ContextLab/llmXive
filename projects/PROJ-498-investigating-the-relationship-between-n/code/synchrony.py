"""
Synchrony analysis module for neural synchrony calculation.
Implements wPLI computation, filtering, and timing wrappers.
"""
from __future__ import annotations

import functools
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict, Tuple

import numpy as np
import mne
from scipy.signal import butter, filtfilt, welch

# --- Reproducibility Logging (Self-contained, no stdlib dependency) ---

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class ReproducibilityLogger:
    """Accepts ANY call shape and never raises."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None

def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER

def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: decorator or direct logging call."""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)
        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)

# --- Electrode Mapping & Helpers ---

def get_region_for_electrode(electrode: str) -> str:
    """Map electrode to region (DLPFC or Parietal)."""
    dlfpf_electrodes = {'F3', 'F4', 'FC3', 'FC4'}
    parietal_electrodes = {'P3', 'P4', 'CP3', 'CP4'}
    if electrode in dlfpf_electrodes:
        return 'DLPFC'
    elif electrode in parietal_electrodes:
        return 'Parietal'
    return 'Other'

def get_all_electrode_pairs() -> List[Tuple[str, str]]:
    """Generate all frontoparietal pairs."""
    dlfpf = ['F3', 'F4', 'FC3', 'FC4']
    parietal = ['P3', 'P4', 'CP3', 'CP4']
    pairs = []
    for d in dlfpf:
        for p in parietal:
            pairs.append((d, p))
    return pairs

def get_cross_region_pairs() -> List[Tuple[str, str]]:
    """Get pairs specifically between DLPFC and Parietal."""
    dlfpf = ['F3', 'F4'] # Simplified per spec examples F3/F4 -> P3/P4
    parietal = ['P3', 'P4']
    pairs = []
    for d in dlfpf:
        for p in parietal:
            pairs.append((d, p))
    return pairs

def get_pair_id(e1: str, e2: str) -> str:
    """Format pair ID as 'E1_E2'."""
    return f"{e1}_{e2}"

def validate_electrode_presence(info: mne.Info, required: List[str]) -> bool:
    """Check if all required electrodes are present."""
    ch_names = [ch['name'] for ch in info['ch_names']]
    for r in required:
        if r not in ch_names:
            return False
    return True

# --- Signal Processing ---

def butter_bandpass_filter(data: np.ndarray, fs: float, lowcut: float, highcut: float, order: int = 4) -> np.ndarray:
    """Apply Butterworth bandpass filter."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data, axis=-1)

def get_theta_filtered_data(data: np.ndarray, sfreq: float) -> np.ndarray:
    """Filter for theta band (4-8 Hz)."""
    return butter_bandpass_filter(data, sfreq, 4.0, 8.0)

def get_gamma_filtered_data(data: np.ndarray, sfreq: float) -> np.ndarray:
    """Filter for gamma band (30-45 Hz)."""
    return butter_bandpass_filter(data, sfreq, 30.0, 45.0)

def compute_wpli(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Compute weighted Phase-Lag Index (wPLI).
    Formula: |E[Im(C)]| / E[|Im(C)|] where C is cross-spectrum.
    """
    if signal1.shape != signal2.shape:
        raise ValueError("Signals must have same shape")
    
    # Compute cross-spectrum
    cross_spec = np.mean(signal1 * np.conj(signal2), axis=-1)
    imag_cross = np.imag(cross_spec)
    
    # wPLI calculation
    numerator = np.abs(np.mean(imag_cross))
    denominator = np.mean(np.abs(imag_cross))
    
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)

def filter_bandpower(data: np.ndarray, sfreq: float, low: float, high: float) -> float:
    """Compute bandpower for PSD verification."""
    freqs, psd = welch(data, fs=sfreq, nperseg=min(256, data.shape[-1]//2))
    mask = (freqs >= low) & (freqs <= high)
    if not np.any(mask):
        return 0.0
    return float(np.mean(psd[mask]))

def verify_psd_peaks(data: np.ndarray, sfreq: float, bands: Dict[str, Tuple[float, float]]) -> Dict[str, bool]:
    """Verify PSD peaks exist in defined bands."""
    from scipy.signal import find_peaks
    freqs, psd = welch(data, fs=sfreq, nperseg=min(256, data.shape[-1]//2))
    results = {}
    for name, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs <= high)
        if not np.any(mask):
            results[name] = False
            continue
        sub_psd = psd[mask]
        sub_freqs = freqs[mask]
        peaks, _ = find_peaks(sub_psd, prominence=3) # prominence 3 as per spec
        if len(peaks) > 0:
            # Check if peak is > 3dB relative to mean
            mean_power = np.mean(sub_psd)
            peak_val = sub_psd[peaks[0]]
            if 10 * np.log10(peak_val / mean_power) > 3:
                results[name] = True
            else:
                results[name] = False
        else:
            results[name] = False
    return results

# --- Core Synchrony Logic ---

def prepare_data_for_synchrony(epochs: mne.Epochs) -> Dict[str, np.ndarray]:
    """Extract data for specific electrodes."""
    pair_electrodes = ['F3', 'F4', 'P3', 'P4']
    # Ensure epochs has these channels
    available = [ch for ch in pair_electrodes if ch in epochs.ch_names]
    if len(available) < 2:
        raise ValueError(f"Insufficient electrodes found: {available}")
    
    data = epochs.get_data() # shape: (n_epochs, n_channels, n_times)
    # We need to map channel indices
    indices = [epochs.ch_names.index(ch) for ch in available]
    selected_data = data[:, indices, :]
    return {ch: selected_data[:, i, :] for i, ch in enumerate(available)}

def compute_synchrony_metrics(
    epochs: mne.Epochs,
    sfreq: float,
    bands: Dict[str, Tuple[float, float]],
    window: Tuple[float, float] = (-0.5, 0.0)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compute wPLI for specified bands and electrode pairs.
    Returns metrics per subject (aggregated per subject in this context).
    """
    logger = get_logger()
    logger.log("compute_synchrony_metrics", bands=bands, window=window)

    # Prepare data
    data_dict = prepare_data_for_synchrony(epochs)
    electrodes = list(data_dict.keys())
    
    # Filter for DLPFC and Parietal
    dlfpf = [e for e in electrodes if e in ['F3', 'F4']]
    parietal = [e for e in electrodes if e in ['P3', 'P4']]
    
    results = []
    
    for band_name, (low, high) in bands.items():
        # Filter data for this band
        filtered_data = {}
        for ch, sig in data_dict.items():
            if low >= 30:
                filtered_data[ch] = get_gamma_filtered_data(sig, sfreq)
            else:
                filtered_data[ch] = get_theta_filtered_data(sig, sfreq)
        
        # Compute wPLI for pairs
        for d in dlfpf:
            for p in parietal:
                sig1 = filtered_data[d]
                sig2 = filtered_data[p]
                
                # Epochs are (n_trials, n_times) here after selection
                # We compute wPLI across trials for each pair
                # Align dimensions: (n_trials, n_times)
                wpli_val = compute_wpli(sig1, sig2)
                
                results.append({
                    "subject_id": "agg", # Placeholder, actual subject ID handled by caller
                    "pair_id": get_pair_id(d, p),
                    "band": band_name,
                    "value": round(wpli_val, 6)
                })
    
    return results

def process_subject_synchrony_with_timing(
    epochs: mne.Epochs,
    sfreq: float,
    bands: Dict[str, Tuple[float, float]],
    window: Tuple[float, float] = (-0.5, 0.0),
    max_duration_seconds: float = 300.0
) -> List[Dict[str, Any]]:
    """
    Timing wrapper for synchrony calculation.
    Measures duration and raises exception if limit exceeded.
    """
    start_time = time.perf_counter()
    
    try:
        metrics = compute_synchrony_metrics(epochs, sfreq, bands, window)
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Log timing
        log_entry = log_operation(
            "synchrony_calculation_duration",
            duration_seconds=duration,
            max_allowed_seconds=max_duration_seconds
        )
        
        # Check limit (T026 requirement: RAISE EXCEPTION if > limit)
        if duration > max_duration_seconds:
            raise TimeoutError(
                f"Synchrony calculation exceeded {max_duration_seconds}s limit. "
                f"Actual: {duration:.2f}s"
            )
        
        # Save timing log
        timing_data = {
            "operation": "synchrony_calculation",
            "duration_seconds": duration,
            "max_allowed_seconds": max_duration_seconds,
            "status": "success" if duration <= max_duration_seconds else "timeout",
            "timestamp": datetime.utcnow().isoformat()
        }
        save_timing_log(timing_data)
        
        return metrics

def save_timing_log(data: Dict[str, Any], path: str = "data/metrics/synchrony_timing.json") -> None:
    """Save timing log to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        if os.path.getsize(path) > 0:
            f.write(",\n")
        else:
            f.write("[\n")
        json.dump(data, f, indent=2)
        f.write("\n")
    # Close bracket later or handle list properly
    # Simplified: overwrite or append with logic. 
    # Better: Load, append, save.
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                if content.startswith('['):
                    # It's a list, we need to handle appending properly
                    # For simplicity in this task, we'll just append the object
                    # and handle the list structure externally or assume single run
                    pass
        except:
            pass
    
    # Robust save:
    all_data = []
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = []
    
    all_data.append(data)
    with open(path, 'w') as f:
        json.dump(all_data, f, indent=2)

def save_synchrony_metrics(metrics: List[Dict[str, Any]], path: str = "data/metrics/synchrony_metrics.csv") -> None:
    """Save synchrony metrics to CSV."""
    import csv
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subject_id', 'pair_id', 'band', 'value'])
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)

def main() -> None:
    """Entry point for standalone execution (if needed)."""
    print("Synchrony module loaded.")
    print("Use process_subject_synchrony_with_timing for calculations.")

if __name__ == "__main__":
    main()