import os
import sys
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json
import time

from config import get_results_dir, get_processed_dir, LlmXiveError

logger = logging.getLogger(__name__)

def detect_tearing_artifacts(frame: np.ndarray, video_id: str, frame_idx: int) -> Optional[Dict]:
    """
    Detect invalid pixel artifacts (tearing) in a single frame.
    
    Detection criteria:
    - Pixel value > 255 or < 0 (invalid range after warping)
    - This indicates severe 3D drift causing corruption during warping
    
    Args:
        frame: numpy array representing the frame (H, W, C) or (H, W)
        video_id: identifier for the source video
        frame_idx: index of the frame being checked
        
    Returns:
        Dict with 'video_id', 'frame_idx', 'artifact_type' if artifact found,
        None otherwise.
    """
    artifact = None
    
    # Check for invalid pixel values
    if frame.dtype == np.float32 or frame.dtype == np.float64:
        # Floating point frames - check for out of range values
        invalid_pixels = np.any((frame < 0) | (frame > 255))
        if invalid_pixels:
            artifact = {
                'video_id': video_id,
                'frame_idx': int(frame_idx),
                'artifact_type': 'invalid_pixel_range',
                'details': f'Frame contains pixel values outside [0, 255] range'
            }
    else:
        # Integer frames - check for overflow/underflow indicators
        # In uint8, values are clamped to 0-255, so we check for suspicious patterns
        # that indicate warping artifacts (e.g., extreme edges, checkerboard patterns)
        
        # Check for completely black or white lines (tearing indicators)
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Check for horizontal tearing (complete black/white lines)
        row_means = np.mean(gray, axis=1)
        black_lines = np.where(row_means < 5)[0]
        white_lines = np.where(row_means > 250)[0]
        
        if len(black_lines) > 10 or len(white_lines) > 10:
            # Check if lines are consecutive (indicating a tear)
            if len(black_lines) > 1:
                diffs = np.diff(black_lines)
                if np.any(diffs == 1):
                    artifact = {
                        'video_id': video_id,
                        'frame_idx': int(frame_idx),
                        'artifact_type': 'horizontal_tearing',
                        'details': f'Detected {len(black_lines)} consecutive black lines'
                    }
            elif len(white_lines) > 1:
                diffs = np.diff(white_lines)
                if np.any(diffs == 1):
                    artifact = {
                        'video_id': video_id,
                        'frame_idx': int(frame_idx),
                        'artifact_type': 'horizontal_tearing',
                        'details': f'Detected {len(white_lines)} consecutive white lines'
                    }
        
        # Check for NaN or Inf in float frames if they somehow got through
        if frame.dtype == np.uint8:
            # Convert to float to check for potential issues
            frame_float = frame.astype(np.float32)
            if np.any(np.isnan(frame_float)) or np.any(np.isinf(frame_float)):
                artifact = {
                    'video_id': video_id,
                    'frame_idx': int(frame_idx),
                    'artifact_type': 'nan_inf_detected',
                    'details': 'Frame contains NaN or Inf values'
                }
    
    return artifact

def scan_video_for_artifacts(video_path: str, video_id: str) -> List[Dict]:
    """
    Scan an entire video for tearing artifacts.
    
    Args:
        video_path: Path to the video file
        video_id: Identifier for the video
        
    Returns:
        List of artifact dictionaries found in the video
    """
    artifacts = []
    
    if not os.path.exists(video_path):
        raise LlmXiveError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise LlmXiveError(f"Failed to open video: {video_path}")
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        artifact = detect_tearing_artifacts(frame, video_id, frame_idx)
        if artifact:
            artifacts.append(artifact)
            logger.warning(f"Artifact detected in {video_id} frame {frame_idx}: {artifact['artifact_type']}")
            
        frame_idx += 1
        
        # Progress logging every 100 frames
        if frame_idx % 100 == 0:
            logger.info(f"Scanned {frame_idx} frames in {video_id}")
    
    cap.release()
    logger.info(f"Completed scanning {video_id}: {len(artifacts)} artifacts found")
    
    return artifacts

def write_artifacts_log(artifacts: List[Dict], output_path: str):
    """
    Write detected artifacts to a JSON log file.
    
    Args:
        artifacts: List of artifact dictionaries
        output_path: Path to the output log file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for artifact in artifacts:
            # Write as JSON lines format
            f.write(json.dumps(artifact) + '\n')
    
    logger.info(f"Wrote {len(artifacts)} artifacts to {output_path}")

def main():
    """
    Main entry point for artifact detection.
    
    Scans all corrected videos in data/processed/corrected_videos/
    and logs any tearing artifacts to results/invalid_frames.log
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    results_dir = get_results_dir()
    processed_dir = get_processed_dir()
    
    corrected_videos_dir = os.path.join(processed_dir, 'corrected_videos')
    
    if not os.path.exists(corrected_videos_dir):
        logger.error(f"Corrected videos directory not found: {corrected_videos_dir}")
        logger.error("Please run the flow correction pipeline (T022) first.")
        sys.exit(1)
    
    # Find all video files
    video_files = []
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        video_files.extend(Path(corrected_videos_dir).glob(f'*{ext}'))
    
    if not video_files:
        logger.warning(f"No video files found in {corrected_videos_dir}")
        sys.exit(0)
    
    logger.info(f"Found {len(video_files)} videos to scan for artifacts")
    
    all_artifacts = []
    
    for video_path in video_files:
        video_id = video_path.stem
        logger.info(f"Scanning {video_id}...")
        
        try:
            artifacts = scan_video_for_artifacts(str(video_path), video_id)
            all_artifacts.extend(artifacts)
        except Exception as e:
            logger.error(f"Error scanning {video_id}: {e}")
            continue
    
    # Write results
    output_path = os.path.join(results_dir, 'invalid_frames.log')
    if all_artifacts:
        write_artifacts_log(all_artifacts, output_path)
        logger.warning(f"Total {len(all_artifacts)} artifacts detected across all videos")
        logger.warning(f"Manual review required for flagged frames")
    else:
        # Create empty log file to indicate completion
        os.makedirs(results_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('# No artifacts detected\n')
        logger.info("No artifacts detected - all frames appear valid")
    
    logger.info("Artifact detection complete")

if __name__ == '__main__':
    main()
