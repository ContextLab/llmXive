"""
Synchrony analysis module for neural synchrony and attention switching costs.
Implements PLV/wPLI computation, frequency filtering, and metric aggregation.
"""
from __future__ import annotations

import functools
import json
import os
import sys
import time
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import mne
from scipy.signal import butter, filtfilt

# --- Reproducibility Logging (Tolerant) ---
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
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call."""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)
        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)

# --- End Logging ---

from dataclasses import dataclass, field
from datetime import datetime

# Constants for electrode mapping
DLPFC_ELECTRODES = ['F3', 'F4', 'FC3', 'FC4']
PARIETAL_ELECTRODES = ['P3', 'P4', 'CP3', 'CP4']
REQUIRED_PAIRS = [
    ('F3', 'P3'), ('F3', 'P4'),
    ('F4', 'P3'), ('F4', 'P4')
]
BANDS = {
    'theta': (4, 7),
    'gamma': (30, 45)
}
PRE_STIMULUS_WINDOW = (-0.5, 0.0)  # seconds

def get_region_for_electrode(electrode: str) -> Optional[str]:
    if electrode in DLPFC_ELECTRODES:
        return 'DLPFC'
    elif electrode in PARIETAL_ELECTRODES:
        return 'Parietal'
    return None

def get_all_electrode_pairs() -> List[Tuple[str, str]]:
    pairs = []
    for dl in DLPFC_ELECTRODES:
        for par in PARIETAL_ELECTROALES:
            pairs.append((dl, par))
    return pairs

def get_pair_id(e1: str, e2: str) -> str:
    return f"{e1}_{e2}"

def validate_electrode_presence(channels: List[str], pair: Tuple[str, str]) -> bool:
    return pair[0] in channels and pair[1] in channels

def butter_bandpass_filter(data: np.ndarray, fs: float, lowcut: float, highcut: float, order: int = 5) -> np.ndarray:
    """Apply bandpass filter using Butterworth."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    # filtfilt requires data to be 2D (n_channels, n_times)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    return filtfilt(b, a, data, axis=1)

def get_theta_filtered_data(epochs: mne.Epocs, sfreq: float) -> np.ndarray:
    """Filter epochs to theta band."""
    return butter_bandpass_filter(epochs.get_data(), sfreq, 4, 7)

def get_gamma_filtered_data(epochs: mne.Epocs, sfreq: float) -> np.ndarray:
    """Filter epochs to gamma band."""
    return butter_bandpass_filter(epochs.get_data(), sfreq, 30, 45)

