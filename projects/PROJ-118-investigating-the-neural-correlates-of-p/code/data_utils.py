"""
Data loading schema and validation logic for the auditory oddball EEG pipeline.

This module provides functions to:
1. Validate configuration parameters against expected schemas.
2. Load raw EEG data from OpenNeuro (ds003645) format.
3. Validate data integrity (channel count, sampling rate, event presence).
"""
import os
import glob
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import mne
import numpy as np
import pandas as pd

from code.config import load_config

# Constants for validation
REQUIRED_CHANNELS = ['Fz', 'FCz', 'Cz', 'Pz', 'POz', 'Oz', 'F3', 'F4', 'C3', 'C4',
                     'P3', 'P4', 'F7', 'F8', 'T7', 'T8', 'P7', 'P8', 'O1', 'O2',
                     'Fz', 'FCz', 'Cz', 'Pz', 'POz', 'Oz'] # Simplified subset for demo, real list is longer
# Actual standard 32-channel montage names for OpenNeuro ds003645 (approx)
# We will validate against a standard set or allow flexible loading with warnings.
EXPECTED_SAMPLING_FREQ = 500.0  # Hz, typical for this dataset, allows tolerance

def validate_config_schema(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the loaded configuration dictionary against the expected schema.

    Args:
        config: The configuration dictionary loaded from YAML.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check required sections
    required_sections = ['preprocessing', 'epochs', 'ica']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required config section: {section}")

    if 'preprocessing' in config:
        pre = config['preprocessing']
        if 'filter' not in pre:
            errors.append("Missing 'filter' config in 'preprocessing'")
        else:
            f = pre['filter']
            if 'lowcut' not in f or 'highcut' not in f:
                errors.append("Missing 'lowcut' or 'highcut' in 'preprocessing.filter'")
            else:
                if not (0 < f['lowcut'] < f['highcut'] < 100):
                    errors.append("Invalid filter cutoffs: lowcut must be > 0 and < highcut < 100")

    if 'epochs' in config:
        e = config['epochs']
        if 'tmin' not in e or 'tmax' not in e:
            errors.append("Missing 'tmin' or 'tmax' in 'epochs'")
        elif not (e['tmin'] < 0 < e['tmax']):
            errors.append("Invalid epoch times: tmin must be negative and tmax positive")

    if 'ica' in config:
        i = config['ica']
        if 'threshold' not in i:
            errors.append("Missing 'threshold' in 'ica'")
        elif not (0.0 <= i['threshold'] <= 1.0):
            errors.append("Invalid ICA threshold: must be between 0.0 and 1.0")

    return len(errors) == 0, errors

def find_raw_files(data_dir: str) -> List[Path]:
    """
    Locates raw EEG files (.fif, .edf, etc.) in the data directory.

    Args:
        data_dir: Path to the raw data directory.

    Returns:
        List of Path objects pointing to raw files.
    """
    data_path = Path(data_dir)
    patterns = ['*.fif', '*.edf', '*.vhdr', '*.bdf']
    files = []
    for pattern in patterns:
        files.extend(data_path.glob(pattern))
        files.extend(data_path.glob(f'**/{pattern}'))
    
    # Filter out directories and ensure existence
    valid_files = [f for f in files if f.is_file()]
    return sorted(valid_files)

def load_raw_data(file_path: Path, preload: bool = False) -> mne.io.Raw:
    """
    Loads raw EEG data from a file using MNE-Python.

    Args:
        file_path: Path to the raw data file.
        preload: Whether to preload data into memory.

    Returns:
        MNE Raw object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or data is corrupted.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    try:
        raw = mne.io.read_raw_fif(file_path, preload=preload, verbose=False)
    except Exception:
        # Try other formats if FIF fails
        try:
            if file_path.suffix == '.edf':
                raw = mne.io.read_raw_edf(file_path, preload=preload, verbose=False)
            elif file_path.suffix == '.bdf':
                raw = mne.io.read_raw_bdf(file_path, preload=preload, verbose=False)
            else:
                # Generic reader attempt
                raw = mne.io.read_raw_raw(file_path, preload=preload, verbose=False)
        except Exception as e:
            raise ValueError(f"Failed to load file {file_path} as a known format: {e}")

    return raw

def validate_raw_data(raw: mne.io.Raw, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Validates the integrity of the loaded raw data.

    Checks:
    - Presence of expected channels (or at least a reasonable number).
    - Sampling frequency is within expected range.
    - Events are present if epoching is expected later.

    Args:
        raw: MNE Raw object.
        config: Optional configuration dict for specific validation rules.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    info = raw.info

    # Check sampling frequency
    sfreq = info['sfreq']
    if config and 'preprocessing' in config:
        # If config specifies expected sfreq, check it (with tolerance)
        # For ds003645, it's typically 500Hz
        if abs(sfreq - 500.0) > 10.0:
            errors.append(f"Unexpected sampling frequency: {sfreq} Hz (expected ~500 Hz)")

    # Check channel count
    ch_names = info['ch_names']
    if len(ch_names) < 10:
        errors.append(f"Very low channel count: {len(ch_names)}. Expected > 10 for EEG.")

    # Check for specific critical channels if config implies it
    # For ds003645, we expect standard 32+ channels
    critical_channels = ['Fz', 'Cz', 'Pz']
    missing_critical = [ch for ch in critical_channels if ch not in ch_names]
    if missing_critical:
        errors.append(f"Missing critical channels: {missing_critical}")

    # Check for events (stimulus channel or annotations)
    # ds003645 usually has events in a separate file or annotations
    has_events = len(raw.annotations) > 0 or 'STI 014' in ch_names
    if not has_events:
        # Not strictly an error for raw loading, but a warning for downstream
        errors.append("No events or annotations detected. Epoching may fail later.")

    return len(errors) == 0, errors

def load_config_and_validate() -> Tuple[Dict[str, Any], List[str]]:
    """
    Loads the configuration file and validates its schema.

    Returns:
        Tuple of (config_dict, list_of_errors).
    """
    config_path = Path('code/config.yaml')
    if not config_path.exists():
        return {}, ["Configuration file 'code/config.yaml' not found."]

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return {}, [f"Failed to load config.yaml: {e}"]

    is_valid, errors = validate_config_schema(config)
    if not is_valid:
        return config, errors

    return config, []

def get_subject_ids(raw_dir: str) -> List[str]:
    """
    Extracts subject IDs from the raw data directory structure.
    Assumes OpenNeuro-like structure: sub-XX/...

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        List of subject ID strings (e.g., 'sub-01').
    """
    raw_path = Path(raw_dir)
    subjects = []
    for item in raw_path.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    return sorted(subjects)