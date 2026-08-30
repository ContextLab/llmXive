import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger, write_json

# Librosa for audio processing
import librosa

logger = get_logger(__name__)

def extract_audio_features(
    audio_path: str,
    clip_id: str,
    dimension: str,
    n_bins: int = 128
) -> Dict[str, Any]:
    """
    Extract audio features (spectral centroid, zero-crossing rate) from an audio file.

    Args:
        audio_path: Path to the audio file.
        clip_id: Identifier for the video clip.
        dimension: Technical sub-dimension label.
        n_bins: Number of bins for spectral centroid calculation.

    Returns:
        Dictionary with clip_id, dimension, feature_vector, and missing_data_flag.
    """
    result = {
        "clip_id": clip_id,
        "dimension": dimension,
        "feature_vector": [],
        "missing_data_flag": False
    }

    try:
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path} for clip {clip_id}")
            result["missing_data_flag"] = True
            return result

        # Load audio file
        # librosa.load returns (y, sr)
        y, sr = librosa.load(audio_path, sr=None)

        if y.size == 0:
            logger.warning(f"Empty audio signal for clip {clip_id}")
            result["missing_data_flag"] = True
            return result

        # Extract Spectral Centroid
        # librosa.feature.spectral_centroid returns an array of shape (1, t)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_bins=n_bins)
        
        # Extract Zero-Crossing Rate
        # librosa.feature.zero_crossing_rate returns an array of shape (1, t)
        zcr = librosa.feature.zero_crossing_rate(y)

        # Aggregate features: compute mean and std for each feature over time
        # We flatten to a 1D vector: [mean_centroid, std_centroid, mean_zcr, std_zcr]
        # Note: spectral_centroid and zcr are 2D arrays (1, t)
        mean_centroid = float(np.mean(spectral_centroid))
        std_centroid = float(np.std(spectral_centroid))
        mean_zcr = float(np.mean(zcr))
        std_zcr = float(np.std(zcr))

        feature_vector = [mean_centroid, std_centroid, mean_zcr, std_zcr]
        result["feature_vector"] = feature_vector

    except Exception as e:
        logger.error(f"Error processing audio for clip {clip_id}: {e}")
        result["missing_data_flag"] = True
        # Do NOT return a zero vector; flag as missing
    
    return result

def process_audio_clips(
    scores_path: str,
    raw_data_dir: Optional[str] = None,
    audio_extension: str = ".wav"
) -> List[Dict[str, Any]]:
    """
    Process a list of clips from a scores CSV and extract audio features.

    Args:
        scores_path: Path to the CSV file containing clip metadata (clip_id, dimension).
        raw_data_dir: Base directory for raw data. Defaults to configured raw data dir.
        audio_extension: File extension for audio files.

    Returns:
        List of result dictionaries.
    """
    if raw_data_dir is None:
        raw_data_dir = str(get_raw_data_dir())

    # Load scores metadata
    df = pd.read_csv(scores_path)
    
    required_cols = ['clip_id', 'dimension']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    results = []
    
    for _, row in df.iterrows():
        clip_id = row['clip_id']
        dimension = row['dimension']
        
        # Construct audio path. Assuming structure: raw_data_dir/{clip_id}{ext}
        # If the dataset has subfolders, this logic might need adjustment, 
        # but we follow the standard pattern implied by the project.
        audio_path = os.path.join(raw_data_dir, f"{clip_id}{audio_extension}")
        
        # If exact path doesn't exist, try common variations if needed, 
        # but for now we assume the mapping is direct or handled by the fetcher.
        
        feature_data = extract_audio_features(
            audio_path=audio_path,
            clip_id=clip_id,
            dimension=dimension,
            n_bins=128
        )
        results.append(feature_data)
        
        if feature_data["missing_data_flag"]:
            logger.info(f"Skipped feature extraction for {clip_id} (missing/failed audio)")

    return results

def main():
    """
    Main entry point for audio feature extraction.
    Reads scores from data/processed/scores.csv and writes features to data/processed/features_audio.json.
    """
    setup_logging(level=logging.INFO)
    
    processed_dir = get_processed_data_dir()
    scores_path = os.path.join(processed_dir, "scores.csv")
    output_path = os.path.join(processed_dir, "features_audio.json")

    if not os.path.exists(scores_path):
        logger.error(f"Input file not found: {scores_path}")
        sys.exit(1)

    logger.info(f"Starting audio feature extraction from {scores_path}")
    
    features = process_audio_clips(scores_path)
    
    logger.info(f"Extracted features for {len(features)} clips")
    
    # Write output JSON
    write_json(output_path, features)
    logger.info(f"Audio features saved to {output_path}")

if __name__ == "__main__":
    main()
