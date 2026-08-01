"""
Data preprocessing and feature extraction utilities.
"""
import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
from src.data.models import VideoClip, FeatureVector

logger = logging.getLogger(__name__)

def extract_optical_flow(video_path: Path) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Extract optical flow magnitude and variance from a video.
    Returns (magnitude_mean, magnitude_variance) or (None, None) on failure.
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return None, None

        prev_gray = None
        magnitudes = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None,
                    0.5, 3, 15, 3, 5, 1.2, 0
                )
                magnitude = cv2.magnitude(flow[:, :, 0], flow[:, :, 1])
                magnitudes.append(np.mean(magnitude))

            prev_gray = gray

        cap.release()

        if len(magnitudes) < 2:
            return None, None

        magnitude_mean = np.mean(magnitudes)
        magnitude_var = np.var(magnitudes)
        return magnitude_mean, magnitude_var

    except Exception as e:
        logger.warning(f"Optical flow extraction failed for {video_path}: {e}")
        return None, None

def extract_audio_features(audio_path: Path) -> Optional[Dict[str, float]]:
    """
    Extract audio features (spectral centroid, zero-crossing rate).
    Returns dict or None on failure.
    """
    try:
        if not audio_path.exists():
            return None

        y, sr = librosa.load(str(audio_path), sr=None)
        
        if len(y) == 0:
            return None

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)

        return {
            "spectral_centroid_mean": float(np.mean(spectral_centroid)),
            "spectral_centroid_std": float(np.std(spectral_centroid)),
            "zcr_mean": float(np.mean(zcr)),
            "zcr_std": float(np.std(zcr)),
        }

    except Exception as e:
        logger.warning(f"Audio feature extraction failed for {audio_path}: {e}")
        return None

def extract_all_features(video_clip: VideoClip) -> Optional[FeatureVector]:
    """
    Extract all features from a video clip.
    Returns FeatureVector or None on complete failure.
    """
    try:
        features_dict = {}
        feature_names = []

        # Optical flow
        flow_mean, flow_var = extract_optical_flow(Path(video_clip.file_path))
        if flow_mean is not None:
            features_dict["optical_flow_mean"] = flow_mean
            features_dict["optical_flow_var"] = flow_var
            feature_names.extend(["optical_flow_mean", "optical_flow_var"])

        # Audio features
        audio_features = extract_audio_features(Path(video_clip.file_path))
        if audio_features:
            for name, value in audio_features.items():
                features_dict[name] = value
                feature_names.append(name)

        if not features_dict:
            return None

        features_array = np.array([features_dict[name] for name in feature_names])

        return FeatureVector(
            clip_id=video_clip.clip_id,
            features=features_array,
            feature_names=feature_names,
            extraction_time=0.0,  # Would be measured in real implementation
            metadata={"source": video_clip.file_path}
        )

    except Exception as e:
        logger.error(f"Feature extraction failed for {video_clip.clip_id}: {e}")
        return None

def process_video_clip(video_path: Path, clip_id: str) -> Optional[FeatureVector]:
    """Process a single video clip and extract features."""
    clip = VideoClip(
        clip_id=clip_id,
        file_path=str(video_path),
        duration=0.0,  # Would be measured
        width=0,
        height=0,
        fps=0.0,
        metadata={}
    )
    return extract_all_features(clip)

def batch_process_clips(video_paths: List[Path], clip_ids: List[str]) -> List[FeatureVector]:
    """Process multiple video clips and return list of feature vectors."""
    results = []
    for path, clip_id in zip(video_paths, clip_ids):
        features = process_video_clip(path, clip_id)
        if features is not None:
            results.append(features)
    return results
