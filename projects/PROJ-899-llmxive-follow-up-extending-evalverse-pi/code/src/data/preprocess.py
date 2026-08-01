import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

def extract_optical_flow(video_path: str, sample_rate: int = 10) -> Optional[np.ndarray]:
    """
    Extract optical flow features (magnitude and variance) from a video clip.
    Returns None if processing fails.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return None

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count < 2:
            return np.zeros(0)

        prev_frame = None
        flow_magnitudes = []

        for i in range(0, frame_count, sample_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_frame is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, gray, None,
                    0.5, 3, 15, 3, 5, 1.2, 0
                )
                mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                flow_magnitudes.append(np.mean(mag))
            
            prev_frame = gray

        cap.release()
        
        if not flow_magnitudes:
            return np.zeros(0)
        
        return np.array([np.mean(flow_magnitudes), np.var(flow_magnitudes)])
    except Exception as e:
        logger.error(f"Optical flow extraction failed for {video_path}: {e}")
        return None

def extract_audio_features(video_path: str) -> Optional[np.ndarray]:
    """
    Extract audio features (spectral centroid, zero-crossing rate).
    Returns None if audio is missing or processing fails.
    """
    try:
        y, sr = librosa.load(video_path, offset=0, duration=30) # Limit duration for speed
        
        if len(y) == 0:
            return np.zeros(0)

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)

        return np.array([
            np.mean(spectral_centroid[0]),
            np.mean(zcr[0])
        ])
    except Exception as e:
        logger.warning(f"Audio extraction failed for {video_path}: {e}")
        return None

def extract_all_features(video_path: str) -> Dict[str, Any]:
    """
    Extracts all features for a given video clip.
    """
    optical_flow = extract_optical_flow(video_path)
    audio_features = extract_audio_features(video_path)

    features = {}
    if optical_flow is not None and len(optical_flow) > 0:
        features["optical_flow"] = optical_flow
    else:
        features["optical_flow"] = np.zeros(0)

    if audio_features is not None and len(audio_features) > 0:
        features["audio"] = audio_features
    else:
        features["audio"] = np.zeros(0)

    return features

def process_video_clip(video_path: str, clip_id: str) -> Optional[Dict[str, Any]]:
    """
    Process a single video clip and return feature dictionary.
    """
    if not os.path.exists(video_path):
        logger.error(f"File not found: {video_path}")
        return None

    features = extract_all_features(video_path)
    return {
        "clip_id": clip_id,
        "features": features
    }

def batch_process_clips(video_paths: List[str], clip_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Process a batch of video clips.
    """
    results = []
    for path, cid in zip(video_paths, clip_ids):
        result = process_video_clip(path, cid)
        if result:
            results.append(result)
    return results
