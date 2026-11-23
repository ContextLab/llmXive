import os
import csv
import logging
import librosa
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from src.utils.config import get_project_root, get_processed_data_dir, get_interim_data_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_spectral_entropy(y: np.ndarray, sr: int) -> float:
    """
    Calculate spectral entropy of an audio signal.
    Spectral entropy is a measure of the complexity/disorder of the signal's spectrum.
    Higher entropy indicates a more complex/noisy signal.
    """
    if len(y) == 0:
        return 0.0
    
    # Compute Short-Time Fourier Transform
    D = np.abs(librosa.stft(y))
    
    # Normalize to get a probability distribution
    S = D ** 2
    S_sum = np.sum(S, axis=0)
    S_sum[S_sum == 0] = 1e-10  # Avoid division by zero
    P = S / S_sum
    
    # Compute entropy
    entropy = -np.sum(P * np.log(P + 1e-10), axis=0)
    
    # Return mean entropy across frames
    return float(np.mean(entropy))

def calculate_bandwidth(y: np.ndarray, sr: int) -> float:
    """
    Calculate spectral bandwidth (spread of frequencies).
    Returns the standard deviation of the frequency distribution.
    """
    if len(y) == 0:
        return 0.0
    
    # Compute spectral bandwidth
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    
    # Return mean bandwidth across frames
    return float(np.mean(bandwidth))

def count_syllables(y: np.ndarray, sr: int, min_duration: float = 0.05, min_energy: float = 0.01) -> int:
    """
    Count the number of syllables (discrete vocal elements) in the audio.
    Uses onset detection to identify syllable boundaries.
    
    Args:
        y: Audio signal
        sr: Sample rate
        min_duration: Minimum duration of a syllable in seconds
        min_energy: Minimum energy threshold for syllable detection
    """
    if len(y) == 0:
        return 0
    
    # Compute onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Detect onsets
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=True)
    
    # Filter by minimum duration and energy
    syllable_count = 0
    if len(onsets) > 0:
        # Calculate energy of each potential syllable
        frame_duration = len(y) / sr
        for i, onset in enumerate(onsets):
            # Estimate end of syllable (next onset or end of signal)
            if i + 1 < len(onsets):
                end_frame = onsets[i + 1]
            else:
                end_frame = len(y)
            
            # Calculate duration in seconds
            duration = (end_frame - onset) / sr
            
            # Calculate energy of this segment
            segment = y[onset:end_frame]
            energy = np.sqrt(np.mean(segment ** 2))
            
            # Count if it meets criteria
            if duration >= min_duration and energy >= min_energy:
                syllable_count += 1
    
    return syllable_count

def extract_vocal_metrics(audio_path: str) -> Dict[str, float]:
    """
    Extract vocal complexity metrics from an audio file.
    
    Metrics:
        - duration: Total duration in seconds
        - syllable_count: Number of discrete vocal elements
        - bandwidth: Spectral bandwidth in Hz
        - spectral_entropy: Spectral entropy (complexity measure)
    
    Args:
        audio_path: Path to the audio file
    
    Returns:
        Dictionary containing extracted metrics
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        
        if len(y) == 0:
            logger.warning(f"Empty audio file: {audio_path}")
            return {
                'duration': 0.0,
                'syllable_count': 0,
                'bandwidth': 0.0,
                'spectral_entropy': 0.0
            }
        
        # Calculate metrics
        duration = librosa.get_duration(y=y, sr=sr)
        syllable_count = count_syllables(y, sr)
        bandwidth = calculate_bandwidth(y, sr)
        spectral_entropy = calculate_spectral_entropy(y, sr)
        
        return {
            'duration': duration,
            'syllable_count': syllable_count,
            'bandwidth': bandwidth,
            'spectral_entropy': spectral_entropy
        }
    
    except Exception as e:
        logger.error(f"Error extracting metrics from {audio_path}: {str(e)}")
        return {
            'duration': 0.0,
            'syllable_count': 0,
            'bandwidth': 0.0,
            'spectral_entropy': 0.0
        }

def extract_metrics_from_dataset(input_csv: str, output_csv: str, audio_dir: Optional[str] = None) -> Tuple[int, int]:
    """
    Process a dataset CSV file and extract vocal metrics for each recording.
    
    Args:
        input_csv: Path to input CSV with audio file paths
        output_csv: Path to output CSV with extracted metrics
        audio_dir: Optional base directory for audio files (if not absolute paths)
    
    Returns:
        Tuple of (processed_count, error_count)
    """
    processed_count = 0
    error_count = 0
    
    # Ensure output directory exists
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read input CSV
    with open(input_csv, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['duration', 'syllable_count', 'bandwidth', 'spectral_entropy']
        
        rows = []
        for row in reader:
            # Determine audio path
            audio_path = row.get('audio_path', '')
            if not audio_path and audio_dir:
                audio_path = os.path.join(audio_dir, row.get('filename', ''))
            
            if not audio_path or not os.path.exists(audio_path):
                logger.warning(f"Audio file not found: {audio_path}")
                error_count += 1
                continue
            
            # Extract metrics
            metrics = extract_vocal_metrics(audio_path)
            
            # Add metrics to row
            row['duration'] = metrics['duration']
            row['syllable_count'] = metrics['syllable_count']
            row['bandwidth'] = metrics['bandwidth']
            row['spectral_entropy'] = metrics['spectral_entropy']
            
            rows.append(row)
            processed_count += 1
    
    # Write output CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Extracted metrics for {processed_count} recordings. Errors: {error_count}")
    return processed_count, error_count

def main():
    """
    Main entry point for vocal metrics extraction.
    Reads from filtered data and outputs to final dataset with metrics.
    """
    project_root = get_project_root()
    
    # Define input and output paths
    interim_dir = get_interim_data_dir()
    processed_dir = get_processed_data_dir()
    
    input_csv = os.path.join(interim_dir, 'filtered_snr.csv')
    output_csv = os.path.join(processed_dir, 'vocal_metrics.csv')
    
    # Check if input file exists
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        logger.error("Please run the SNR filtering task (T017) first.")
        return 1
    
    # Find audio directory (assuming it's in data/raw)
    audio_dir = os.path.join(project_root, 'data', 'raw', 'audio')
    if not os.path.exists(audio_dir):
        # Try alternative location
        audio_dir = os.path.join(project_root, 'data', 'raw')
    
    logger.info(f"Processing audio files from: {audio_dir}")
    logger.info(f"Input: {input_csv}")
    logger.info(f"Output: {output_csv}")
    
    # Extract metrics
    processed, errors = extract_metrics_from_dataset(input_csv, output_csv, audio_dir)
    
    if processed == 0:
        logger.error("No recordings were processed. Check input data and audio files.")
        return 1
    
    logger.info(f"Successfully extracted metrics for {processed} recordings.")
    logger.info(f"Output saved to: {output_csv}")
    
    return 0

if __name__ == '__main__':
    exit(main())
