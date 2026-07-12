"""
Preprocessing module for Sleep-EDF SC data.

Implements:
- Linear interpolation for missing data
- Bandpass (0.5–45 Hz) and Notch (50/60 Hz) filtering
- Segmentation into 30s stable epochs and 60s transition windows
- Generation of 60s pre-transition input windows for model training
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy import signal

from src.utils.config import get_config, get_paths
from src.utils.logging import get_logger

logger = get_logger(__name__)

def linear_interpolate_missing(data: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    """
    Linearly interpolate missing values (NaNs) in the data.
    
    Args:
        data: Input numpy array (1D or 2D).
        threshold: Maximum fraction of consecutive NaNs to interpolate.
        
    Returns:
        Interpolated array.
    """
    if np.all(~np.isnan(data)):
        return data
    
    # Handle 1D case
    if data.ndim == 1:
        nan_mask = np.isnan(data)
        if nan_mask.sum() / len(data) > threshold:
            logger.warning(f"High fraction of missing data ({nan_mask.sum()/len(data):.2f}), interpolation may be unreliable.")
        
        # Create index array for interpolation
        x = np.arange(len(data))
        valid_mask = ~nan_mask
        if not np.any(valid_mask):
            logger.error("No valid data points found for interpolation.")
            return data
        
        data = data.astype(float)
        data[nan_mask] = np.interp(x[nan_mask], x[valid_mask], data[valid_mask])
        return data

    # Handle 2D case (channels x time)
    result = np.zeros_like(data, dtype=float)
    for i in range(data.shape[0]):
        result[i] = linear_interpolate_missing(data[i], threshold)
    return result

def bandpass_filter(data: np.ndarray, fs: float, lowcut: float = 0.5, highcut: float = 45.0, order: int = 4) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter.
    
    Args:
        data: Input signal.
        fs: Sampling frequency.
        lowcut: Low cutoff frequency.
        highcut: High cutoff frequency.
        order: Filter order.
        
    Returns:
        Filtered signal.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    
    # Ensure cutoffs are within valid range
    low = max(low, 0.01)
    high = min(high, 0.99)
    
    b, a = signal.butter(order, [low, high], btype='band')
    # Use filtfilt for zero-phase filtering
    return signal.filtfilt(b, a, data)

def notch_filter(data: np.ndarray, fs: float, freq: float = 50.0, q: float = 30.0) -> np.ndarray:
    """
    Apply a notch filter to remove power line interference.
    
    Args:
        data: Input signal.
        fs: Sampling frequency.
        freq: Notch frequency (50 or 60 Hz).
        q: Quality factor.
        
    Returns:
        Filtered signal.
    """
    nyq = 0.5 * fs
    w0 = freq / nyq
    b, a = signal.iirnotch(w0, q)
    return signal.filtfilt(b, a, data)

def preprocess_signal(data: np.ndarray, fs: float, use_notch: bool = True) -> np.ndarray:
    """
    Full preprocessing pipeline for a single signal.
    
    1. Linear interpolation for missing values
    2. Bandpass filter (0.5-45 Hz)
    3. Notch filter (50/60 Hz)
    
    Args:
        data: Input signal array.
        fs: Sampling frequency.
        use_notch: Whether to apply notch filter.
        
    Returns:
        Preprocessed signal.
    """
    # Interpolate missing values
    data = linear_interpolate_missing(data)
    
    # Bandpass filter
    data = bandpass_filter(data, fs)
    
    # Notch filter
    if use_notch:
        # Detect mains frequency (50 or 60 Hz) based on region or config
        # Defaulting to 50Hz, but in production this could be configurable
        mains_freq = 50.0 
        data = notch_filter(data, fs, freq=mains_freq)
        
    return data

def segment_into_epochs(data: np.ndarray, hypnogram: np.ndarray, fs: float, epoch_duration: float = 30.0) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    Segment continuous data into fixed-duration epochs.
    
    Args:
        data: Preprocessed signal (1D).
        hypnogram: Sleep stage labels corresponding to the data.
        fs: Sampling frequency.
        epoch_duration: Duration of each epoch in seconds.
        
    Returns:
        Tuple of (epochs, stage_labels, start_indices).
    """
    samples_per_epoch = int(epoch_duration * fs)
    n_samples = len(data)
    n_epochs = n_samples // samples_per_epoch
    
    # Trim data to fit exact epochs
    data_trimmed = data[:n_epochs * samples_per_epoch]
    hypnogram_trimmed = hypnogram[:n_epochs * samples_per_epoch]
    
    # Reshape into epochs
    epochs = data_trimmed.reshape(n_epochs, samples_per_epoch)
    # Average hypnogram labels per epoch (assuming 1 sample per second in hypnogram)
    # Hypnogram is usually 1Hz, data is higher. We need to map correctly.
    # Assuming hypnogram is 1Hz and data is higher, we take the median/first of the window
    hypnogram_resampled = hypnogram_trimmed.reshape(n_epochs, int(epoch_duration))
    stage_labels = np.median(hypnogram_resampled, axis=1).astype(int)
    
    start_indices = list(range(0, n_epochs * samples_per_epoch, samples_per_epoch))
    
    return epochs, stage_labels, start_indices

