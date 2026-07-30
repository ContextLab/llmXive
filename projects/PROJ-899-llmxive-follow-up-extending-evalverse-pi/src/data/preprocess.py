import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List

from src.data.models import VideoClip, FeatureVector, DimensionScore
from src.utils import get_logger

logger = get_logger(__name__)

# Constants for feature extraction
OPTICAL_FLOW_WINDOW_SIZE = 10
HOG_CELL_SIZE = 8
HOG_BLOCK_SIZE = 2
AUDIO_SAMPLE_RATE = 22050
AUDIO_HOP_LENGTH = 512
N_MELS = 128

def extract_optical_flow(video_path: str) -> Optional[Dict[str, float]]:
    """
    Extract optical flow magnitude and variance features from a video file.
    Uses OpenCV's Farneback dense optical flow algorithm (CPU-only).
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with 'flow_magnitude_mean', 'flow_magnitude_std', 
        'flow_variance_mean', 'flow_variance_std', or None if extraction fails.
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found: {video_path}")
        return None
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return None
    
    # Read first frame
    ret, prev_frame = cap.read()
    if not ret:
        logger.error(f"Failed to read first frame: {video_path}")
        cap.release()
        return None
    
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    flow_magnitudes = []
    flow_variances = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Compute dense optical flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, frame_gray, None,
            pyr_scale=0.5,
            levels=3,
            winsize=OPTICAL_FLOW_WINDOW_SIZE,
            iterations=5,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )
        
        # Calculate magnitude and direction
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Aggregate statistics
        flow_magnitudes.append(np.mean(magnitude))
        flow_variances.append(np.var(magnitude))
        
        frame_count += 1
        prev_gray = frame_gray
    
    cap.release()
    
    if frame_count < 2:
        logger.warning(f"Not enough frames for optical flow in: {video_path}")
        return None
    
    return {
        'flow_magnitude_mean': float(np.mean(flow_magnitudes)),
        'flow_magnitude_std': float(np.std(flow_magnitudes)),
        'flow_variance_mean': float(np.mean(flow_variances)),
        'flow_variance_std': float(np.std(flow_variances))
    }

def extract_hog_density(video_path: str) -> Optional[Dict[str, float]]:
    """
    Extract HOG (Histogram of Oriented Gradients) density features from a video.
    Uses OpenCV's HOGDescriptor (CPU-only).
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with 'hog_density_mean', 'hog_density_std', or None if extraction fails.
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found: {video_path}")
        return None
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return None
    
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Configure HOG parameters
    hog.winSize = (64, 128)
    hog.blockSize = (HOG_BLOCK_SIZE * 8, HOG_BLOCK_SIZE * 8)
    hog.blockStride = (4, 4)
    hog.cellSize = (HOG_CELL_SIZE, HOG_CELL_SIZE)
    hog.nbins = 9
    
    hog_densities = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize to standard size for consistent HOG computation
        frame_resized = cv2.resize(frame, (64, 128))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        # Compute HOG descriptors
        try:
            descriptors = hog.compute(gray)
            # HOG descriptor length for 64x128 with 9 bins: 
            # (7*15) blocks * (2*4) cells/block * 9 bins = 3780
            if len(descriptors) > 0:
                # Calculate density as L2 norm of the descriptor
                density = np.linalg.norm(descriptors) / len(descriptors)
                hog_densities.append(float(density))
                frame_count += 1
        except Exception as e:
            logger.debug(f"HOG computation failed for frame in {video_path}: {e}")
            continue
    
    cap.release()
    
    if frame_count == 0:
        logger.warning(f"No valid frames for HOG in: {video_path}")
        return None
    
    return {
        'hog_density_mean': float(np.mean(hog_densities)),
        'hog_density_std': float(np.std(hog_densities))
    }

