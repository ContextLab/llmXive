import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
from src.data.models import VideoClip, FeatureVector
from src.utils import get_logger

logger = get_logger(__name__)

# Constants for feature extraction
OPTICAL_FLOW_METHOD = cv2.OPTFLOW_LK
OPTICAL_FLOW_WIN_SIZE = (15, 15)
OPTICAL_FLOW_MAX_LEVEL = 3
AUDIO_SR = 22050
AUDIO_HOP_LENGTH = 512
N_MELS = 128
N_FFT = 2048

def extract_optical_flow(video_path: str, clip: VideoClip) -> FeatureVector:
    """
    Extract optical flow features (magnitude and variance) from a video clip.
    
    Gracefully handles failures by returning a zero-filled vector.
    
    Args:
        video_path: Path to the video file
        clip: VideoClip object containing metadata (start, end)
        
    Returns:
        FeatureVector with optical flow features. If extraction fails,
        returns a vector of zeros with a 'failed' flag.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.warning(f"Failed to open video: {video_path}")
            return FeatureVector(
                features=np.zeros(2),
                feature_names=["optical_flow_magnitude", "optical_flow_variance"],
                failed=True,
                error_type="optical_flow_open_failed"
            )
        
        # Set start position
        fps = cap.get(cv2.CAP_PROP_FPS)
        start_frame = int(clip.start_time * fps)
        end_frame = int(clip.end_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Read first frame
        prev_gray = None
        magnitudes = []
        
        frame_count = 0
        while frame_count < (end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Calculate optical flow
                flow = cv2.calcOpticalFlowPyrLK(
                    prev_gray, gray,
                    None, None,
                    maxLevel=OPTICAL_FLOW_MAX_LEVEL,
                    winSize=OPTICAL_FLOW_WIN_SIZE,
                    flags=OPTICAL_FLOW_METHOD
                )
                
                # Extract magnitude from flow
                if flow[0] is not None and flow[1] is not None:
                    flow_vectors = flow[1] - flow[0]
                    magnitudes.append(np.linalg.norm(flow_vectors, axis=2))
            
            prev_gray = gray
            frame_count += 1
        
        cap.release()
        
        if not magnitudes:
            logger.warning(f"No valid frames for optical flow in: {video_path}")
            return FeatureVector(
                features=np.zeros(2),
                feature_names=["optical_flow_magnitude", "optical_flow_variance"],
                failed=True,
                error_type="optical_flow_no_frames"
            )
        
        # Aggregate magnitudes
        all_magnitudes = np.concatenate(magnitudes)
        mean_magnitude = np.mean(all_magnitudes)
        var_magnitude = np.var(all_magnitudes)
        
        return FeatureVector(
            features=np.array([mean_magnitude, var_magnitude]),
            feature_names=["optical_flow_magnitude", "optical_flow_variance"],
            failed=False,
            error_type=None
        )
        
    except Exception as e:
        logger.error(f"Optical flow extraction failed for {video_path}: {str(e)}")
        return FeatureVector(
            features=np.zeros(2),
            feature_names=["optical_flow_magnitude", "optical_flow_variance"],
            failed=True,
            error_type=f"optical_flow_exception_{type(e).__name__}"
        )

def extract_audio_features(video_path: str, clip: VideoClip) -> FeatureVector:
    """
    Extract audio features (spectral centroid, zero-crossing rate) from a video clip.
    
    Gracefully handles missing audio tracks by returning a zero-filled vector.
    
    Args:
        video_path: Path to the video file
        clip: VideoClip object containing metadata (start, end)
        
    Returns:
        FeatureVector with audio features. If audio is missing or extraction fails,
        returns a vector of zeros with a 'failed' flag.
    """
    try:
        # Load audio segment
        y, sr = librosa.load(video_path, offset=clip.start_time, duration=clip.end_time - clip.start_time)
        
        if len(y) == 0:
            logger.warning(f"Empty audio segment for: {video_path}")
            return FeatureVector(
                features=np.zeros(2),
                feature_names=["spectral_centroid", "zero_crossing_rate"],
                failed=True,
                error_type="audio_empty_segment"
            )
        
        # Extract spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        mean_spectral_centroid = np.mean(spectral_centroid)
        
        # Extract zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = np.mean(zcr)
        
        return FeatureVector(
            features=np.array([mean_spectral_centroid, mean_zcr]),
            feature_names=["spectral_centroid", "zero_crossing_rate"],
            failed=False,
            error_type=None
        )
        
    except librosa.util.exceptions.ParameterError as e:
        # This often happens when no audio track is found
        logger.warning(f"No audio track found or parameter error for {video_path}: {str(e)}")
        return FeatureVector(
            features=np.zeros(2),
            feature_names=["spectral_centroid", "zero_crossing_rate"],
            failed=True,
            error_type="audio_missing_or_invalid"
        )
    except Exception as e:
        logger.error(f"Audio feature extraction failed for {video_path}: {str(e)}")
        return FeatureVector(
            features=np.zeros(2),
            feature_names=["spectral_centroid", "zero_crossing_rate"],
            failed=True,
            error_type=f"audio_exception_{type(e).__name__}"
        )

def extract_all_features(video_path: str, clip: VideoClip) -> FeatureVector:
    """
    Extract all features (optical flow + audio) for a video clip.
    
    Handles failures in individual feature extraction gracefully by
    returning zero vectors for failed components and aggregating results.
    
    Args:
        video_path: Path to the video file
        clip: VideoClip object containing metadata
        
    Returns:
        Combined FeatureVector with all features. If all extractions fail,
        returns a zero vector with a composite error flag.
    """
    # Extract optical flow
    flow_features = extract_optical_flow(video_path, clip)
    
    # Extract audio features
    audio_features = extract_audio_features(video_path, clip)
    
    # Combine features
    if flow_features.failed and audio_features.failed:
        logger.warning(f"All feature extraction failed for {video_path}")
        return FeatureVector(
            features=np.zeros(4),
            feature_names=[
                "optical_flow_magnitude",
                "optical_flow_variance",
                "spectral_centroid",
                "zero_crossing_rate"
            ],
            failed=True,
            error_type="all_features_failed"
        )
    
    # Concatenate features, replacing failed ones with zeros
    combined_features = []
    combined_names = []
    
    if not flow_features.failed:
        combined_features.extend(flow_features.features.tolist())
        combined_names.extend(flow_features.feature_names)
    else:
        combined_features.extend([0.0, 0.0])
        combined_names.extend(flow_features.feature_names)
        logger.info(f"Optical flow failed for {video_path}, using zeros")
    
    if not audio_features.failed:
        combined_features.extend(audio_features.features.tolist())
        combined_names.extend(audio_features.feature_names)
    else:
        combined_features.extend([0.0, 0.0])
        combined_names.extend(audio_features.feature_names)
        logger.info(f"Audio features failed for {video_path}, using zeros")
    
    return FeatureVector(
        features=np.array(combined_features),
        feature_names=combined_names,
        failed=False,
        error_type=None
    )

def process_video_clip(video_path: str, clip: VideoClip) -> FeatureVector:
    """
    Process a single video clip and extract all features.
    
    This is a wrapper that ensures proper error handling and logging.
    
    Args:
        video_path: Path to the video file
        clip: VideoClip object containing metadata
        
    Returns:
        FeatureVector with extracted features
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return FeatureVector(
            features=np.zeros(4),
            feature_names=[
                "optical_flow_magnitude",
                "optical_flow_variance",
                "spectral_centroid",
                "zero_crossing_rate"
            ],
            failed=True,
            error_type="video_file_not_found"
        )
    
    return extract_all_features(video_path, clip)

def batch_process_clips(video_paths: List[str], clips: List[VideoClip]) -> List[FeatureVector]:
    """
    Process multiple video clips and extract features for each.
    
    Handles individual clip failures gracefully, continuing with the rest.
    
    Args:
        video_paths: List of paths to video files
        clips: List of VideoClip objects
        
    Returns:
        List of FeatureVector objects, one for each clip
    """
    if len(video_paths) != len(clips):
        raise ValueError("Number of video paths must match number of clips")
    
    results = []
    failed_count = 0
    
    for i, (video_path, clip) in enumerate(zip(video_paths, clips)):
        try:
            feature_vector = process_video_clip(video_path, clip)
            results.append(feature_vector)
            if feature_vector.failed:
                failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing clip {i}: {str(e)}")
            # Add a failed vector for this clip
            results.append(FeatureVector(
                features=np.zeros(4),
                feature_names=[
                    "optical_flow_magnitude",
                    "optical_flow_variance",
                    "spectral_centroid",
                    "zero_crossing_rate"
                ],
                failed=True,
                error_type=f"unexpected_exception_{type(e).__name__}"
            ))
            failed_count += 1
    
    logger.info(f"Batch processing complete: {len(results)} clips, {failed_count} failures")
    return results