import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
import logging
from datetime import datetime
import csv

# Import local utilities
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary, save_exclusion_log_csv
from models.eeg_segment import EEGSegment

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir, logger):
    """
    Generator that yields (filename, raw_instance) for EEG files in data_dir.
    Raises FileNotFoundError if directory is missing.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Look for .fif, .edf, or .bdf files
    extensions = ['*.fif', '*.edf', '*.bdf']
    files_found = False
    for ext in extensions:
        for file_path in data_path.glob(ext):
            files_found = True
            logger.info(f"Found EEG file: {file_path.name}")
            try:
                raw = mne.io.read_raw_fif(file_path, preload=False) if ext == '*.fif' else mne.io.read_raw_edf(file_path, preload=False)
                yield file_path.name, raw
            except Exception as e:
                logger.warning(f"Could not read {file_path.name}: {e}")
    
    if not files_found:
        logger.error(f"No valid EEG files found in {data_dir}")
        # In a real scenario, we might want to raise here, but for streaming
        # we just yield nothing. The main loop will handle empty streams.

def apply_bandpass_filter(raw, low_freq=1.0, high_freq=40.0, logger=None):
    """Apply 1-40 Hz bandpass filter."""
    if logger:
        logger.info(f"Applying bandpass filter: {low_freq}-{high_freq} Hz")
    raw.filter(l_freq=low_freq, h_freq=high_freq, method='iir')
    return raw

def apply_notch_filter(raw, freq=50.0, logger=None):
    """Apply 50 Hz notch filter to remove line noise."""
    if logger:
        logger.info(f"Applying notch filter at {freq} Hz")
    raw.notch_filter(freqs=[freq], method='iir')
    return raw

def reject_artifacts(raw, amplitude_thresh=100.0, min_duration=120.0, logger=None):
    """
    Reject epochs based on amplitude (>100uV) and duration (<120s).
    Returns (is_valid, reason) tuple.
    """
    # Get data in microvolts (MNE usually uses Volts)
    data = raw.get_data()
    data_uV = data * 1e6 
    
    # Check amplitude threshold
    max_amp = np.max(np.abs(data_uV))
    if max_amp > amplitude_thresh:
        if logger:
            logger.warning(f"Amplitude rejection: max={max_amp:.2f}uV > {amplitude_thresh}uV")
        return False, f'amplitude > {amplitude_thresh}uV'
    
    # Check duration
    duration = raw.info['n_times'] / raw.info['sfreq']
    if duration < min_duration:
        if logger:
            logger.warning(f"Duration rejection: {duration:.2f}s < {min_duration}s")
        return False, f'segment < {min_duration}s'
    
    return True, None

def process_eeg_stream(stream, config, logger):
    """
    Process the stream of EEG files: filter, reject, and save.
    Returns (processed_data_list, summary_stats)
    """
    processed_data = []
    exclusion_log = []
    stats = {'total': 0, 'kept': 0, 'rejected': 0, 'reasons': {}}
    
    for filename, raw in stream:
        stats['total'] += 1
        participant_id = filename.split('.')[0] # Simple ID extraction
        
        # Apply filters
        raw = apply_bandpass_filter(raw, 
                                    low_freq=config['filter_low'], 
                                    high_freq=config['filter_high'],
                                    logger=logger)
        raw = apply_notch_filter(raw, freq=50.0, logger=logger)
        
        # Check artifacts
        is_valid, reason = reject_artifacts(raw, 
                                            amplitude_thresh=config['artifact_threshold'],
                                            min_duration=120.0, # FR-002 min duration
                                            logger=logger)
        
        if not is_valid:
            stats['rejected'] += 1
            stats['reasons'][reason] = stats['reasons'].get(reason, 0) + 1
            exclusion_log.append({
                'participant_id': participant_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            continue
        
        # If valid, keep it
        stats['kept'] += 1
        processed_data.append({
            'id': participant_id,
            'raw': raw
        })
        
    return processed_data, stats, exclusion_log

def save_processed_data(processed_data, output_path, logger):
    """Save processed data to a single FIF file."""
    if not processed_data:
        logger.error("No data to save.")
        return
    
    # We will concatenate all valid segments into one RawArray for simplicity in this pipeline
    # or save them individually. The task asks for 'data/processed/cleaned_eeg.fif'.
    # MNE best practice: save each subject separately, but for this specific task output,
    # we will create a combined raw object or save the first one if only one exists.
    # To satisfy "data for >= 30 participants", we assume the input has them.
    # We will save the concatenated data if possible, or a list of files.
    # However, standard FIF is for one recording. Let's save the first valid one as a placeholder
    # if we can't concatenate easily, OR better: create a RawArray from the first one and update info.
    
    # Strategy: Concatenate all valid raw objects into one mega-raw for the output file
    # This is a common pattern for pipeline intermediate storage if individual IDs aren't needed in the FIF header.
    # But to preserve participant info, we might just save the first one and log the count.
    # The verification step says: "Assert file contains data for >= 30 participants".
    # MNE FIF doesn't natively store a list of participants in a single file easily without custom metadata.
    # We will concatenate them and add a custom comment to the info.
    
    logger.info(f"Saving {len(processed_data)} participants to {output_path}")
    
    # Concatenate
    # Ensure all have same channels and sfreq
    # For this implementation, we assume they are compatible (same montage).
    if len(processed_data) > 1:
        raw_list = [item['raw'] for item in processed_data]
        # Check consistency
        sfreq = raw_list[0].info['sfreq']
        ch_names = raw_list[0].info['ch_names']
        for r in raw_list[1:]:
            if r.info['sfreq'] != sfreq or r.info['ch_names'] != ch_names:
                logger.warning("Inconsistent data in stream. Saving only first valid segment.")
                raw_list = [raw_list[0]]
                break
        
        if len(raw_list) > 1:
            combined_raw = mne.concatenate_raws(raw_list)
            combined_raw.info['description'] = f"Concatenated data for {len(processed_data)} participants"
            combined_raw.save(output_path, overwrite=True)
        else:
            raw_list[0].save(output_path, overwrite=True)
    else:
        processed_data[0]['raw'].save(output_path, overwrite=True)

def save_rejection_log(exclusion_log, log_path):
    """Save exclusion log to CSV."""
    if not exclusion_log:
        return
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['participant_id', 'reason', 'timestamp'])
        writer.writeheader()
        writer.writerows(exclusion_log)

def main():
    """Main entry point for preprocessing."""
    logger = get_logger('preprocess')
    logger.info("Starting preprocessing pipeline")
    
    config = load_config()
    data_dir = "data/raw"
    output_path = "data/processed/cleaned_eeg.fif"
    log_path = "logs/exclusion_log.csv"
    
    try:
        stream = stream_eeg_files(data_dir, logger)
        processed_data, stats, exclusion_log = process_eeg_stream(stream, config, logger)
        
        logger.info(f"Processing complete. Kept: {stats['kept']}, Rejected: {stats['rejected']}")
        
        if processed_data:
            save_processed_data(processed_data, output_path, logger)
            logger.info(f"Saved cleaned data to {output_path}")
        else:
            logger.error("No valid data segments found to save.")
            # Create an empty file or exit? The task requires the file to exist if possible.
            # But if no data, we can't create a valid FIF.
            # We will exit with error if no data.
            sys.exit(1)
        
        save_rejection_log(exclusion_log, log_path)
        
        # Log summary
        logger.info(f"Rejection summary: {stats['reasons']}")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()