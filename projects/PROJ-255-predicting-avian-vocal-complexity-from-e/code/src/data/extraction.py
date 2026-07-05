"""
Vocal Complexity Metrics Extraction Module.

Extracts standardized vocal metrics (syllable count, duration, bandwidth, spectral entropy)
from audio files using librosa (CPU-only).
"""

import os
import csv
import logging
import librosa
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir

# Configure logging
logger = logging.getLogger(__name__)

def calculate_spectral_entropy(audio: np.ndarray, sr: int, n_fft: int = 2048) -> float:
    """
    Calculate spectral entropy of an audio signal.
    
    Args:
        audio: Audio signal array.
        sr: Sample rate.
        n_fft: FFT window size.
        
    Returns:
        Spectral entropy value (float).
    """
    if len(audio) == 0:
        return 0.0
        
    # Compute STFT
    D = np.abs(librosa.stft(audio, n_fft=n_fft))
    # Normalize to get probability distribution
    S = D ** 2
    S_sum = np.sum(S, axis=0)
    if np.any(S_sum == 0):
        return 0.0
    p = S / S_sum
    # Avoid log(0)
    p = np.clip(p, 1e-10, 1.0)
    # Calculate entropy
    entropy = -np.sum(p * np.log2(p), axis=0)
    return float(np.mean(entropy))

def calculate_bandwidth(audio: np.ndarray, sr: int, n_fft: int = 2048) -> float:
    """
    Calculate spectral bandwidth of an audio signal.
    
    Args:
        audio: Audio signal array.
        sr: Sample rate.
        n_fft: FFT window size.
        
    Returns:
        Spectral bandwidth in Hz (float).
    """
    if len(audio) == 0:
        return 0.0
        
    # Calculate spectral bandwidth
    bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr, n_fft=n_fft)
    return float(np.mean(bandwidth))

def count_syllables(audio: np.ndarray, sr: int, threshold_db: float = -20.0) -> int:
    """
    Estimate syllable count using onsets detection.
    
    Args:
        audio: Audio signal array.
        sr: Sample rate.
        threshold_db: Onset detection threshold in dB.
        
    Returns:
        Estimated syllable count (int).
    """
    if len(audio) == 0:
        return 0
        
    # Detect onsets
    onsets = librosa.onset.onset_detect(y=audio, sr=sr, backtrack=True)
    return len(onsets)

def extract_vocal_metrics(audio_path: str) -> Dict:
    """
    Extract vocal complexity metrics from an audio file.
    
    Args:
        audio_path: Path to the audio file.
        
    Returns:
        Dictionary containing extracted metrics.
    """
    try:
        # Load audio file
        audio, sr = librosa.load(audio_path, sr=None, mono=True)
        
        if len(audio) == 0:
            logger.warning(f"Empty audio file: {audio_path}")
            return {
                'duration': 0.0,
                'syllable_count': 0,
                'bandwidth_hz': 0.0,
                'spectral_entropy': 0.0
            }
        
        # Calculate metrics
        duration = librosa.get_duration(y=audio, sr=sr)
        syllable_count = count_syllables(audio, sr)
        bandwidth = calculate_bandwidth(audio, sr)
        spectral_entropy = calculate_spectral_entropy(audio, sr)
        
        return {
            'duration': duration,
            'syllable_count': syllable_count,
            'bandwidth_hz': bandwidth,
            'spectral_entropy': spectral_entropy
        }
        
    except Exception as e:
        logger.error(f"Error processing {audio_path}: {e}")
        return {
            'duration': 0.0,
            'syllable_count': 0,
            'bandwidth_hz': 0.0,
            'spectral_entropy': 0.0
        }

def extract_metrics_from_dataset(input_csv: str, output_csv: str) -> Tuple[int, int]:
    """
    Extract vocal metrics from a dataset of audio files.
    
    Args:
        input_csv: Path to input CSV with audio file paths.
        output_csv: Path to output CSV for metrics.
        
    Returns:
        Tuple of (successful_count, failed_count).
    """
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    # Read input CSV
    if not os.path.exists(input_csv):
        logger.error(f"Input CSV not found: {input_csv}")
        return 0, 0
        
    with open(input_csv, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            logger.error("Input CSV has no headers")
            return 0, 0
            
        rows = list(reader)
    
    if not rows:
        logger.warning("Input CSV is empty")
        return 0, 0
        
    successful = 0
    failed = 0
    
    # Prepare output fieldnames
    output_fieldnames = list(fieldnames) + ['duration', 'syllable_count', 'bandwidth_hz', 'spectral_entropy']
    
    # Extract metrics for each row
    output_rows = []
    for row in rows:
        audio_path = row.get('audio_path', '')
        
        # Handle relative paths
        if not os.path.isabs(audio_path):
            # Try to find the file relative to project root
            full_path = os.path.join(project_root, audio_path)
            if not os.path.exists(full_path):
                # Try relative to interim data dir
                full_path = os.path.join(interim_dir, audio_path)
            audio_path = full_path
        
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            failed += 1
            # Add default metrics for missing files
            metrics = {
                'duration': 0.0,
                'syllable_count': 0,
                'bandwidth_hz': 0.0,
                'spectral_entropy': 0.0
            }
            output_row = {**row, **metrics}
            output_rows.append(output_row)
            continue
        
        metrics = extract_vocal_metrics(audio_path)
        output_row = {**row, **metrics}
        output_rows.append(output_row)
        
        if metrics['duration'] > 0:
            successful += 1
        else:
            failed += 1
    
    # Write output CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    logger.info(f"Extraction complete: {successful} successful, {failed} failed")
    return successful, failed

def main():
    """
    Main entry point for vocal metrics extraction.
    """
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    processed_dir = get_processed_data_dir()
    
    # Ensure directories exist
    os.makedirs(processed_dir, exist_ok=True)
    
    # Define input and output paths
    input_csv = os.path.join(interim_dir, 'filtered_snr.csv')
    output_csv = os.path.join(processed_dir, 'vocal_metrics.csv')
    
    logger.info(f"Starting vocal metrics extraction from {input_csv}")
    
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        logger.error("Please ensure T017b has been executed to generate filtered_snr.csv")
        return 1
    
    successful, failed = extract_metrics_from_dataset(input_csv, output_csv)
    
    if successful == 0:
        logger.error("No successful extractions. Check input data and audio files.")
        return 1
        
    logger.info(f"Extraction complete. Output written to {output_csv}")
    logger.info(f"Success rate: {successful}/{successful + failed} ({100*successful/(successful+failed):.1f}%)")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
