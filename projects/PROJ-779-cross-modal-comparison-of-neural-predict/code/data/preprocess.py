import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import mne
import json
from datetime import datetime

from code.config import get_config, ensure_directories
from code.data.data_loader import validate_sampling_rate, validate_trial_counts
from code.utils.logger import get_logger

logger = get_logger(__name__)

def apply_bandpass_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0) -> mne.io.Raw:
    """Apply bandpass filter to raw data."""
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', fir_design='firwin')
    return raw_filtered

def run_ica_artifact_removal(raw: mne.io.Raw, n_components: float = 0.95) -> mne.io.Raw:
    """Run ICA for artifact removal."""
    logger.info("Running ICA artifact removal")
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42, method='fastica')
    ica.fit(raw)
    
    # Find EOG and ECG components (simplified heuristic for demo)
    # In a real pipeline, we would use more robust detection or manual selection
    eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name='EOG', threshold=3.0)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw, ch_name='ECG', threshold=3.0)
    
    components_to_drop = list(set(eog_indices + ecg_indices))
    if components_to_drop:
        logger.info(f"Removing ICA components: {components_to_drop}")
        ica.exclude = components_to_drop
        raw_clean = ica.apply(raw)
    else:
        logger.info("No ICA components to exclude")
        raw_clean = raw.copy()
        
    return raw_clean

def apply_re_reference(raw: mne.io.Raw) -> mne.io.Raw:
    """Apply common average re-referencing."""
    logger.info("Applying common average re-referencing")
    raw_ref = raw.copy()
    raw_ref.set_eeg_reference('average', projection=False)
    return raw_ref

def preprocess_dataset(
    input_path: str,
    output_dir: str,
    l_freq: float = 1.0,
    h_freq: float = 40.0,
    ica_n_components: float = 0.95
) -> Tuple[str, Dict[str, Any]]:
    """
    Full preprocessing pipeline: Filter -> ICA -> Re-reference -> Save.
    
    Returns:
        Tuple of (output_path, metadata_dict)
    """
    config = get_config()
    ensure_directories([output_dir])
    
    logger.info(f"Loading dataset from {input_path}")
    raw = mne.io.read_raw_fif(input_path, preload=True)
    
    # Validate sampling rate
    sfreq = raw.info['sfreq']
    if not validate_sampling_rate(sfreq, config['sampling_rate_threshold']):
        raise ValueError(f"Sampling rate {sfreq} Hz is below threshold {config['sampling_rate_threshold']} Hz")
    
    # Count trials (simplified: count events in annotation or stim channel)
    events = mne.find_events(raw, shortest_event=1)
    trial_counts = {'total': len(events)}
    if not validate_trial_counts(trial_counts['total'], config['min_standard_trials'], config['min_oddball_trials']):
        logger.warning(f"Trial count {trial_counts['total']} might be insufficient, but proceeding.")
    
    # Step 1: Filter
    raw_processed = apply_bandpass_filter(raw, l_freq, h_freq)
    
    # Step 2: ICA
    raw_processed = run_ica_artifact_removal(raw_processed, ica_n_components)
    
    # Step 3: Re-reference
    raw_processed = apply_re_reference(raw_processed)
    
    # Step 4: Save cleaned artifact
    base_name = Path(input_path).stem
    output_filename = f"{base_name}_cleaned.fif"
    output_path = str(Path(output_dir) / output_filename)
    
    logger.info(f"Saving cleaned data to {output_path}")
    raw_processed.save(output_path, overwrite=True)
    
    # Generate metadata
    metadata = {
        'input_file': input_path,
        'output_file': output_path,
        'sampling_rate': sfreq,
        'trial_count': trial_counts['total'],
        'processing_steps': ['filter', 'ica', 're-reference'],
        'filter_params': {'l_freq': l_freq, 'h_freq': h_freq},
        'ica_params': {'n_components': ica_n_components, 'excluded_components': []}, # Simplified
        'timestamp': datetime.now().isoformat(),
        'status': 'success'
    }
    
    # Log rejection info (simplified: no specific trial rejection in this version)
    metadata['rejected_trials'] = []
    
    logger.info(f"Preprocessing complete. Output: {output_path}")
    return output_path, metadata

def main():
    """Main entry point for preprocessing."""
    config = get_config()
    
    # Determine input path
    # In a real scenario, this might be passed via CLI or config
    # For now, we look for the downloaded raw file in data/raw
    raw_dir = Path(config['data_raw_dir'])
    processed_dir = Path(config['data_processed_dir'])
    
    # Find the most recent raw file (or specific one)
    raw_files = list(raw_dir.glob("*.fif"))
    if not raw_files:
        logger.error("No raw .fif files found in data/raw. Please run download first.")
        sys.exit(1)
    
    input_file = raw_files[-1] # Pick the last one found
    logger.info(f"Processing {input_file}")
    
    try:
        output_path, metadata = preprocess_dataset(
            input_path=str(input_file),
            output_dir=str(processed_dir),
            l_freq=config['filter_l_freq'],
            h_freq=config['filter_h_freq'],
            ica_n_components=config['ica_n_components']
        )
        
        # Save metadata log
        log_path = processed_dir / "preprocessing_log.json"
        with open(log_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Preprocessing log saved to {log_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()