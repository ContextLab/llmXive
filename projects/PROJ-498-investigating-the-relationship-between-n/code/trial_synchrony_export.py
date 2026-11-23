import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

# Import from local project modules as per API surface
from config import ensure_directories
from logging_setup import get_logger
from exclusion_tracker import get_excluded_subjects

logger = get_logger(__name__)

# Constants derived from config/task requirements
# Epoch window: -1000ms to +2000ms
# Pre-stimulus window for synchrony: typically baseline, e.g., [-1000, 0]
# We need to extract synchrony per trial.
# The synchrony metrics (T025) are aggregated. We need to go back to the epoch level.
# We assume preprocessed epochs are saved in data/processed/ as .fif files or similar.
# However, the task description for T036 implies we need to compute trial-level synchrony
# from the epoch data.
# Let's assume the epoch files are named: data/processed/sub-{subject_id}_epo.fif
# And we need to re-load them, compute synchrony for the pre-stim window for each epoch.

# Since T025 produced aggregated metrics, we might not have the raw per-trial synchrony.
# But T035 and T036 require trial-level analysis.
# We must re-process the epochs to get per-trial synchrony.
# We will assume the epoch data is available in MNE format.

def load_subject_data(subject_id: str, data_dir: Path) -> Optional[object]:
    """
    Load preprocessed epoch data for a subject.
    Returns an MNE Epochs object or None if not found.
    """
    # Look for the epoch file. Standard naming convention from T019
    epoch_file = data_dir / f"sub-{subject_id}_epo.fif"
    if not epoch_file.exists():
        logger.warning(f"Epoch file not found for {subject_id} at {epoch_file}")
        return None
    
    try:
        import mne
        epochs = mne.read_epochs(str(epoch_file), preload=True)
        return epochs
    except Exception as e:
        logger.error(f"Error loading epochs for {subject_id}: {e}")
        return None

