from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import numpy as np
import mne

# Electrode to Region Mapping
ELECTRODE_REGION_MAP = {
    # DLPFC
    "F3": "DLPFC", "F4": "DLPFC",
    "FC3": "DLPFC", "FC4": "DLPFC",
    # Parietal
    "P3": "Parietal", "P4": "Parietal",
    "CP3": "Parietal", "CP4": "Parietal",
    # Additional standard 10-20 for robustness (optional expansion)
    "F7": "Frontal", "F8": "Frontal",
    "P7": "Parietal", "P8": "Parietal",
}

# Frequency Bands (Hz)
THETA_BAND = (4, 7)
GAMMA_BAND = (30, 45)

def get_region_for_electrode(electrode: str) -> Optional[str]:
    """
    Map an electrode name to a brain region.
    
    Args:
        electrode: Electrode name (e.g., 'F3').
        
    Returns:
        Region string or None if not found.
    """
    return ELECTRODE_REGION_MAP.get(electrode)

def get_all_electrode_pairs(electrodes: List[str]) -> List[Tuple[str, str]]:
    """
    Generate all unique pairs of electrodes.
    
    Args:
        electrodes: List of electrode names.
        
    Returns:
        List of tuples (e1, e2) where e1 < e2.
    """
    pairs = []
    for i in range(len(electrodes)):
        for j in range(i + 1, len(electrodes)):
            e1, e2 = sorted([electrodes[i], electrodes[j]])
            pairs.append((e1, e2))
    return pairs

def get_cross_region_pairs(electrodes: List[str]) -> List[Tuple[str, str]]:
    """
    Filter pairs to only those spanning different regions.
    
    Args:
        electrodes: List of electrode names.
        
    Returns:
        List of cross-region pairs.
    """
    pairs = get_all_electrode_pairs(electrodes)
    cross_region = []
    for e1, e2 in pairs:
        r1 = get_region_for_electrode(e1)
        r2 = get_region_for_electrode(e2)
        if r1 and r2 and r1 != r2:
            cross_region.append((e1, e2))
    return cross_region

def validate_electrode_presence(info: mne.Info, required_electrodes: List[str]) -> List[str]:
    """
    Check which required electrodes are present in the info object.
    
    Args:
        info: MNE info object.
        required_electrodes: List of electrode names to check.
        
    Returns:
        List of missing electrodes.
    """
    present = set(info['ch_names'])
    missing = [e for e in required_electrodes if e not in present]
    return missing

def get_pair_id(pair: Tuple[str, str]) -> str:
    """
    Generate a unique ID for an electrode pair.
    
    Args:
        pair: Tuple (e1, e2).
        
    Returns:
        String ID like 'F3-F4'.
    """
    return f"{pair[0]}-{pair[1]}"

def is_valid_pair(pair: Tuple[str, str]) -> bool:
    """
    Check if a pair is valid (both electrodes exist in map).
    
    Args:
        pair: Tuple (e1, e2).
        
    Returns:
        True if valid.
    """
    return get_region_for_electrode(pair[0]) is not None and \
           get_region_for_electrode(pair[1]) is not None

def get_region_pairs(electrodes: List[str]) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """
    Group electrode pairs by the regions they connect.
    
    Args:
        electrodes: List of electrode names.
        
    Returns:
        Dict mapping (region1, region2) to list of pairs.
    """
    region_map = defaultdict(list)
    pairs = get_all_electrode_pairs(electrodes)
    for e1, e2 in pairs:
        r1 = get_region_for_electrode(e1)
        r2 = get_region_for_electrode(e2)
        if r1 and r2:
            key = tuple(sorted([r1, r2]))
            region_map[key].append((e1, e2))
    return region_map

def get_pair_region_type(pair: Tuple[str, str]) -> Optional[str]:
    """
    Determine if a pair is intra-region or cross-region.
    
    Args:
        pair: Tuple (e1, e2).
        
    Returns:
        'intra' or 'cross' or None.
    """
    r1 = get_region_for_electrode(pair[0])
    r2 = get_region_for_electrode(pair[1])
    if not r1 or not r2:
        return None
    return 'intra' if r1 == r2 else 'cross'

