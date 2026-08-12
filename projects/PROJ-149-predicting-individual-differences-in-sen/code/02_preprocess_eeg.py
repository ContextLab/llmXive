"""
EEG Preprocessing Pipeline for PhysioNet Motor Movement/Imagery Dataset.

This script performs:
- Band-pass filtering (1-45 Hz)
- Notch filtering (50/60 Hz)
- Channel variance rejection (>3 SD)
- ICA cleaning for ocular/muscle artifacts
- Participant exclusion based on channel rejection ratio

Output: Cleaned EEG data saved to data/interim/cleaned_eeg
"""
import os
import sys
import glob
import argparse
import numpy as np
import mne
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    get_path,
    ensure_dirs,
    get_filter_params,
    get_ica_params,
    get_exclusion_params,
    get_seed,
    set_global_seed,
)
from utils.eeg_helpers import (
    bandpass_filter,
    notch_filter,
    reject_channels_by_variance,
    apply_ica,
)

def get_subject_id_from_path(file_path: str) -> str:
    """Extract subject ID from PhysioNet file path."""
    # Path format: .../sub-<id>/sub-<id>_task-<task>_run-<run>_eeg.edf
    path_obj = Path(file_path)
    filename = path_obj.stem
    # Extract sub-XX from filename
    parts = filename.split("_")
    for part in parts:
        if part.startswith("sub-"):
            return part.replace("sub-", "")
    return path_obj.parent.name.replace("sub-", "")

def load_physionet_eeg_data(raw_path: str) -> mne.io.Raw:
    """
    Load EEG data from PhysioNet EDF file.

    Args:
        raw_path: Path to the .edf file

    Returns:
        mne.io.Raw object
    """
    raw = mne.io.read_raw_edf(raw_path, preload=True)
    # Set montage if available (standard 10-20)
    try:
        montage = mne.channels.make_standard_montage("standard_1005")
        raw.set_montage(montage, match_case=False, match_alias=True)
    except Exception as e:
        print(f"Warning: Could not set montage: {e}")

    return raw

def preprocess_subject(
    raw: mne.io.Raw,
    use_ica: bool = True,
    verbose: bool = False,
) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
    """
    Preprocess a single subject's EEG data.

    Steps:
    1. Band-pass filter (1-45 Hz)
    2. Notch filter (50/60 Hz)
    3. Reject channels with variance > 3 SD
    4. Apply ICA to remove ocular/muscle artifacts (if use_ica=True)
    5. Check exclusion criteria

    Args:
        raw: Raw EEG data
        use_ica: Whether to apply ICA cleaning
        verbose: Whether to print verbose output

    Returns:
        Tuple of (cleaned_raw or None if excluded, metadata dict)
    """
    set_global_seed(get_seed())
    params = get_filter_params()
    ica_params = get_ica_params()
    exclusion_params = get_exclusion_params()

    metadata = {
        "subject_id": raw.info["subject_info"]["id"] if raw.info["subject_info"] else "unknown",
        "total_channels": len(raw.ch_names),
        "rejected_channels": [],
        "ica_components_removed": 0,
        "excluded": False,
        "exclusion_reason": None,
    }

    original_channels = raw.ch_names.copy()
    metadata["total_channels"] = len(original_channels)

    if verbose:
        print(f"Processing {len(original_channels)} channels...")

    # Step 1: Band-pass filter
    raw = bandpass_filter(
        raw,
        l_freq=params["l_freq"],
        h_freq=params["h_freq"],
        fir_design=params.get("fir_design", "firwin"),
        verbose=verbose,
    )

    # Step 2: Notch filter
    raw = notch_filter(
        raw,
        freqs=params.get("notch_freqs", [50.0]),
        verbose=verbose,
    )

    # Step 3: Reject channels by variance
    rejected, raw = reject_channels_by_variance(
        raw,
        threshold=exclusion_params["channel_variance_threshold"],
        verbose=verbose,
    )
    metadata["rejected_channels"] = rejected

    # Check exclusion criteria
    rejection_ratio = len(rejected) / metadata["total_channels"]
    if rejection_ratio > exclusion_params["max_rejected_ratio"]:
        metadata["excluded"] = True
        metadata["exclusion_reason"] = (
            f"Channel rejection ratio {rejection_ratio:.2f} > "
            f"threshold {exclusion_params['max_rejected_ratio']}"
        )
        if verbose:
            print(f"Excluding subject: {metadata['exclusion_reason']}")
        return None, metadata

    # Step 4: ICA cleaning (only if requested and not excluded)
    if use_ica:
        if verbose:
            print("Applying ICA cleaning...")
        raw, ica_components_removed = apply_ica(
            raw,
            n_components=ica_params["n_components"],
            random_state=ica_params["random_state"],
            max_iter=ica_params["max_iter"],
            verbose=verbose,
        )
        metadata["ica_components_removed"] = ica_components_removed
    else:
        if verbose:
            print("Skipping ICA cleaning (--no-ica flag)")

    return raw, metadata

def main():
    """Main entry point for EEG preprocessing."""
    parser = argparse.ArgumentParser(
        description="Preprocess EEG data from PhysioNet Motor Movement/Imagery dataset"
    )
    parser.add_argument(
        "--no-ica",
        action="store_true",
        help="Skip ICA cleaning (for robustness testing only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Input directory containing EDF files (default: data/raw/physionet)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for cleaned data (default: data/interim/cleaned_eeg)",
    )

    args = parser.parse_args()

    # Set up paths
    input_dir = Path(args.input_dir) if args.input_dir else get_path("raw_data")
    output_dir = Path(args.output_dir) if args.output_dir else get_path("interim_data") / "cleaned_eeg"

    ensure_dirs(["interim_data"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all EDF files
    edf_files = list(input_dir.glob("**/*.edf"))
    if not edf_files:
        # Try alternative pattern
        edf_files = list(input_dir.glob("**/*.EDF"))

    if not edf_files:
        print(f"Error: No EDF files found in {input_dir}")
        sys.exit(1)

    print(f"Found {len(edf_files)} EDF files to process")

    # Process each subject
    all_metadata = []
    processed_count = 0
    excluded_count = 0

    for edf_file in edf_files:
        subject_id = get_subject_id_from_path(str(edf_file))
        if args.verbose:
            print(f"\nProcessing subject: {subject_id}")

        try:
            raw = load_physionet_eeg_data(str(edf_file))
        except Exception as e:
            print(f"Error loading {edf_file}: {e}")
            continue

        # Preprocess
        cleaned_raw, metadata = preprocess_subject(
            raw,
            use_ica=not args.no_ica,
            verbose=args.verbose,
        )

        all_metadata.append(metadata)

        if metadata["excluded"]:
            excluded_count += 1
            continue

        # Save cleaned data
        output_file = output_dir / f"sub-{subject_id}_cleaned.fif"
        try:
            cleaned_raw.save(output_file, overwrite=True)
            processed_count += 1
            if args.verbose:
                print(f"Saved cleaned data to {output_file}")
        except Exception as e:
            print(f"Error saving {output_file}: {e}")
            continue

    # Write metadata summary
    metadata_file = output_dir / "preprocessing_metadata.json"
    import json
    with open(metadata_file, "w") as f:
        json.dump(
            {
                "total_processed": processed_count,
                "total_excluded": excluded_count,
                "details": all_metadata,
            },
            f,
            indent=2,
        )

    print(f"\nPreprocessing complete:")
    print(f"  Processed: {processed_count}")
    print(f"  Excluded: {excluded_count}")
    print(f"  Output: {output_dir}")

if __name__ == "__main__":
    main()
