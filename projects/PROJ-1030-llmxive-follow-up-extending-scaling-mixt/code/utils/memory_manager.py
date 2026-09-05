import math
from typing import List, Optional, Tuple
import numpy as np

def estimate_frame_memory(frame_height: int, frame_width: int, channels: int = 3, dtype: str = 'float32') -> int:
    """
    Estimate memory usage for a single video frame in bytes.
    
    Args:
        frame_height: Height of the frame in pixels
        frame_width: Width of the frame in pixels
        channels: Number of color channels (default 3 for RGB)
        dtype: Data type string (default 'float32')
    
    Returns:
        Estimated memory usage in bytes
    """
    dtype_bytes = 4 if dtype == 'float32' else 2 if dtype == 'float16' else 8
    return frame_height * frame_width * channels * dtype_bytes

def calculate_max_frames(
    total_memory_limit_gb: float,
    frame_height: int,
    frame_width: int,
    channels: int = 3,
    dtype: str = 'float32',
    overhead_factor: float = 1.2
) -> int:
    """
    Calculate the maximum number of frames that can fit in memory.
    
    Args:
        total_memory_limit_gb: Total available memory in GB (e.g., 7.0 for 7GB)
        frame_height: Height of the frame in pixels
        frame_width: Width of the frame in pixels
        channels: Number of color channels
        dtype: Data type string
        overhead_factor: Factor to account for Python overhead, model weights, etc.
    
    Returns:
        Maximum number of frames that can be held in memory simultaneously
    """
    total_memory_bytes = total_memory_limit_gb * (1024 ** 3)
    frame_mem = estimate_frame_memory(frame_height, frame_width, channels, dtype)
    
    # Account for overhead
    available_mem = total_memory_bytes / overhead_factor
    
    max_frames = int(available_mem / frame_mem)
    return max(1, max_frames)  # Ensure at least 1 frame

def generate_subsample_indices(
    total_frames: int,
    max_frames: int,
    strategy: str = 'uniform',
    seed: Optional[int] = None
) -> List[int]:
    """
    Generate indices for subsampling frames from a video.
    
    Args:
        total_frames: Total number of frames in the video
        max_frames: Maximum number of frames to keep
        strategy: Subsampling strategy ('uniform', 'random', 'keyframe')
        seed: Random seed for reproducibility (only used for 'random')
    
    Returns:
        List of frame indices to keep
    """
    if total_frames <= max_frames:
        return list(range(total_frames))
    
    if strategy == 'uniform':
        indices = np.linspace(0, total_frames - 1, max_frames, dtype=int).tolist()
        return indices
    
    elif strategy == 'random':
        if seed is not None:
            np.random.seed(seed)
        indices = np.random.choice(total_frames, size=max_frames, replace=False)
        return sorted(indices.tolist())
    
    elif strategy == 'keyframe':
        # Simplified keyframe strategy: assume every nth frame is a keyframe
        # In a real implementation, this would use actual keyframe detection
        step = math.ceil(total_frames / max_frames)
        indices = list(range(0, total_frames, step))[:max_frames]
        return indices
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def generate_temporal_chunks(
    total_frames: int,
    chunk_size: int,
    overlap: int = 0
) -> List[Tuple[int, int]]:
    """
    Generate temporal chunks (start, end) for processing video segments.
    
    Args:
        total_frames: Total number of frames in the video
        chunk_size: Number of frames per chunk
        overlap: Number of overlapping frames between consecutive chunks
    
    Returns:
        List of (start, end) tuples representing frame ranges
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    chunks = []
    start = 0
    while start < total_frames:
        end = min(start + chunk_size, total_frames)
        chunks.append((start, end))
        # Move start forward by (chunk_size - overlap)
        start = end - overlap
        if start >= total_frames:
            break
    
    return chunks

def get_processing_plan(
    total_frames: int,
    max_memory_gb: float,
    frame_height: int,
    frame_width: int,
    channels: int = 3,
    dtype: str = 'float32',
    subsample_strategy: str = 'uniform',
    chunk_overlap: int = 0,
    seed: Optional[int] = None
) -> dict:
    """
    Generate a complete processing plan to stay within memory limits.
    
    This function calculates:
    1. Maximum frames that can fit in memory
    2. Subsampled frame indices if needed
    3. Temporal chunks for sequential processing
    
    Args:
        total_frames: Total frames in the video
        max_memory_gb: Available memory in GB
        frame_height: Frame height
        frame_width: Frame width
        channels: Color channels
        dtype: Data type
        subsample_strategy: Strategy for subsampling
        chunk_overlap: Overlap between chunks
        seed: Random seed for subsampling
    
    Returns:
        Dictionary containing:
            - max_frames: Maximum frames allowed
            - subsample_indices: List of indices to use (if subsampling needed)
            - chunks: List of (start, end) tuples for processing
            - needs_subsampling: Boolean flag
    """
    max_frames = calculate_max_frames(
        max_memory_gb, frame_height, frame_width, channels, dtype
    )
    
    needs_subsampling = total_frames > max_frames
    
    if needs_subsampling:
        subsample_indices = generate_subsample_indices(
            total_frames, max_frames, subsample_strategy, seed
        )
    else:
        subsample_indices = list(range(total_frames))
    
    # Generate chunks based on the subsampled set (or full set)
    # If subsampled, we process only those frames in chunks
    # For simplicity, we define chunks over the original timeline but only process selected frames
    effective_frames = len(subsample_indices)
    if effective_frames <= max_frames:
        # If subsampling brought us under limit, we can process in one go or small chunks
        chunk_size = min(max_frames, effective_frames)
        chunks = generate_temporal_chunks(effective_frames, chunk_size, chunk_overlap)
    else:
        # Fallback: process in chunks of max_frames
        chunks = generate_temporal_chunks(effective_frames, max_frames, chunk_overlap)
    
    return {
        'max_frames': max_frames,
        'subsample_indices': subsample_indices,
        'chunks': chunks,
        'needs_subsampling': needs_subsampling,
        'total_frames_original': total_frames,
        'total_frames_processed': effective_frames
    }
