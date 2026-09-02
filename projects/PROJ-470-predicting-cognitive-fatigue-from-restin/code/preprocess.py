import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime
import pandas as pd
from code.utils.logging import log_artifact_rejection, save_exclusion_log_csv

def load_config(config_path='code/config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file='data/processed/preprocess.log'):
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(name)

def stream_eeg_files(raw_dir='data/raw'):
    """Yields paths to EEG files in the raw directory."""
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    # Look for .fif, .edf, .bdf files
    extensions = ['.fif', '.edf', '.bdf', '.vhdr']
    files = []
    for ext in extensions:
        files.extend(raw_path.glob(f'*{ext}'))
        # Also look in subdirectories
        files.extend(raw_path.rglob(f'*{ext}'))
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    for f in files:
        yield f

def apply_bandpass_filter(raw_eeg, low_cut, high_cut, logger):
    """Apply bandpass filter to EEG data."""
    logger.info(f"Applying bandpass filter: {low_cut}-{high_cut} Hz")
    raw_eeg.filter(low_freq=low_cut, high_freq=high_cut, fir_design='firwin')
    return raw_eeg

def detect_line_noise_peak(raw_eeg, notch_freq, logger):
    """Detect if line noise peak exists at notch_freq."""
    # Compute PSD
    psd, freqs = raw_eeg.compute_psd(fmax=notch_freq + 10, fmin=notch_freq - 10)
    psd_data = psd.get_data()
    peak_idx = np.argmax(np.mean(psd_data, axis=0))
    peak_freq = freqs[peak_idx]
    peak_power = np.mean(psd_data[:, peak_idx])
    logger.info(f"Detected peak at {peak_freq:.2f} Hz with power {peak_power:.2e}")
    return peak_freq, peak_power

def apply_notch_filter(raw_eeg, notch_freq, logger):
    """Apply notch filter to remove line noise."""
    logger.info(f"Applying notch filter at {notch_freq} Hz")
    raw_eeg.notch_filter(notch_freq, method='iir')
    return raw_eeg

def reject_artifacts(raw_eeg, threshold_uV, logger, exclusion_log_path):
    """Reject epochs with amplitude exceeding threshold."""
    # Convert to microvolts if necessary (MNE usually uses Volts)
    data = raw_eeg.get_data()
    data_uV = data * 1e6  # Convert to microvolts
    
    # Check for epochs exceeding threshold
    exceeds = np.abs(data_uV) > threshold_uV
    rejected_channels = []
    
    for ch_idx, ch_name in enumerate(raw_eeg.ch_names):
        if np.any(exceeds[ch_idx]):
            rejected_channels.append(ch_name)
            log_artifact_rejection(
                exclusion_log_path,
                participant_id=raw_eeg.info.get('subject_info', {}).get('his_id', 'unknown'),
                reason=f"Amplitude exceeded {threshold_uV}µV in channel {ch_name}",
                timestamp=datetime.now().isoformat()
            )
    
    if rejected_channels:
        logger.warning(f"Rejected channels due to high amplitude: {rejected_channels}")
        # Bad channels are marked, not removed, to preserve data structure
        raw_eeg.info['bads'].extend(rejected_channels)
    
    return raw_eeg

def process_eeg_stream(config, logger, exclusion_log_path):
    """Process all EEG files in the stream."""
    raw_dir = config.get('raw_data_dir', 'data/raw')
    output_path = Path('data/processed/cleaned_eeg.fif')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    filter_low = config.get('filter_low', 1)
    filter_high = config.get('filter_high', 40)
    notch_freq = config.get('notch_frequency', 50)
    artifact_threshold = config.get('artifact_threshold_uV', 100)
    
    processed_count = 0
    excluded_count = 0
    
    for eeg_file in stream_eeg_files(raw_dir):
        logger.info(f"Processing file: {eeg_file}")
        try:
            # Read the EEG file
            if eeg_file.suffix.lower() == '.fif':
                raw = mne.io.read_raw_fif(eeg_file, preload=True)
            elif eeg_file.suffix.lower() in ['.edf', '.bdf']:
                raw = mne.io.read_raw_edf(eeg_file, preload=True)
            elif eeg_file.suffix.lower() in ['.vhdr']:
                raw = mne.io.read_raw_brainvision(eeg_file, preload=True)
            else:
                logger.warning(f"Unsupported file format: {eeg_file.suffix}, skipping")
                continue
            
            # Apply bandpass filter
            raw = apply_bandpass_filter(raw, filter_low, filter_high, logger)
            
            # Detect and remove line noise
            peak_freq, peak_power = detect_line_noise_peak(raw, notch_freq, logger)
            if abs(peak_freq - notch_freq) < 2:  # Close to notch frequency
                raw = apply_notch_filter(raw, notch_freq, logger)
            
            # Reject artifacts
            raw = reject_artifacts(raw, artifact_threshold, logger, exclusion_log_path)
            
            # Save the cleaned data
            raw.save(str(output_path), overwrite=True)
            processed_count += 1
            logger.info(f"Successfully processed and saved: {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing {eeg_file}: {str(e)}")
            excluded_count += 1
            log_artifact_rejection(
                exclusion_log_path,
                participant_id=eeg_file.stem,
                reason=f"Processing error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    return processed_count, excluded_count

def save_processed_data(raw_eeg, output_path):
    """Save processed EEG data to FIF file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    raw_eeg.save(output_path, overwrite=True)

def main():
    """Main entry point for preprocessing pipeline."""
    logger = setup_logger('preprocess')
    config = load_config()
    
    exclusion_log_path = 'data/processed/exclusion_log.csv'
    
    # Ensure directories exist
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting preprocessing pipeline")
    
    try:
        processed_count, excluded_count = process_eeg_stream(config, logger, exclusion_log_path)
        logger.info(f"Pipeline complete. Processed: {processed_count}, Excluded: {excluded_count}")
        
        # Verify output file exists
        output_file = Path('data/processed/cleaned_eeg.fif')
        if output_file.exists():
            logger.info(f"Output file created: {output_file}")
            # Save exclusion log if any rejections occurred
            if excluded_count > 0 and os.path.exists(exclusion_log_path):
                logger.info(f"Exclusion log saved to: {exclusion_log_path}")
        else:
            logger.error("Output file was not created!")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()