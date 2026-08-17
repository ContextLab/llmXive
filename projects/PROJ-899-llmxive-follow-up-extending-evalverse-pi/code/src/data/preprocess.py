"""
Preprocessing module for EvalVerse dataset.
Implements CPU-tractable feature extraction for optical flow and audio.
"""
import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
from src.config import get_raw_data_dir, get_processed_data_dir
from src.utils import get_logger, ensure_directories

logger = get_logger(__name__)

# Constants for feature extraction
OPTICAL_FLOW_SAMPLE_RATE = 5  # Process every 5th frame
OPTICAL_FLOW_METHOD = cv2.DIFF_COF  # CPU-efficient method
AUDIO_SR = 22050  # Standard sampling rate
AUDIO_HOP_LENGTH = 512
N_MFCC = 13
HOG_CELL_SIZE = (8, 8)
HOG_BLOCK_SIZE = (2, 2)

def extract_optical_flow(video_path: str) -> Dict[str, float]:
    """
    Extract optical flow features (magnitude and variance) from a video.
    Uses CPU-only OpenCV implementation for tractability.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary with optical flow features:
        - mean_magnitude: Average flow magnitude
        - std_magnitude: Standard deviation of flow magnitude
        - flow_variance: Variance of flow vectors
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return {"mean_magnitude": 0.0, "std_magnitude": 0.0, "flow_variance": 0.0}

        frame_count = 0
        magnitudes = []

        prev_gray = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Sample frames
            if frame_count % OPTICAL_FLOW_SAMPLE_RATE == 0:
                if prev_gray is not None:
                    # Calculate optical flow
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, gray, None,
                        pyr_scale=0.5,
                        levels=3,
                        winsize=15,
                        iterations=3,
                        poly_n=5,
                        poly_sigma=1.2,
                        flags=0
                    )

                    # Calculate magnitude
                    magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    magnitudes.extend(magnitude.flatten())

                prev_gray = gray

            frame_count += 1

        cap.release()

        if not magnitudes:
            return {"mean_magnitude": 0.0, "std_magnitude": 0.0, "flow_variance": 0.0}

        magnitudes = np.array(magnitudes)
        return {
            "mean_magnitude": float(np.mean(magnitudes)),
            "std_magnitude": float(np.std(magnitudes)),
            "flow_variance": float(np.var(magnitudes))
        }

    except Exception as e:
        logger.error(f"Optical flow extraction failed for {video_path}: {e}")
        return {"mean_magnitude": 0.0, "std_magnitude": 0.0, "flow_variance": 0.0}

def extract_hog_density(video_path: str) -> Dict[str, float]:
    """
    Extract HOG (Histogram of Oriented Gradients) density features.
    CPU-optimized implementation using OpenCV.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary with HOG features:
        - hog_mean_density: Average HOG magnitude
        - hog_std_density: Standard deviation of HOG
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Could not open video: {video_path}")
            return {"hog_mean_density": 0.0, "hog_std_density": 0.0}

        hog_descriptors = []
        frame_count = 0
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % OPTICAL_FLOW_SAMPLE_RATE == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Resize for faster processing
                gray = cv2.resize(gray, (64, 128))
                hog_desc = hog.compute(gray)
                if len(hog_desc) > 0:
                    hog_descriptors.append(np.linalg.norm(hog_desc))

            frame_count += 1

        cap.release()

        if not hog_descriptors:
            return {"hog_mean_density": 0.0, "hog_std_density": 0.0}

        hog_descriptors = np.array(hog_descriptors)
        return {
            "hog_mean_density": float(np.mean(hog_descriptors)),
            "hog_std_density": float(np.std(hog_descriptors))
        }

    except Exception as e:
        logger.error(f"HOG extraction failed for {video_path}: {e}")
        return {"hog_mean_density": 0.0, "hog_std_density": 0.0}

def extract_audio_features(video_path: str) -> Dict[str, float]:
    """
    Extract audio features using librosa.
    Handles missing audio tracks gracefully.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary with audio features:
        - spectral_centroid: Center of mass of spectrum
        - zero_crossing_rate: Rate of zero crossings
        - rms_energy: Root mean square energy
    """
    try:
        # Load audio from video
        y, sr = librosa.load(video_path, sr=AUDIO_SR, mono=True)

        if len(y) == 0:
            return {"spectral_centroid": 0.0, "zero_crossing_rate": 0.0, "rms_energy": 0.0}

        # Spectral centroid
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

        # Zero crossing rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))

        # RMS energy
        rms = np.mean(librosa.feature.rms(y=y))

        return {
            "spectral_centroid": float(spectral_centroid),
            "zero_crossing_rate": float(zcr),
            "rms_energy": float(rms)
        }

    except Exception as e:
        # Missing audio or loading error - return zeros
        logger.warning(f"Audio extraction failed for {video_path}: {e}")
        return {"spectral_centroid": 0.0, "zero_crossing_rate": 0.0, "rms_energy": 0.0}

def extract_all_features(video_path: str) -> Dict[str, Any]:
    """
    Extract all features from a video clip.
    Combines optical flow, HOG, and audio features.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary containing all extracted features
    """
    logger.info(f"Extracting features for: {video_path}")

    features = {
        "video_path": video_path,
        **extract_optical_flow(video_path),
        **extract_hog_density(video_path),
        **extract_audio_features(video_path)
    }

    return features

def process_video_clip(video_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single video clip and save features.

    Args:
        video_path: Path to the video file
        output_dir: Directory to save processed features (optional)

    Returns:
        Dictionary containing extracted features
    """
    if output_dir is None:
        output_dir = get_processed_data_dir()

    ensure_directories(output_dir)

    features = extract_all_features(video_path)

    # Save features
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_features.json")

    import json
    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)

    logger.info(f"Saved features to: {output_path}")
    return features

def batch_process_clips(video_paths: List[str], output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Process multiple video clips in batch.
    Optimized for CPU processing with error handling.

    Args:
        video_paths: List of paths to video files
        output_dir: Directory to save processed features

    Returns:
        List of feature dictionaries for each video
    """
    if output_dir is None:
        output_dir = get_processed_data_dir()

    ensure_directories(output_dir)

    all_features = []
    failed_count = 0

    for video_path in video_paths:
        try:
            features = extract_all_features(video_path)
            features["status"] = "success"
            all_features.append(features)
        except Exception as e:
            logger.error(f"Failed to process {video_path}: {e}")
            failed_count += 1
            all_features.append({
                "video_path": video_path,
                "status": "failed",
                "error": str(e)
            })

    # Save batch results
    import json
    output_path = os.path.join(output_dir, "batch_features.json")
    with open(output_path, 'w') as f:
        json.dump(all_features, f, indent=2)

    logger.info(f"Batch processing complete: {len(all_features) - failed_count} succeeded, {failed_count} failed")
    return all_features
