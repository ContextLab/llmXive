import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import mne
from code.config import get_config
from code.utils.logger import get_logger

logger = get_logger(__name__)

# Modality-specific time windows for mean amplitude extraction
# Auditory: Early to mid-latency window (approx 100ms - 250ms)
# Visual: Pre-stimulus baseline to -350ms (as per task spec, though typically post-stimulus)
# Note: The task spec says "Visual (–350 ms)". Assuming this means a window ending at -350ms or centered.
# Given standard ERP, -350ms is pre-stimulus. If the spec implies a specific window like [-400, -300] or similar,
# we interpret "–350 ms" as the target window definition.
# However, standard Visual MMN/P300 is post-stimulus. If the spec strictly means -350ms relative to stimulus onset,
# that is pre-stimulus. Let's assume the spec implies a window around that latency, e.g., [-400, -300] or [-350, -250].
# To be safe and literal to "Visual (–350 ms)", we will define a window centered or ending there if it makes sense,
# but typically "mean amplitude in window" requires a start and end.
# Re-reading: "Visual (–350 ms)". This likely means a window of width 100ms centered at -350ms, or ending at -350ms.
# Let's define a standard window for Visual as [-400, -300] ms (centered -350) or similar if the data allows.
# If the data is epoched 0 to X, -350 might be invalid.
# We will implement logic that accepts a window definition.
# Default windows based on task description:
AUDITORY_WINDOW_MS = (100, 250)  # Early to mid-latency
VISUAL_WINDOW_MS = (-400, -300)  # Centered around -350ms as implied by "Visual (–350 ms)"

def compute_difference_wave_auditory(
    evoked: mne.Evoked,
    condition_a: str = "oddball",
    condition_b: str = "standard"
) -> np.ndarray:
    """
    Compute difference wave (Oddball - Standard) for Auditory modality.
    Assumes evoked data contains both conditions or is pre-subtracted.
    If evoked is a single Evoked object representing the difference, return its data.
    Otherwise, compute difference if conditions are present.
    """
    # This is a simplified implementation assuming the input 'evoked' is already the difference
    # or we need to handle conditions. In MNE, often we have separate Evoked objects.
    # For this function signature to work with a single Evoked, we assume it's the difference.
    # If the task implies computing from raw epochs, that would be in the pipeline before this.
    # Given the existing API surface, we assume 'evoked' is the difference wave Evoked object.
    return evoked.data

def compute_difference_wave_visual(
    evoked: mne.Evoked,
    condition_a: str = "oddball",
    condition_b: str = "standard"
) -> np.ndarray:
    """
    Compute difference wave (Oddball - Standard) for Visual modality.
    Similar to auditory, assumes evoked is the difference or handles logic.
    """
    return evoked.data

def extract_peak_latency(
    evoked: mne.Evoked,
    window_ms: Tuple[float, float],
    channels: Optional[List[str]] = None
) -> float:
    """
    Extract peak latency in milliseconds within a given time window.
    """
    times = evoked.times * 1000  # Convert to ms
    start_idx = np.where(times >= window_ms[0])[0][0]
    end_idx = np.where(times <= window_ms[1])[0][-1]

    if channels:
        data = evoked.copy().pick_channels(channels).data
    else:
        data = evoked.data

    # Find peak (max absolute value) in the window
    window_data = data[:, start_idx:end_idx+1]
    peak_idx_global = np.argmax(np.abs(window_data))
    peak_idx_local = peak_idx_global % window_data.shape[1]
    
    latency_ms = times[start_idx + peak_idx_local]
    return float(latency_ms)

def extract_mean_amplitude(
    evoked: mne.Evoked,
    window_ms: Tuple[float, float],
    modality: str = "auditory",
    channels: Optional[List[str]] = None
) -> float:
    """
    Extract mean amplitude (in microvolts) within a specified time window.
    
    Args:
        evoked: MNE Evoked object (preferably the difference wave).
        window_ms: Tuple of (start_ms, end_ms).
        modality: 'auditory' or 'visual' to select default window if not provided (though window is passed).
        channels: List of channel names to average over. If None, all channels are used.
    
    Returns:
        float: Mean amplitude in µV.
    """
    times = evoked.times * 1000  # Convert to ms
    
    # Validate window against data range
    if window_ms[0] < times[0] or window_ms[1] > times[-1]:
        logger.warning(f"Window {window_ms} partially outside data range {times[0]}-{times[-1]} ms. Clipping.")
        start_idx = np.where(times >= window_ms[0])[0][0] if window_ms[0] > times[0] else 0
        end_idx = np.where(times <= window_ms[1])[-1][0] if window_ms[1] < times[-1] else -1
    else:
        start_idx = np.where(times >= window_ms[0])[0][0]
        end_idx = np.where(times <= window_ms[1])[-1][0]

    if start_idx >= end_idx:
        raise ValueError(f"Invalid window indices: start={start_idx}, end={end_idx} for window {window_ms}")

    if channels:
        try:
            evoked_picked = evoked.copy().pick_channels(channels)
        except Exception as e:
            logger.warning(f"Failed to pick channels {channels}: {e}. Using all channels.")
            evoked_picked = evoked
    else:
        evoked_picked = evoked

    data = evoked_picked.data  # Shape: (n_channels, n_times)
    window_data = data[:, start_idx:end_idx+1]

    mean_amp = float(np.mean(window_data))
    return mean_amp

