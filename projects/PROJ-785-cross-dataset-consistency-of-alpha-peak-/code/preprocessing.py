"""
Preprocessing pipelines for EEG data (Pipeline A and Pipeline B).
Implements filtering, referencing, ICA artifact rejection, and NaN verification.
"""
import os
import numpy as np
import mne
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from config import get_project_root, get_data_path
from logger import get_logger, log_structured_event
from exceptions import DataIntegrityError

# Initialize logger for this module
logger = get_logger(__name__)

def apply_bandpass(signal: np.ndarray, sfreq: float, low: float = 1.0, high: float = 45.0) -> np.ndarray:
    """
    Apply bandpass filter to signal.
    
    Args:
        signal: 2D array (n_channels, n_times) or 1D array
        sfreq: Sampling frequency in Hz
        low: Low cutoff frequency
        high: High cutoff frequency
        
    Returns:
        Filtered signal
    """
    # Ensure signal is 2D for MNE compatibility
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)
        
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(signal.shape[0])], 
                           sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    raw.filter(l_freq=low, h_freq=high, method='iir')
    return raw.get_data()

def apply_bandpass_alt(signal: np.ndarray, sfreq: float, low: float = 0.5, high: float = 40.0) -> np.ndarray:
    """
    Apply alternative bandpass filter (Pipeline B).
    
    Args:
        signal: 2D array (n_channels, n_times) or 1D array
        sfreq: Sampling frequency in Hz
        low: Low cutoff frequency (0.5 Hz for Pipeline B)
        high: High cutoff frequency (40.0 Hz for Pipeline B)
        
    Returns:
        Filtered signal
    """
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)
        
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(signal.shape[0])], 
                           sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    raw.filter(l_freq=low, h_freq=high, method='iir')
    return raw.get_data()

def apply_notch(signal: np.ndarray, sfreq: float, frequency: float = 50.0) -> np.ndarray:
    """
    Apply notch filter to remove line noise.
    
    Args:
        signal: 2D array (n_channels, n_times)
        sfreq: Sampling frequency in Hz
        frequency: Line noise frequency (50 or 60 Hz)
        
    Returns:
        Notch-filtered signal
    """
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)
        
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(signal.shape[0])], 
                           sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    raw.notch_filter(frequencies=frequency)
    return raw.get_data()

def apply_notch_alt(signal: np.ndarray, sfreq: float, frequency: float = 50.0) -> np.ndarray:
    """
    Apply alternative notch filter (Pipeline B).
    
    Args:
        signal: 2D array (n_channels, n_times)
        sfreq: Sampling frequency in Hz
        frequency: Line noise frequency
        
    Returns:
        Notch-filtered signal
    """
    return apply_notch(signal, sfreq, frequency)

def apply_car(data: np.ndarray) -> np.ndarray:
    """
    Apply Common Average Reference.
    
    Args:
        data: 2D array (n_channels, n_times)
        
    Returns:
        CAR-referenced data
    """
    if data.ndim != 2:
        raise ValueError("Data must be 2D array (n_channels, n_times)")
    
    mean_signal = np.mean(data, axis=0, keepdims=True)
    return data - mean_signal

def apply_mastoid_reference(data: np.ndarray, info: Optional[mne.Info] = None, 
                             mastoid_ch_names: Optional[List[str]] = None) -> np.ndarray:
    """
    Apply mastoid reference (Pipeline B deviation).
    
    Args:
        data: 2D array (n_channels, n_times)
        info: MNE info object containing channel names
        mastoid_ch_names: List of mastoid channel names (e.g., ['M1', 'M2'])
        
    Returns:
        Mastoid-referenced data
    """
    if info is None and mastoid_ch_names is None:
        # Fallback: assume last two channels are mastoids if info not provided
        if data.shape[0] < 2:
            raise ValueError("Need at least 2 channels for mastoid reference")
        mastoid_indices = [-2, -1]
    else:
        # Find mastoid channel indices
        if info is not None:
            ch_names = info['ch_names']
        else:
            ch_names = [f'EEG{i}' for i in range(data.shape[0])]
            
        if mastoid_ch_names is None:
            # Default mastoid names
            mastoid_ch_names = ['M1', 'M2', 'A1', 'A2']
            
        mastoid_indices = []
        for name in mastoid_ch_names:
            if name in ch_names:
                mastoid_indices.append(ch_names.index(name))
                
        if len(mastoid_indices) == 0:
            # Fall back to last two channels
            mastoid_indices = [-2, -1]
        
        # Convert to positive indices
        mastoid_indices = [i if i >= 0 else data.shape[0] + i for i in mastoid_indices]
    
    # Average mastoid signal
    mastoid_signal = np.mean(data[mastoid_indices], axis=0, keepdims=True)
    
    return data - mastoid_signal