def filter_bandpower(data: np.ndarray, sfreq: float, band: Tuple[float, float]) -> np.ndarray:
    """
    Apply a bandpass filter to data.
    
    Args:
        data: 1D or 2D numpy array (n_channels, n_times).
        sfreq: Sampling frequency.
        band: (low, high) frequency tuple.
        
    Returns:
        Filtered data.
    """
    if data.ndim == 1:
        data = data.reshape(1, -1)
    
    # Use MNE's filter for consistency with pipeline
    # Note: In a real pipeline, we might use mne.filter.filter_data directly
    # Here we simulate or delegate if mne is available
    try:
        from mne.filter import filter_data
        filtered = np.zeros_like(data)
        for i, ch in enumerate(data):
            filtered[i] = filter_data(ch, sfreq, band[0], band[1], l_trans_bandwidth='auto', h_trans_bandwidth='auto')
        return filtered
    except Exception:
        # Fallback to scipy if mne filter is not available or fails
        from scipy.signal import butter, filtfilt
        order = 4
        nyq = 0.5 * sfreq
        low = band[0] / nyq
        high = band[1] / nyq
        b, a = butter(order, [low, high], btype='band')
        filtered = np.zeros_like(data)
        for i, ch in enumerate(data):
            filtered[i] = filtfilt(b, a, ch)
        return filtered

def get_theta_filtered_data(epochs: mne.Epochs) -> np.ndarray:
    """
    Extract and filter theta band data from epochs.
    
    Args:
        epochs: MNE Epochs object.
        
    Returns:
        Filtered data array (n_epochs, n_channels, n_times).
    """
    data = epochs.get_data()
    sfreq = epochs.info['sfreq']
    return filter_bandpower(data, sfreq, THETA_BAND)

def get_gamma_filtered_data(epochs: mne.Epochs) -> np.ndarray:
    """
    Extract and filter gamma band data from epochs.
    
    Args:
        epochs: MNE Epochs object.
        
    Returns:
        Filtered data array (n_epochs, n_channels, n_times).
    """
    data = epochs.get_data()
    sfreq = epochs.info['sfreq']
    return filter_bandpower(data, sfreq, GAMMA_BAND)

def prepare_data_for_synchrony(epochs: mne.Epochs, electrode_pairs: List[Tuple[str, str]], band: str = 'theta') -> Dict[str, np.ndarray]:
    """
    Prepare filtered data for synchrony computation.
    
    Args:
        epochs: MNE Epochs object.
        electrode_pairs: List of electrode pairs.
        band: 'theta' or 'gamma'.
        
    Returns:
        Dict mapping pair_id to filtered data (n_epochs, 2, n_times).
    """
    if band == 'theta':
        filtered_data = get_theta_filtered_data(epochs)
    else:
        filtered_data = get_gamma_filtered_data(epochs)
    
    ch_names = epochs.ch_names
    ch_indices = [ch_names.index(e) for e, _ in electrode_pairs] + \
                 [ch_names.index(e) for _, e in electrode_pairs]
    
    # This is a simplified extraction; in reality, we need to map correctly
    # Assuming filtered_data is (n_epochs, n_channels, n_times)
    result = {}
    for i, (e1, e2) in enumerate(electrode_pairs):
        idx1 = ch_names.index(e1)
        idx2 = ch_names.index(e2)
        pair_data = filtered_data[:, [idx1, idx2], :]
        result[get_pair_id((e1, e2))] = pair_data
        
    return result

