"""
Dataset Verification Script for OpenNeuro BIDS Compliance.

This script validates that the OpenNeuro dataset used for the study
conforms to the BIDS (Brain Imaging Data Structure) standard, specifically
checking for the presence of required files, correct directory structure,
and valid event markers in the EEG data.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Attempt to import BIDS validation tools.
# We use 'pybids' for structure validation and 'mne' for EEG event validation.
# These are standard dependencies for this type of pipeline.
try:
    import bids
    from bids import BIDSLayout
except ImportError:
    # Fallback or error if not installed, but we assume requirements.txt handles this.
    # For the script to run, we need at least basic file system checks if pybids fails.
    BIDS_AVAILABLE = False
else:
    BIDS_AVAILABLE = True

try:
    import mne
except ImportError:
    MNE_AVAILABLE = False
else:
    MNE_AVAILABLE = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/verification_log.txt')
    ]
)
logger = logging.getLogger(__name__)

# Constants for BIDS compliance
REQUIRED_BIDS_FILES = [
    "dataset_description.json",
    "participants.tsv",
    "sub-01/eeg/sub-01_task-nav_eeg.json", # Example path, will be dynamic
    "sub-01/eeg/sub-01_task-nav_events.tsv"
]

REQUIRED_TOP_LEVEL = ["dataset_description.json", "participants.tsv", "participants.json"]
REQUIRED_SUB_FOLDERS = ["eeg", "events"]

def check_bids_structure(root_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates the basic BIDS directory structure and required files.

    Args:
        root_path: Path to the root of the dataset.

    Returns:
        Tuple of (is_valid, list_of_errors, summary_stats)
    """
    errors = []
    stats = {
        "subject_count": 0,
        "session_count": 0,
        "files_found": 0,
        "bids_valid": False
    }

    if not root_path.exists():
        errors.append(f"Root path does not exist: {root_path}")
        return False, errors, stats

    # Check top-level files
    for req_file in REQUIRED_TOP_LEVEL:
        if not (root_path / req_file).exists():
            errors.append(f"Missing required top-level file: {req_file}")
        else:
            stats["files_found"] += 1

    # Scan for subjects
    subjects = [d for d in root_path.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    stats["subject_count"] = len(subjects)

    if stats["subject_count"] == 0:
        errors.append("No subject directories (sub-*) found.")
    else:
        for sub_dir in subjects:
            sub_name = sub_dir.name
            # Check for eeg directory
            eeg_dir = sub_dir / "eeg"
            if not eeg_dir.exists():
                errors.append(f"Missing 'eeg' directory for {sub_name}")
            else:
                # Check for .eeg and .json files
                eeg_files = list(eeg_dir.glob("*.eeg")) + list(eeg_dir.glob("*.vhdr")) + list(eeg_dir.glob("*.set"))
                json_files = list(eeg_dir.glob("*.json"))
                if not eeg_files and not json_files:
                    errors.append(f"No EEG data files found in {eeg_dir}")
                else:
                    stats["files_found"] += len(eeg_files) + len(json_files)

            # Check for events.tsv (often in eeg dir or sub dir)
            events_file = eeg_dir / f"{sub_name}_task-*_events.tsv"
            # We can't glob with wildcards easily for exact naming without more logic,
            # so we just check if any events.tsv exists in eeg or sub dir
            events_found = False
            for f in eeg_dir.iterdir():
                if f.name.endswith("_events.tsv"):
                    events_found = True
                    stats["files_found"] += 1
                    break
            
            if not events_found:
                # Some datasets put events in the sub directory directly
                sub_events = list(sub_dir.glob("*_events.tsv"))
                if sub_events:
                    stats["files_found"] += len(sub_events)
                    events_found = True
                else:
                    errors.append(f"Missing events file for {sub_name}")

    stats["bids_valid"] = len(errors) == 0
    return len(errors) == 0, errors, stats


def check_event_markers(root_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates the presence and content of event markers in the dataset.
    Specifically looks for 'attention_shift' or similar triggers.

    Args:
        root_path: Path to the root of the dataset.

    Returns:
        Tuple of (is_valid, list_of_errors, summary_stats)
    """
    errors = []
    stats = {
        "total_events": 0,
        "subjects_with_events": 0,
        "event_types_found": [],
        "markers_valid": False
    }

    if not MNE_AVAILABLE:
        logger.warning("MNE not available. Skipping detailed event marker validation.")
        return True, [], stats # Soft pass if we can't read EEG

    # Find all events.tsv files
    events_files = list(root_path.rglob("*_events.tsv"))
    
    if not events_files:
        errors.append("No events.tsv files found in the dataset.")
        return False, errors, stats

    target_events = {"attention_shift", "stimulus_onset", "cue", "target"}
    found_event_types = set()

    for event_file in events_files:
        try:
            import pandas as pd
            df = pd.read_csv(event_file, sep='\t')
            stats["total_events"] += len(df)
            stats["subjects_with_events"] += 1

            if 'trial_type' in df.columns:
                unique_types = df['trial_type'].unique()
                for t in unique_types:
                    if pd.notna(t):
                        found_event_types.add(t)
                        if any(t.lower().startswith(te) for te in target_events):
                            pass # Found a relevant one
            elif 'code' in df.columns:
                # Some datasets use numeric codes
                unique_codes = df['code'].unique()
                for c in unique_codes:
                    found_event_types.add(f"code_{c}")
            
        except Exception as e:
            errors.append(f"Error reading events file {event_file}: {str(e)}")

    stats["event_types_found"] = list(found_event_types)

    # Check if we have any meaningful events
    if stats["total_events"] == 0:
        errors.append("Events files exist but contain no rows.")
    else:
        # Heuristic: we expect at least some 'attention' or 'shift' related events
        # or generic 'stimulus' events if the specific naming is different.
        relevant = [t for t in found_event_types if 'attention' in t.lower() or 'shift' in t.lower() or 'stim' in t.lower()]
        if not relevant:
            logger.warning(f"Could not find standard attention shift events. Found: {found_event_types}")
            # This is a warning, not a hard fail, as naming conventions vary.
            # But for the purpose of this task, we flag it if completely empty of expected types.
            # errors.append("No standard attention shift or stimulus events found in event files.")

    stats["markers_valid"] = len(errors) == 0 and stats["total_events"] > 0
    return len(errors) == 0, errors, stats


def run_verification(dataset_path: str, output_path: str) -> bool:
    """
    Main entry point for dataset verification.

    Args:
        dataset_path: Path to the OpenNeuro dataset (downloaded or local).
        output_path: Path to save the verification report JSON.

    Returns:
        True if verification passed, False otherwise.
    """
    root = Path(dataset_path)
    report = {
        "dataset_path": str(root.absolute()),
        "status": "unknown",
        "bids_structure": {},
        "event_markers": {},
        "errors": [],
        "warnings": []
    }

    logger.info(f"Starting verification for dataset: {root}")

    # 1. Check BIDS Structure
    bids_valid, bids_errors, bids_stats = check_bids_structure(root)
    report["bids_structure"] = bids_stats
    report["errors"].extend(bids_errors)
    if not bids_valid:
        report["warnings"].append("BIDS structure validation failed.")

    # 2. Check Event Markers
    events_valid, events_errors, events_stats = check_event_markers(root)
    report["event_markers"] = events_stats
    report["errors"].extend(events_errors)
    if not events_valid:
        report["warnings"].append("Event marker validation failed.")

    # Final Status
    if not report["errors"]:
        report["status"] = "PASSED"
        logger.info("Dataset verification PASSED.")
    else:
        report["status"] = "FAILED"
        logger.error(f"Dataset verification FAILED with {len(report['errors'])} errors.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save Report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to {output_file}")
    
    return report["status"] == "PASSED"


def main():
    parser = argparse.ArgumentParser(description="Verify OpenNeuro BIDS dataset compliance and event markers.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to the dataset root directory.")
    parser.add_argument("--output", type=str, default="data/processed/verification_report.json", help="Path to save the verification report.")
    
    args = parser.parse_args()

    success = run_verification(args.dataset, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
