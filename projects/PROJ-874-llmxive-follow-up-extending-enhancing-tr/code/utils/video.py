"""
code/utils/video.py

Utilities for frame extraction, video I/O, and metadata handling.
Designed to work with CPU-only environments and standard video codecs.
"""

import os
import cv2
import numpy as np
from typing import List, Optional, Tuple, Generator
import logging

logger = logging.getLogger(__name__)


def get_video_metadata(video_path: str) -> dict:
    """
    Extracts metadata from a video file.

    Args:
        video_path: Path to the video file.

    Returns:
        A dictionary containing:
            - 'fps': Frames per second.
            - 'width': Video width in pixels.
            - 'height': Video height in pixels.
            - 'frame_count': Total number of frames.
            - 'duration': Duration in seconds.
            - 'codec': FourCC codec string.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the video cannot be opened or has invalid properties.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        codec_fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = chr(codec_fourcc & 0xFF) + \
                chr((codec_fourcc >> 8) & 0xFF) + \
                chr((codec_fourcc >> 16) & 0xFF) + \
                chr((codec_fourcc >> 24) & 0xFF)

        if fps <= 0:
            fps = 30.0  # Fallback if fps is 0 or invalid
        
        duration = frame_count / fps if fps > 0 else 0.0

        return {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "duration": duration,
            "codec": codec,
            "path": video_path
        }
    finally:
        cap.release()


def extract_frames(
    video_path: str,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
    target_fps: Optional[float] = None
) -> Generator[np.ndarray, None, None]:
    """
    Generator that yields frames from a video file.

    This is memory efficient as it does not load all frames into RAM at once.

    Args:
        video_path: Path to the video file.
        start_frame: Index of the first frame to yield (inclusive).
        end_frame: Index of the last frame to yield (exclusive). If None, yields to end.
        target_fps: If provided, skips frames to match this FPS.

    Yields:
        np.ndarray: BGR frame images (H, W, 3).
    
    Raises:
        FileNotFoundError: If video file missing.
        ValueError: If video cannot be opened.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if end_frame is None:
            end_frame = total_frames
        
        end_frame = min(end_frame, total_frames)
        
        if target_fps and fps > 0:
            skip_interval = int(fps / target_fps)
        else:
            skip_interval = 1

        current_frame = 0
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if current_frame >= start_frame and current_frame < end_frame:
                if (current_frame - start_frame) % skip_interval == 0:
                    yield frame
            
            current_frame += 1
    finally:
        cap.release()


def extract_frames_to_list(
    video_path: str,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
    target_fps: Optional[float] = None
) -> List[np.ndarray]:
    """
    Extracts all requested frames from a video and returns them as a list.
    
    WARNING: This loads all frames into memory. Use `extract_frames` generator
    for large videos to avoid OOM errors.

    Args:
        video_path: Path to the video file.
        start_frame: First frame index.
        end_frame: Last frame index (exclusive).
        target_fps: Optional target FPS for subsampling.

    Returns:
        List of BGR frame images.
    """
    return list(extract_frames(video_path, start_frame, end_frame, target_fps))


def write_video(
    output_path: str,
    frames: List[np.ndarray],
    fps: float = 30.0,
    codec: str = 'mp4v'
) -> None:
    """
    Writes a list of frames to a video file.

    Args:
        output_path: Path to save the output video.
        frames: List of BGR frame images (H, W, 3).
        fps: Frames per second for the output video.
        codec: FourCC codec string (e.g., 'mp4v', 'XVID', 'MJPG').

    Raises:
        ValueError: If frames list is empty or frames have inconsistent shapes.
        RuntimeError: If video writer cannot be initialized.
    """
    if not frames:
        raise ValueError("Cannot write video: frames list is empty.")

    height, width = frames[0].shape[:2]
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        raise RuntimeError(f"Failed to initialize VideoWriter for {output_path}. "
                           f"Codec: {codec}, Size: {width}x{height}")

    try:
        for i, frame in enumerate(frames):
            if frame.shape[:2] != (height, width):
                logger.warning(f"Frame {i} shape mismatch. Skipping or resizing logic needed.")
                # Optional: resize here if strict consistency is required, 
                # but usually this indicates a logic error upstream.
                continue
            out.write(frame)
    finally:
        out.release()
    
    logger.info(f"Wrote video to {output_path} ({len(frames)} frames).")


def extract_frames_from_directory(
    directory_path: str,
    extension: str = '.png',
    sort_key: Optional[str] = 'natural'
) -> List[np.ndarray]:
    """
    Loads frames from a directory of image files.

    Args:
        directory_path: Path to directory containing images.
        extension: File extension to look for (e.g., '.png', '.jpg').
        sort_key: Sorting method. 'natural' (alphanumeric), 'lexicographic', or 'modified_time'.

    Returns:
        List of BGR image arrays.

    Raises:
        FileNotFoundError: If directory does not exist or no images found.
    """
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    files = [f for f in os.listdir(directory_path) if f.lower().endswith(extension.lower())]
    
    if not files:
        raise FileNotFoundError(f"No files with extension '{extension}' found in {directory_path}")

    if sort_key == 'natural':
        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split('([0-9]+)', s)]
        files.sort(key=natural_sort_key)
    elif sort_key == 'lexicographic':
        files.sort()
    elif sort_key == 'modified_time':
        files.sort(key=lambda x: os.path.getmtime(os.path.join(directory_path, x)))
    else:
        raise ValueError(f"Unknown sort_key: {sort_key}")

    frames = []
    for f in files:
        img_path = os.path.join(directory_path, f)
        img = cv2.imread(img_path)
        if img is None:
            logger.warning(f"Failed to read image: {img_path}, skipping.")
            continue
        frames.append(img)

    if not frames:
        raise FileNotFoundError("No valid images could be read from the directory.")
    
    return frames


def resize_frames(
    frames: List[np.ndarray],
    width: Optional[int] = None,
    height: Optional[int] = None,
    keep_aspect_ratio: bool = True
) -> List[np.ndarray]:
    """
    Resizes a list of frames to specified dimensions.

    Args:
        frames: List of BGR images.
        width: Target width.
        height: Target height.
        keep_aspect_ratio: If True, scales to fit within (width, height) maintaining aspect ratio.

    Returns:
        List of resized BGR images.
    """
    if not frames:
        return []

    resized_frames = []
    first_h, first_w = frames[0].shape[:2]

    if width is None and height is None:
        return frames

    if keep_aspect_ratio:
        if width is None:
            scale = height / first_h
            new_w = int(first_w * scale)
            new_h = height
        elif height is None:
            scale = width / first_w
            new_w = width
            new_h = int(first_h * scale)
        else:
            # Fit within box
            w_scale = width / first_w
            h_scale = height / first_h
            scale = min(w_scale, h_scale)
            new_w = int(first_w * scale)
            new_h = int(first_h * scale)
    else:
        # Force exact dimensions (may distort)
        new_w = width if width else first_w
        new_h = height if height else first_h

    for frame in frames:
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        resized_frames.append(resized)

    return resized_frames


def get_frame_at_time(
    video_path: str,
    timestamp: float
) -> Optional[np.ndarray]:
    """
    Extracts a single frame at a specific timestamp.

    Args:
        video_path: Path to video file.
        timestamp: Time in seconds.

    Returns:
        BGR frame image or None if timestamp is out of bounds.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return None

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_index = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        
        ret, frame = cap.read()
        if ret:
            return frame
        return None
    finally:
        cap.release()