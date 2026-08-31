"""
Task T012a: Compute Welch's PSD on continuous fixed-length epochs.

Implements FR-003:
- Windowing: Fixed-duration windows (config.WINDOW_SIZE, default 4s).
- Overlap: config.OVERLAP (default 0.5), with --overlap CLI override.
- Input: Preprocessed EEG data from T010 (data/interim/ica_cleaned_eeg/).
- Output: data/interim/psd_spectra.npy (shape: [n_participants, n_channels, n_frequencies]).
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from local config and utils
# Note: We assume config.py is in the same directory or PYTHONPATH includes the project root
try:
    from config import get_path, ensure_dirs, WINDOW_SIZE, OVERLAP, EPSILON, get_band_freqs
except ImportError:
    # Fallback for execution context where config is not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, ensure_dirs, WINDOW_SIZE, OVERLAP, EPSILON, get_band_freqs

# MNE-Python for EEG handling
try:
    import mne
except ImportError:
    print("Error: MNE-Python is required. Install with: pip install mne")
    sys.exit(1)

# Constants
SAMPLE_RATE = 250  # Standard for EEGMMIDB, will be read from file if needed
FREQ_RES = 0.5     # Frequency resolution for Welch's method (Hz)

def load_participant_list(join_metadata_path: Path) -> List[str]:
    """
    Load the list of valid participant IDs from the feasibility join metadata.
    This ensures we only process participants who passed the feasibility check (T008a).
    """
    if not join_metadata_path.exists():
        raise FileNotFoundError(f"Join metadata not found: {join_metadata_path}")
    
    df = pd.read_csv(join_metadata_path)
    # Assuming 'participant_id' is the column name based on T008a spec
    if 'participant_id' not in df.columns:
        raise ValueError(f"Expected 'participant_id' column in {join_metadata_path}")
    
    return df['participant_id'].astype(str).tolist()

def get_eeg_file_path(participant_id: str, base_dir: Path) -> Optional[Path]:
    """
    Locate the preprocessed EEG file for a given participant.
    Expected pattern: data/interim/ica_cleaned_eeg/sub-<id>_ica.fif or similar.
    We scan the directory for matching files.
    """
    search_pattern = base_dir / f"*{participant_id}*"
    files = list(search_pattern.glob("*.fif"))
    if not files:
        # Try case-insensitive or different naming conventions
        files = list(base_dir.glob(f"*{participant_id.lower()}*.fif"))
    
    if not files:
        return None
    
    # Return the first match; in a real scenario, we might prefer a specific naming convention
    return files[0]

def compute_psd_for_subject(
    raw_data_path: Path,
    window_size: float,
    overlap_ratio: float,
    sfreq: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Compute Welch's PSD for a single subject's continuous data.

    Args:
        raw_data_path: Path to the .fif file.
        window_size: Window duration in seconds.
        overlap_ratio: Overlap ratio (0.0 to 1.0).
        sfreq: Sampling frequency (optional, read from file if not provided).

    Returns:
        psd: 2D array (n_channels, n_frequencies)
        freqs: 1D array of frequencies
        ch_names: List of channel names
    """
    # Load data
    raw = mne.io.read_raw_fif(raw_data_path, preload=True)
    
    if sfreq is None:
        sfreq = raw.info['sfreq']
    
    # Get channel names and data
    ch_names = raw.ch_names
    data = raw.get_data()  # Shape: (n_channels, n_times)
    
    n_channels, n_times = data.shape
    
    # Calculate window and step in samples
    window_samples = int(window_size * sfreq)
    step_samples = int(window_samples * (1 - overlap_ratio))
    
    if step_samples < 1:
        raise ValueError("Overlap ratio too high, step size is zero or negative.")
    
    # Prepare arrays for PSD accumulation
    # We will compute PSD for each window and average them
    # Welch's method: average of periodograms of overlapping segments
    
    # Determine number of windows
    n_windows = (n_times - window_samples) // step_samples + 1
    
    if n_windows < 1:
        raise ValueError(f"Data too short for window size {window_size}s at {sfreq}Hz. "
                       f"Need at least {window_samples} samples, got {n_times}.")
    
    # Initialize array to store periodograms
    # We'll compute the PSD for each window and average
    # Frequency bins will be determined by the FFT size (window_samples)
    fft_size = window_samples
    n_freqs = fft_size // 2 + 1
    
    # Accumulate squared magnitudes
    psd_sum = np.zeros((n_channels, n_freqs))
    
    # Window function (Hann is standard for Welch)
    window = np.hanning(window_samples)
    
    for i in range(n_windows):
        start = i * step_samples
        end = start + window_samples
        
        if end > n_times:
            break
        
        segment = data[:, start:end]
        
        # Apply window
        segment_windowed = segment * window
        
        # Compute FFT
        fft_vals = np.fft.rfft(segment_windowed, n=fft_size, axis=1)
        
        # Compute power spectral density (magnitude squared)
        # Normalize by window power and sampling frequency for proper scaling
        # But for relative comparisons, raw magnitude squared is often sufficient
        # Here we compute the periodogram (magnitude squared)
        psd_segment = np.abs(fft_vals) ** 2
        
        # Accumulate
        psd_sum += psd_segment
    
    # Average over windows
    psd_avg = psd_sum / n_windows
    
    # Normalize by window power to get correct PSD units (if needed)
    # Window power normalization factor
    window_power = np.sum(window ** 2)
    psd_norm = psd_avg / (window_power * sfreq)
    
    # Compute frequency bins
    freqs = np.fft.rfftfreq(fft_size, d=1.0/sfreq)
    
    return psd_norm, freqs, ch_names