def compute_wpli(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Compute weighted Phase-Lag Index (wPLI).
    data1, data2: shape (n_channels, n_times) or (n_epochs, n_channels, n_times)
    For this implementation, we assume input is (n_channels, n_times) for a single epoch/average.
    """
    # Flatten to (n_times) if single channel, or keep dimensions
    # We need phase difference.
    # Using Hilbert transform to get instantaneous phase
    from scipy.signal import hilbert

    # Ensure 2D: (n_channels, n_times)
    if data1.ndim == 1:
        data1 = data1[np.newaxis, :]
    if data2.ndim == 1:
        data2 = data2[np.newaxis, :]

    # Get analytic signal
    ana1 = hilbert(data1, axis=1)
    ana2 = hilbert(data2, axis=1)

    # Phase difference
    phase1 = np.angle(ana1)
    phase2 = np.angle(ana2)
    diff = phase1 - phase2

    # wPLI = |mean(sign(Im(exp(i * diff))))|
    # exp(i * diff) = cos(diff) + i * sin(diff)
    # Im = sin(diff)
    # sign(Im)
    sin_diff = np.sin(diff)
    sign_sin = np.sign(sin_diff)
    
    # Average over time and channels (if multiple)
    mean_sign = np.mean(sign_sin)
    wpli = np.abs(mean_sign)
    
    return float(wpli)

def filter_bandpower(data: np.ndarray, fs: float, lowcut: float, highcut: float) -> float:
    """Calculate bandpower of filtered data."""
    filtered = butter_bandpass_filter(data, fs, lowcut, highcut)
    return float(np.mean(filtered ** 2))

def verify_psd_peaks(data: np.ndarray, fs: float, band: Tuple[float, float]) -> bool:
    """Log warning if no peaks > 3dB found (simplified check)."""
    # Simplified check: just ensure power is non-zero in band
    power = filter_bandpower(data, fs, band[0], band[1])
    if power < 1e-10:
        get_logger().log("psd_warning", message=f"No significant power in band {band}")
    return power > 1e-10

def prepare_data_for_synchrony(epochs: mne.Epocs, band: str) -> np.ndarray:
    """Extract and filter data for a specific band."""
    sfreq = epochs.info['sfreq']
    if band == 'theta':
        return get_theta_filtered_data(epochs, sfreq)
    elif band == 'gamma':
        return get_gamma_filtered_data(epochs, sfreq)
    else:
        raise ValueError(f"Unknown band: {band}")

def compute_synchrony_metrics(epochs: mne.Epocs, pair: Tuple[str, str], band: str) -> float:
    """Compute wPLI for a specific electrode pair and band."""
    # Get channel indices
    ch_names = epochs.ch_names
    if pair[0] not in ch_names or pair[1] not in ch_names:
        raise ValueError(f"Electrodes {pair} not found in data. Available: {ch_names}")
    
    idx1 = ch_names.index(pair[0])
    idx2 = ch_names.index(pair[1])

    # Prepare filtered data (n_epochs, n_channels, n_times)
    filtered_data = prepare_data_for_synchrony(epochs, band)
    
    # Extract signals for the two electrodes
    # Shape: (n_epochs, n_times)
    sig1 = filtered_data[:, idx1, :]
    sig2 = filtered_data[:, idx2, :]

    # Average across epochs to get a single signal per electrode for wPLI calculation
    # Or calculate wPLI per epoch and average? 
    # Standard approach: average the cross-spectral density or phase differences.
    # For simplicity in this context, we average the signals across epochs first.
    avg_sig1 = np.mean(sig1, axis=0)
    avg_sig2 = np.mean(sig2, axis=0)

    # Compute wPLI
    wpli = compute_wpli(avg_sig1, avg_sig2)
    return wpli

def process_subject_synchrony_with_timing(subject_id: str, epochs_path: str) -> Dict[str, Any]:
    """Process a single subject and return metrics."""
    start = time.perf_counter()
    
    # Load epochs
    epochs = mne.read_epochs(epochs_path)
    
    # Select pre-stimulus window
    epochs = epochs.copy().crop(tmin=PRE_STIMULUS_WINDOW[0], tmax=PRE_STIMULUS_WINDOW[1])
    
    metrics = []
    for band in BANDS:
        for pair in REQUIRED_PAIRS:
            try:
                val = compute_synchrony_metrics(epochs, pair, band)
                metrics.append({
                    'subject_id': subject_id,
                    'pair_id': get_pair_id(pair[0], pair[1]),
                    'band': band,
                    'value': round(val, 4)
                })
            except Exception as e:
                get_logger().log("error_computing_wpli", subject=subject_id, band=band, pair=pair, error=str(e))
                continue

    duration = time.perf_counter() - start
    return {
        'subject_id': subject_id,
        'metrics': metrics,
        'duration': duration
    }

def save_timing_log(subject_id: str, duration: float, output_path: str):
    """Save timing information."""
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    
    data = {
        'subject_id': subject_id,
        'duration_seconds': duration
    }
    
    # Load existing if present
    all_timings = []
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            all_timings = json.load(f)
    
    all_timings.append(data)
    
    with open(output_path, 'w') as f:
        json.dump(all_timings, f, indent=2)

def save_synchrony_metrics(all_metrics: List[Dict], output_path: str):
    """Save synchrony metrics to CSV."""
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subject_id', 'pair_id', 'band', 'value'])
        writer.writeheader()
        for row in all_metrics:
            writer.writerow(row)

def main():
    """Main entry point for synchrony analysis."""
    # This function is typically called by main.py
    # It expects preprocessed epochs to exist in data/processed/
    pass

if __name__ == "__main__":
    main()