def reject_ica_components(raw: mne.io.Raw, correlation_threshold: float = 0.8, 
                          variance_threshold: float = 0.15) -> Tuple[mne.io.Raw, Dict[str, Any]]:
    """
    Reject ICA components based on EOG/ECG correlation and variance.
    
    Args:
        raw: MNE Raw object
        correlation_threshold: Threshold for EOG/ECG correlation
        variance_threshold: Threshold for component variance
        
    Returns:
        Tuple of (cleaned Raw object, metadata dict with rejection info)
    """
    logger.info("Starting ICA artifact rejection")
    
    # Create ICA
    n_components = min(0.99, len(raw.ch_names))  # Use 99% of variance
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42)
    ica.fit(raw)
    
    # Find EOG components
    eog_indices, eog_scores = ica.find_bads_eog(raw, threshold=correlation_threshold)
    
    # Find ECG components
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw, threshold=correlation_threshold)
    
    # Combine indices
    all_bad_components = list(set(eog_indices + ecg_indices))
    
    # Calculate variance explained by each component
    variance_explained = ica.get_explained_variance()
    high_variance_components = [i for i, var in enumerate(variance_explained) 
                                if var > variance_threshold]
    
    # Log artifact rejection status
    rejection_metadata = {
        'n_components_total': len(ica),
        'n_eog_components': len(eog_indices),
        'n_ecg_components': len(ecg_indices),
        'n_rejected_components': len(all_bad_components),
        'rejected_components': all_bad_components,
        'eog_components': eog_indices,
        'ecg_components': ecg_indices,
        'high_variance_components': high_variance_components,
        'eog_scores': eog_scores.tolist() if len(eog_scores) > 0 else [],
        'ecg_scores': ecg_scores.tolist() if len(ecg_scores) > 0 else [],
        'variance_explained': variance_explained.tolist()
    }
    
    # Log specific rejection status
    if len(eog_indices) == 0:
        logger.info("EOG components: None Detected")
        log_structured_event(
            event_type="artifact_rejection_status",
            artifact_type="EOG",
            status="None Detected",
            count=0
        )
    else:
        logger.info(f"EOG components detected: {len(eog_indices)}")
        log_structured_event(
            event_type="artifact_rejection_status",
            artifact_type="EOG",
            status="Detected",
            count=len(eog_indices),
            components=eog_indices,
            scores=eog_scores.tolist()
        )
        
    if len(ecg_indices) == 0:
        logger.info("ECG components: None Detected")
        log_structured_event(
            event_type="artifact_rejection_status",
            artifact_type="ECG",
            status="None Detected",
            count=0
        )
    else:
        logger.info(f"ECG components detected: {len(ecg_indices)}")
        log_structured_event(
            event_type="artifact_rejection_status",
            artifact_type="ECG",
            status="Detected",
            count=len(ecg_indices),
            components=ecg_indices,
            scores=ecg_scores.tolist()
        )
    
    # Reject components
    if len(all_bad_components) > 0:
        ica.exclude = all_bad_components
        ica.apply(raw)
        logger.info(f"Rejected {len(all_bad_components)} ICA components")
    else:
        logger.info("No components to reject")
    
    return raw, rejection_metadata

def verify_no_nans(data: np.ndarray, data_name: str = "signal") -> bool:
    """
    Verify that data contains no NaN values.
    
    Args:
        data: numpy array to check
        data_name: Name of data for logging purposes
        
    Returns:
        True if no NaNs found
        
    Raises:
        DataIntegrityError: If NaN values are detected
    """
    if np.any(np.isnan(data)):
        nan_count = np.sum(np.isnan(data))
        error_msg = f"NaN values detected in {data_name}: {nan_count} NaNs found"
        logger.error(error_msg)
        log_structured_event(
            event_type="data_integrity_error",
            error_type="NaN Detected",
            data_name=data_name,
            nan_count=int(nan_count)
        )
        raise DataIntegrityError(error_msg)
    
    logger.debug(f"No NaN values found in {data_name}")
    return True