def compute_trial_synchrony(epochs: object, config: Dict) -> pd.DataFrame:
    """
    Compute synchrony (wPLI/PLV) for each trial in the pre-stimulus window.
    Returns a DataFrame with columns: subject_id, trial_id, condition, synchrony, rt.
    
    Args:
        epochs: MNE Epochs object
        config: Configuration dictionary containing electrode mappings and bands
    
    Returns:
        pd.DataFrame with trial-level synchrony data
    """
    import mne
    import numpy as np
    
    # Extract event information to get condition and RT
    # Assuming events array is available in epochs
    events = epochs.events
    event_id = epochs.event_id
    info = epochs.info
    ch_names = info['ch_names']
    
    # Define electrode pairs for frontoparietal synchrony
    # Based on T022: F3/F4, FC3/FC4 -> DLPFC; P3/P4, CP3/CP4 -> Parietal
    # We need to compute synchrony between DLPFC and Parietal pairs.
    # Let's define a set of pairs: (F3, P3), (F3, P4), (F4, P3), (F4, P4), etc.
    # For simplicity, we'll compute the mean synchrony across a defined set of pairs.
    
    # Define pairs of interest (DLPFC <-> Parietal)
    pairs = [
        ('F3', 'P3'), ('F3', 'P4'),
        ('F4', 'P3'), ('F4', 'P4'),
        ('FC3', 'CP3'), ('FC3', 'CP4'),
        ('FC4', 'CP3'), ('FC4', 'CP4')
    ]
    
    # Filter for theta and gamma bands
    # Theta: 4-7 Hz, Gamma: 30-45 Hz (approximations based on T023)
    # We will compute synchrony in the pre-stimulus window: [-1000ms, 0ms]
    # Note: T005 says pre-stim to 0ms, epoch to +2000ms.
    
    pre_stim_start = -1.0  # seconds
    pre_stim_end = 0.0     # seconds
    
    # Check if electrodes exist
    missing_electrodes = []
    for pair in pairs:
        for ch in pair:
            if ch not in ch_names:
                missing_electrodes.append(ch)
    
    if missing_electrodes:
        logger.warning(f"Missing electrodes for synchrony computation: {missing_electrodes}")
        # We might need to skip or use available ones. For now, let's assume they exist.
        # If critical electrodes are missing, we might skip the subject.
        # But let's try to proceed with available pairs.
        pairs = [p for p in pairs if all(ch in ch_names for ch in p)]
    
    if not pairs:
        logger.error("No valid electrode pairs found for synchrony computation.")
        return pd.DataFrame()
    
    # Extract data for the pre-stimulus window
    # We need to extract the data for each trial and compute synchrony
    # MNE Epochs data shape: (n_epochs, n_channels, n_times)
    
    # Get indices for the pre-stimulus window
    sfreq = info['sfreq']
    start_idx = int(pre_stim_start * sfreq)
    end_idx = int(pre_stim_end * sfreq)
    
    # Ensure indices are within bounds
    n_times = epochs.get_data().shape[2]
    if start_idx < 0:
        start_idx = 0
    if end_idx > n_times:
        end_idx = n_times
    
    if start_idx >= end_idx:
        logger.error("Invalid time window for pre-stimulus extraction.")
        return pd.DataFrame()
    
    # Get channel indices for the pairs
    ch_indices = {ch: ch_names.index(ch) for ch in ch_names if ch in [c for p in pairs for c in p]}
    
    # Prepare to collect trial data
    trial_data = []
    
    # Iterate over epochs
    for i in range(len(epochs)):
        # Get epoch data for this trial
        epoch_data = epochs.get_data()[i]  # (n_channels, n_times)
        
        # Extract pre-stimulus data
        pre_stim_data = epoch_data[:, start_idx:end_idx]  # (n_channels, n_timepoints)
        
        # Compute synchrony for each pair and average
        pair_synchronies = []
        
        for ch1, ch2 in pairs:
            idx1 = ch_indices[ch1]
            idx2 = ch_indices[ch2]
            
            data1 = pre_stim_data[idx1, :]
            data2 = pre_stim_data[idx2, :]
            
            # Compute wPLI (Weighted Phase Lag Index)
            # wPLI = |mean(imag(Z1 * conj(Z2)))| / mean(|imag(Z1 * conj(Z2))|)
            # where Z1, Z2 are complex signals from Hilbert transform or FFT
            
            # Using Hilbert transform for phase extraction
            from scipy.signal import hilbert
            
            # Apply Hilbert transform to get analytic signal
            analytic1 = hilbert(data1)
            analytic2 = hilbert(data2)
            
            # Compute cross-spectrum phase
            cross_phase = analytic1 * np.conj(analytic2)
            imag_cross = np.imag(cross_phase)
            
            # wPLI calculation
            numerator = np.abs(np.mean(imag_cross))
            denominator = np.mean(np.abs(imag_cross))
            
            if denominator > 1e-10:
                wpli = numerator / denominator
            else:
                wpli = 0.0
            
            pair_synchronies.append(wpli)
        
        # Average synchrony across pairs
        mean_synchrony = np.mean(pair_synchronies) if pair_synchronies else 0.0
        
        # Get condition and RT from events
        # events[i] = [sample, 0, event_code]
        event_code = events[i, 2]
        
        # Map event code to condition name
        # This depends on the dataset. We'll assume a mapping or use the code directly.
        # For task-switching, we might have 'switch' and 'stay' conditions.
        # Let's try to infer from the event_id mapping
        condition_name = str(event_code)
        if event_id:
            for name, code in event_id.items():
                if code == event_code:
                    condition_name = name
                    break
        
        # RT extraction
        # RT is typically stored in the metadata or as a separate annotation.
        # If not available, we might need to compute it from the events.
        # For now, let's assume RT is not directly available in the epochs.
        # We might need to load it from a separate file or compute it.
        # Since T030 computes switching costs from RT, we assume RT is available.
        # Let's try to get it from the epochs metadata if available.
        rt = np.nan
        if hasattr(epochs, 'metadata') and epochs.metadata is not None:
            try:
                rt = epochs.metadata.iloc[i]['rt']  # Assuming 'rt' column exists
            except (KeyError, IndexError):
                rt = np.nan
        
        # If RT is still nan, we might skip this trial or mark it as missing.
        # The task says "exclude rows with missing synchrony", but RT is also needed.
        # Let's include the row but with nan RT, and the downstream analysis can handle it.
        
        trial_data.append({
            'subject_id': epochs.subject_info.get('subject', 'unknown') if epochs.subject_info else 'unknown',
            'trial_id': i,
            'condition': condition_name,
            'synchrony': mean_synchrony,
            'rt': rt
        })
    
    df = pd.DataFrame(trial_data)
    return df

