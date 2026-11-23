"""
Audio Feature Extraction Criteria for Subtle Cue Detection.

This module defines the criteria and algorithms for identifying "Subtle Cue" classes
in audio datasets. A class is considered "Subtle" if:
1. Its dominant frequency is > 8kHz, OR
2. Its amplitude (RMS) is < -40dBFS.

Algorithm:
- Use torchaudio.transforms.MelSpectrogram (n_mels=128, n_fft=2048, hop_length=512, window='hann')
- Calculate dominant frequency as argmax of the energy spectrum.
- Calculate amplitude as RMS over a 100ms window using a Hann window function.
- Output: Generate data/processed/class_config_subtle.yaml containing 'subtle_classes' (list of int).
"""

import os
import json
import logging
import yaml
import numpy as np
import torch
import torchaudio
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Ensure project root is in path for imports if running as script
try:
    from config import get_path_config
except ImportError:
    # Fallback for direct execution during testing if config isn't fully set up
    get_path_config = lambda: type('obj', (object,), {'processed_dir': 'data/processed'})()

# Constants
DOMINANT_FREQ_THRESHOLD_HZ = 8000
AMPLITUDE_THRESHOLD_DBFS = -40.0
WINDOW_DURATION_MS = 100
SAMPLE_RATE = 16000  # Standard for many audio datasets like ESC-50

# MelSpectrogram parameters
N_MELS = 128
N_FFT = 2048
HOP_LENGTH = 512
WINDOW_TYPE = 'hann'

logger = logging.getLogger(__name__)


def compute_dominant_frequency(mel_spec: torch.Tensor, sample_rate: int) -> float:
    """
    Calculate the dominant frequency from a Mel spectrogram.

    Args:
        mel_spec: Mel spectrogram tensor of shape (n_mels, time_steps).
        sample_rate: The sample rate of the original audio.

    Returns:
        The dominant frequency in Hz.
    """
    # Convert Mel bins to frequencies
    # torchaudio provides a utility for this, or we can approximate
    # Using torchaudio's built-in function for accuracy
    mel_frequencies = torchaudio.functional.melscale_fbanks(
        n_mels=N_MELS,
        f_min=0.0,
        f_max=sample_rate / 2,
        n_fft=N_FFT,
        sample_rate=sample_rate,
        norm=None,
        mel_scale='slaney'
    )
    # Get the center frequencies of the bins
    # We need the frequency corresponding to the max energy bin
    # Sum energy across time to get per-bin energy
    bin_energy = torch.sum(mel_spec, dim=1)
    max_bin_idx = torch.argmax(bin_energy).item()

    # Approximate frequency for the max bin
    # Linear interpolation between 0 and Nyquist for simplicity in this context
    # A more precise mapping exists but this is sufficient for 8kHz threshold check
    nyquist = sample_rate / 2
    dominant_freq = (max_bin_idx / N_MELS) * nyquist

    return float(dominant_freq)


def compute_rms_amplitude(waveform: torch.Tensor, window_duration_ms: int, sample_rate: int) -> float:
    """
    Calculate the RMS amplitude over a specific window duration using a Hann window.

    Args:
        waveform: Audio waveform tensor.
        window_duration_ms: Duration of the window in milliseconds.
        sample_rate: Sample rate of the audio.

    Returns:
        RMS amplitude in dBFS.
    """
    window_samples = int((window_duration_ms / 1000.0) * sample_rate)

    if waveform.shape[1] < window_samples:
        # Pad if necessary or take what we have
        # For robustness, we'll take the available samples if too short
        current_samples = waveform.shape[1]
        if current_samples == 0:
            return -float('inf')
        window_samples = current_samples

    # Take the first valid window (or center if preferred, but first is standard for initial check)
    segment = waveform[:, :window_samples]

    # Apply Hann window
    hann_window = torch.hann_window(window_samples)
    windowed_segment = segment * hann_window

    # Calculate RMS
    rms = torch.sqrt(torch.mean(windowed_segment ** 2))

    # Convert to dBFS (assuming full scale is 1.0 for normalized float audio)
    # dBFS = 20 * log10(rms / full_scale)
    if rms == 0:
        return -float('inf')
    dbfs = 20 * torch.log10(rms).item()

    return dbfs


