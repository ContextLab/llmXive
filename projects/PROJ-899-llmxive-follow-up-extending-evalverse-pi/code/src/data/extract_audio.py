import os
import sys
import logging
import numpy as np
import pandas as pd
import librosa
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger, ensure_directories, write_csv

# Constants
SAMPLE_RATE = 22050
N_BINS = 128
HOP_LENGTH = 512

logger = get_logger(__name__)

def extract_audio_features(audio_path: str) -> Tuple[np.ndarray, bool]:
    """
    Extract audio features (Spectral Centroid and Zero-Crossing Rate) from an audio file.
    
    Args:
        audio_path: Path to the audio file.
        
    Returns:
        Tuple of (feature_vector, missing_data_flag).
        - feature_vector: 1D numpy array of features.
        - missing_data_flag: True if audio could not be processed, False otherwise.
    """
    try:
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            return None, True

        # Load audio
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        
        if y.size == 0:
            logger.warning(f"Empty audio file: {audio_path}")
            return None, True

        # Extract Spectral Centroid
        # librosa.feature.spectral_centroid returns shape (1, n_frames)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=2048, hop_length=HOP_LENGTH)
        
        # Extract Zero-Crossing Rate
        # librosa.feature.zero_crossing_rate returns shape (1, n_frames)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=HOP_LENGTH)

        # Aggregate features (mean over frames)
        # We take the mean to get a single value per feature type per clip
        # For a more robust vector, we could use more statistics (std, max, etc.), 
        # but the task specifies "spectral centroid, zero-crossing rate".
        # To match the "feature_vector" requirement as a flattened array string,
        # we will create a vector of these two values. 
        # If the task implies per-frame features, the vector would be huge. 
        # Given the context of "dimensional viability" and correlation with human scores,
        # a clip-level summary (mean) is standard.
        # However, to ensure a "vector" as requested, let's create a small fixed-size vector
        # representing the clip's audio characteristics.
        
        # Let's extract a few statistics to make it a proper "vector"
        # Mean Centroid, Std Centroid, Mean ZCR, Std ZCR
        mean_sc = np.mean(spectral_centroid)
        std_sc = np.std(spectral_centroid)
        mean_zcr = np.mean(zcr)
        std_zcr = np.std(zcr)
        
        feature_vector = np.array([mean_sc, std_sc, mean_zcr, std_zcr])
        
        return feature_vector, False

    except Exception as e:
        logger.error(f"Error processing audio {audio_path}: {e}")
        return None, True

def process_audio_clips(metadata_df: pd.DataFrame, raw_data_dir: str) -> pd.DataFrame:
    """
    Process a batch of audio clips based on metadata.
    
    Args:
        metadata_df: DataFrame containing clip_id, dimension, and file path info.
        raw_data_dir: Directory containing the raw audio files.
        
    Returns:
        DataFrame with columns [clip_id, dimension, feature_vector, missing_data_flag].
    """
    results = []
    
    # Ensure raw data dir exists
    if not os.path.exists(raw_data_dir):
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")

    for idx, row in metadata_df.iterrows():
        clip_id = row['clip_id']
        dimension = row['dimension']
        
        # Assume audio files are named {clip_id}.wav or similar in the raw dir
        # We need to locate the actual file. 
        # Strategy: Look for files matching clip_id in the raw directory
        found_file = None
        for ext in ['.wav', '.mp3', '.flac', '.ogg']:
            candidate = os.path.join(raw_data_dir, f"{clip_id}{ext}")
            if os.path.exists(candidate):
                found_file = candidate
                break
        
        if not found_file:
            # If not found by exact name, maybe it's in a subdirectory or named differently.
            # For now, we assume the metadata points to a relative path or we construct it.
            # If the metadata has a 'file_path' column, use that.
            if 'file_path' in row:
                found_file = os.path.join(raw_data_dir, row['file_path'])
            else:
                logger.warning(f"Could not locate audio file for clip_id: {clip_id}")
                # Create a NaN-filled vector as per constraint
                # We need a fixed length. Let's use 4 as defined in extract_audio_features.
                nan_vector = np.full(4, np.nan)
                results.append({
                    'clip_id': clip_id,
                    'dimension': dimension,
                    'feature_vector': nan_vector,
                    'missing_data_flag': True
                })
                continue

        feature_vector, missing_flag = extract_audio_features(found_file)
        
        if missing_flag or feature_vector is None:
            # Create a NaN-filled vector of the same length as a valid vector would be
            # Since we don't know the exact length if it failed before creation, 
            # we assume the standard length (4) or try to infer from a successful run.
            # To be safe, we'll use a standard length of 4.
            nan_vector = np.full(4, np.nan)
            results.append({
                'clip_id': clip_id,
                'dimension': dimension,
                'feature_vector': nan_vector,
                'missing_data_flag': True
            })
        else:
            results.append({
                'clip_id': clip_id,
                'dimension': dimension,
                'feature_vector': feature_vector,
                'missing_data_flag': False
            })

    return pd.DataFrame(results)

def main():
    """
    Main entry point for audio feature extraction.
    Reads metadata from processed scores (T042 output) and extracts audio features.
    Outputs to data/processed/features_audio.csv.
    """
    setup_logging()
    
    processed_dir = get_processed_data_dir()
    raw_data_dir = get_raw_data_dir()
    
    scores_file = os.path.join(processed_dir, 'scores.csv')
    output_file = os.path.join(processed_dir, 'features_audio.csv')
    
    if not os.path.exists(scores_file):
        logger.error(f"Input file not found: {scores_file}")
        sys.exit(1)
    
    logger.info(f"Loading metadata from {scores_file}")
    df = pd.read_csv(scores_file)
    
    # Ensure required columns exist
    required_cols = ['clip_id', 'dimension']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Input file missing required columns: {required_cols}")
        sys.exit(1)
    
    logger.info(f"Processing {len(df)} clips for audio features...")
    results_df = process_audio_clips(df, raw_data_dir)
    
    # Convert feature_vector to string representation for CSV storage
    results_df['feature_vector'] = results_df['feature_vector'].apply(lambda x: ','.join(map(str, x)))
    
    logger.info(f"Saving results to {output_file}")
    ensure_directories(output_file)
    results_df.to_csv(output_file, index=False)
    
    logger.info("Audio feature extraction completed.")

if __name__ == "__main__":
    main()