def compute_wpli(e1_data: np.ndarray, e2_data: np.ndarray) -> float:
    """
    Compute weighted Phase-Lag Index (wPLI).
    
    Args:
        e1_data: Data for electrode 1 (n_epochs, n_times).
        e2_data: Data for electrode 2 (n_epochs, n_times).
        
    Returns:
        Mean wPLI across epochs.
    """
    # Cross-spectral density or Hilbert transform approach
    # Using Hilbert transform for phase extraction
    from scipy.signal import hilbert
    
    phases1 = np.angle(hilbert(e1_data, axis=1))
    phases2 = np.angle(hilbert(e2_data, axis=1))
    
    # Phase difference
    diff = phases1 - phases2
    
    # Imaginary part of cross-spectrum approximation
    # wPLI = |E[sign(Im(XY*)) * |Im(XY*)|]| / E[|Im(XY*)|]
    # Simplified: mean of sign(imag) * abs(imag) / mean of abs(imag)
    # But we have phase difference directly.
    # wPLI = |mean( sign(sin(diff)) * |sin(diff)| )| / mean(|sin(diff)|)
    # Actually, wPLI is often defined on the cross-spectrum.
    # Let's use the standard definition: wPLI = |<sign(Im(CSD)) * |Im(CSD)>| / <|Im(CSD)>|
    # Since we have phase, Im(CSD) ~ sin(phase_diff)
    
    imag_part = np.sin(diff)
    wpli_numerator = np.abs(np.mean(np.sign(imag_part) * np.abs(imag_part), axis=1))
    wpli_denominator = np.mean(np.abs(imag_part), axis=1)
    
    # Avoid division by zero
    wpli_denominator = np.where(wpli_denominator == 0, 1e-10, wpli_denominator)
    wpli_values = wpli_numerator / wpli_denominator
    
    return np.mean(wpli_values)

def compute_plv(e1_data: np.ndarray, e2_data: np.ndarray) -> float:
    """
    Compute Phase-Locking Value (PLV).
    
    Args:
        e1_data: Data for electrode 1 (n_epochs, n_times).
        e2_data: Data for electrode 2 (n_epochs, n_times).
        
    Returns:
        Mean PLV across epochs.
    """
    from scipy.signal import hilbert
    
    phases1 = np.angle(hilbert(e1_data, axis=1))
    phases2 = np.angle(hilbert(e2_data, axis=1))
    
    diff = phases1 - phases2
    plv_values = np.abs(np.mean(np.exp(1j * diff), axis=1))
    
    return np.mean(plv_values)

def compute_synchrony_metrics(
    epochs: mne.Epochs,
    band: str = 'theta',
    method: str = 'wpli'
) -> Dict[str, float]:
    """
    Compute synchrony metrics for all cross-region pairs.
    
    Args:
        epochs: MNE Epochs object.
        band: 'theta' or 'gamma'.
        method: 'wpli' or 'plv'.
        
    Returns:
        Dict mapping pair_id to metric value.
    """
    # Define target electrodes based on spec
    target_electrodes = ["F3", "F4", "FC3", "FC4", "P3", "P4", "CP3", "CP4"]
    valid_electrodes = [e for e in target_electrodes if e in epochs.ch_names]
    
    if len(valid_electrodes) < 2:
        return {}
    
    pairs = get_cross_region_pairs(valid_electrodes)
    if not pairs:
        return {}
    
    data_dict = prepare_data_for_synchrony(epochs, pairs, band)
    
    results = {}
    for pair_id, pair_data in data_dict.items():
        # pair_data shape: (n_epochs, 2, n_times)
        e1_data = pair_data[:, 0, :]
        e2_data = pair_data[:, 1, :]
        
        if method == 'wpli':
            results[pair_id] = compute_wpli(e1_data, e2_data)
        elif method == 'plv':
            results[pair_id] = compute_plv(e1_data, e2_data)
        else:
            raise ValueError(f"Unknown method: {method}")
            
    return results

def main() -> None:
    """
    CLI entry point for synchrony analysis.
    Placeholder for future CLI functionality.
    """
    print("Synchrony Analysis Module")
    print(f"Theta Band: {THETA_BAND} Hz")
    print(f"Gamma Band: {GAMMA_BAND} Hz")

if __name__ == "__main__":
    main()