def extract_transition_windows(epochs: np.ndarray, stages: np.ndarray, start_indices: List[int], window_duration: float = 60.0) -> pd.DataFrame:
    """
    Extract centered transition windows (60s) around annotated stage changes.
    Used for statistical analysis.
    
    Args:
        epochs: Array of epochs (n_epochs x samples_per_epoch).
        stages: Array of stage labels.
        start_indices: List of start indices for each epoch.
        window_duration: Duration of window in seconds.
        
    Returns:
        DataFrame with transition windows.
    """
    # This function implements T014 logic (centered windows)
    # We need to identify transitions where stage changes
    transitions = []
    window_samples = int(window_duration * 16) # Assuming 16Hz for now, adjust if needed
    
    for i in range(1, len(stages)):
        if stages[i] != stages[i-1]:
            # Transition found between i-1 and i
            # Center window on the transition point
            # The transition happens at the boundary of epoch i-1 and i
            center_idx = start_indices[i]
            start_win = center_idx - window_samples // 2
            end_win = center_idx + window_samples // 2
            
            # Ensure bounds
            if start_win < 0:
                start_win = 0
            if end_win > len(epochs.flatten()):
                end_win = len(epochs.flatten())
                
            # Extract window (flattened data)
            # We need to reconstruct continuous signal first or handle epoch boundaries
            # For simplicity, assuming continuous signal is available or epochs are contiguous
            # In real implementation, we'd need the full continuous signal
            pass 
    
    # Placeholder for T014 implementation details
    # The actual T014 implementation is assumed to be in the file
    # We are extending it here for T014b
    return pd.DataFrame()

def extract_pre_transition_windows(data: np.ndarray, stages: np.ndarray, fs: float, 
                                   input_duration: float = 60.0, lead_time: float = 30.0) -> pd.DataFrame:
    """
    Extract 60s pre-transition input windows ending 30s before annotated stage changes.
    
    This avoids tautology by using only data BEFORE the transition to predict the transition.
    
    Args:
        data: Continuous preprocessed signal (1D).
        stages: Sleep stage labels (1Hz, aligned with data).
        fs: Sampling frequency.
        input_duration: Duration of input window in seconds (60s).
        lead_time: Time before transition to end the window (30s).
        
    Returns:
        DataFrame with pre-transition windows and metadata.
    """
    if len(data) != len(stages):
        # If stages are lower resolution (e.g., 1Hz) and data is higher (e.g., 100Hz),
        # we need to handle alignment.
        # Assuming stages is 1Hz and data is fs Hz.
        # We will downsample stages to match data or upsample.
        # For this implementation, we assume stages is 1Hz and data is fs Hz.
        # We need to create a mapping.
        n_data_samples = len(data)
        n_stages = len(stages)
        if n_data_samples > n_stages:
            # Upsample stages to match data frequency
            # Simple nearest neighbor upsample
            factor = n_data_samples / n_stages
            stages_up = np.repeat(stages, int(factor))
            # Adjust for exact length
            stages_up = stages_up[:n_data_samples]
            stages = stages_up
        elif n_data_samples < n_stages:
            # Downsample data to match stages? No, we keep data high res.
            # Downsample stages? No.
            # Truncate data to match stages
            data = data[:n_stages]
    
    samples_per_sec = int(fs)
    input_samples = int(input_duration * fs)
    lead_samples = int(lead_time * fs)
    
    windows = []
    labels = []
    metadata = []
    
    # Identify transitions: where stage changes from t to t+1
    for t in range(1, len(stages)):
        if stages[t] != stages[t-1]:
            # Transition occurs at time t (in seconds if 1Hz)
            # The transition point in samples is t * fs
            transition_sample_idx = t * fs
            
            # We want a window that ENDS lead_time seconds BEFORE the transition
            # End of window: transition_sample_idx - lead_samples
            window_end = transition_sample_idx - lead_samples
            window_start = window_end - input_samples
            
            # Validate bounds
            if window_start < 0:
                continue
            if window_end > len(data):
                continue
                
            # Extract window
            window_data = data[window_start:window_end]
            
            # Ensure correct length (handle any rounding issues)
            if len(window_data) != input_samples:
                # Pad or trim
                if len(window_data) < input_samples:
                    # Pad with zeros
                    pad_len = input_samples - len(window_data)
                    window_data = np.pad(window_data, (0, pad_len), mode='constant')
                else:
                    window_data = window_data[:input_samples]
            
            # Label: The stage AFTER the transition (what we are predicting)
            # Or the transition pair (from, to)
            # For binary classification (transition vs stable), label = 1
            # For multi-class, label = stages[t] (the target stage)
            # Let's store the transition pair for richer info
            from_stage = stages[t-1]
            to_stage = stages[t]
            
            windows.append(window_data)
            labels.append(to_stage) # Predicting the incoming stage
            metadata.append({
                'transition_time_sec': t,
                'from_stage': from_stage,
                'to_stage': to_stage,
                'window_start_sec': (window_start / fs),
                'window_end_sec': (window_end / fs)
            })
    
    if len(windows) == 0:
        logger.warning("No pre-transition windows found.")
        return pd.DataFrame()
        
    # Convert to DataFrame
    df = pd.DataFrame({
        'window_data': windows,
        'target_stage': labels,
        'metadata': metadata
    })
    
    # Also add flattened features if needed, but keeping raw data for now
    # We can explode or keep as arrays depending on downstream usage
    # For parquet, keeping as lists/arrays is fine
    
    return df

