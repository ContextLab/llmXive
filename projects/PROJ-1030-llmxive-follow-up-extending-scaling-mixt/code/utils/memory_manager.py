import math
from typing import List, Optional, Tuple
import numpy as np
import os
import sys
import gc

def estimate_frame_memory(frame_height: int = 224, frame_width: int = 224, channels: int = 3, dtype: str = 'float32') -> int:
    """
    Estimate memory usage for a single frame in bytes.
    
    Args:
        frame_height: Height of the frame
        frame_width: Width of the frame
        channels: Number of color channels
        dtype: Data type string (e.g., 'float32', 'uint8')
        
    Returns:
        Memory usage in bytes
    """
    type_sizes = {
        'float32': 4,
        'float64': 8,
        'uint8': 1,
        'uint16': 2,
        'int32': 4,
        'int64': 8
    }
    bytes_per_pixel = type_sizes.get(dtype, 4)
    return frame_height * frame_width * channels * bytes_per_pixel

def calculate_max_frames(memory_limit_mb: float, frame_height: int = 224, frame_width: int = 224, channels: int = 3, dtype: str = 'float32', safety_factor: float = 0.8) -> int:
    """
    Calculate maximum number of frames that can fit in memory.
    
    Args:
        memory_limit_mb: Memory limit in megabytes
        frame_height: Height of frames
        frame_width: Width of frames
        channels: Number of channels
        dtype: Data type string
        safety_factor: Factor to leave headroom (0.8 = 80% usage)
        
    Returns:
        Maximum number of frames
    """
    memory_limit_bytes = memory_limit_mb * 1024 * 1024 * safety_factor
    frame_bytes = estimate_frame_memory(frame_height, frame_width, channels, dtype)
    return max(1, int(memory_limit_bytes // frame_bytes))

def generate_subsample_indices(total_frames: int, subsample_rate: int) -> np.ndarray:
    """
    Generate indices for frame subsampling.
    
    Args:
        total_frames: Total number of frames in the clip
        subsample_rate: Rate at which to subsample (e.g., 2 = every 2nd frame)
        
    Returns:
        NumPy array of frame indices to keep
    """
    if subsample_rate < 1:
        subsample_rate = 1
    
    indices = np.arange(0, total_frames, subsample_rate)
    return indices

def generate_temporal_chunks(total_frames: int, chunk_size: int) -> List[Tuple[int, int]]:
    """
    Split frames into temporal chunks.
    
    Args:
        total_frames: Total number of frames
        chunk_size: Number of frames per chunk
        
    Returns:
        List of (start, end) tuples representing chunk boundaries
    """
    if chunk_size <= 0:
        chunk_size = total_frames
    
    chunks = []
    for start in range(0, total_frames, chunk_size):
        end = min(start + chunk_size, total_frames)
        chunks.append((start, end))
    
    return chunks

def get_processing_plan(clip_duration: float, fps: int, memory_limit_mb: float = 7168, frame_height: int = 224, frame_width: int = 224) -> dict:
    """
    Generate a complete processing plan for a video clip.
    
    Args:
        clip_duration: Duration of the clip in seconds
        fps: Frames per second
        memory_limit_mb: Memory limit in MB (default 7GB)
        frame_height: Frame height
        frame_width: Frame width
        
    Returns:
        Dictionary containing the processing plan
    """
    total_frames = int(clip_duration * fps)
    max_frames = calculate_max_frames(memory_limit_mb, frame_height, frame_width)
    
    if total_frames <= max_frames:
        # No subsampling needed
        strategy = "full"
        frame_indices = np.arange(total_frames)
        chunks = []
    else:
        # Need to reduce frames
        subsample_rate = math.ceil(total_frames / max_frames)
        frame_indices = generate_subsample_indices(total_frames, subsample_rate)
        
        # If still too large, chunk
        if len(frame_indices) > max_frames:
            strategy = "chunk"
            chunks = generate_temporal_chunks(len(frame_indices), max_frames)
        else:
            strategy = "subsample"
            chunks = []
    
    return {
        "total_frames": total_frames,
        "max_frames": max_frames,
        "strategy": strategy,
        "frame_indices": frame_indices.tolist() if len(frame_indices) < 10000 else "large_array",
        "chunks": chunks,
        "subsample_rate": subsample_rate if strategy != "full" else 1
    }
