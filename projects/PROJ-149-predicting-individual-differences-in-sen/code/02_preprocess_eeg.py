"""
code/02_preprocess_eeg.py

Preprocesses raw EEG data from PhysioNet EEG Motor Movement/Imagery dataset.
Applies band-pass filtering, notch filtering, channel variance rejection, and ICA cleaning.
Implements participant exclusion logic based on channel rejection rates.

Outputs cleaned EEG data to data/interim/cleaned_eeg/
"""

import os
import sys
import glob
import argparse
import numpy as np
import mne
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs, get_filter_params, get_seed
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica


def get_subject_id_from_path(file_path: str) -> Optional[str]:
    """
    Extract subject ID from PhysioNet file path.
    
    Args:
        file_path: Path to EEG data file
        
    Returns:
        Subject ID string or None if not found
    """
    path = Path(file_path)
    # PhysioNet naming: sub-<ID>_task-<TASK>_run-<RUN>_eeg.edf
    # Or: sub-<ID>_eeg.edf
    if path.name.startswith('sub-'):
        parts = path.name.split('_')
        if len(parts) >= 2:
            return parts[0].replace('sub-', '')
    return None


def load_physionet_eeg_data(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load all EEG files from the PhysioNet data directory.
    
    Args:
        data_dir: Path to raw EEG data directory
        
    Returns:
        List of dictionaries with file paths and subject IDs
    """
    data_path = Path(data_dir)
    eeg_files = []
    
    # Look for .edf files (standard format for PhysioNet EEG)
    edf_files = list(data_path.rglob('*.edf'))
    edf_files += list(data_path.rglob('*.EDF'))
    
    for file_path in edf_files:
        subject_id = get_subject_id_from_path(str(file_path))
        if subject_id:
            eeg_files.append({
                'path': str(file_path),
                'subject_id': subject_id,
                'filename': file_path.name
            })
    
    if not eeg_files:
        raise FileNotFoundError(f"No EEG files found in {data_dir}")
    
    return eeg_files


def preprocess_subject(
    file_path: str,
    subject_id: str,
    output_dir: str,
    no_ica: bool = False,
    filter_params: Optional[Dict] = None,
    variance_threshold: float = 3.0,
    exclusion_threshold: float = 0.30
) -> Dict[str, Any]:
    """
    Preprocess a single subject's EEG data.
    
    Args:
        file_path: Path to the raw EEG file
        subject_id: Subject identifier
        output_dir: Directory to save cleaned data
        no_ica: If True, skip ICA cleaning
        filter_params: Dictionary with filter parameters (lowcut, highcut, notch_freqs)
        variance_threshold: Channels with variance > threshold * median are rejected
        exclusion_threshold: Exclude subject if > this fraction of channels are rejected
        
    Returns:
        Dictionary with processing results and statistics
    """
    if filter_params is None:
        filter_params = get_filter_params()
    
    results = {
        'subject_id': subject_id,
        'input_file': file_path,
        'output_file': None,
        'status': 'success',
        'channels_rejected': 0,
        'total_channels': 0,
        'rejection_rate': 0.0,
        'excluded': False,
        'ica_components_removed': 0,
        'message': ''
    }
    
    try:
        # Load raw data
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        
        # Set montage if available (standard 10-20 system)
        try:
            montage = mne.channels.make_standard_montage('standard_1005')
            raw.set_montage(montage, match_case=False, match_alias=True, on_missing='ignore')
        except Exception as e:
            results['message'] += f"Montage setting failed: {str(e)}. "
        
        # Filter: Band-pass 1-40 Hz
        lowcut = filter_params.get('lowcut', 1.0)
        highcut = filter_params.get('highcut', 40.0)
        raw = bandpass_filter(raw, lowcut, highcut, verbose=False)
        
        # Notch filter: 50 Hz or 60 Hz (depending on region)
        # We'll apply both to be safe, or detect from file
        notch_freqs = filter_params.get('notch_freqs', [50.0, 60.0])
        for freq in notch_freqs:
            raw = notch_filter(raw, freq, verbose=False)
        
        # Store total channels before rejection
        results['total_channels'] = len(raw.ch_names)
        
        # Reject channels with high variance (>3SD from median)
        raw, rejected_indices = reject_channels_by_variance(
            raw, threshold=variance_threshold, verbose=False
        )
        results['channels_rejected'] = len(rejected_indices)
        
        # Calculate rejection rate
        results['rejection_rate'] = results['channels_rejected'] / results['total_channels']
        
        # Check exclusion criteria
        if results['rejection_rate'] > exclusion_threshold:
            results['excluded'] = True
            results['status'] = 'excluded'
            results['message'] = f"Excluded: {results['rejection_rate']:.1%} channels rejected (>30% threshold)"
            return results
        
        # ICA cleaning (unless --no-ica flag is set)
        if not no_ica:
            raw, n_removed = apply_ica(raw, verbose=False)
            results['ica_components_removed'] = n_removed
        
        # Save cleaned data
        output_path = Path(output_dir) / f"sub-{subject_id}_cleaned.fif"
        raw.save(str(output_path), overwrite=True, verbose=False)
        results['output_file'] = str(output_path)
        
        # Store channel info
        results['final_channels'] = len(raw.ch_names)
        results['sfreq'] = raw.info['sfreq']
        results['ch_names'] = raw.ch_names
        
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f"Processing error: {str(e)}"
    
    return results


def main():
    """Main entry point for EEG preprocessing."""
    parser = argparse.ArgumentParser(
        description='Preprocess EEG data from PhysioNet dataset'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default=None,
        help='Path to raw EEG data directory (default: from config)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Path to output directory (default: data/interim/cleaned_eeg)'
    )
    parser.add_argument(
        '--no-ica',
        action='store_true',
        help='Skip ICA cleaning for robustness testing'
    )
    parser.add_argument(
        '--variance-threshold',
        type=float,
        default=3.0,
        help='Variance threshold for channel rejection (default: 3.0)'
    )
    parser.add_argument(
        '--exclusion-threshold',
        type=float,
        default=0.30,
        help='Exclusion threshold for participant rejection (default: 0.30)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    get_seed()
    
    # Get paths
    data_dir = args.data_dir or str(get_path('raw_eeg'))
    output_dir = args.output_dir or str(get_path('cleaned_eeg'))
    
    # Ensure output directory exists
    ensure_dirs([output_dir])
    
    print(f"Loading EEG data from: {data_dir}")
    try:
        eeg_files = load_physionet_eeg_data(data_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Found {len(eeg_files)} EEG files")
    
    # Process each subject
    results = []
    excluded_count = 0
    error_count = 0
    
    for file_info in eeg_files:
        print(f"\nProcessing subject {file_info['subject_id']}...")
        
        result = preprocess_subject(
            file_path=file_info['path'],
            subject_id=file_info['subject_id'],
            output_dir=output_dir,
            no_ica=args.no_ica,
            variance_threshold=args.variance_threshold,
            exclusion_threshold=args.exclusion_threshold
        )
        
        results.append(result)
        
        if result['status'] == 'excluded':
            excluded_count += 1
            print(f"  -> EXCLUDED: {result['message']}")
        elif result['status'] == 'error':
            error_count += 1
            print(f"  -> ERROR: {result['message']}")
        else:
            print(f"  -> SUCCESS: {result['final_channels']} channels, "
                  f"{result['ica_components_removed']} ICA components removed")
    
    # Save processing log
    log_path = Path(output_dir) / 'preprocessing_log.json'
    import json
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PREPROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total subjects processed: {len(results)}")
    print(f"Successfully cleaned: {len(results) - excluded_count - error_count}")
    print(f"Excluded (>30% channels rejected): {excluded_count}")
    print(f"Errors: {error_count}")
    print(f"Output directory: {output_dir}")
    print(f"Log saved to: {log_path}")
    
    if excluded_count > 0:
        print(f"\nWARNING: {excluded_count} subjects excluded due to excessive channel rejection.")
    
    return results


if __name__ == '__main__':
    main()
