"""
Task T010/T010b: Preprocess EEG data (Filter, Reject, ICA).

This script implements the preprocessing pipeline for PhysioNet EEG Motor Movement/Imagery data.
It applies band-pass (1-40Hz), notch (50/60Hz) filtering, rejects channels with >3SD variance,
applies ICA for artifact removal, and handles participant exclusion logic.

Output: Preprocessed data saved to data/interim/preprocessed_eeg/
"""
import os
import sys
import glob
import numpy as np
import mne
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import get_path, set_global_seed, ensure_dirs, get_filter_params
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

# Configuration constants
MIN_CHANNELS_KEEP_RATIO = 0.70  # Keep participant if >= 70% channels remain
VARIANCE_THRESHOLD_SD = 3.0     # Reject channels > 3 SD variance
NOTCH_FREQS = [50, 60]          # Support both 50Hz and 60Hz mains

def load_physionet_eeg_data(subject_id: str) -> mne.io.BaseRaw:
    """
    Load raw EEG data for a subject from the downloaded PhysioNet directory.
    
    Args:
        subject_id: String ID of the subject (e.g., '001')
        
    Returns:
        mne.io.Raw object containing the EEG data
        
    Raises:
        FileNotFoundError: If the raw data files are not found
    """
    raw_dir = get_path("raw_eeg")
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw EEG directory not found: {raw_dir}. Run T007 to download data.")
        
    # PhysioNet EEG Motor Movement/Imagery data structure:
    # sub-001/ses-1/motion/EEG/001_mn_01_eeg.edf (example pattern)
    # We look for .edf files matching the subject ID pattern
    
    # Search for files matching the subject pattern
    patterns = [
        f"sub-{subject_id}*/**/*.edf",
        f"sub-{subject_id}*/**/*.EDF",
        f"*{subject_id}*.edf",
        f"*{subject_id}*.EDF"
    ]
    
    found_files = []
    for pattern in patterns:
        found_files.extend(list(raw_dir.glob(pattern)))
        
    if not found_files:
        raise FileNotFoundError(
            f"No EEG files found for subject {subject_id} in {raw_dir}. "
            f"Please verify T007 (download) completed successfully."
        )
    
    # Use the first found file (typically the main recording)
    raw_file = found_files[0]
    print(f"Loading EEG data from: {raw_file}")
    
    # Load with MNE
    raw = mne.io.read_raw_edf(raw_file, preload=True, verbose=False)
    
    # Set standard montage if not present
    if raw.info['ch_names'] and raw.info['ch_names'][0].startswith('EEG'):
        try:
            mne.channels.make_standard_montage('standard_1005', ch_names=raw.ch_names)
            raw.set_montage('standard_1005', match_case=False, match_alias=True, on_missing='ignore')
        except Exception as e:
            print(f"Warning: Could not set montage: {e}")
    
    return raw

def get_subject_id_from_path(filepath: str) -> str:
    """Extract subject ID from file path."""
    basename = os.path.basename(filepath)
    # Handle various naming conventions: sub-001_ses-1..., 001_mn_01..., etc.
    if basename.startswith('sub-'):
        parts = basename.split('_')
        if len(parts) > 0:
            return parts[0].replace('sub-', '').split('/')[0]
    elif basename[0].isdigit():
        # Extract leading digits
        import re
        match = re.match(r'^(\d+)', basename)
        if match:
            return match.group(1)
    return basename.split('.')[0].split('_')[0]

