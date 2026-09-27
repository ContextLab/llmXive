"""
Feature extraction module for EEG complexity metrics.
Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import mne
import nolds
from pyentropy import permutation_entropy

# Import local utilities using the API surface defined in the project
from utils.logging import get_logger, log_operation
from config import load_config


def setup_logger(name: str) -> Any:
    """Initialize and return a logger instance."""
    return get_logger(name)


def load_eeg_data(input_dir: str) -> List[Dict[str, Any]]:
    """
    Load cleaned EEG data files from the processed directory.
    Returns a list of dictionaries containing file paths and metadata.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger = get_logger("features")
        logger.error(f"Input directory not found: {input_dir}")
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    eeg_files = list(input_path.glob("*.fif"))
    if not eeg_files:
        logger = get_logger("features")
        logger.error(f"No .fif files found in {input_dir}")
        raise FileNotFoundError(f"No .fif files found in {input_dir}")

    data_list = []
    for f_path in eeg_files:
        # Extract participant ID from filename (assumes format: cleaned_eeg_<participant_id>.fif)
        # If not, we'll try to parse the raw file or use the filename stem
        participant_id = f_path.stem.replace("cleaned_eeg_", "")
        if participant_id == "cleaned_eeg":
            # Fallback: just use the stem if pattern doesn't match
            participant_id = f_path.stem

        data_list.append({
            "path": str(f_path),
            "participant_id": participant_id,
            "filename": f_path.name
        })

    return data_list


def extract_lempel_ziv_complexity(signal: np.ndarray, n_bins: int = 2) -> float:
    """
    Calculate Lempel-Ziv Complexity using median quantization.
    
    Args:
        signal: 1D numpy array of EEG data.
        n_bins: Number of bins for quantization (default 2 for median split).
        
    Returns:
        Normalized Lempel-Ziv Complexity value (0.0 to 1.0).
    """
    if len(signal) == 0:
        return 0.0
        
    # Quantize signal using median
    median_val = np.median(signal)
    if n_bins == 2:
        # Binary quantization: 0 if below median, 1 if above or equal
        quantized = (signal >= median_val).astype(int)
    else:
        # General quantization
        quantized = np.digitize(signal, np.linspace(np.min(signal), np.max(signal), n_bins))
        
    # Calculate LZC using nolds
    try:
        # nolds.lz76 expects a binary sequence or sequence of integers
        lzc = nolds.lz76(quantized)
        # Normalize by sequence length
        normalized_lzc = lzc / len(signal)
        return float(normalized_lzc)
    except Exception as e:
        logger = get_logger("features")
        logger.warning(f"Error calculating LZC for signal of length {len(signal)}: {e}")
        return 0.0


def extract_permutation_entropy(signal: np.ndarray, embedding_dim: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy.
    
    Args:
        signal: 1D numpy array of EEG data.
        embedding_dim: Dimension of the embedding (default 3).
        delay: Time delay for embedding (default 1).
        
    Returns:
        Permutation Entropy value (normalized to 0.0 to log2(n!)).
    """
    if len(signal) < embedding_dim:
        return 0.0
        
    try:
        # pyentropy.permutation_entropy returns the raw entropy
        pe = permutation_entropy(signal, order=embedding_dim, delay=delay)
        
        # Normalize by maximum possible entropy (log2(embedding_dim!))
        max_entropy = np.log2(np.math.factorial(embedding_dim))
        if max_entropy > 0:
            normalized_pe = pe / max_entropy
        else:
            normalized_pe = 0.0
            
        return float(normalized_pe)
    except Exception as e:
        logger = get_logger("features")
        logger.warning(f"Error calculating PE for signal of length {len(signal)}: {e}")
        return 0.0


def process_segment(
    raw: mne.io.Raw,
    participant_id: str,
    segment_id: str,
    channel: str,
    logger: Any
) -> Dict[str, Any]:
    """
    Process a single EEG segment/channel to extract complexity metrics.
    
    Args:
        raw: MNE Raw object containing the EEG data.
        participant_id: Unique identifier for the participant.
        segment_id: Identifier for the specific segment.
        channel: Channel name to process.
        logger: Logger instance.
        
    Returns:
        Dictionary with metrics: participant_id, channel, segment_id, lzc_value, pe_value.
    """
    if channel not in raw.ch_names:
        logger.warning(f"Channel {channel} not found in {raw.filenames[0] if raw.filenames else 'data'}")
        return None
        
    # Get data for the channel
    data, _ = raw[[channel]]
    signal = data[0]
    
    # Extract metrics
    lzc_value = extract_lempel_ziv_complexity(signal)
    pe_value = extract_permutation_entropy(signal, embedding_dim=3, delay=1)
    
    return {
        "participant_id": participant_id,
        "channel": channel,
        "segment_id": segment_id,
        "lzc_value": lzc_value,
        "pe_value": pe_value
    }


def write_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write extracted metrics to a CSV file.
    
    Args:
        metrics: List of metric dictionaries.
        output_path: Path to the output CSV file.
    """
    if not metrics:
        logger = get_logger("features")
        logger.warning("No metrics to write.")
        return
        
    fieldnames = ["participant_id", "channel", "segment_id", "lzc_value", "pe_value"]
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            if metric:  # Skip None entries
                writer.writerow(metric)
                
    logger = get_logger("features")
    logger.info(f"Wrote {len(metrics)} metrics to {output_path}")


def main() -> None:
    """Main entry point for feature extraction."""
    parser = argparse.ArgumentParser(description="Extract complexity metrics from EEG data.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Directory containing cleaned EEG .fif files."
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/analysis/complexity_metrics.csv",
        help="Path to output CSV file."
    )
    
    args = parser.parse_args()
    
    logger = setup_logger("features")
    logger.info("Starting feature extraction pipeline.")
    
    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
        
    # Load EEG data
    try:
        eeg_files = load_eeg_data(args.input_dir)
        logger.info(f"Found {len(eeg_files)} EEG files to process.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
        
    all_metrics = []
    
    # Process each file
    for file_info in eeg_files:
        participant_id = file_info["participant_id"]
        file_path = file_info["path"]
        
        logger.info(f"Processing {file_path} for participant {participant_id}...")
        
        try:
            # Load the raw data
            raw = mne.io.read_raw_fif(file_path, preload=True)
            
            # Define segments (assuming whole file is one segment for now, or split by event)
            # For resting-state, we often treat the whole file as one segment or split into fixed windows
            # Here we assume the file contains one continuous segment labeled as "segment_0"
            # In a more complex scenario, we would split by events or fixed windows
            segment_id = "segment_0"
            
            # Process each channel
            channels_to_process = [ch for ch in raw.ch_names if ch in raw.pick_types(eeg=True).ch_names]
            
            for channel in channels_to_process:
                try:
                    metrics = process_segment(raw, participant_id, segment_id, channel, logger)
                    if metrics:
                        all_metrics.append(metrics)
                except Exception as e:
                    logger.warning(f"Error processing channel {channel}: {e}")
                    
            # Close the raw object to free memory
            raw.close()
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            continue
            
    # Write results to CSV
    if all_metrics:
        write_metrics_to_csv(all_metrics, args.output_file)
        logger.info(f"Feature extraction complete. Output saved to {args.output_file}")
    else:
        logger.warning("No metrics were extracted. Output file not created.")
        
    logger.info("Feature extraction pipeline finished.")


if __name__ == "__main__":
    main()