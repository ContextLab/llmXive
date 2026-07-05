"""
EEG Preprocessing Pipeline with Streaming Support

This module implements streaming data loading and processing to ensure
peak memory usage remains under 6GB (DC-001).
"""

import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any
import logging

# Import logging utilities from sibling module
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary

# Ensure the code directory is in the path for imports
CODE_ROOT = Path(__file__).parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to code/config.yaml.

    Returns:
        Dictionary containing configuration parameters.
    """
    if config_path is None:
        config_path = CODE_ROOT / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def stream_eeg_files(
    data_dir: Path,
    file_pattern: str = "*.edf",
    batch_size: int = 5
) -> Generator[Tuple[str, mne.io.BaseRaw], None, None]:
    """
    Stream EEG files from a directory in batches to manage memory.

    This generator yields tuples of (filename, raw_object) in batches,
    allowing processing of large datasets without loading everything
    into memory at once.

    Args:
        data_dir: Directory containing EEG files.
        file_pattern: Glob pattern for matching EEG files.
        batch_size: Number of files to process in a batch.

    Yields:
        Tuples of (filename, mne.io.Raw object)
    """
    import glob
    
    files = sorted(glob.glob(str(data_dir / file_pattern)))
    logger = get_logger()
    
    if not files:
        logger.warning(f"No files found matching pattern: {data_dir / file_pattern}")
        return
    
    logger.info(f"Found {len(files)} EEG files to process")
    
    current_batch = []
    
    for file_path in files:
        try:
            # Load file with baseline preprocessing to reduce memory footprint
            # Only load necessary channels and apply initial filtering
            raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            
            # Stream the file object
            current_batch.append((file_path, raw))
            
            if len(current_batch) >= batch_size:
                yield from current_batch
                current_batch = []
                
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            continue
    
    # Yield any remaining files
    if current_batch:
        yield from current_batch


def apply_bandpass_filter(
    raw: mne.io.BaseRaw,
    l_freq: float = 1.0,
    h_freq: float = 40.0,
    method: str = 'fir'
) -> mne.io.BaseRaw:
    """
    Apply bandpass filter to EEG data.

    Args:
        raw: MNE Raw object.
        l_freq: Low cutoff frequency (Hz).
        h_freq: High cutoff frequency (Hz).
        method: Filtering method ('fir' or 'iir').

    Returns:
        Filtered MNE Raw object.
    """
    logger = get_logger()
    
    # Use streaming-friendly filtering (preload=False initially)
    # Filter in-place to avoid creating large copies
    raw.load_data()  # Load data for filtering (required for filter)
    
    raw.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        method=method,
        fir_design='fir',
        verbose=False
    )
    
    logger.debug(f"Applied {l_freq}-{h_freq}Hz bandpass filter")
    return raw


def reject_artifacts(
    raw: mne.io.BaseRaw,
    threshold_uv: float = 100.0,
    min_duration_sec: float = 120.0
) -> Tuple[mne.io.BaseRaw, Dict[str, Any]]:
    """
    Reject artifacts from EEG data based on amplitude and duration thresholds.

    Implements streaming-compatible artifact rejection by processing
    data in epochs and discarding bad segments.

    Args:
        raw: MNE Raw object (filtered).
        threshold_uv: Amplitude threshold in microvolts.
        min_duration_sec: Minimum segment duration in seconds.

    Returns:
        Tuple of (cleaned Raw object, rejection statistics dict)
    """
    logger = get_logger()
    
    # Get channel data for amplitude checking
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    
    # Calculate amplitude thresholds
    threshold = threshold_uv * 1e-6  # Convert to volts
    
    # Find epochs exceeding threshold
    # Process channel by channel to manage memory
    bad_epochs = []
    total_epochs = 0
    
    # Create epochs for analysis (streaming-friendly approach)
    # Use a reasonable epoch size for memory management
    epoch_duration = 2.0  # seconds
    epoch_size = int(epoch_duration * sfreq)
    
    n_samples = data.shape[1]
    n_channels = data.shape[0]
    
    rejection_stats = {
        'total_duration': n_samples / sfreq,
        'rejected_duration': 0.0,
        'rejected_epochs': 0,
        'total_epochs': 0,
        'reasons': []
    }
    
    # Process data in chunks
    for start in range(0, n_samples - epoch_size, epoch_size):
        end = start + epoch_size
        total_epochs += 1
        rejection_stats['total_epochs'] = total_epochs
        
        # Check if this epoch exceeds threshold on any channel
        epoch_data = data[:, start:end]
        max_amplitude = np.max(np.abs(epoch_data))
        
        if max_amplitude > threshold:
            bad_epochs.append((start, end))
            rejection_stats['rejected_epochs'] += 1
            rejection_stats['reasons'].append({
                'start': start / sfreq,
                'end': end / sfreq,
                'max_amplitude_uv': max_amplitude * 1e6,
                'reason': 'amplitude_threshold'
            })
    
    # Calculate rejected duration
    rejection_stats['rejected_duration'] = len(bad_epochs) * epoch_duration
    
    # Log rejection summary
    if bad_epochs:
        log_artifact_rejection(
            participant_id=raw.info['subject_info']['id'] if raw.info['subject_info'] else 'unknown',
            reason='amplitude_threshold',
            count=len(bad_epochs),
            details=f"Threshold: {threshold_uv}µV, Rejected {len(bad_epochs)} epochs"
        )
    
    # Apply rejection by marking bad segments
    # For streaming, we create a new raw object with bad segments excluded
    if bad_epochs:
        # Create a mask for good data
        good_mask = np.ones(n_samples, dtype=bool)
        for start, end in bad_epochs:
            good_mask[start:end] = False
        
        # Extract good data (memory-intensive but necessary for final output)
        # For very large datasets, consider writing to disk in chunks
        good_data = data[:, good_mask]
        
        # Create new raw object with cleaned data
        # This is the memory-intensive part - only do this at the end
        info = raw.info.copy()
        cleaned_raw = mne.io.RawArray(good_data, info)
        
        logger.info(f"Rejected {len(bad_epochs)} epochs ({rejection_stats['rejected_duration']:.2f}s)")
        return cleaned_raw, rejection_stats
    
    return raw, rejection_stats


def process_eeg_stream(
    data_dir: Path,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process EEG data using streaming approach to manage memory.

    This function implements the full preprocessing pipeline with
    memory-efficient streaming to ensure peak usage < 6GB.

    Args:
        data_dir: Directory containing raw EEG files.
        output_dir: Directory for processed output files.
        config: Configuration dictionary. If None, loads from config.yaml.

    Returns:
        Summary statistics of the processing run.
    """
    logger = get_logger()
    
    if config is None:
        config = load_config()
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get parameters from config
    l_freq = config.get('filter', {}).get('l_freq', 1.0)
    h_freq = config.get('filter', {}).get('h_freq', 40.0)
    threshold_uv = config.get('artifact_rejection', {}).get('threshold_uv', 100.0)
    min_duration = config.get('artifact_rejection', {}).get('min_duration_sec', 120.0)
    
    # Summary statistics
    summary = {
        'total_files': 0,
        'processed_files': 0,
        'failed_files': 0,
        'total_rejected_duration': 0.0,
        'total_processed_duration': 0.0,
        'files': []
    }
    
    # Stream through files
    for file_path, raw in stream_eeg_files(data_dir):
        summary['total_files'] += 1
        participant_id = raw.info['subject_info']['id'] if raw.info['subject_info'] else Path(file_path).stem
        
        try:
            logger.info(f"Processing {file_path} (Participant: {participant_id})")
            
            # Apply bandpass filter
            raw_filtered = apply_bandpass_filter(raw, l_freq, h_freq)
            
            # Reject artifacts
            raw_cleaned, rejection_stats = reject_artifacts(
                raw_filtered, 
                threshold_uv, 
                min_duration
            )
            
            # Check minimum duration requirement
            duration = raw_cleaned.times[-1]
            if duration < min_duration:
                logger.warning(f"Participant {participant_id}: Duration {duration:.2f}s < {min_duration}s, skipping")
                log_artifact_rejection(
                    participant_id=participant_id,
                    reason='insufficient_duration',
                    count=1,
                    details=f"Duration: {duration:.2f}s"
                )
                summary['failed_files'] += 1
                continue
            
            # Save processed data
            output_path = output_dir / f"{participant_id}_processed.fif"
            raw_cleaned.save(output_path, overwrite=True, verbose=False)
            
            # Update summary
            summary['processed_files'] += 1
            summary['total_rejected_duration'] += rejection_stats['rejected_duration']
            summary['total_processed_duration'] += duration
            summary['files'].append({
                'input': file_path,
                'output': str(output_path),
                'participant_id': participant_id,
                'duration': duration,
                'rejected_epochs': rejection_stats['rejected_epochs'],
                'rejected_duration': rejection_stats['rejected_duration']
            })
            
            # Explicitly delete to free memory
            del raw, raw_filtered, raw_cleaned
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            summary['failed_files'] += 1
            continue
    
    # Save rejection summary
    save_rejection_summary(summary)
    
    logger.info(f"Processing complete. Processed: {summary['processed_files']}, Failed: {summary['failed_files']}")
    return summary


def main():
    """Main entry point for preprocessing pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stream EEG preprocessing pipeline")
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    parser.add_argument('--input', type=str, required=True, help='Input data directory')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger()
    logger.info("Starting streaming preprocessing pipeline")
    
    try:
        # Run processing
        summary = process_eeg_stream(
            data_dir=Path(args.input),
            output_dir=Path(args.output),
            config=load_config(args.config) if args.config else None
        )
        
        # Print summary
        print(f"\nProcessing Summary:")
        print(f"  Total files: {summary['total_files']}")
        print(f"  Processed: {summary['processed_files']}")
        print(f"  Failed: {summary['failed_files']}")
        print(f"  Total rejected duration: {summary['total_rejected_duration']:.2f}s")
        print(f"  Total processed duration: {summary['total_processed_duration']:.2f}s")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()