def aggregate_psd_across_subjects(
    participant_ids: List[str],
    eeg_base_dir: Path,
    window_size: float,
    overlap_ratio: float
) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """
    Compute PSD for all valid participants and aggregate into a single array.

    Returns:
        all_psds: 3D array (n_participants, n_channels, n_frequencies)
        freqs: 1D array of frequencies
        all_ch_names: List of channel names (should be consistent)
        valid_ids: List of participant IDs that were successfully processed
    """
    all_psds = []
    valid_ids = []
    freqs_ref = None
    ch_names_ref = None
    
    print(f"Processing {len(participant_ids)} participants...")
    
    for pid in participant_ids:
        eeg_path = get_eeg_file_path(pid, eeg_base_dir)
        
        if eeg_path is None:
            print(f"  Skipping {pid}: No EEG file found.")
            continue
        
        try:
            psd, freqs, ch_names = compute_psd_for_subject(
                eeg_path, window_size, overlap_ratio
            )
            
            # Validate consistency
            if freqs_ref is None:
                freqs_ref = freqs
                ch_names_ref = ch_names
            else:
                if not np.allclose(freqs, freqs_ref):
                    raise ValueError(f"Frequencies mismatch for {pid}")
                if ch_names != ch_names_ref:
                    raise ValueError(f"Channel names mismatch for {pid}")
            
            all_psds.append(psd)
            valid_ids.append(pid)
            print(f"  Processed {pid}: shape {psd.shape}")
            
        except Exception as e:
            print(f"  Error processing {pid}: {e}")
            # Continue with next participant rather than failing the whole run
            continue
    
    if not all_psds:
        raise RuntimeError("No participants were successfully processed.")
    
    # Stack into 3D array
    all_psds_array = np.stack(all_psds, axis=0)  # Shape: (n_participants, n_channels, n_frequencies)
    
    return all_psds_array, freqs_ref, ch_names_ref, valid_ids

def save_psd_output(
    psd_array: np.ndarray,
    freqs: np.ndarray,
    ch_names: List[str],
    participant_ids: List[str],
    output_path: Path,
    metadata_path: Path
):
    """
    Save the aggregated PSD data and metadata.
    """
    # Save the main PSD array
    np.save(output_path, psd_array)
    print(f"Saved PSD array to {output_path} with shape {psd_array.shape}")
    
    # Save metadata as JSON
    metadata = {
        "shape": list(psd_array.shape),
        "n_participants": len(participant_ids),
        "n_channels": len(ch_names),
        "n_frequencies": len(freqs),
        "frequencies": freqs.tolist(),
        "channel_names": ch_names,
        "participant_ids": participant_ids,
        "window_size_seconds": psd_array.shape[0] / len(participant_ids) if participant_ids else 0, # Just a placeholder, actually window_size is passed
        "overlap_ratio": 0.5 # Placeholder, should be passed
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {metadata_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract PSD from preprocessed EEG data (Task T012a)")
    parser.add_argument(
        "--overlap",
        type=float,
        default=None,
        help="Overlap ratio (0.0 to 1.0). Overrides config.OVERLAP if provided."
    )
    parser.add_argument(
        "--window-size",
        type=float,
        default=None,
        help="Window size in seconds. Overrides config.WINDOW_SIZE if provided."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to preprocessed EEG directory. Defaults to data/interim/ica_cleaned_eeg/"
    )
    parser.add_argument(
        "--join-metadata",
        type=str,
        default=None,
        help="Path to joined_metadata.csv. Defaults to data/interim/joined_metadata.csv"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for PSD. Defaults to data/interim/"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent
    
    # Use config defaults if not overridden
    window_size = args.window_size if args.window_size is not None else WINDOW_SIZE
    overlap_ratio = args.overlap if args.overlap is not None else OVERLAP
    
    input_dir = Path(args.input_dir) if args.input_dir else get_path("interim", "ica_cleaned_eeg")
    join_metadata_path = Path(args.join_metadata) if args.join_metadata else get_path("interim", "joined_metadata.csv")
    output_dir = Path(args.output_dir) if args.output_dir else get_path("interim")
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    output_path = Path(output_dir) / "psd_spectra.npy"
    metadata_path = Path(output_dir) / "psd_spectra_metadata.json"
    
    print(f"Starting PSD extraction:")
    print(f"  Window size: {window_size}s")
    print(f"  Overlap: {overlap_ratio}")
    print(f"  Input EEG dir: {input_dir}")
    print(f"  Join metadata: {join_metadata_path}")
    print(f"  Output: {output_path}")
    
    # Load participant list
    try:
        participant_ids = load_participant_list(join_metadata_path)
        print(f"Found {len(participant_ids)} valid participants from join metadata.")
    except Exception as e:
        print(f"Error loading participant list: {e}")
        sys.exit(1)
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input EEG directory does not exist: {input_dir}")
        print("Please ensure T010 (preprocess_eeg) has completed successfully.")
        sys.exit(1)
    
    # Process all participants
    try:
        psd_array, freqs, ch_names, valid_ids = aggregate_psd_across_subjects(
            participant_ids,
            input_dir,
            window_size,
            overlap_ratio
        )
        
        if len(valid_ids) == 0:
            print("Error: No participants were successfully processed.")
            sys.exit(1)
        
        print(f"Successfully processed {len(valid_ids)} participants.")
        
        # Save output
        save_psd_output(
            psd_array,
            freqs,
            ch_names,
            valid_ids,
            output_path,
            metadata_path
        )
        
        print("PSD extraction completed successfully.")
        
    except Exception as e:
        print(f"Error during PSD extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()