def preprocess_subject(subject_id: str, output_dir: Path) -> dict:
    """
    Preprocess a single subject's EEG data.
    
    Steps:
    1. Load raw data
    2. Apply band-pass filter (1-40 Hz)
    3. Apply notch filter (50/60 Hz)
    4. Reject channels with variance > 3SD
    5. Apply ICA to remove ocular/muscle artifacts
    6. Save preprocessed data
    
    Args:
        subject_id: Subject identifier
        output_dir: Directory to save preprocessed data
        
    Returns:
        dict: Processing statistics (channels kept, rejected, etc.)
    """
    stats = {
        "subject_id": subject_id,
        "status": "success",
        "channels_initial": 0,
        "channels_rejected": 0,
        "channels_final": 0,
        "ica_components_removed": 0,
        "excluded": False,
        "exclusion_reason": None
    }
    
    try:
        # 1. Load raw data
        raw = load_physionet_eeg_data(subject_id)
        stats["channels_initial"] = len(raw.ch_names)
        
        # 2. Apply band-pass filter (1-40 Hz)
        filter_params = get_filter_params()
        l_freq = filter_params.get('l_freq', 1.0)
        h_freq = filter_params.get('h_freq', 40.0)
        
        raw_filtered = bandpass_filter(raw, l_freq=l_freq, h_freq=h_freq)
        print(f"[{subject_id}] Applied band-pass filter: {l_freq}-{h_freq} Hz")
        
        # 3. Apply notch filter (50/60 Hz)
        raw_notched = notch_filter(raw_filtered, freqs=NOTCH_FREQS)
        print(f"[{subject_id}] Applied notch filter: {NOTCH_FREQS} Hz")
        
        # 4. Reject channels with variance > 3SD
        rejected_chs, kept_chs = reject_channels_by_variance(
            raw_notched, 
            threshold_sd=VARIANCE_THRESHOLD_SD
        )
        stats["channels_rejected"] = len(rejected_chs)
        stats["channels_final"] = len(kept_chs)
        
        if rejected_chs:
            print(f"[{subject_id}] Rejected channels: {rejected_chs}")
        
        # 5. Check participant exclusion criteria
        total_initial = stats["channels_initial"]
        kept_ratio = len(kept_chs) / total_initial if total_initial > 0 else 0
        
        if kept_ratio < MIN_CHANNELS_KEEP_RATIO:
            stats["excluded"] = True
            stats["exclusion_reason"] = f"Only {kept_ratio:.1%} channels kept (threshold: {MIN_CHANNELS_KEEP_RATIO:.0%})"
            print(f"[{subject_id}] EXCLUDED: {stats['exclusion_reason']}")
            return stats
        
        # 6. Apply ICA for artifact removal
        raw_ica, n_removed = apply_ica(raw_notched, rejected_channels=rejected_chs)
        stats["ica_components_removed"] = n_removed
        stats["channels_final"] = len(raw_ica.ch_names)  # May have changed after ICA
        print(f"[{subject_id}] ICA removed {n_removed} components")
        
        # 7. Save preprocessed data
        output_file = output_dir / f"sub-{subject_id}_preprocessed.fif"
        raw_ica.save(output_file, overwrite=True, verbose=False)
        print(f"[{subject_id}] Saved preprocessed data to: {output_file}")
        
    except Exception as e:
        stats["status"] = "failed"
        stats["exclusion_reason"] = str(e)
        print(f"[{subject_id}] ERROR: {e}")
        raise
        
    return stats

def main():
    """
    Main entry point for preprocessing pipeline.
    Iterates over all subjects in the raw data directory and preprocesses them.
    """
    set_global_seed()
    ensure_dirs()
    
    raw_dir = get_path("raw_eeg")
    output_dir = get_path("interim_preprocessed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all subject directories
    if not raw_dir.exists():
        print("ERROR: Raw EEG directory not found. Run T007 (download) first.")
        sys.exit(1)
        
    # Discover subjects by scanning for EDF files
    subject_ids = set()
    for edf_file in raw_dir.rglob("*.edf"):
        sid = get_subject_id_from_path(str(edf_file))
        if sid:
            subject_ids.add(sid)
    for edf_file in raw_dir.rglob("*.EDF"):
        sid = get_subject_id_from_path(str(edf_file))
        if sid:
            subject_ids.add(sid)
    
    if not subject_ids:
        print("ERROR: No subject data found. Run T007 (download) first.")
        sys.exit(1)
    
    print(f"Found {len(subject_ids)} subjects to process: {sorted(subject_ids)}")
    
    # Process each subject
    all_stats = []
    excluded_count = 0
    
    for subject_id in sorted(subject_ids):
        try:
            stats = preprocess_subject(subject_id, output_dir)
            all_stats.append(stats)
            if stats["excluded"]:
                excluded_count += 1
        except Exception as e:
            print(f"Failed to process subject {subject_id}: {e}")
            all_stats.append({
                "subject_id": subject_id,
                "status": "failed",
                "exclusion_reason": str(e)
            })
    
    # Write processing report
    report_file = output_dir / "preprocessing_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            "total_subjects": len(subject_ids),
            "processed": len(all_stats),
            "excluded": excluded_count,
            "stats": all_stats
        }, f, indent=2)
    
    print(f"\nPreprocessing complete.")
    print(f"Total subjects: {len(subject_ids)}")
    print(f"Successfully processed: {len(all_stats) - excluded_count}")
    print(f"Excluded: {excluded_count}")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()