def verify_no_nans_in_file(file_path: Path) -> bool:
    """
    Verify that a file contains no NaN values when loaded.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if no NaNs found
    """
    try:
        raw = mne.io.read_raw_fif(file_path, preload=True)
        data = raw.get_data()
        verify_no_nans(data, str(file_path))
        return True
    except Exception as e:
        logger.error(f"Error verifying file {file_path}: {str(e)}")
        raise

def process_subject_pipeline_a(raw: mne.io.Raw) -> Tuple[mne.io.Raw, Dict[str, Any]]:
    """
    Process subject data using Pipeline A (Bandpass 1-45Hz, Notch, CAR, ICA).
    
    Args:
        raw: MNE Raw object
        
    Returns:
        Tuple of (processed Raw object, processing metadata)
    """
    sfreq = raw.info['sfreq']
    metadata = {
        'pipeline': 'A',
        'steps': []
    }
    
    # Step 1: Bandpass filter
    data = raw.get_data()
    data = apply_bandpass(data, sfreq, low=1.0, high=45.0)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'bandpass', 'low': 1.0, 'high': 45.0})
    
    # Step 2: Notch filter
    # Assume 50Hz for now - in real implementation, read from BIDS metadata
    data = raw.get_data()
    data = apply_notch(data, sfreq, frequency=50.0)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'notch', 'frequency': 50.0})
    
    # Step 3: Common Average Reference
    data = raw.get_data()
    data = apply_car(data)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'car'})
    
    # Step 4: ICA artifact rejection
    raw, ica_metadata = reject_ica_components(raw)
    metadata['ica'] = ica_metadata
    metadata['steps'].append({'step': 'ica_rejection'})
    
    # Step 5: Verify no NaNs
    verify_no_nans(raw.get_data(), f"Pipeline A output for {raw.filenames[0] if raw.filenames else 'raw'}")
    metadata['steps'].append({'step': 'nan_verification', 'status': 'passed'})
    
    return raw, metadata

def process_subject_pipeline_b(raw: mne.io.Raw) -> Tuple[mne.io.Raw, Dict[str, Any]]:
    """
    Process subject data using Pipeline B (Bandpass 0.5-40Hz, Notch, Mastoid Reference).
    Note: Pipeline B does NOT include ICA rejection (Constitutional Override).
    
    Args:
        raw: MNE Raw object
        
    Returns:
        Tuple of (processed Raw object, processing metadata)
    """
    sfreq = raw.info['sfreq']
    metadata = {
        'pipeline': 'B',
        'steps': []
    }
    
    # Step 1: Bandpass filter (alternative)
    data = raw.get_data()
    data = apply_bandpass_alt(data, sfreq, low=0.5, high=40.0)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'bandpass_alt', 'low': 0.5, 'high': 40.0})
    
    # Step 2: Notch filter (alternative)
    data = raw.get_data()
    data = apply_notch_alt(data, sfreq, frequency=50.0)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'notch_alt', 'frequency': 50.0})
    
    # Step 3: Mastoid reference (Pipeline B deviation)
    data = raw.get_data()
    data = apply_mastoid_reference(data, raw.info)
    raw = mne.io.RawArray(data, raw.info)
    metadata['steps'].append({'step': 'mastoid_reference'})
    
    # Step 4: Verify no NaNs
    verify_no_nans(raw.get_data(), f"Pipeline B output for {raw.filenames[0] if raw.filenames else 'raw'}")
    metadata['steps'].append({'step': 'nan_verification', 'status': 'passed'})
    
    return raw, metadata

def preprocess_and_verify(raw: mne.io.Raw, pipeline: str = 'A') -> Tuple[mne.io.Raw, Dict[str, Any]]:
    """
    Main preprocessing entry point with verification.
    
    Args:
        raw: MNE Raw object
        pipeline: 'A' or 'B'
        
    Returns:
        Tuple of (processed Raw object, metadata)
    """
    if pipeline == 'A':
        return process_subject_pipeline_a(raw)
    elif pipeline == 'B':
        return process_subject_pipeline_b(raw)
    else:
        raise ValueError(f"Unknown pipeline: {pipeline}. Must be 'A' or 'B'")
