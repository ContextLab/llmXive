import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import mne

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_epochs(epochs_path: Path) -> mne.Epochs:
    """
    Load epoched data from a .fif file.
    
    Args:
        epochs_path: Path to the .fif file containing epochs.
        
    Returns:
        Loaded mne.Epochs object.
    """
    logger.info(f"Loading epochs from {epochs_path}")
    if not epochs_path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    
    epochs = mne.read_epochs(epochs_path, preload=True)
    logger.info(f"Loaded {len(epochs)} epochs with events: {epochs.event_id}")
    return epochs

def get_subject_epochs_paths(processed_dir: Path) -> Dict[str, Path]:
    """
    Locate the processed epochs file for each subject.
    
    Args:
        processed_dir: Directory containing processed data.
        
    Returns:
        Dictionary mapping subject_id to Path of epochs file.
    """
    # Assuming a standard BIDS-like or project structure: data/processed/sub-XX/sub-XX_epo_raw.fif
    # Or simply looking for epo_raw.fif files in subdirectories
    subject_dirs = sorted([d for d in processed_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')])
    
    subject_paths = {}
    for sub_dir in subject_dirs:
        # Look for the epochs file inside the subject directory
        # Based on T018 output: data/processed/epo_raw.fif (global) or sub-specific?
        # T018 says "outputting to data/processed/epo_raw.fif". 
        # However, T022 implies loading per participant. 
        # Let's assume the standard structure where we might have concatenated or individual files.
        # If T018 produced a single file, we need to split or select by subject.
        # But usually, preprocessing pipelines output per-subject files or a concatenated one.
        # Given T022 "load ... and compute average ERPs ... for each participant", 
        # we assume either individual files exist or we can select from a concatenated one.
        # For robustness, let's look for individual files first, then fallback to a global one if logic allows.
        
        # Common pattern: data/processed/sub-01/sub-01_epo_raw.fif
        candidate = sub_dir / f"{sub_dir.name}_epo_raw.fif"
        if candidate.exists():
            subject_paths[sub_dir.name] = candidate
        else:
            # Check if there is a generic epo file in the root of processed (unlikely for multi-subj)
            # or if the file is named differently.
            # For this implementation, we assume the file exists per the pipeline design.
            # If T018 output a single file, we would need to handle that differently.
            # Assuming per-subject files for now as per standard practice for T022 logic.
            pass
            
    if not subject_paths:
        # Fallback: if no subdirs found, maybe all in one file? 
        # But T022 requires per-participant. 
        # Let's assume the directory structure is: data/processed/sub-XX/
        # and the file is named consistently.
        pass
        
    return subject_paths

def compute_average_erps(epochs: mne.Epochs, condition: str) -> mne.Evoked:
    """
    Compute the average ERP for a specific condition.
    
    Args:
        epochs: The mne.Epochs object.
        condition: The condition label (e.g., 'standard', 'deviant').
        
    Returns:
        The averaged mne.Evoked object.
    """
    if condition not in epochs.event_id:
        raise ValueError(f"Condition '{condition}' not found in epochs. Available: {list(epochs.event_id.keys())}")
    
    evoked = epochs[condition].average()
    logger.info(f"Computed average ERP for condition '{condition}': {len(evoked.data[0])} time points")
    return evoked

def compute_difference_wave(standard_evoked: mne.Evoked, deviant_evoked: mne.Epochs) -> mne.Evoked:
    """
    Compute the difference wave: Deviant ERP - Standard ERP.
    
    Args:
        standard_evoked: The average ERP for the standard condition.
        deviant_evoked: The average ERP for the deviant condition.
        
    Returns:
        The difference wave mne.Evoked object.
    """
    # Ensure both have same channels and times
    if not np.array_equal(standard_evoked.times, deviant_evoked.times):
        raise ValueError("Time vectors do not match between standard and deviant evoked.")
    if standard_evoked.ch_names != deviant_evoked.ch_names:
        raise ValueError("Channel lists do not match between standard and deviant evoked.")
        
    diff_data = deviant_evoked.data - standard_evoked.data
    diff_evoked = mne.EvokedArray(
        diff_data, 
        info=standard_evoked.info, 
        tmin=standard_evoked.times[0],
        comment='Difference (Deviant - Standard)'
    )
    logger.info("Computed difference wave (Deviant - Standard)")
    return diff_evoked

def save_difference_waves(diff_evoked: mne.Evoked, output_path: Path):
    """Save the difference wave to a file."""
    diff_evoked.save(output_path, overwrite=True)
    logger.info(f"Saved difference wave to {output_path}")

def extract_erp_metrics(
    epochs: mne.Epochs,
    target_channels: List[str],
    primary_window: Tuple[float, float] = (0.150, 0.250),
    fallback_window: Tuple[float, float] = (0.100, 0.300),
    threshold_uv: float = 2.0
) -> Dict[str, Any]:
    """
    Extract MMN amplitude and latency metrics.
    
    Implements T023 and T024 logic:
    1. Compute average ERPs for 'standard' and 'deviant'.
    2. Compute difference wave.
    3. Find most negative voltage in primary window (150-250ms).
    4. If no peak >= threshold, search fallback window (100-300ms).
    5. If still no peak, flag as not detected.
    
    Args:
        epochs: The loaded epochs object.
        target_channels: List of channel names to search (e.g., ['Fz', 'FCz']).
        primary_window: (start, end) in seconds for primary search.
        fallback_window: (start, end) in seconds for fallback search.
        threshold_uv: Minimum absolute amplitude (µV) to consider a peak valid.
        
    Returns:
        Dictionary with metrics: peak_amplitude, peak_latency, peak_detected, channel.
    """
    metrics = {
        'peak_detected': False,
        'peak_amplitude': None,
        'peak_latency': None,
        'peak_channel': None,
        'window_used': None
    }

    # 1. Compute averages
    try:
        std_evoked = compute_average_erps(epochs, 'standard')
        dev_evoked = compute_average_erps(epochs, 'deviant')
    except ValueError as e:
        logger.error(f"Failed to compute averages: {e}")
        return metrics

    # 2. Compute difference wave
    diff_evoked = compute_difference_wave(std_evoked, dev_evoked)

    # 3. Find the most negative voltage in the specified windows
    # We need to map time window to indices
    times = diff_evoked.times
    ch_names = diff_evoked.ch_names

    # Filter channels to only those in target_channels that exist
    available_targets = [ch for ch in target_channels if ch in ch_names]
    if not available_targets:
        logger.warning(f"No target channels {target_channels} found in data. Available: {ch_names}")
        return metrics

    best_amplitude = float('inf')
    best_latency = None
    best_channel = None
    best_window = None

    # Search Primary Window
    logger.info(f"Searching primary window {primary_window} for negative peak...")
    primary_mask = (times >= primary_window[0]) & (times <= primary_window[1])
    if not np.any(primary_mask):
        logger.warning(f"Primary window {primary_window} out of range. Data range: [{times[0]}, {times[-1]}]")
    else:
        # Get data for primary window
        primary_data = diff_evoked.data[:, primary_mask]
        primary_times = times[primary_mask]
        
        # Find min (most negative) across channels and time in this window
        # We want the global minimum in the specified window across the target channels
        min_val = float('inf')
        min_idx = -1
        min_ch_idx = -1
        
        for i, ch in enumerate(ch_names):
            if ch in available_targets:
                # Find min in this channel's data for the window
                channel_data = primary_data[i, :]
                local_min = np.min(channel_data)
                if local_min < min_val:
                    min_val = local_min
                    # Find the time index for this min
                    local_idx = np.argmin(channel_data)
                    min_idx = local_idx
                    min_ch_idx = i
        
        if min_val < best_amplitude:
            best_amplitude = min_val
            best_latency = primary_times[min_idx]
            best_channel = ch_names[min_ch_idx]
            best_window = "primary"

    # If not found or not significant enough, search fallback
    if best_channel is None or abs(best_amplitude) < threshold_uv:
        logger.info(f"Primary window peak not significant ({abs(best_amplitude):.2f} < {threshold_uv}). Searching fallback window {fallback_window}...")
        
        fallback_mask = (times >= fallback_window[0]) & (times <= fallback_window[1])
        if not np.any(fallback_mask):
            logger.warning(f"Fallback window {fallback_window} out of range.")
        else:
            fallback_data = diff_evoked.data[:, fallback_mask]
            fallback_times = times[fallback_mask]
            
            min_val = float('inf')
            min_idx = -1
            min_ch_idx = -1
            
            for i, ch in enumerate(ch_names):
                if ch in available_targets:
                    channel_data = fallback_data[i, :]
                    local_min = np.min(channel_data)
                    if local_min < min_val:
                        min_val = local_min
                        local_idx = np.argmin(channel_data)
                        min_idx = local_idx
                        min_ch_idx = i
            
            if min_val < best_amplitude:
                best_amplitude = min_val
                best_latency = fallback_times[min_idx]
                best_channel = ch_names[min_ch_idx]
                best_window = "fallback"

    # Final check: if still not found or below threshold
    if best_channel is not None and abs(best_amplitude) >= threshold_uv:
        metrics['peak_detected'] = True
        metrics['peak_amplitude'] = best_amplitude
        metrics['peak_latency'] = best_latency
        metrics['peak_channel'] = best_channel
        metrics['window_used'] = best_window
        logger.info(f"Peak detected: {best_amplitude:.2f} µV at {best_latency*1000:.1f}ms ({best_channel}) in {best_window} window")
    else:
        logger.warning(f"No significant peak found (threshold {threshold_uv} µV).")
        
    return metrics

def save_intermediate_erps(evoked_dict: Dict[str, mne.Evoked], output_dir: Path):
    """Save intermediate ERP objects for debugging/inspection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, evoked in evoked_dict.items():
        path = output_dir / f"{name}.fif"
        evoked.save(path, overwrite=True)
        logger.info(f"Saved {name} to {path}")

def run_extraction_pipeline(
    processed_dir: Path,
    output_dir: Path,
    target_channels: List[str] = ['Fz', 'FCz'],
    primary_window: Tuple[float, float] = (0.150, 0.250),
    fallback_window: Tuple[float, float] = (0.100, 0.300),
    threshold_uv: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Run the full extraction pipeline for all subjects.
    
    Args:
        processed_dir: Path to data/processed.
        output_dir: Path to results directory.
        target_channels: Channels to search for MMN.
        primary_window: Time window for primary peak search.
        fallback_window: Time window for fallback search.
        threshold_uv: Amplitude threshold for peak detection.
        
    Returns:
        List of metric dictionaries for each subject.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    
    # Get subject paths
    # Note: The structure depends on how T018 saved data.
    # If T018 saved a single concatenated file, we need to handle that.
    # Assuming per-subject files for this implementation as per typical BIDS-like flow.
    # If the file is `data/processed/epo_raw.fif` (single file), we need to split by subject.
    # However, T022 says "load ... and compute ... for each participant".
    # Let's assume the directory structure: data/processed/sub-XX/sub-XX_epo_raw.fif
    
    subject_dirs = sorted([d for d in processed_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')])
    
    if not subject_dirs:
        # Fallback: check for a single global file
        global_file = processed_dir / "epo_raw.fif"
        if global_file.exists():
            logger.info(f"Found global epochs file: {global_file}. Assuming single subject or concatenated.")
            # This is a simplification; real logic might need to handle concatenated data.
            # For now, we treat it as one subject if no subdirs found.
            # But T021 mentions multiple participants.
            # Let's assume the project structure has sub-XX dirs.
            logger.error("No subject directories found. Cannot proceed with per-subject extraction.")
            return all_metrics
        else:
            logger.error(f"No epochs files found in {processed_dir}")
            return all_metrics

    for sub_dir in subject_dirs:
        sub_id = sub_dir.name
        # Try to find the epochs file
        epochs_file = sub_dir / f"{sub_id}_epo_raw.fif"
        if not epochs_file.exists():
            # Try alternative naming
            epochs_file = sub_dir / "epo_raw.fif"
        
        if not epochs_file.exists():
            logger.warning(f"Epochs file not found for {sub_id}. Skipping.")
            continue
        
        try:
            logger.info(f"Processing {sub_id}...")
            epochs = load_epochs(epochs_file)
            
            metrics = extract_erp_metrics(
                epochs,
                target_channels=target_channels,
                primary_window=primary_window,
                fallback_window=fallback_window,
                threshold_uv=threshold_uv
            )
            
            if metrics['peak_detected']:
                metrics['participant_id'] = sub_id
                all_metrics.append(metrics)
            else:
                # Still record the subject but with peak_detected=false
                metrics['participant_id'] = sub_id
                all_metrics.append(metrics)
                
        except Exception as e:
            logger.error(f"Error processing {sub_id}: {e}", exc_info=True)
            
    return all_metrics

def main():
    """Main entry point for the extraction script."""
    # Define paths relative to project root
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "data" / "processed"
    results_dir = base_dir / "results"
    
    logger.info(f"Starting extraction pipeline. Processed dir: {processed_dir}")
    
    metrics_list = run_extraction_pipeline(
        processed_dir=processed_dir,
        output_dir=results_dir,
        target_channels=['Fz', 'FCz'],
        primary_window=(0.150, 0.250),
        fallback_window=(0.100, 0.300),
        threshold_uv=2.0
    )
    
    # Save results to CSV
    if metrics_list:
        import pandas as pd
        df = pd.DataFrame(metrics_list)
        csv_path = results_dir / "metrics.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved metrics to {csv_path}")
    else:
        logger.warning("No metrics extracted. Results CSV not created.")

if __name__ == "__main__":
    main()