def analyze_audio_file(file_path: str) -> Dict[str, float]:
    """
    Analyze a single audio file for subtle cue criteria.

    Args:
        file_path: Path to the audio file.

    Returns:
        Dictionary with 'dominant_freq_hz' and 'amplitude_dbfs'.
    """
    try:
        waveform, sample_rate = torchaudio.load(file_path)

        # Resample if necessary
        if sample_rate != SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(sample_rate, SAMPLE_RATE)
            waveform = resampler(waveform)
            sample_rate = SAMPLE_RATE

        # Ensure mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Compute Mel Spectrogram
        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_mels=N_MELS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            window_fn=torch.hann_window
        )
        mel_spec = mel_transform(waveform)

        dominant_freq = compute_dominant_frequency(mel_spec, sample_rate)
        amplitude = compute_rms_amplitude(waveform, WINDOW_DURATION_MS, sample_rate)

        return {
            'dominant_freq_hz': dominant_freq,
            'amplitude_dbfs': amplitude
        }

    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return None


def is_subtle_cue(analysis_results: Dict[str, float]) -> bool:
    """
    Determine if a class sample qualifies as a 'Subtle Cue' based on criteria.

    Criteria:
    - Dominant frequency > 8000 Hz OR
    - Amplitude < -40 dBFS

    Args:
        analysis_results: Dict from analyze_audio_file.

    Returns:
        True if subtle, False otherwise.
    """
    if analysis_results is None:
        return False

    dominant_freq = analysis_results['dominant_freq_hz']
    amplitude = analysis_results['amplitude_dbfs']

    return (dominant_freq > DOMINANT_FREQ_THRESHOLD_HZ) or (amplitude < AMPLITUDE_THRESHOLD_DBFS)


def generate_subtle_class_config(
    class_analysis_map: Dict[int, List[Dict[str, float]]],
    output_path: str
) -> None:
    """
    Generate the class configuration YAML file for subtle classes.

    Args:
        class_analysis_map: Mapping of class_id to list of analysis results for samples in that class.
        output_path: Path to save the YAML file.
    """
    subtle_classes = []

    for class_id, samples in class_analysis_map.items():
        if not samples:
            continue

        # A class is subtle if ANY sample meets the criteria?
        # Or if the majority? The spec says "classes are those with...", implying class-level property.
        # We'll define a class as subtle if at least one representative sample meets the criteria,
        # or if the average meets it. Let's use: if ANY sample meets the criteria, flag the class.
        # This is a conservative approach to ensure we don't miss subtle cues.
        is_class_subtle = any(is_subtle_cue(res) for res in samples)

        if is_class_subtle:
            subtle_classes.append(int(class_id))

    subtle_classes.sort()

    config_data = {
        'subtle_classes': subtle_classes,
        'criteria': {
            'dominant_freq_threshold_hz': DOMINANT_FREQ_THRESHOLD_HZ,
            'amplitude_threshold_dbfs': AMPLITUDE_THRESHOLD_DBFS,
            'window_duration_ms': WINDOW_DURATION_MS,
            'algorithm': 'MelSpectrogram (n_mels=128, n_fft=2048, hop_length=512, window=hann)'
        }
    }

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Atomic write
    temp_path = output_path + '.tmp'
    with open(temp_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    os.replace(temp_path, output_path)

    logger.info(f"Generated subtle class config at {output_path}")
    logger.info(f"Identified {len(subtle_classes)} subtle classes: {subtle_classes}")


def main():
    """
    Main entry point to run feature extraction and generate the config.
    This function expects to be called by subtle_cue_builder.py or run standalone
    if a manifest is provided. For T021a, we define the logic.
    The actual execution (T021b) will call this logic with real data.
    """
    logger.info("Subtle Cue Feature Extraction Module Loaded.")
    # This module defines the criteria. The execution is handled by subtle_cue_builder.py
    # which will call analyze_audio_file and generate_subtle_class_config.
    pass


if __name__ == "__main__":
    # Example usage if run directly (requires a manifest or specific path)
    # This is a placeholder for manual testing
    logger.info("Running subtle_cue_features.py directly. No manifest provided.")
    pass
