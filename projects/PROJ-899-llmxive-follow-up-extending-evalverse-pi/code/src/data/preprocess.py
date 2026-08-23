import os
import logging
import numpy as np
import cv2
import librosa
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
from pathlib import Path

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import get_logger, ensure_directories

logger = get_logger(__name__)

def extract_optical_flow(video_path: str) -> Tuple[np.ndarray, bool]:
    """
    Extract optical flow magnitude and variance using OpenCV.
    
    Args:
        video_path: Path to the video file.
        
    Returns:
        Tuple of (feature_vector, missing_data_flag).
        feature_vector: [mean_magnitude, std_magnitude, mean_direction_variance]
        missing_data_flag: True if extraction failed, False otherwise.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Failed to open video: {video_path}")
            return np.array([0.0, 0.0, 0.0]), True
        
        # Read first frame
        ret, prev_frame = cap.read()
        if not ret:
            logger.warning(f"Failed to read first frame: {video_path}")
            cap.release()
            return np.array([0.0, 0.0, 0.0]), True
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        
        magnitudes = []
        directions = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Compute optical flow
            flow = cv2.calcOpticalFlowPyrLK(
                prev_gray, gray, None, None,
                winSize=(15, 15),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
            )
            
            if flow[0] is not None and len(flow[0]) > 0:
                # Calculate magnitude and direction
                dx = flow[1][:, 0, 0] - flow[0][:, 0, 0]
                dy = flow[1][:, 0, 1] - flow[0][:, 0, 1]
                
                mag = np.sqrt(dx**2 + dy**2)
                angle = np.arctan2(dy, dx)
                
                magnitudes.extend(mag)
                directions.extend(angle)
            
            prev_gray = gray.copy()
        
        cap.release()
        
        if not magnitudes:
            logger.warning(f"No optical flow computed for: {video_path}")
            return np.array([0.0, 0.0, 0.0]), True
        
        mean_mag = np.mean(magnitudes)
        std_mag = np.std(magnitudes)
        mean_dir_var = np.var(directions) if directions else 0.0
        
        return np.array([mean_mag, std_mag, mean_dir_var]), False
        
    except Exception as e:
        logger.warning(f"Optical flow extraction failed for {video_path}: {e}")
        return np.array([0.0, 0.0, 0.0]), True

def extract_hog_density(video_path: str) -> Tuple[np.ndarray, bool]:
    """
    Extract HOG density features using OpenCV.
    
    Args:
        video_path: Path to the video file.
        
    Returns:
        Tuple of (feature_vector, missing_data_flag).
        feature_vector: [mean_hog_density, std_hog_density, max_hog_density]
        missing_data_flag: True if extraction failed, False otherwise.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Failed to open video: {video_path}")
            return np.array([0.0, 0.0, 0.0]), True
        
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        densities = []
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize for faster processing
            frame = cv2.resize(frame, (640, 360))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Compute HOG features
            win_size = (64, 128)
            block_size = (16, 16)
            block_stride = (8, 8)
            cell_size = (16, 16)
            nbins = 9
            
            hog_descriptor = cv2.HOGDescriptor(
                win_size, block_size, block_stride, cell_size, nbins
            )
            
            # Calculate HOG density (non-zero descriptors ratio)
            try:
                descriptors = hog_descriptor.compute(gray)
                if len(descriptors) > 0:
                    non_zero = np.count_nonzero(descriptors)
                    density = non_zero / len(descriptors)
                    densities.append(density)
            except Exception:
                pass
            
            frame_count += 1
            if frame_count >= 50:  # Limit to first 50 frames
                break
        
        cap.release()
        
        if not densities:
            logger.warning(f"No HOG density computed for: {video_path}")
            return np.array([0.0, 0.0, 0.0]), True
        
        return np.array([
            np.mean(densities),
            np.std(densities),
            np.max(densities)
        ]), False
        
    except Exception as e:
        logger.warning(f"HOG density extraction failed for {video_path}: {e}")
        return np.array([0.0, 0.0, 0.0]), True

def extract_audio_features(video_path: str) -> Tuple[np.ndarray, bool]:
    """
    Extract audio features (spectral centroid, zero-crossing rate) using Librosa.
    
    Args:
        video_path: Path to the video file.
        
    Returns:
        Tuple of (feature_vector, missing_data_flag).
        feature_vector: [mean_spectral_centroid, std_spectral_centroid, 
                        mean_zcr, std_zcr, spectral_bandwidth]
        missing_data_flag: True if extraction failed (e.g., no audio), False otherwise.
        
    Note:
        If audio extraction fails, missing_data_flag is set to True and a warning
        is logged. A zero vector is NOT returned in case of failure.
    """
    try:
        # Load audio from video file
        y, sr = librosa.load(video_path, duration=30)  # Limit to 30s for performance
        
        if len(y) == 0:
            logger.warning(f"Empty audio extracted from: {video_path}")
            return np.array([0.0, 0.0, 0.0, 0.0, 0.0]), True
        
        # Spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        mean_sc = np.mean(spectral_centroids)
        std_sc = np.std(spectral_centroids)
        
        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        mean_zcr = np.mean(zcr)
        std_zcr = np.std(zcr)
        
        # Spectral bandwidth
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        mean_bw = np.mean(spectral_bandwidth)
        
        return np.array([mean_sc, std_sc, mean_zcr, std_zcr, mean_bw]), False
        
    except Exception as e:
        logger.warning(f"Audio feature extraction failed for {video_path}: {e}")
        # Return None to indicate failure - caller should handle this
        return None, True

