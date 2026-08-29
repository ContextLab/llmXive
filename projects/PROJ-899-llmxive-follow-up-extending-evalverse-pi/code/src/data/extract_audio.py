import os
import sys
import logging
import json
import numpy as np
import pandas as pd
import librosa
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger

# Constants for audio features
SAMPLE_RATE = 22050
DURATION = None  # Load full audio
HOP_LENGTH = 512
N_BINS = 128  # As per task requirement for spectral centroid

def extract_audio_features(clip_path: str, clip_id: str, dimension: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Extract audio features (spectral centroid, zero-crossing rate) from a single audio file.
    
    Args:
        clip_path: Path to the audio file
        clip_id: Identifier for the clip
        dimension: The dimension label associated with this clip
        logger: Logger instance
        
    Returns:
        Dictionary with clip_id, dimension, feature_vector, and missing_data_flag
    """
    result = {
        "clip_id": clip_id,
        "dimension": dimension,
        "feature_vector": [],
        "missing_data_flag": False
    }
    
    if not os.path.exists(clip_path):
        logger.warning(f"Audio file not found: {clip_path}. Setting missing_data_flag=True.")
        result["missing_data_flag"] = True
        return result
    
    try:
        # Load audio file
        y, sr = librosa.load(clip_path, sr=SAMPLE_RATE, duration=DURATION)
        
        if len(y) == 0:
            logger.warning(f"Empty audio loaded for {clip_id}. Setting missing_data_flag=True.")
            result["missing_data_flag"] = True
            return result
        
        # Extract Spectral Centroid
        # librosa.feature.spectral_centroid returns shape (1, n_frames)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_bins=N_BINS)
        
        # Extract Zero-Crossing Rate
        # librosa.feature.zero_crossing_rate returns shape (1, n_frames)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=HOP_LENGTH)
        
        # Aggregate features per clip (mean over frames)
        # We take the mean of the spectral centroid and zcr across all frames
        mean_spectral_centroid = np.mean(spectral_centroid)
        mean_zcr = np.mean(zcr)
        
        # Create a feature vector. 
        # Since we have two scalar aggregates, we can either return [mean_sc, mean_zcr]
        # or a more detailed vector. The task asks for "feature_vector": [float].
        # To ensure robustness, we will return a vector containing the mean and standard deviation 
        # of the features across frames, which provides more information than just the mean.
        
        std_spectral_centroid = np.std(spectral_centroid)
        std_zcr = np.std(zcr)
        
        feature_vector = [
            float(mean_spectral_centroid),
            float(std_spectral_centroid),
            float(mean_zcr),
            float(std_zcr)
        ]
        
        result["feature_vector"] = feature_vector
        logger.debug(f"Extracted features for {clip_id}: {feature_vector}")
        
    except Exception as e:
        logger.error(f"Error extracting audio features for {clip_id}: {e}")
        result["missing_data_flag"] = True
        
    return result

def process_audio_clips(scores_df: pd.DataFrame, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Process all clips from the scores dataframe and extract audio features.
    
    Args:
        scores_df: DataFrame containing clip_id, dimension, and file paths (or metadata to find paths)
        logger: Logger instance
        
    Returns:
        List of feature dictionaries
    """
    features = []
    
    # Determine raw data directory
    raw_data_dir = get_raw_data_dir()
    
    # Assuming the scores_df has 'clip_id' and potentially 'file_path' or we construct it
    # Based on T042 output: [clip_id, dimension, human_score, vlm_proxy_score]
    # We need to map clip_id to actual file path. 
    # If the raw data structure is known (e.g., data/raw/evalverse/{dimension}/{clip_id}.wav), we construct it.
    # If the dataframe has a 'file_path' column, use that.
    # Since T042 description says "extract... from raw data", let's assume standard naming or a path column.
    # If 'file_path' is missing, we attempt to construct it based on common patterns or fail gracefully.
    
    if 'file_path' in scores_df.columns:
        clip_paths = scores_df[['clip_id', 'dimension', 'file_path']]
    else:
        # Fallback: Assume files are in raw_data_dir/{dimension}/{clip_id}.wav or .mp3
        # This is a heuristic. If the actual data structure differs, this might need adjustment.
        # For now, we iterate and try common extensions.
        clip_paths = scores_df[['clip_id', 'dimension']].copy()
        clip_paths['file_path'] = clip_paths.apply(
            lambda row: next(
                (str(p) for ext in ['.wav', '.mp3', '.flac'] 
                 if (p := Path(raw_data_dir) / row['dimension'] / f"{row['clip_id']}{ext}").exists()),
                None
            ),
            axis=1
        )
    
    for _, row in clip_paths.iterrows():
        clip_id = row['clip_id']
        dimension = row['dimension']
        file_path = row['file_path']
        
        if file_path is None:
            logger.warning(f"Could not locate file for clip_id: {clip_id}, dimension: {dimension}")
            # Still add a record with missing flag
            features.append({
                "clip_id": clip_id,
                "dimension": dimension,
                "feature_vector": [],
                "missing_data_flag": True
            })
            continue
        
        feat = extract_audio_features(str(file_path), clip_id, dimension, logger)
        features.append(feat)
        
    return features

def main():
    """
    Main entry point for audio feature extraction.
    Reads scores from data/processed/scores.csv, extracts features, and saves to data/processed/features_audio.json.
    """
    logger = setup_logging("extract_audio")
    logger.info("Starting audio feature extraction...")
    
    processed_dir = get_processed_data_dir()
    scores_path = Path(processed_dir) / "scores.csv"
    output_path = Path(processed_dir) / "features_audio.json"
    
    if not scores_path.exists():
        logger.error(f"Scores file not found: {scores_path}. Please run T042 first.")
        sys.exit(1)
    
    # Load scores
    try:
        scores_df = pd.read_csv(scores_path)
        logger.info(f"Loaded {len(scores_df)} records from {scores_path}")
    except Exception as e:
        logger.error(f"Failed to load scores: {e}")
        sys.exit(1)
    
    # Extract features
    features = process_audio_clips(scores_df, logger)
    
    # Save results
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=2)
        logger.info(f"Successfully saved audio features to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save features: {e}")
        sys.exit(1)
        
    logger.info("Audio feature extraction completed.")

if __name__ == "__main__":
    main()