def generate_trial_level_synchrony_csv(data_dir: Path, output_path: Path, config: Optional[Dict] = None):
    """
    Generate the per-trial synchrony CSV file for all valid subjects.
    
    Args:
        data_dir: Path to the processed data directory (data/processed)
        output_path: Path to save the output CSV (data/trial_level/per_trial_synchrony.csv)
        config: Optional configuration dictionary
    """
    if config is None:
        config = {}
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get list of subjects
    # We can get subject IDs from the exclusion tracker or by scanning the directory
    excluded_subjects = get_excluded_subjects()
    
    all_subject_data = []
    
    # Scan data/processed for epoch files
    for f in data_dir.iterdir():
        if f.is_file() and f.name.endswith('_epo.fif'):
            # Extract subject ID from filename
            # Expected format: sub-{subject_id}_epo.fif
            parts = f.stem.split('_')
            if len(parts) >= 2 and parts[0] == 'sub':
                subject_id = parts[1]
                
                # Skip excluded subjects
                if subject_id in excluded_subjects:
                    logger.info(f"Skipping excluded subject: {subject_id}")
                    continue
                
                logger.info(f"Processing subject: {subject_id}")
                
                epochs = load_subject_data(subject_id, data_dir)
                if epochs is None:
                    continue
                
                # Compute trial synchrony
                df = compute_trial_synchrony(epochs, config)
                
                if not df.empty:
                    # Add subject_id to the dataframe if not already present
                    if 'subject_id' not in df.columns:
                        df['subject_id'] = subject_id
                    all_subject_data.append(df)
    
    if not all_subject_data:
        logger.warning("No trial-level synchrony data generated. Check if epoch files exist and subjects are not excluded.")
        # Create an empty CSV with the required columns
        empty_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'condition', 'synchrony', 'rt'])
        empty_df.to_csv(output_path, index=False)
        return
    
    # Concatenate all data
    final_df = pd.concat(all_subject_data, ignore_index=True)
    
    # Exclude rows with missing synchrony
    final_df = final_df.dropna(subset=['synchrony'])
    
    # Also handle RT: the task says "exclude rows with missing synchrony", but RT is also a column.
    # We keep rows with missing RT for now, as the task only specifies excluding missing synchrony.
    # However, for downstream analysis (T035), missing RT might be an issue.
    # Let's log a warning if there are missing RTs.
    missing_rt_count = final_df['rt'].isna().sum()
    if missing_rt_count > 0:
        logger.warning(f"Found {missing_rt_count} trials with missing RT. These rows are included but may affect downstream analysis.")
    
    # Sort by subject_id and trial_id for consistency
    final_df = final_df.sort_values(by=['subject_id', 'trial_id'])
    
    # Save to CSV
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved trial-level synchrony data to {output_path} with {len(final_df)} rows.")

def main():
    """
    Main entry point for generating trial-level synchrony CSV.
    """
    from config import ensure_directories
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "processed"
    output_path = base_dir / "data" / "trial_level" / "per_trial_synchrony.csv"
    
    # Configuration (can be extended)
    config = {
        'pre_stim_window': [-1.0, 0.0],
        'bands': ['theta', 'gamma'],
        'electrode_pairs': [
            ('F3', 'P3'), ('F3', 'P4'),
            ('F4', 'P3'), ('F4', 'P4'),
            ('FC3', 'CP3'), ('FC3', 'CP4'),
            ('FC4', 'CP3'), ('FC4', 'CP4')
        ]
    }
    
    # Generate the CSV
    generate_trial_level_synchrony_csv(data_dir, output_path, config)

if __name__ == "__main__":
    main()