def extract_audio_features(video_path: str) -> Optional[Dict[str, float]]:
    """
    Extract audio features (spectral centroid, zero-crossing rate) from a video file.
    Uses Librosa for audio processing.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with audio features or None if extraction fails/missing audio.
    """
    # Extract audio from video using librosa (it handles video files with audio)
    try:
        # librosa.load can handle video files if ffmpeg is installed
        y, sr = librosa.load(video_path, sr=AUDIO_SAMPLE_RATE)
    except Exception as e:
        # Check if it's specifically a missing audio issue
        if "audio" in str(e).lower() or "no audio" in str(e).lower():
            logger.info(f"No audio track found in: {video_path}")
            # Return zeros for audio features as per T008 requirement
            return {
                'spectral_centroid_mean': 0.0,
                'spectral_centroid_std': 0.0,
                'zero_crossing_rate_mean': 0.0,
                'zero_crossing_rate_std': 0.0
            }
        else:
            logger.error(f"Failed to load audio from {video_path}: {e}")
            return None
    
    if len(y) == 0:
        logger.warning(f"Empty audio signal in: {video_path}")
        return {
            'spectral_centroid_mean': 0.0,
            'spectral_centroid_std': 0.0,
            'zero_crossing_rate_mean': 0.0,
            'zero_crossing_rate_std': 0.0
        }
    
    # Calculate spectral centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    # Calculate zero-crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    
    return {
        'spectral_centroid_mean': float(np.mean(spectral_centroid)),
        'spectral_centroid_std': float(np.std(spectral_centroid)),
        'zero_crossing_rate_mean': float(np.mean(zcr)),
        'zero_crossing_rate_std': float(np.std(zcr))
    }

def extract_all_features(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract all features (optical flow, HOG, audio) from a video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary containing all extracted features, or None if all extractions fail.
    """
    features = {}
    
    # Extract optical flow
    flow_features = extract_optical_flow(video_path)
    if flow_features:
        features.update(flow_features)
    else:
        # Add zeros for missing optical flow as per T008
        logger.warning(f"Optical flow extraction failed for {video_path}, using zeros")
        features.update({
            'flow_magnitude_mean': 0.0,
            'flow_magnitude_std': 0.0,
            'flow_variance_mean': 0.0,
            'flow_variance_std': 0.0
        })
    
    # Extract HOG density
    hog_features = extract_hog_density(video_path)
    if hog_features:
        features.update(hog_features)
    else:
        # Add zeros for missing HOG as per T008
        logger.warning(f"HOG extraction failed for {video_path}, using zeros")
        features.update({
            'hog_density_mean': 0.0,
            'hog_density_std': 0.0
        })
    
    # Extract audio features
    audio_features = extract_audio_features(video_path)
    if audio_features:
        features.update(audio_features)
    else:
        # Add zeros for missing audio as per T008
        logger.warning(f"Audio extraction failed for {video_path}, using zeros")
        features.update({
            'spectral_centroid_mean': 0.0,
            'spectral_centroid_std': 0.0,
            'zero_crossing_rate_mean': 0.0,
            'zero_crossing_rate_std': 0.0
        })
    
    return features

def process_video_clip(clip: VideoClip) -> Optional[FeatureVector]:
    """
    Process a single VideoClip and extract all features.
    
    Args:
        clip: VideoClip object containing video path and metadata
        
    Returns:
        FeatureVector with extracted features, or None if extraction completely fails.
    """
    features = extract_all_features(clip.video_path)
    
    if features is None:
        logger.error(f"Failed to extract any features from {clip.video_path}")
        return None
    
    # Create FeatureVector
    feature_vector = FeatureVector(
        clip_id=clip.clip_id,
        features=features,
        timestamp=clip.timestamp
    )
    
    return feature_vector

def batch_process_clips(
    clips: List[VideoClip],
    output_path: Optional[str] = None
) -> List[FeatureVector]:
    """
    Process a batch of VideoClips and optionally save results.
    
    Args:
        clips: List of VideoClip objects to process
        output_path: Optional path to save results as CSV
        
    Returns:
        List of FeatureVector objects
    """
    feature_vectors = []
    success_count = 0
    fail_count = 0
    
    for i, clip in enumerate(clips):
        logger.info(f"Processing clip {i+1}/{len(clips)}: {clip.clip_id}")
        
        fv = process_video_clip(clip)
        if fv is not None:
            feature_vectors.append(fv)
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"Batch processing complete: {success_count} success, {fail_count} failed")
    
    if output_path:
        # Save results to CSV
        import csv
        import os
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            header = ['clip_id', 'timestamp']
            if feature_vectors:
                header.extend(list(feature_vectors[0].features.keys()))
            writer.writerow(header)
            
            # Write data
            for fv in feature_vectors:
                row = [fv.clip_id, fv.timestamp]
                row.extend([fv.features.get(k, 0.0) for k in list(feature_vectors[0].features.keys())])
                writer.writerow(row)
        
        logger.info(f"Results saved to {output_path}")
    
    return feature_vectors