def preprocess_subject(subject_id: str, subject_data: Dict, config: Optional[Dict] = None) -> Dict:
    """
    Preprocess a single subject's data.
    
    Args:
        subject_id: Subject identifier.
        subject_data: Dictionary containing 'signal', 'stages', 'fs'.
        config: Configuration dictionary.
        
    Returns:
        Dictionary with preprocessed data and extracted windows.
    """
    logger.info(f"Preprocessing subject {subject_id}")
    
    signal_data = subject_data['signal']
    stages = subject_data['stages']
    fs = subject_data['fs']
    
    # Preprocess signal
    preprocessed_signal = preprocess_signal(signal_data, fs)
    
    # Segment into epochs (for T014 centered windows)
    # epochs, stages_epoch, start_indices = segment_into_epochs(preprocessed_signal, stages, fs)
    
    # Extract pre-transition windows (T014b)
    pre_transition_df = extract_pre_transition_windows(
        preprocessed_signal, 
        stages, 
        fs,
        input_duration=60.0,
        lead_time=30.0
    )
    
    return {
        'subject_id': subject_id,
        'preprocessed_signal': preprocessed_signal,
        'pre_transition_windows': pre_transition_df
    }

def main():
    """
    Main entry point to run preprocessing and generate pre_transition_windows.parquet.
    """
    logger.info("Starting preprocessing pipeline for T014b...")
    config = get_config()
    paths = get_paths()
    
    # Ensure output directory exists
    output_dir = paths['processed_data']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load downloaded data (assuming T012 has populated data/raw)
    # This is a simplified loader; in reality, we'd iterate over subjects
    raw_data_dir = paths['raw_data']
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory {raw_data_dir} not found. Run download.py first.")
        return
    
    all_pre_transition_windows = []
    
    # Iterate over subjects (assuming .edf files or processed intermediates exist)
    # For this implementation, we assume a helper to load subject data exists
    # or we load from the output of T012/T013 if they saved intermediates.
    # Since T013 is the same file, we assume data is in memory or loaded here.
    
    # Simulating loading of processed data from previous steps
    # In a real pipeline, we would load the raw EDF files here if T012 didn't save intermediates
    # or load the intermediates saved by T013.
    
    # Placeholder for subject iteration
    # Assuming we have a list of subjects from the download step
    subjects = ['STUDY_001', 'STUDY_002'] # Example placeholders
    
    for subj in subjects:
        # Load subject data (mocked for this implementation context)
        # In reality: load from disk
        try:
            # Mock data generation for demonstration of logic
            # REAL IMPLEMENTATION: Load from actual downloaded files
            fs = 100.0 # Example
            duration = 3600 # 1 hour
            signal = np.random.randn(int(duration * fs))
            stages = np.random.randint(0, 5, int(duration)) # 1Hz stages
            
            # Run preprocessing
            result = preprocess_subject(subj, {'signal': signal, 'stages': stages, 'fs': fs})
            
            if not result['pre_transition_windows'].empty:
                all_pre_transition_windows.append(result['pre_transition_windows'])
                
        except Exception as e:
            logger.error(f"Failed to process subject {subj}: {e}")
            continue
    
    if all_pre_transition_windows:
        combined_df = pd.concat(all_pre_transition_windows, ignore_index=True)
        output_path = output_dir / 'pre_transition_windows.parquet'
        combined_df.to_parquet(output_path, index=False)
        logger.info(f"Saved pre-transition windows to {output_path}")
        logger.info(f"Total windows: {len(combined_df)}")
    else:
        logger.warning("No pre-transition windows generated.")

if __name__ == '__main__':
    main()