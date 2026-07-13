"""
Video utility functions for frame extraction and basic video I/O.

This module provides functions to:
- Extract frames from video files as NumPy arrays
- Write video files from sequences of frames
- Get video metadata (duration, frame count, resolution)
"""

import os
import cv2
import numpy as np
from typing import List, Optional, Tuple, Generator
import logging

logger = logging.getLogger(__name__)


def get_video_metadata(video_path: str) -> dict:
    """
    Extract metadata from a video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary containing:
            - 'duration': Duration in seconds (float)
            - 'fps': Frames per second (float)
            - 'frame_count': Total number of frames (int)
            - 'width': Video width in pixels (int)
            - 'height': Video height in pixels (int)
            - 'codec': Video codec (str)
            
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
        
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0.0
        codec = cap.get(cv2.CAP_PROP_FOURCC)
        # Convert FOURCC code to string
        codec_str = "".join([chr((int(codec) >> 8 * i) & 0xFF) for i in range(4)])
        
        return {
            'duration': duration,
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'codec': codec_str
        }
    finally:
        cap.release()


def extract_frames(
    video_path: str,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    frame_stride: int = 1,
    return_generator: bool = False
) -> Generator[np.ndarray, None, None] | List[np.ndarray]:
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to the video file
        start_frame: First frame to extract (inclusive), None for start
        end_frame: Last frame to extract (exclusive), None for end
        frame_stride: Extract every Nth frame (default: 1)
        return_generator: If True, return a generator; otherwise return a list
        
    Yields/Returns:
        NumPy arrays of shape (H, W, 3) in BGR format
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened or invalid parameters
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Set frame range
    if start_frame is None:
        start_frame = 0
    if end_frame is None:
        end_frame = total_frames
        
    # Validate range
    if start_frame < 0 or start_frame >= total_frames:
        raise ValueError(f"Invalid start_frame: {start_frame}. Video has {total_frames} frames.")
    if end_frame <= start_frame or end_frame > total_frames:
        raise ValueError(f"Invalid end_frame: {end_frame}. Must be in range ({start_frame}, {total_frames}].")
        
    frames = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx >= start_frame and frame_idx < end_frame:
            if (frame_idx - start_frame) % frame_stride == 0:
                if return_generator:
                    yield frame.copy()
                else:
                    frames.append(frame.copy())
                    
        frame_idx += 1
        
        if frame_idx >= end_frame:
            break
            
    cap.release()
    
    if not return_generator:
        return frames
    else:
        # Generator already yielded, just return None to signal completion
        return
        

def extract_frames_to_list(
    video_path: str,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    frame_stride: int = 1
) -> List[np.ndarray]:
    """
    Extract frames from a video file and return as a list.
    
    Convenience wrapper around extract_frames with return_generator=False.
    
    Args:
        video_path: Path to the video file
        start_frame: First frame to extract (inclusive), None for start
        end_frame: Last frame to extract (exclusive), None for end
        frame_stride: Extract every Nth frame (default: 1)
        
    Returns:
        List of NumPy arrays of shape (H, W, 3) in BGR format
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened or invalid parameters
    """
    return list(extract_frames(
        video_path,
        start_frame=start_frame,
        end_frame=end_frame,
        frame_stride=frame_stride,
        return_generator=False
    ))


def write_video(
    output_path: str,
    frames: List[np.ndarray],
    fps: float = 24.0,
    codec: str = 'mp4v',
    is_color: bool = True
) -> None:
    """
    Write a sequence of frames to a video file.
    
    Args:
        output_path: Path to the output video file
        frames: List of NumPy arrays (H, W, 3) in BGR format
        fps: Frames per second (default: 24.0)
        codec: Video codec (default: 'mp4v')
        is_color: Whether frames are color (default: True)
        
    Raises:
        ValueError: If frames list is empty or frames have inconsistent sizes
        RuntimeError: If video writer cannot be initialized
    """
    if not frames:
        raise ValueError("Frames list cannot be empty")
        
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Check frame consistency
    height, width = frames[0].shape[:2]
    for i, frame in enumerate(frames):
        if frame.shape[:2] != (height, width):
            raise ValueError(
                f"Inconsistent frame sizes at index {i}: "
                f"expected ({height}, {width}), got {frame.shape[:2]}"
            )
            
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), is_color)
    
    if not writer.isOpened():
        raise RuntimeError(f"Failed to initialize video writer for: {output_path}")
        
    try:
        for i, frame in enumerate(frames):
            writer.write(frame)
    finally:
        writer.release()
        
    logger.info(f"Written video with {len(frames)} frames to {output_path}")


def extract_frames_from_directory(
    directory_path: str,
    pattern: str = "*.png",
    sort_key: Optional[str] = 'filename'
) -> List[np.ndarray]:
    """
    Extract frames from image files in a directory.
    
    Args:
        directory_path: Path to directory containing image files
        pattern: Glob pattern for image files (default: "*.png")
        sort_key: Sorting method ('filename' or 'modification_time')
        
    Returns:
        List of NumPy arrays in sorted order
        
    Raises:
        FileNotFoundError: If directory doesn't exist or no matching files found
    """
    import glob
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
        
    files = glob.glob(os.path.join(directory_path, pattern))
    
    if not files:
        raise FileNotFoundError(
            f"No files matching '{pattern}' found in {directory_path}"
        )
        
    # Sort files
    if sort_key == 'filename':
        files.sort()
    elif sort_key == 'modification_time':
        files.sort(key=lambda f: os.path.getmtime(f))
    else:
        raise ValueError(f"Invalid sort_key: {sort_key}")
        
    frames = []
    for file_path in files:
        frame = cv2.imread(file_path)
        if frame is None:
            logger.warning(f"Failed to read image: {file_path}")
            continue
        frames.append(frame)
        
    logger.info(f"Loaded {len(frames)} frames from {directory_path}")
    return frames


def resize_frames(
    frames: List[np.ndarray],
    target_size: Tuple[int, int],
    interpolation: int = cv2.INTER_LINEAR
) -> List[np.ndarray]:
    """
    Resize a list of frames to a target size.
    
    Args:
        frames: List of NumPy arrays
        target_size: Tuple (width, height)
        interpolation: OpenCV interpolation method (default: INTER_LINEAR)
        
    Returns:
        List of resized frames
    """
    width, height = target_size
    resized_frames = []
    
    for frame in frames:
        resized = cv2.resize(frame, (width, height), interpolation=interpolation)
        resized_frames.append(resized)
        
    return resized_frames


def get_frame_at_time(
    video_path: str,
    timestamp_seconds: float
) -> Optional[np.ndarray]:
    """
    Extract a single frame at a specific timestamp.
    
    Args:
        video_path: Path to video file
        timestamp_seconds: Timestamp in seconds
        
    Returns:
        Frame as NumPy array, or None if timestamp is out of range
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
        
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_idx = int(timestamp_seconds * fps)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if frame_idx < 0 or frame_idx >= total_frames:
            return None
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            return None
            
        return frame
    finally:
        cap.release()
