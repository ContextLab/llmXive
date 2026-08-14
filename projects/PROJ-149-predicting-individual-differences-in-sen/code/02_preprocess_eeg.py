"""
EEG Preprocessing Script (Part 2): Participant Exclusion Logic.

This script implements T010b: Apply participant exclusion logic.
Constraint: Exclude participant if channels_rejected / total_channels > 0.30.
Output: data/interim/cleaned_eeg_final/ directory containing .fif files for retained participants
        and data/interim/exclusion_log.csv.
"""
import os
import sys
import glob
import argparse
import numpy as np
import mne
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import local config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_path, ensure_dirs, get_exclusion_params, set_global_seed

# Import from utils
from utils.eeg_helpers import reject_channels_by_variance, apply_ica

def get_subject_id_from_path(file_path: str) -> str:
    """Extract subject ID from file path."""
    filename = os.path.basename(file_path)
    # Expected format: sub-<id>_task-<task>_...
    if filename.startswith("sub-"):
        parts = filename.split("_")
        if len(parts) > 0:
            return parts[0].replace("sub-", "")
    return os.path.splitext(filename)[0]

def load_physionet_eeg_data(input_dir: str) -> List[str]:
    """Load list of EEG files from input directory."""
    pattern = os.path.join(input_dir, "*.fif")
    files = glob.glob(pattern)
    return sorted(files)

def preprocess_subject(
    raw_path: str,
    output_dir: str,
    exclude_ratio_threshold: float = 0.30
) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
    """
    Process a single subject's EEG data and apply exclusion logic.
    
    Args:
        raw_path: Path to the cleaned (ICA applied) .fif file from T010a
        output_dir: Directory to save retained .fif files
        exclude_ratio_threshold: Threshold for channel rejection ratio (default 0.30)
    
    Returns:
        Tuple of (processed_raw or None, metadata_dict)
    """
    subject_id = get_subject_id_from_path(raw_path)
    metadata = {
        "subject_id": subject_id,
        "input_file": raw_path,
        "excluded": False,
        "reason": "",
        "total_channels": 0,
        "channels_rejected": 0,
        "rejection_ratio": 0.0,
        "output_file": None
    }
    
    try:
        # Load the already cleaned data (from T010a)
        raw = mne.io.read_raw_fif(raw_path, preload=True)
        metadata["total_channels"] = len(raw.ch_names)
        
        # Count bad channels (already marked in T010a or via variance)
        # We assume T010a already applied ICA and marked bad channels
        # Here we just verify the count against the threshold
        
        # Get bad channels
        bad_channels = raw.info['bads']
        metadata["channels_rejected"] = len(bad_channels)
        
        # Calculate rejection ratio
        if metadata["total_channels"] > 0:
            metadata["rejection_ratio"] = metadata["channels_rejected"] / metadata["total_channels"]
        
        # Apply exclusion logic
        if metadata["rejection_ratio"] > exclude_ratio_threshold:
            metadata["excluded"] = True
            metadata["reason"] = f"Channel rejection ratio ({metadata['rejection_ratio']:.2f}) exceeds threshold ({exclude_ratio_threshold})"
            return None, metadata
        
        # If not excluded, save the file
        output_filename = f"sub-{subject_id}_cleaned.fif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the raw object
        raw.save(output_path, overwrite=True)
        metadata["output_file"] = output_path
        
        return raw, metadata
        
    except Exception as e:
        metadata["excluded"] = True
        metadata["reason"] = f"Error processing file: {str(e)}"
        return None, metadata

def main():
    """Main execution function for T010b."""
    parser = argparse.ArgumentParser(description="EEG Preprocessing Part 2: Participant Exclusion")
    parser.add_argument("--input-dir", type=str, default=None,
                        help="Input directory containing cleaned EEG files (from T010a)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for retained EEG files")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Channel rejection ratio threshold (default from config)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Resolve paths
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = get_path("interim", "cleaned_eeg_raw")
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = get_path("interim", "cleaned_eeg_final")
    
    # Get threshold from args or config
    if args.threshold:
        threshold = args.threshold
    else:
        config_params = get_exclusion_params()
        threshold = config_params.get("max_channel_rejection_ratio", 0.30)
    
    print(f"Starting T010b: Participant Exclusion")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Exclusion threshold: {threshold}")
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    # Get list of input files
    input_files = load_physionet_eeg_data(input_dir)
    
    if not input_files:
        print(f"No files found in {input_dir}")
        # Still create empty logs
        exclusion_log_path = get_path("interim", "exclusion_log.csv")
        ensure_dirs(exclusion_log_path)
        pd.DataFrame(columns=[
            "subject_id", "input_file", "excluded", "reason",
            "total_channels", "channels_rejected", "rejection_ratio", "output_file"
        ]).to_csv(exclusion_log_path, index=False)
        return
    
    print(f"Found {len(input_files)} files to process")
    
    # Process each subject
    results = []
    retained_count = 0
    excluded_count = 0
    
    for file_path in input_files:
        print(f"Processing: {file_path}")
        raw, metadata = preprocess_subject(file_path, output_dir, threshold)
        results.append(metadata)
        
        if metadata["excluded"]:
            excluded_count += 1
            print(f"  -> EXCLUDED: {metadata['reason']}")
        else:
            retained_count += 1
            print(f"  -> RETAINED")
    
    # Create exclusion log
    df_results = pd.DataFrame(results)
    exclusion_log_path = get_path("interim", "exclusion_log.csv")
    ensure_dirs(exclusion_log_path)
    df_results.to_csv(exclusion_log_path, index=False)
    
    print(f"\n--- Summary ---")
    print(f"Total processed: {len(input_files)}")
    print(f"Retained: {retained_count}")
    print(f"Excluded: {excluded_count}")
    print(f"Exclusion log saved to: {exclusion_log_path}")
    print(f"Retained EEG files saved to: {output_dir}")

if __name__ == "__main__":
    main()