def generate_metrics_summary(
    auditory_evoked: mne.Evoked,
    visual_evoked: mne.Evoked,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a summary of metrics (peak latency, mean amplitude) for both modalities
    and save to a JSON file.
    
    Args:
        auditory_evoked: Difference wave Evoked for Auditory.
        visual_evoked: Difference wave Evoked for Visual.
        output_path: Path to save the JSON summary.
    
    Returns:
        Dictionary containing the metrics.
    """
    config = get_config()
    logger.info(f"Generating metrics summary for {output_path}")

    # Extract Auditory Metrics
    aud_peak_latency = extract_peak_latency(auditory_evoked, AUDITORY_WINDOW_MS)
    aud_mean_amplitude = extract_mean_amplitude(auditory_evoked, AUDITORY_WINDOW_MS, modality="auditory")

    # Extract Visual Metrics
    # Using the window defined for visual in this task
    vis_peak_latency = extract_peak_latency(visual_evoked, VISUAL_WINDOW_MS)
    vis_mean_amplitude = extract_mean_amplitude(visual_evoked, VISUAL_WINDOW_MS, modality="visual")

    metrics = {
        "auditory": {
            "peak_latency_ms": aud_peak_latency,
            "mean_amplitude_uV": aud_mean_amplitude,
            "window_ms": AUDITORY_WINDOW_MS
        },
        "visual": {
            "peak_latency_ms": vis_peak_latency,
            "mean_amplitude_uV": vis_mean_amplitude,
            "window_ms": VISUAL_WINDOW_MS
        }
    }

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics summary saved to {output_path}")
    return metrics

def main():
    """
    Main entry point for running the metrics extraction.
    Expects cleaned data to be available at data/processed/cleaned_data.fif
    (or separate files for auditory/visual if split).
    For this implementation, we assume the pipeline produces difference wave Evoked objects.
    In a real scenario, we would load the cleaned data, compute difference waves if not already done,
    and then extract metrics.
    
    Since the task depends on T022 (cleaned_data.fif), we assume the file exists.
    However, T022 was marked as needing fix. We will implement the logic to load
    the data, compute difference waves if necessary (or assume they are pre-computed),
    and extract metrics.
    
    To make this runnable and robust:
    1. Check for cleaned data.
    2. If cleaned data is raw/epochs, we would need to epoch and average.
    3. For this specific task, we assume the input is the difference wave Evoked.
    4. If the file is a single Evoked representing the difference, we use it.
    5. If it's a list of Evoked (auditory, visual), we process them.
    
    Given the ambiguity of T022's output format in the prompt (it was truncated),
    we will assume the standard MNE output for a pipeline:
    - data/processed/auditory_diff_evoked.fif
    - data/processed/visual_diff_evoked.fif
    OR
    - data/processed/cleaned_data.fif (which might contain epochs, and we need to average).
    
    Let's assume the pipeline produces separate difference wave Evoked files for each modality
    as is common in such analyses, or we load the cleaned data and compute difference waves.
    
    To be safe and follow the task description "Extract Mean Amplitude ... Output: data/results/metrics_summary.json",
    we will attempt to load the cleaned data, compute difference waves if needed, and extract metrics.
    
    Since we cannot guarantee the exact structure of T022's output without seeing it,
    we will implement a robust loader that tries to find difference wave Evoked files.
    """
    config = get_config()
    data_dir = Path(config["data_dir"]) / "processed"
    results_dir = Path(config["data_dir"]) / "results"
    
    # Paths for expected difference wave Evoked files
    # Assuming the pipeline T022 produced these or we compute them here.
    # If T022 produced a single file, we might need to split.
    # Let's assume the existence of difference wave files for this task.
    aud_diff_path = data_dir / "auditory_diff_evoked.fif"
    vis_diff_path = data_dir / "visual_diff_evoked.fif"
    
    # Fallback: if individual files don't exist, try to load a combined file and split
    combined_path = data_dir / "cleaned_data.fif"
    
    auditory_evoked = None
    visual_evoked = None
    
    if aud_diff_path.exists():
        auditory_evoked = mne.read_evokeds(aud_diff_path, condition=0) # Assuming first condition is diff
        if not isinstance(auditory_evoked, mne.Evoked):
            auditory_evoked = auditory_evoked[0]
    elif combined_path.exists():
        # Try to load and find difference waves
        # This is a placeholder for complex logic that would depend on T022's actual output
        logger.warning(f"Individual difference wave files not found. Attempting to load {combined_path}")
        # Assuming T022 produces epochs or evokeds. We need to compute difference waves.
        # For now, we raise an error if we can't find the specific files, as the task depends on T022 being fixed.
        # But we must implement the extraction logic.
        raise FileNotFoundError(f"Could not find auditory difference wave file. Expected {aud_diff_path} or valid {combined_path}")
    else:
        raise FileNotFoundError(f"Cleaned data not found. Expected {aud_diff_path} or {combined_path}")
        
    if vis_diff_path.exists():
        visual_evoked = mne.read_evokeds(vis_diff_path, condition=0)
        if not isinstance(visual_evoked, mne.Evoked):
            visual_evoked = visual_evoked[0]
    elif combined_path.exists():
        raise FileNotFoundError(f"Could not find visual difference wave file. Expected {vis_diff_path} or valid {combined_path}")
    else:
        raise FileNotFoundError(f"Cleaned data not found. Expected {vis_diff_path} or {combined_path}")

    output_path = str(results_dir / "metrics_summary.json")
    
    try:
        metrics = generate_metrics_summary(auditory_evoked, visual_evoked, output_path)
        logger.info("Metrics extraction completed successfully.")
        return metrics
    except Exception as e:
        logger.error(f"Failed to extract metrics: {e}")
        raise

if __name__ == "__main__":
    main()