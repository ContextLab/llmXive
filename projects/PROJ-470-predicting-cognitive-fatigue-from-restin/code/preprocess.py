import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
import logging
from datetime import datetime
import json

# Import local logging utility
try:
    from utils.logging import get_logger, log_artifact_rejection, save_exclusion_log_csv
except ImportError:
    # Fallback for direct execution without package structure
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
    from logging import get_logger, log_artifact_rejection, save_exclusion_log_csv

def load_config(config_path='code/config.yaml'):
    """Load pipeline configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(raw_dir, config):
    """
    Generator to yield EEG file paths from the raw directory.
    Uses MNE's preload=False strategy for memory efficiency.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Data directory not found: {raw_dir}")
    
    # Find .edf or .fif files
    files = list(raw_path.glob('*.edf')) + list(raw_path.glob('*.fif'))
    if not files:
        raise FileNotFoundError(f"No EEG files (.edf, .fif) found in {raw_dir}")
    
    for file_path in files:
        yield file_path

def apply_bandpass_filter(raw, low_cut, high_cut, picks='eeg'):
    """Apply bandpass filter to the raw data."""
    raw_copy = raw.copy()
    raw_copy.filter(low_freq=low_cut, high_freq=high_cut, picks=picks, fir_design='fir')
    return raw_copy

def detect_line_noise_peak(raw, freq_target=50.0, threshold_db=20.0):
    """
    Perform PSD analysis to detect a peak at the target frequency.
    Returns True if a significant peak is detected, False otherwise.
    """
    # Compute PSD
    psd, freqs = mne.time_frequency.psd_welch(
        raw, 
        fmin=45.0, 
        fmax=55.0, 
        n_fft=256, 
        n_overlap=128, 
        picks='eeg', 
        average='mean'
    )
    
    # Convert to dB
    psd_db = 10 * np.log10(psd)
    
    # Find peak in the vicinity of 50Hz
    peak_idx = np.argmax(psd_db)
    peak_freq = freqs[peak_idx]
    peak_power = psd_db[0, peak_idx]
    
    # Calculate noise floor (median power in the band)
    noise_floor = np.median(psd_db)
    
    # Check if peak exceeds threshold relative to floor
    if peak_power - noise_floor > threshold_db:
        logging.info(f"Line noise detected: Peak at {peak_freq:.2f} Hz, Power: {peak_power:.2f} dB, Floor: {noise_floor:.2f} dB")
        return True, peak_freq
    
    logging.warning(f"No significant line noise peak detected. Max peak at {peak_freq:.2f} Hz ({peak_power:.2f} dB), Floor: {noise_floor:.2f} dB")
    return False, peak_freq

def apply_notch_filter(raw, freq=50.0):
    """Apply notch filter to remove line noise."""
    raw_copy = raw.copy()
    raw_copy.notch_filter(freqs=freq, picks='eeg', method='iir')
    return raw_copy

def reject_artifacts(raw, amplitude_threshold=100.0, min_duration=120):
    """
    Reject epochs based on amplitude and duration.
    Returns a list of (participant_id, reason) tuples for rejected segments.
    """
    rejected = []
    # Get data in microvolts
    data = raw.get_data(picks='eeg') * 1e6 
    info = raw.info
    
    # Check amplitude
    if np.max(np.abs(data)) > amplitude_threshold:
        rejected.append(('amplitude > 100uV', np.max(np.abs(data))))
    
    # Check duration (in seconds)
    duration = raw.times[-1] - raw.times[0]
    if duration < min_duration:
        rejected.append(('segment < 120s', duration))
        
    return rejected

