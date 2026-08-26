"""
Audio Feature Extraction Module for EvalVerse Dataset.

This module implements the extraction of audio features (Spectral Centroid,
Zero-Crossing Rate) from video clips using Librosa. It handles missing
audio tracks gracefully by flagging them and returning NaN-filled vectors,
adhering to the constraint of not returning zero vectors for missing data.

Output: data/processed/features_audio.csv
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import librosa
import pandas as pd

# Add project root to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger, ensure_directories

# Constants
TARGET_SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_BINS = 128  # As per task requirement
FEATURE_VECTOR_LENGTH = N_BINS + 1  # Centroid (1) + ZCR (1) + Centroid stats (N_BINS - 1)? 
# Actually, task says: spectral_centroid (n_bins=128) and zero_crossing_rate.
# librosa.feature.spectral_centroid returns shape (1, n_frames) if n_bins is not used, 
# but with n_bins it returns (n_bins, n_frames).
# librosa.feature.zero_crossing_rate returns (1, n_frames).
# We will aggregate these per clip to a single vector.
# Strategy: Compute mean and std for each feature across frames to get a fixed-length vector per clip.
# Spectral Centroid: shape (128, n_frames) -> mean(128), std(128) = 256 features?
# Or just mean across frames for each bin? 
# Let's follow a standard approach: Mean and Std of the feature vector across time.
# Spectral Centroid (128 bins) -> 128 means + 128 stds = 256
# ZCR (1 channel) -> 1 mean + 1 std = 2
# Total = 258 features.
# However, task says "feature_vector" is a flattened array string.
# Let's compute: 
# 1. Spectral Centroid (128 bins): Mean over time -> 128 values.
# 2. Zero Crossing Rate: Mean over time -> 1 value.
# This is simpler and standard for clip-level representation.
# Total length = 129.

FEATURE_LENGTH = N_BINS + 1  # 128 centroids + 1 zcr mean

logger = setup_logging()

def load_clip_audio(clip_id: str, raw_data_dir: Path) -> Optional[Tuple[np.ndarray, int]]:
    """
    Loads audio from a clip. Returns (audio, sr) or None if missing/failed.
    """
    # Expected file pattern: raw_data_dir / {clip_id}.mp3 or .wav
    # EvalVerse usually has audio embedded or separate. 
    # We assume the raw data directory contains the audio files or we extract from video.
    # Since T012 (Optical) likely processes video files, we assume video files exist here.
    # Librosa can load video files directly.
    
    possible_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav']
    audio_path = None
    
    for ext in possible_extensions:
        path = raw_data_dir / f"{clip_id}{ext}"
        if path.exists():
            audio_path = path
            break
    
    if audio_path is None:
        logger.warning(f"Audio file not found for clip {clip_id} in {raw_data_dir}")
        return None

    try:
        y, sr = librosa.load(str(audio_path), sr=TARGET_SAMPLE_RATE, mono=True)
        return y, sr
    except Exception as e:
        logger.warning(f"Failed to load audio for clip {clip_id}: {e}")
        return None

def extract_audio_features(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Extracts spectral centroid and zero-crossing rate from audio.
    Returns a flattened feature vector.
    """
    # Spectral Centroid: shape (128, n_frames)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_bins=N_BINS)
    
    # Zero Crossing Rate: shape (1, n_frames)
    zcr = librosa.feature.zero_crossing_rate(y)

    # Aggregate to clip-level: Mean over frames
    # Centroid: 128 values
    centroid_mean = np.mean(spectral_centroid, axis=1)
    
    # ZCR: 1 value
    zcr_mean = np.mean(zcr)

    # Combine
    feature_vector = np.concatenate([centroid_mean, [zcr_mean]])
    return feature_vector

def process_clip(clip_id: str, dimension: str, raw_data_dir: Path) -> Dict[str, Any]:
    """
    Processes a single clip: extracts audio features or flags missing data.
    """
    audio_data = load_clip_audio(clip_id, raw_data_dir)
    
    if audio_data is None:
        # Missing audio: return NaN-filled vector
        logger.warning(f"Missing audio for clip {clip_id}, marking as missing_data_flag=True")
        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": ",".join([str(np.nan)] * FEATURE_LENGTH),
            "missing_data_flag": True
        }

    try:
        y, sr = audio_data
        features = extract_audio_features(y, sr)
        
        # Ensure no NaNs in valid extraction (unless audio is silent, but librosa handles that)
        if np.any(np.isnan(features)):
            logger.warning(f"NaN detected in extracted features for {clip_id}, marking as missing")
            return {
                "clip_id": clip_id,
                "dimension": dimension,
                "feature_vector": ",".join([str(np.nan)] * FEATURE_LENGTH),
                "missing_data_flag": True
            }

        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": ",".join(map(str, features)),
            "missing_data_flag": False
        }
    except Exception as e:
        logger.error(f"Error extracting features for {clip_id}: {e}")
        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": ",".join([str(np.nan)] * FEATURE_LENGTH),
            "missing_data_flag": True
        }

def batch_process_clips(clips: List[Dict[str, str]], raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Processes a list of clips.
    """
    results = []
    for clip in clips:
        clip_id = clip.get("clip_id")
        dimension = clip.get("dimension", "unknown")
        if not clip_id:
            continue
        result = process_clip(clip_id, dimension, raw_data_dir)
        results.append(result)
    return results

def save_audio_features(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves results to CSV.
    """
    ensure_directories([output_path.parent])
    df = pd.DataFrame(results)
    # Ensure column order
    df = df[["clip_id", "dimension", "feature_vector", "missing_data_flag"]]
    df.to_csv(output_path, index=False)
    logger.info(f"Saved audio features to {output_path} with {len(df)} rows")

def load_scores_for_audio_extraction() -> List[Dict[str, str]]:
    """
    Loads the preprocessed scores to determine which clips/dimensions to process.
    Reads from data/processed/scores.csv (output of T042).
    """
    scores_path = get_processed_data_dir() / "scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"Scores file not found at {scores_path}. Run T042 first.")
    
    df = pd.read_csv(scores_path)
    # We need to process every row (clip, dimension) as a distinct unit for feature extraction
    # or group by clip if features are clip-level. 
    # The task output requires [clip_id, dimension, ...].
    # So we iterate rows.
    return df.to_dict(orient='records')

def main() -> None:
    """
    Main entry point for audio feature extraction.
    """
    logger.info("Starting Audio Feature Extraction (T013)")
    
    raw_data_dir = get_raw_data_dir()
    output_dir = get_processed_data_dir()
    output_path = output_dir / "features_audio.csv"
    
    # Ensure directories exist
    ensure_directories([output_dir])
    
    # Load input data
    try:
        clips_data = load_scores_for_audio_extraction()
        logger.info(f"Loaded {len(clips_data)} clip-dimension pairs for processing.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not clips_data:
        logger.warning("No clips found to process.")
        # Create empty file with headers
        df = pd.DataFrame(columns=["clip_id", "dimension", "feature_vector", "missing_data_flag"])
        df.to_csv(output_path, index=False)
        return

    # Process
    results = batch_process_clips(clips_data, raw_data_dir)
    
    # Save
    save_audio_features(results, output_path)
    
    # Summary
    missing_count = sum(1 for r in results if r["missing_data_flag"])
    logger.info(f"Extraction complete. Total: {len(results)}, Missing: {missing_count}")

if __name__ == "__main__":
    main()