def extract_all_features(video_path: str, clip_id: str, dimension: str) -> Dict[str, Any]:
    """
    Extract all features (optical flow, HOG, audio) for a video clip.
    
    Args:
        video_path: Path to the video file.
        clip_id: Identifier for the clip.
        dimension: Dimension label for the clip.
        
    Returns:
        Dictionary with feature vectors and missing data flags.
    """
    result = {
        'clip_id': clip_id,
        'dimension': dimension,
        'optical_features': None,
        'hog_features': None,
        'audio_features': None,
        'optical_missing': False,
        'hog_missing': False,
        'audio_missing': False
    }
    
    # Extract optical flow
    optical_vec, optical_missing = extract_optical_flow(video_path)
    result['optical_features'] = optical_vec
    result['optical_missing'] = optical_missing
    
    # Extract HOG density
    hog_vec, hog_missing = extract_hog_density(video_path)
    result['hog_features'] = hog_vec
    result['hog_missing'] = hog_missing
    
    # Extract audio features
    audio_vec, audio_missing = extract_audio_features(video_path)
    result['audio_features'] = audio_vec
    result['audio_missing'] = audio_missing
    
    return result

def process_video_clip(video_path: str, clip_id: str, dimension: str) -> Dict[str, Any]:
    """
    Process a single video clip and extract audio features.
    
    Args:
        video_path: Path to the video file.
        clip_id: Identifier for the clip.
        dimension: Dimension label for the clip.
        
    Returns:
        Dictionary with audio features and missing data flag.
    """
    audio_vec, missing = extract_audio_features(video_path)
    
    return {
        'clip_id': clip_id,
        'dimension': dimension,
        'feature_vector': audio_vec,
        'missing_data_flag': missing
    }

def batch_process_clips(video_paths: List[str], clip_ids: List[str], 
                       dimensions: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple video clips and extract audio features.
    
    Args:
        video_paths: List of paths to video files.
        clip_ids: List of clip identifiers.
        dimensions: List of dimension labels.
        
    Returns:
        List of dictionaries with audio features and missing data flags.
    """
    results = []
    for path, clip_id, dim in zip(video_paths, clip_ids, dimensions):
        result = process_video_clip(path, clip_id, dim)
        results.append(result)
    return results

def save_audio_features(results: List[Dict[str, Any]], output_path: str):
    """
    Save audio features to CSV file.
    
    Args:
        results: List of dictionaries with audio features.
        output_path: Path to output CSV file.
    """
    ensure_directories(output_path)
    
    rows = []
    for r in results:
        if r['feature_vector'] is not None:
            feature_str = ';'.join(map(str, r['feature_vector']))
        else:
            feature_str = ''
        
        rows.append({
            'clip_id': r['clip_id'],
            'dimension': r['dimension'],
            'feature_vector': feature_str,
            'missing_data_flag': int(r['missing_data_flag'])
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved audio features to {output_path}")

def main():
    """Main function to extract audio features from EvalVerse dataset."""
    logger.info("Starting audio feature extraction")
    
    raw_data_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    
    # Check if data exists
    if not os.path.exists(raw_data_dir):
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        return 1
    
    # Find all video files
    video_files = []
    clip_ids = []
    dimensions = []
    
    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_path = os.path.join(root, file)
                video_files.append(video_path)
                
                # Extract clip_id and dimension from filename or metadata
                # Assuming filename format: clip_{id}_{dimension}.mp4
                base_name = os.path.splitext(file)[0]
                parts = base_name.split('_')
                if len(parts) >= 3:
                    clip_id = parts[1]
                    dimension = parts[2]
                else:
                    clip_id = base_name
                    dimension = "unknown"
                
                clip_ids.append(clip_id)
                dimensions.append(dimension)
    
    if not video_files:
        logger.warning("No video files found in raw data directory")
        return 0
    
    logger.info(f"Found {len(video_files)} video files")
    
    # Extract audio features
    results = batch_process_clips(video_files, clip_ids, dimensions)
    
    # Save results
    output_path = os.path.join(processed_dir, "features_audio.csv")
    save_audio_features(results, output_path)
    
    # Count missing data
    missing_count = sum(1 for r in results if r['missing_data_flag'])
    logger.info(f"Audio features extracted: {len(results)} clips, {missing_count} with missing data")
    
    return 0

if __name__ == "__main__":
    exit(main())