def process_eeg_stream(raw_files, config):
    """
    Process a stream of EEG files: filter, check noise, reject artifacts.
    Returns a list of processed raw objects and a rejection log.
    """
    processed_files = []
    rejection_log = []
    
    low_cut = config['filter_low']
    high_cut = config['filter_high']
    artifact_threshold = config['artifact_threshold']
    min_duration = 120 # seconds, per FR-002
    
    for file_path in raw_files:
        participant_id = file_path.stem
        logging.info(f"Processing {participant_id}...")
        
        try:
            # Load with preload=False for streaming efficiency
            raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            
            # 1. Apply Bandpass Filter
            raw = apply_bandpass_filter(raw, low_cut, high_cut)
            
            # 2. Detect Line Noise and Conditionally Apply Notch
            needs_notch, detected_freq = detect_line_noise_peak(raw)
            notch_applied = False
            if needs_notch:
                raw = apply_notch_filter(raw, freq=50.0)
                notch_applied = True
                # Log justification for this specific participant
                logging.info(f"Notch filter applied for {participant_id} at {detected_freq:.2f} Hz")
            else:
                logging.warning(f"Notch filter skipped for {participant_id}")
            
            # 3. Artifact Rejection
            rejections = reject_artifacts(raw, artifact_threshold, min_duration)
            if rejections:
                for reason, value in rejections:
                    log_artifact_rejection(participant_id, reason, str(value))
                    rejection_log.append({
                        'participant_id': participant_id,
                        'reason': reason,
                        'value': value,
                        'timestamp': datetime.now().isoformat()
                    })
                # If rejected due to amplitude or duration, we might skip saving or mark it
                # For this implementation, we save the cleaned data but log the rejection
                # If the segment is too short, it might be unusable for feature extraction
                if any(r[0] == 'segment < 120s' for r in rejections):
                    logging.warning(f"Segment for {participant_id} too short, skipping save.")
                    continue
                
            processed_files.append(raw)
            
        except Exception as e:
            logging.error(f"Failed to process {file_path}: {e}")
            rejection_log.append({
                'participant_id': participant_id,
                'reason': f'processing_error: {str(e)}',
                'value': 0,
                'timestamp': datetime.now().isoformat()
            })
            
    return processed_files, rejection_log

def save_processed_data(processed_raws, output_path):
    """Save processed data to a FIF file."""
    if not processed_raws:
        logging.warning("No processed data to save.")
        return
    
    # Concatenate all raws if multiple, or save single
    # MNE FIF format is standard for processed EEG
    # For simplicity in this pipeline, we save the first valid one or concatenate if same channels
    # A more robust approach would save individual files, but the task specifies one output file
    # We will save the first valid processed raw as the representative 'cleaned_eeg'
    # In a real multi-participant pipeline, we would likely save a directory of files.
    # However, adhering to the task: "Output preprocessed data to data/processed/cleaned_eeg.fif"
    # We assume the stream processes one large file or we save the last valid one for demonstration
    # OR we concatenate if they are compatible. Let's save the last valid one to ensure we have data.
    
    if len(processed_raws) > 1:
        # Attempt to concatenate if compatible
        try:
            combined = mne.concatenate_raws(processed_raws)
            combined.save(output_path, overwrite=True)
            logging.info(f"Saved {len(processed_raws)} participants concatenated to {output_path}")
        except Exception as e:
            logging.warning(f"Could not concatenate files: {e}. Saving last valid file.")
            processed_raws[-1].save(output_path, overwrite=True)
    else:
        processed_raws[0].save(output_path, overwrite=True)
        logging.info(f"Saved processed data to {output_path}")

def save_rejection_log(rejection_log, output_path):
    """Save rejection log to CSV."""
    if not rejection_log:
        logging.info("No rejections to log.")
        return
    
    import pandas as pd
    df = pd.DataFrame(rejection_log)
    df.to_csv(output_path, index=False)
    logging.info(f"Rejection log saved to {output_path}")

def main():
    """Main entry point for preprocessing."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    config = load_config()
    raw_dir = config.get('raw_data_dir', 'data/raw')
    output_dir = config.get('processed_data_dir', 'data/processed')
    output_path = os.path.join(output_dir, 'cleaned_eeg.fif')
    log_path = os.path.join(output_dir, 'exclusion_log.csv')
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize logging infrastructure
    # Assuming utils.logging handles file creation
    # If not, we rely on the standard log setup above
    
    try:
        raw_files = list(stream_eeg_files(raw_dir, config))
        if not raw_files:
            logging.error("No files found to process.")
            return
        
        processed_raws, rejection_log = process_eeg_stream(raw_files, config)
        
        if processed_raws:
            save_processed_data(processed_raws, output_path)
        else:
            logging.error("No valid data processed. Check exclusion log.")
            
        save_rejection_log(rejection_log, log_path)
        
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
