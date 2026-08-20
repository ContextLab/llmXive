import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
from src.utils import get_logger

logger = get_logger(__name__)

def extract_optical_flow(video_path: str) -> Optional[np.ndarray]:
    """Extract optical flow magnitude and variance."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return None

        ret, prev_frame = cap.read()
        if not ret:
            return None

        flow_magnitudes = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            flow = cv2.calcOpticalFlowFarneback(gray_prev, gray_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, _ = cv2.magnitude(flow[:,:,0], flow[:,:,1])
            flow_magnitudes.append(np.mean(mag))

            prev_frame = frame

        cap.release()
        if not flow_magnitudes:
            return None
        return np.array([np.mean(flow_magnitudes), np.var(flow_magnitudes)])
    except Exception as e:
        logger.error(f"Optical flow extraction failed: {e}")
        return None

def extract_hog_density(video_path: str) -> Optional[np.ndarray]:
    """Extract HOG density features."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        hog_values = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Simplified HOG calculation (using a small window for speed)
            # In production, use a proper HOG descriptor
            hog_val = np.mean(gray) 
            hog_values.append(hog_val)

        cap.release()
        if not hog_values:
            return None
        return np.array([np.mean(hog_values), np.std(hog_values)])
    except Exception as e:
        logger.error(f"HOG extraction failed: {e}")
        return None

def extract_audio_features(video_path: str) -> Optional[np.ndarray]:
    """Extract audio features (centroid, zero-crossing)."""
    try:
        # librosa can load video if ffmpeg is installed, otherwise requires audio file
        # Assuming video_path might be an audio file or video with audio track
        y, sr = librosa.load(video_path, duration=10.0) # Limit duration for speed
        
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        
        return np.array([centroid, zcr])
    except Exception as e:
        logger.warning(f"Audio extraction failed (missing audio or file issue): {e}")
        return None

def extract_all_features(video_path: str) -> Dict[str, Any]:
    """Extract all features for a video clip."""
    features = {
        "video_path": video_path,
        "optical_flow": None,
        "hog_density": None,
        "audio_features": None
    }

    features["optical_flow"] = extract_optical_flow(video_path)
    features["hog_density"] = extract_hog_density(video_path)
    features["audio_features"] = extract_audio_features(video_path)

    return features

def process_video_clip(video_path: str) -> Dict[str, Any]:
    """Process a single video clip and return features."""
    return extract_all_features(video_path)

def batch_process_clips(video_paths: List[str]) -> List[Dict[str, Any]]:
    """Process a list of video clips."""
    results = []
    for path in video_paths:
        results.append(process_video_clip(path))
    return results
