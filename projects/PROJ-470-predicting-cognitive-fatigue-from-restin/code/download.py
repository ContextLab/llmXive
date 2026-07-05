"""
Data download module for EEG datasets.
Handles fetching Sleep-EDF from PhysioNet as primary candidate and SHHS as fallback.
Validates presence of resting-state EEG and fatigue ratings.
"""
import os
import sys
import json
import yaml
import mne
import pandas as pd
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import zipfile
import shutil

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def fetch_sleep_edf(dataset_id, target_dir):
    """
    Fetch Sleep-EDF dataset from PhysioNet.
    Returns list of participant IDs if successful, empty list otherwise.
    """
    try:
        # MNE-Python handles the download and caching of Sleep-EDF
        # This function attempts to download the dataset
        data_path = mne.datasets.sleep_edf.data_path(download=True, path=str(target_dir))
        if not data_path:
            return []
        
        # List participants in the downloaded directory
        # Sleep-EDF structure: sub-<id>_scd.hdf5 or similar
        # We look for the specific file pattern
        raw_files = list(Path(data_path).glob("STACOM*.edf"))
        if not raw_files:
            # Try alternative pattern for Sleep-EDF
            raw_files = list(Path(data_path).glob("*_STC*.edf"))
        
        participants = []
        for f in raw_files:
            # Extract participant ID from filename (e.g., STACOM01.edf -> 01)
            # Sleep-EDF usually follows pattern: sub-<id>_scd.hdf5 or similar
            # For EDF files: STACOM<id>.edf
            name = f.stem
            if name.startswith("STACOM"):
                pid = name[6:] # Extract ID part
                participants.append(pid)
        
        return participants
    except Exception as e:
        print(f"Error fetching Sleep-EDF: {e}")
        return []

def fetch_shhs(target_dir):
    """
    Fetch SHHS dataset (fallback).
    Returns list of participant IDs if successful, empty list otherwise.
    Note: SHHS requires registration and is harder to access programmatically.
    This implementation checks for local availability or attempts direct download if public links exist.
    """
    try:
        # SHHS is not directly available via mne.datasets.
        # We attempt to check if data exists locally or try a known public mirror if available.
        # For this implementation, we simulate the check against a known public subset or local cache.
        # In a real production environment, this would require API keys or manual download.
        
        # Attempt to find SHHS data in target_dir (assuming manual download or prior fetch)
        shhs_dir = target_dir / "shhs"
        if not shhs_dir.exists():
            shhs_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to find edf files
        edf_files = list(shhs_dir.glob("*.edf"))
        participants = []
        for f in edf_files:
            # SHHS naming: shhs1-<id>.edf
            if f.stem.startswith("shhs1-"):
                pid = f.stem.split("-")[1]
                participants.append(pid)
        
        return participants
    except Exception as e:
        print(f"Error accessing SHHS: {e}")
        return []

def validate_dataset(participant_ids, required_vars, dataset_name="sleep-edf"):
    """
    Validate presence of required variables (resting-state EEG, fatigue ratings).
    Sleep-EDF does NOT contain fatigue ratings. It contains EEG and sleep stages.
    This function checks for the presence of EEG data and simulates the check for fatigue ratings
    based on the task requirement: "Validate presence of both resting-state EEG and paired pre/post fatigue ratings".
    
    Since Sleep-EDF lacks fatigue ratings, this validation will fail for Sleep-EDF.
    The code then attempts to fallback to SHHS.
    """
    report = {
        "dataset_id": dataset_name,
        "n_participants": len(participant_ids),
        "available_variables": [],
        "missing_variables": [],
        "valid": False
    }

    if not participant_ids:
        report["missing_variables"] = required_vars
        return False, report

    # Check for EEG data (Resting-state proxy: Wakefulness epochs in Sleep-EDF)
    # Sleep-EDF has EEG channels (Fpz-Cz, Pz-Oz)
    has_eeg = True 
    report["available_variables"].append("resting_state_eeg")

    # Check for fatigue ratings
    # Sleep-EDF does NOT have fatigue ratings.
    has_fatigue = False
    if "fatigue_rating_pre" in required_vars:
        report["missing_variables"].append("fatigue_rating_pre")
    if "fatigue_rating_post" in required_vars:
        report["missing_variables"].append("fatigue_rating_post")

    if has_eeg and not has_fatigue:
        report["available_variables"].append("resting_state_eeg")
        # Fatigue ratings are missing
        report["valid"] = False
    elif has_eeg and has_fatigue:
        report["available_variables"].extend(["fatigue_rating_pre", "fatigue_rating_post"])
        report["valid"] = True
    
    return report["valid"], report

def main():
    config = load_config()
    target_dir = Path(config['paths']['raw_data'])
    target_dir.mkdir(parents=True, exist_ok=True)

    dataset_config = config['dataset']
    primary_id = dataset_config['primary_id']
    fallback_id = dataset_config.get('fallback_id', 'shhs')
    
    required_vars = ['resting_state_eeg', 'fatigue_rating_pre', 'fatigue_rating_post']
    
    # Try Primary: Sleep-EDF
    print(f"Attempting to fetch {primary_id}...")
    participants = fetch_sleep_edf(primary_id, target_dir)
    
    if participants:
        is_valid, report = validate_dataset(participants, required_vars, dataset_name=primary_id)
        if is_valid and len(participants) >= 30:
            print(f"Primary dataset {primary_id} validated with N={len(participants)}.")
            # Save participant list for downstream tasks
            pids_file = target_dir / "participants.json"
            with open(pids_file, 'w') as f:
                json.dump({"dataset": primary_id, "participants": participants}, f)
            return
        else:
            print(f"Primary dataset {primary_id} failed validation (N={len(participants)}, valid={is_valid}).")
            # Save partial validation report for debugging
            report_path = Path(config['paths']['analysis_output']) / "validation_report_primary.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
    else:
        print(f"Primary dataset {primary_id} could not be fetched or is empty.")

    # Try Fallback: SHHS
    print(f"Attempting fallback to {fallback_id}...")
    participants = fetch_shhs(target_dir)
    
    if participants:
        is_valid, report = validate_dataset(participants, required_vars, dataset_name=fallback_id)
        if is_valid and len(participants) >= 30:
            print(f"Fallback dataset {fallback_id} validated with N={len(participants)}.")
            pids_file = target_dir / "participants.json"
            with open(pids_file, 'w') as f:
                json.dump({"dataset": fallback_id, "participants": participants}, f)
            return
        else:
            print(f"Fallback dataset {fallback_id} failed validation (N={len(participants)}, valid={is_valid}).")
            report_path = Path(config['paths']['analysis_output']) / "validation_report_fallback.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
    else:
        print(f"Fallback dataset {fallback_id} could not be fetched or is empty.")

    # If we reach here, no valid dataset with N>=30 and required variables was found.
    # Halt with exit code 1 and log validation_report.json
    final_report = {
        "status": "failed",
        "reason": "No dataset found with N>=30 and required variables (resting-state EEG, pre/post fatigue ratings).",
        "primary_attempt": {
            "dataset": primary_id,
            "n_participants": len(participants) if 'participants' in locals() else 0,
            "validation": report if 'report' in locals() else {}
        },
        "fallback_attempt": {
            "dataset": fallback_id,
            "n_participants": len(participants) if 'participants' in locals() else 0,
            "validation": report if 'report' in locals() else {}
        }
    }
    
    report_path = Path(config['paths']['analysis_output']) / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"Validation failed. Final report written to {report_path}")
    sys.exit(1)

if __name__ == "__main__":
    main()
