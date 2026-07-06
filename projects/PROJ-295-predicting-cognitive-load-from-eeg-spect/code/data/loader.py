"""
Data loader module with chunked loading logic for memory safety.
Loads EEG epochs by epoch_id to ensure memory usage stays within limits.
"""
import os
import glob
import numpy as np
import pandas as pd
from typing import Iterator, Dict, Any, List, Optional, Tuple
import mne

def estimate_memory_usage(epochs: mne.Epochs) -> float:
    """
    Estimate memory usage of an Epochs object in GB.
    
    Args:
        epochs: The MNE Epochs object.
        
    Returns:
        Estimated memory usage in GB.
    """
    n_epochs = len(epochs)
    n_channels = len(epochs.ch_names)
    n_times = epochs.get_data().shape[2]
    # float64 is 8 bytes
    size_bytes = n_epochs * n_channels * n_times * 8
    return size_bytes / (1024 ** 3)

def get_epoch_metadata(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Scan the raw directory for epoch metadata files.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        List of metadata dictionaries for each epoch.
    """
    metadata_files = glob.glob(os.path.join(raw_dir, '*', '*-epo.fif'))
    metadata = []
    for f in metadata_files:
        # Extract epoch_id from filename
        epoch_id = os.path.basename(f).replace('-epo.fif', '')
        metadata.append({'epoch_id': epoch_id, 'path': f})
    return metadata

def load_epochs_chunked(raw_dir: str, chunk_size: int = 10, max_memory_gb: float = 6.5) -> Iterator[Dict[str, Any]]:
    """
    Generator that loads epochs in chunks to ensure memory safety.
    
    Args:
        raw_dir: Path to the raw data directory.
        chunk_size: Number of epochs to load in each batch.
        max_memory_gb: Maximum allowed memory usage in GB.
        
    Yields:
        Dictionary containing the loaded epochs and their metadata.
    """
    metadata = get_epoch_metadata(raw_dir)
    current_batch = []
    current_memory = 0.0

    for item in metadata:
        try:
            epochs = mne.read_epochs(item['path'], preload=False)
            # Estimate memory if preloaded
            est_mem = estimate_memory_usage(epochs)
            
            if current_memory + est_mem > max_memory_gb:
                # Yield current batch and reset
                yield {'epochs': current_batch, 'memory_gb': current_memory}
                current_batch = []
                current_memory = 0.0
            
            current_batch.append({'epoch_id': item['epoch_id'], 'data': epochs})
            current_memory += est_mem

        except Exception as e:
            print(f"Warning: Failed to load {item['path']}: {e}")
            continue

    if current_batch:
        yield {'epochs': current_batch, 'memory_gb': current_memory}

def load_all_epochs(raw_dir: str) -> mne.Epochs:
    """
    Load all epochs into memory (use with caution).
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        Concatenated MNE Epochs object.
    """
    all_epochs = []
    for batch in load_epochs_chunked(raw_dir, chunk_size=50):
        for item in batch['epochs']:
            all_epochs.append(item['data'])
    
    if not all_epochs:
        raise ValueError("No epochs loaded.")
    
    return mne.concatenate_epochs(all_epochs)
