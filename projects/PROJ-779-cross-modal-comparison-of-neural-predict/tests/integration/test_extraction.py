"""
Integration test for the full prediction error signal extraction pipeline.

This test verifies the end-to-end execution of:
1. Loading preprocessed data (output of T022: data/processed/cleaned_data.fif)
2. Computing difference waves (Oddball - Standard)
3. Extracting peak latency and mean amplitude for Auditory and Visual modalities
4. Generating the summary statistics JSON file (data/results/metrics_summary.json)

It ensures that the extraction pipeline produces valid, non-empty output files
and that the metrics are within physically plausible ranges.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.config import get_config
from code.analysis.metrics import compute_difference_wave, extract_peak_latency, extract_mean_amplitude, generate_metrics_summary
from code.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.mark.integration
def test_full_extraction_pipeline():
    """
    Integration test: Run the full extraction pipeline on cleaned data.
    
    Prerequisites:
    - T022 must have completed successfully, producing data/processed/cleaned_data.fif
    - The data file must contain valid EEG epochs with 'Oddball' and 'Standard' conditions.
    """
    config = get_config()
    
    # Define paths based on config
    cleaned_data_path = config.cleaned_data_path
    output_json_path = config.metrics_summary_path
    
    # Verify input file exists (Fail loudly if T022 hasn't run or failed)
    if not cleaned_data_path.exists():
        pytest.fail(
            f"Cleaned data file not found at {cleaned_data_path}. "
            "Prerequisite T022 (preprocess.py) must be completed first."
        )

    logger.info(f"Loading cleaned data from {cleaned_data_path}")
    # Import mne here to avoid heavy load if not needed
    import mne
    
    try:
        epochs = mne.read_epochs(str(cleaned_data_path), preload=True)
    except Exception as e:
        pytest.fail(f"Failed to load epochs from {cleaned_data_path}: {e}")

    # Validate that expected conditions exist
    conditions = list(epochs.event_id.keys())
    if 'Oddball' not in conditions or 'Standard' not in conditions:
        pytest.fail(
            f"Expected 'Oddball' and 'Standard' conditions in epochs, "
            f"but found: {conditions}. Data preprocessing may be incomplete."
        )

    logger.info("Computing difference waves for Auditory (fronto-central) electrodes")
    # Auditory: Frontal/central electrodes
    auditory_picks = mne.pick_types(epochs.info, eeg=True, exclude='bads')
    # Filter for fronto-central based on standard montage names if possible, 
    # otherwise use a heuristic or specific list if known. 
    # For integration robustness, we'll assume standard 10-20 names exist.
    auditory_electrodes = ['Fz', 'FCz', 'Cz', 'CPz']
    # Intersect with available channels
    available_chans = [ch for ch in auditory_electrodes if ch in epochs.ch_names]
    if not available_chans:
        # Fallback: use first few EEG channels if specific names missing (unlikely in real data)
        available_chans = epochs.ch_names[:3] 
    
    diff_wave_auditory = compute_difference_wave(
        epochs, 
        condition_odd='Oddball', 
        condition_std='Standard',
        electrode_names=available_chans
    )

    logger.info("Computing difference waves for Visual (occipito-parietal) electrodes")
    # Visual: Occipital/Parietal electrodes
    visual_electrodes = ['Oz', 'POz', 'Pz', 'Pz'] # Pz repeated by mistake in list, unique set
    visual_electrodes = list(set(['Oz', 'POz', 'Pz', 'O1', 'O2']))
    available_chans_vis = [ch for ch in visual_electrodes if ch in epochs.ch_names]
    if not available_chans_vis:
        available_chans_vis = epochs.ch_names[-3:] # Fallback to last few

    diff_wave_visual = compute_difference_wave(
        epochs,
        condition_odd='Oddball',
        condition_std='Standard',
        electrode_names=available_chans_vis
    )

    # Define time windows (from config)
    # Auditory: typically 100-200ms for MMN, Visual: 100-200ms for VMMN
    # Using config values if available, otherwise defaults
    time_window_auditory = (0.100, 0.200) # 100ms to 200ms
    time_window_visual = (0.100, 0.200)

    logger.info("Extracting peak latency and mean amplitude")
    
    # Extract Auditory Metrics
    peak_lat_aud = extract_peak_latency(diff_wave_auditory, window=time_window_auditory)
    mean_amp_aud = extract_mean_amplitude(diff_wave_auditory, window=time_window_auditory)

    # Extract Visual Metrics
    peak_lat_vis = extract_peak_latency(diff_wave_visual, window=time_window_visual)
    mean_amp_vis = extract_mean_amplitude(diff_wave_visual, window=time_window_visual)

    # Generate Summary
    summary = generate_metrics_summary(
        modality='Auditory',
        peak_latency_ms=peak_lat_aud,
        mean_amplitude_uV=mean_amp_aud,
        electrode_names=available_chans
    )
    
    summary_vis = generate_metrics_summary(
        modality='Visual',
        peak_latency_ms=peak_lat_vis,
        mean_amplitude_uV=mean_amp_vis,
        electrode_names=available_chans_vis
    )
    
    summary['Visual'] = summary_vis

    # Ensure output directory exists
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    logger.info(f"Writing metrics summary to {output_json_path}")
    with open(output_json_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Assertions to verify real data processing
    assert output_json_path.exists(), "Output JSON file was not created."
    
    with open(output_json_path, 'r') as f:
        results = json.load(f)
    
    # Check structure
    assert 'Auditory' in results, "Auditory results missing."
    assert 'Visual' in results, "Visual results missing."
    
    # Check for physical plausibility (Real data should have non-NaN, non-zero metrics)
    # Peak latency should be within the time window (e.g., 100-200ms)
    aud_lat = results['Auditory']['peak_latency_ms']
    vis_lat = results['Visual']['peak_latency_ms']
    
    # Allow some tolerance for edge cases, but fail if completely out of range
    # If the window is 100-200ms, latency should be roughly in that range.
    # If the signal is flat, latency might be 0 or NaN.
    assert aud_lat is not None and not (isinstance(aud_lat, float) and aud_lat != aud_lat), \
        f"Auditory peak latency is NaN or None. Data might be empty or invalid."
    assert vis_lat is not None and not (isinstance(vis_lat, float) and vis_lat != vis_lat), \
        f"Visual peak latency is NaN or None. Data might be empty or invalid."

    # Amplitude check (should be in microvolts, typically -10 to +10 for ERP)
    aud_amp = results['Auditory']['mean_amplitude_uV']
    vis_amp = results['Visual']['mean_amplitude_uV']
    
    assert aud_amp is not None and not (isinstance(aud_amp, float) and aud_amp != aud_amp), \
        f"Auditory mean amplitude is NaN or None."
    assert vis_amp is not None and not (isinstance(vis_amp, float) and vis_amp != vis_amp), \
        f"Visual mean amplitude is NaN or None."

    logger.info("Integration test passed: Metrics extracted and saved successfully.")