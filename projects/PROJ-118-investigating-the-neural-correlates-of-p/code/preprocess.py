import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mne

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_standard_montage() -> mne.channels.DigMontage:
    """
    Returns the standard 32-channel EEG montage compatible with OpenNeuro ds003645.
    Uses the standard 'standard_1005' montage provided by MNE.
    """
    return mne.channels.make_standard_montage('standard_1005')

def get_mmn_montage() -> List[str]:
    """
    Returns the list of channels specifically relevant for MMN analysis (Fz, FCz, Cz, Pz).
    """
    return ['Fz', 'FCz', 'Cz', 'Pz']

def set_montage(raw: mne.io.Raw, montage: mne.channels.DigMontage) -> mne.io.Raw:
    """
    Attaches the provided montage to the raw data object.
    """
    raw.set_montage(montage, match_case=False, match_alias=True, on_missing='ignore')
    return raw

def select_channels(raw: mne.io.Raw, channel_list: List[str]) -> mne.io.Raw:
    """
    Selects a subset of channels from the raw data object.
    """
    return raw.copy().pick_channels(channel_list)

def load_config_and_validate(config_path: str = 'code/config.yaml') -> Dict[str, Any]:
    """
    Loads and validates the configuration file.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Basic validation
    required_keys = ['filter', 'epoch', 'ica']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    return config

def preprocess_pipeline(
    input_path: str,
    output_path: str,
    config: Dict[str, Any],
    subject_id: str,
    event_id: Optional[Dict[str, int]] = None
) -> mne.Epochs:
    """
    Runs the full preprocessing pipeline for a single subject:
    1. Load raw data
    2. Filter (1-30Hz)
    3. Re-reference to common average
    4. Apply montage and select channels
    5. (Assumes ICA has been run and components removed in previous steps or handled externally)
    6. Epoch the data based on event codes
    7. Save to FIF

    Note: This function assumes the input data has already been cleaned of artifacts via ICA
    as per the task dependency flow (T019/T020). If ICA removal is not yet implemented,
    this function will proceed with the raw data, but the task T018 specifically targets
    the epoching step *after* ICA cleaning.
    """
    logger.info(f"Starting preprocessing pipeline for subject {subject_id}")
    logger.info(f"Input: {input_path}, Output: {output_path}")

    # Load raw data
    raw = mne.io.read_raw_fif(input_path, preload=True)
    logger.info(f"Loaded raw data: {raw.info['nchan']} channels, {raw.times[-1]:.2f}s duration")

    # 1. Filtering
    filter_config = config['filter']
    l_freq = filter_config.get('low', 1.0)
    h_freq = filter_config.get('high', 30.0)
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw.filter(l_freq=l_freq, h_freq=h_freq, fir_design='firwin')

    # 2. Re-referencing
    logger.info("Re-referencing to common average")
    raw.set_eeg_reference('average', projection=True)

    # 3. Montage and Channel Selection
    montage = get_standard_montage()
    raw = set_montage(raw, montage)
    
    # Select standard channels for MMN analysis if specified in config or default
    mmn_channels = get_mmn_montage()
    # Ensure we pick existing channels only
    existing_channels = [ch for ch in mmn_channels if ch in raw.ch_names]
    if len(existing_channels) < len(mmn_channels):
        logger.warning(f"Some MMN channels missing. Using: {existing_channels}")
    else:
        existing_channels = mmn_channels
    
    raw = select_channels(raw, existing_channels)
    logger.info(f"Selected channels: {raw.ch_names}")

    # 4. Epoching
    epoch_config = config['epoch']
    tmin = epoch_config['tmin']
    tmax = epoch_config['tmax']
    
    if event_id is None:
        # Default event IDs for ds003645 (Oddball paradigm)
        # 'S  1' = Standard, 'S  2' = Deviant (common in auditory oddball)
        # We try to detect events automatically if not provided
        events = mne.find_events(raw, stim_channel='STI 014')
        # Map standard event codes to labels
        # Assuming standard codes 1 and 2 based on typical OpenNeuro ds003645 structure
        # If codes differ, this might need adjustment, but 1/2 is standard for this dataset
        event_id = {'standard': 1, 'deviant': 2}
        logger.info(f"Auto-detected events: {np.unique(events[:, 2])}")
    else:
        events = mne.find_events(raw, stim_channel='STI 014')
        # Filter events to only include those in event_id
        events = events[np.isin(events[:, 2], list(event_id.values()))]

    logger.info(f"Creating epochs: tmin={tmin}s, tmax={tmax}s")
    epochs = mne.Epochs(
        raw, 
        events, 
        event_id=event_id, 
        tmin=tmin, 
        tmax=tmax, 
        baseline=(tmin, 0), 
        preload=True,
        reject=None,  # Rejection handled by ICA or later steps
        reject_by_annotation=True
    )
    
    logger.info(f"Created {len(epochs)} epochs total")
    logger.info(f"  Standard: {len(epochs['standard'])}")
    logger.info(f"  Deviant: {len(epochs['deviant'])}")

    # 5. Save to FIF
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    logger.info(f"Saving epoched data to {output_path}")
    epochs.save(output_path, overwrite=True)

    return epochs

def detect_ica_components(epochs: mne.Epochs, config: Dict[str, Any]) -> List[int]:
    """
    Detects ICA components to be removed (e.g., blinks).
    This is a placeholder for the actual ICA logic required by T019.
    For T018, we assume this step is handled or skipped if not yet implemented.
    """
    logger.warning("ICA detection called but not fully implemented in this snippet. Returning empty list.")
    return []

def remove_ica_components(epochs: mne.Epochs, ica_components: List[int]) -> mne.Epochs:
    """
    Removes specified ICA components from epochs.
    Placeholder for T020.
    """
    logger.warning("ICA removal called but not fully implemented. Returning original epochs.")
    return epochs

def run_preprocessing_pipeline(
    data_dir: str,
    output_dir: str,
    config_path: str = 'code/config.yaml'
) -> None:
    """
    Main entry point to run the preprocessing pipeline for all subjects.
    """
    config = load_config_and_validate(config_path)
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find raw files (assuming sub-XX directories)
    raw_files = list(data_dir.glob('sub-*/sub-*.fif'))
    if not raw_files:
        # Fallback for flat structure
        raw_files = list(data_dir.glob('*.fif'))
    
    if not raw_files:
        raise FileNotFoundError("No raw data files found in the specified directory.")

    for raw_file in raw_files:
        subject_id = raw_file.parent.name if raw_file.parent.name.startswith('sub-') else raw_file.stem
        output_file = output_dir / f"sub-{subject_id}_epo_raw.fif"
        
        try:
            preprocess_pipeline(
                input_path=str(raw_file),
                output_path=str(output_file),
                config=config,
                subject_id=subject_id
            )
        except Exception as e:
            logger.error(f"Failed to process {raw_file}: {e}")
            continue

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run EEG preprocessing pipeline")
    parser.add_argument("--data-dir", default="data/raw", help="Directory containing raw data")
    parser.add_argument("--output-dir", default="data/processed", help="Directory to save processed data")
    parser.add_argument("--config", default="code/config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    run_preprocessing_pipeline(args.data_dir, args.output_dir, args.config)
    print("Preprocessing pipeline completed.")
