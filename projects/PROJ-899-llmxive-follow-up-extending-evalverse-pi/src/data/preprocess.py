import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import json

from src.config import get_state_root, get_processed_data_dir, get_raw_data_dir
from src.utils import write_json, get_logger, read_json

logger = get_logger(__name__)

def extract_optical_flow(video_path: str, sample_interval: int = 5) -> Optional[np.ndarray]:
    """
    Extract optical flow magnitude and variance from a video clip.
    Returns None if extraction fails (e.g., missing file, unreadable video).
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return None

        prev_frame = None
        flow_magnitudes = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_frame is not None:
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                    )
                    mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                    flow_magnitudes.append(mag)

                prev_frame = gray
            frame_count += 1

        cap.release()

        if not flow_magnitudes:
            logger.warning(f"No frames processed for optical flow: {video_path}")
            return None

        all_flow = np.concatenate([f.flatten() for f in flow_magnitudes])
        return np.array([np.mean(all_flow), np.var(all_flow)])

    except Exception as e:
        logger.error(f"Optical flow extraction failed for {video_path}: {e}", exc_info=True)
        return None

def extract_audio_features(audio_path: str, duration: float = 10.0) -> Optional[np.ndarray]:
    """
    Extract spectral centroid and zero-crossing rate from an audio file.
    Returns None if extraction fails (e.g., missing file, unsupported format).
    """
    try:
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            return None

        y, sr = librosa.load(audio_path, duration=duration)
        
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)

        return np.array([
            np.mean(spectral_centroid),
            np.mean(zcr)
        ])
    except Exception as e:
        logger.error(f"Audio feature extraction failed for {audio_path}: {e}", exc_info=True)
        return None

def extract_all_features(clip_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all features for a single clip based on metadata.
    Returns a dictionary with extracted features and status flags.
    """
    video_path = clip_metadata.get('video_path')
    audio_path = clip_metadata.get('audio_path')
    
    result = {
        'clip_id': clip_metadata.get('clip_id', 'unknown'),
        'optical_flow': None,
        'audio_features': None,
        'optical_flow_error': False,
        'audio_error': False
    }

    if video_path and os.path.exists(video_path):
        result['optical_flow'] = extract_optical_flow(video_path)
        if result['optical_flow'] is None:
            result['optical_flow_error'] = True
    else:
        result['optical_flow_error'] = True

    if audio_path and os.path.exists(audio_path):
        result['audio_features'] = extract_audio_features(audio_path)
        if result['audio_features'] is None:
            result['audio_error'] = True
    else:
        result['audio_error'] = True

    return result

def process_video_clip(clip_metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """
    Process a single video clip and return features along with error status.
    Returns (features_dict, has_error).
    """
    features = extract_all_features(clip_metadata)
    has_error = features['optical_flow_error'] or features['audio_error']
    return features, has_error

def batch_process_clips(metadata_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Process a batch of clips and return aggregated results.
    Returns (processed_list, error_count, total_count).
    """
    processed = []
    error_count = 0
    total_count = len(metadata_list)

    for meta in metadata_list:
        features, has_error = process_video_clip(meta)
        processed.append(features)
        if has_error:
            error_count += 1

    return processed, error_count, total_count

def calculate_global_error_rate(metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the global error rate across the dataset.
    If error rate > 0.05, exclude those samples from correlation calculation.
    Writes results to state/global_error_rate.json.
    Returns the processed list with error samples excluded.
    """
    logger.info("Calculating global error rate across dataset...")
    
    processed_list, error_count, total_count = batch_process_clips(metadata_list)
    
    if total_count == 0:
        logger.error("No clips found in metadata list.")
        return []

    error_rate = error_count / total_count
    
    state_dir = get_state_root()
    os.makedirs(state_dir, exist_ok=True)
    
    output_path = os.path.join(state_dir, "global_error_rate.json")
    
    excluded_count = 0
    valid_list = []
    
    if error_rate > 0.05:
        logger.warning(f"Global error rate {error_rate:.4f} exceeds threshold 0.05. Excluding error samples.")
        for item in processed_list:
            if not (item['optical_flow_error'] or item['audio_error']):
                valid_list.append(item)
            else:
                excluded_count += 1
        logger.info(f"Excluded {excluded_count} samples with errors. Remaining: {len(valid_list)}")
    else:
        logger.info(f"Global error rate {error_rate:.4f} is within threshold. All samples retained.")
        valid_list = processed_list

    result_data = {
        "total_samples": total_count,
        "error_count": error_count,
        "error_rate": error_rate,
        "threshold": 0.05,
        "excluded_count": excluded_count,
        "remaining_count": len(valid_list),
        "status": "excluded" if error_rate > 0.05 else "retained"
    }

    write_json(output_path, result_data)
    logger.info(f"Global error rate report written to {output_path}")

    return valid_list

def main():
    """
    Main entry point for T040: Calculate global error rate and filter dataset.
    Expects metadata to be loaded from data/raw/evalverse_metadata.json (or similar).
    """
    import sys
    from src.data.download import is_data_available, fetch_evalverse_dataset
    from src.utils import read_json

    raw_data_dir = get_raw_data_dir()
    metadata_path = os.path.join(raw_data_dir, "evalverse_metadata.json")

    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file not found: {metadata_path}")
        sys.exit(1)

    logger.info(f"Loading metadata from {metadata_path}")
    metadata_list = read_json(metadata_path)

    if not isinstance(metadata_list, list):
        logger.error("Metadata file does not contain a list of clips.")
        sys.exit(1)

    valid_clips = calculate_global_error_rate(metadata_list)
    
    logger.info(f"Pipeline ready for correlation analysis with {len(valid_clips)} valid samples.")
    return valid_clips

if __name__ == "__main__":
    main()
