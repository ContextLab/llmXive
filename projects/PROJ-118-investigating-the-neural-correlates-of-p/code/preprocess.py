import os
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any
import mne
from mne.preprocessing import ICA

# Configure logging to file as well as console if needed
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_channel_montage(config: Dict[str, Any]) -> List[str]:
    """Extract the montage channel list from config."""
    return config.get('montage', {}).get('channels', [])

def get_filter_params(config: Dict[str, Any]) -> Dict[str, float]:
    """Extract filter parameters from config."""
    return config.get('filter', {'low': 1.0, 'high': 30.0})

def get_epoch_params(config: Dict[str, Any]) -> Dict[str, float]:
    """Extract epoch parameters from config."""
    return config.get('epoch', {'tmin': -0.2, 'tmax': 0.6})

def get_ica_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ICA parameters from config."""
    return config.get('ica', {'threshold': 0.8, 'n_components': 0.99})

def load_raw_data(raw_path: str) -> mne.io.BaseRaw:
    """Load raw data from file."""
    logger.info(f"Loading raw data from {raw_path}")
    return mne.io.read_raw_fif(raw_path, preload=True)

def subsample_channels(raw: mne.io.BaseRaw, channels: List[str]) -> mne.io.BaseRaw:
    """Subsample raw data to specified channels."""
    # Create a copy to avoid modifying the original
    raw_copy = raw.copy()
    # Filter channels to only those that exist in the data
    available_channels = [ch for ch in channels if ch in raw_copy.ch_names]
    missing_channels = [ch for ch in channels if ch not in raw_copy.ch_names]
    if missing_channels:
        logger.warning(f"Channels not found in data: {missing_channels}")
    raw_copy.pick_channels(available_channels)
    return raw_copy

def apply_filter_and_reference(raw: mne.io.BaseRaw, filter_params: Dict[str, float]) -> mne.io.BaseRaw:
    """Apply bandpass filter and re-reference to average."""
    raw_filtered = raw.copy()
    raw_filtered.filter(filter_params['low'], filter_params['high'])
    raw_filtered.set_eeg_reference('average')
    return raw_filtered

def epoch_data(raw: mne.io.BaseRaw, epoch_params: Dict[str, float], events: List[tuple]) -> mne.Epochs:
    """Create epochs from raw data."""
    # In a real scenario, events would be derived from the raw data or metadata
    # For this implementation, we assume events are provided or extracted
    # Here we simulate event extraction for the sake of the pipeline structure
    # In a real ds003645 dataset, events are typically in the raw object or sidecar
    if not events:
        # Fallback: create dummy events if none provided (should not happen in real run)
        logger.warning("No events provided, creating dummy events for demonstration")
        # This part would be replaced by actual event extraction logic in production
        events = mne.find_events(raw)
    
    epochs = mne.Epochs(
        raw,
        events,
        event_id={'standard': 1, 'deviant': 2}, # Assuming event codes 1 and 2
        tmin=epoch_params['tmin'],
        tmax=epoch_params['tmax'],
        baseline=(None, 0),
        reject=None, # We will handle rejection manually to log counts
        preload=True
    )
    return epochs

def run_ica_and_clean(epochs: mne.Epochs, ica_params: Dict[str, Any], montage_channels: List[str]) -> tuple:
    """Run ICA, identify bad components, and clean epochs."""
    # Select frontal channels for EOG detection
    frontal_channels = [ch for ch in ['Fp1', 'Fp2', 'F7', 'F8', 'Fz', 'FCz'] if ch in epochs.ch_names]
    
    ica = ICA(n_components=ica_params['n_components'], method='fastica', random_state=42)
    ica.fit(epochs)
    
    # Find bad EOG components
    eog_indices, eog_scores = ica.find_bads_eog(epochs, ch_name=frontal_channels, threshold=ica_params['threshold'])
    
    # Log the number of removed components
    ica_removed_count = len(eog_indices)
    
    # Apply ICA to remove bad components
    if eog_indices:
        ica.apply(epochs, exclude=eog_indices)
    
    return epochs, ica_removed_count

def save_epochs(epochs: mne.Epochs, output_path: str):
    """Save epochs to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    epochs.save(output_path, overwrite=True)
    logger.info(f"Saved epochs to {output_path}")

def write_preprocess_log(subject_id: str, rejected_count: int, ica_removed_count: int, log_path: str):
    """Write preprocessing log entry for a subject."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_entry = f"Subject {subject_id}: Rejected {rejected_count} epochs, Removed {ica_removed_count} ICA components\n"
    with open(log_path, 'a') as f:
        f.write(log_entry)
    logger.info(f"Logged preprocessing stats for subject {subject_id}")

def main():
    """Main execution function for the preprocessing pipeline."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load config
    config = load_config()
    montage_channels = get_channel_montage(config)
    filter_params = get_filter_params(config)
    epoch_params = get_epoch_params(config)
    ica_params = get_ica_params(config)
    
    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    results_dir = Path("results")
    log_path = results_dir / "preprocess_log.txt"
    output_path = processed_dir / "epo.fif"
    
    # Clear previous log if exists
    if log_path.exists():
        log_path.unlink()
    
    # Iterate over raw files (assuming .fif or .edf)
    raw_files = list(raw_dir.glob("*.fif")) + list(raw_dir.glob("*.edf"))
    
    if not raw_files:
        logger.error("No raw data files found in data/raw/")
        return

    for raw_file in raw_files:
        subject_id = raw_file.stem # Extract subject ID from filename
        logger.info(f"Processing subject: {subject_id}")
        
        try:
            # 1. Load raw data
            raw = load_raw_data(str(raw_file))
            
            # 2. Subsample to 32 channels
            raw = subsample_channels(raw, montage_channels)
            
            # 3. Filter and re-reference
            raw = apply_filter_and_reference(raw, filter_params)
            
            # 4. Epoch data
            # Note: In a real scenario, events would be extracted from the raw data
            # For ds003645, we might need to extract events from the stim channel
            events = mne.find_events(raw)
            epochs = epoch_data(raw, epoch_params, events)
            
            # 5. Run ICA and clean
            # We need to reject bad epochs first to count them
            # Using a simple rejection criteria for demonstration
            reject_criteria = dict(eeg=150e-6) # 150 uV
            epochs_clean, rejected_log = epochs.drop_bad(reject=reject_criteria, return_log=True)
            rejected_count = len(epochs) - len(epochs_clean)
            
            # 6. Run ICA on clean epochs
            epochs_clean, ica_removed_count = run_ica_and_clean(epochs_clean, ica_params, montage_channels)
            
            # 7. Write log
            write_preprocess_log(subject_id, rejected_count, ica_removed_count, str(log_path))
            
            # 8. Save final epochs (overwrite for demo, in real use would save per subject or aggregate)
            # For this demo, we save the last processed subject's epochs
            save_epochs(epochs_clean, str(output_path))
            
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            raise

    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()