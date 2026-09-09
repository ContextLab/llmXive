import math
from typing import List, Optional, Tuple
import numpy as np
import os
import sys
import gc

# Add project root to path to ensure imports work if run as script
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.logging_config import get_logger, fail_loudly

logger = get_logger(__name__)

# Configuration constants
# Target max RAM in GB (FR-006)
TARGET_MAX_RAM_GB = 7.0
TARGET_MAX_RAM_BYTES = TARGET_MAX_RAM_GB * 1024**3
# Overhead factor for Python objects, model weights, etc. (conservative estimate)
OVERHEAD_FACTOR = 1.5
# Estimated bytes per pixel (RGB float32)
BYTES_PER_PIXEL = 3 * 4  # 3 channels * 4 bytes
# Estimated max frame size (1920x1080 typical for video datasets)
DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080

def estimate_frame_memory(width: int = DEFAULT_FRAME_WIDTH, height: int = DEFAULT_FRAME_HEIGHT) -> float:
    """
    Estimates the memory footprint of a single frame in bytes.
    Assumes float32 RGB data.
    """
    return width * height * BYTES_PER_PIXEL

def calculate_max_frames(
    width: int = DEFAULT_FRAME_WIDTH,
    height: int = DEFAULT_FRAME_HEIGHT,
    target_ram_gb: float = TARGET_MAX_RAM_GB
) -> int:
    """
    Calculates the maximum number of frames that can be held in memory
    while respecting the target RAM limit, accounting for overhead.
    """
    frame_mem = estimate_frame_memory(width, height)
    available_mem = (target_ram_gb * 1024**3) / OVERHEAD_FACTOR
    max_frames = int(available_mem / frame_mem)
    # Ensure at least 1 frame can be processed
    return max(1, max_frames)

def generate_subsample_indices(
    total_frames: int,
    max_frames: int,
    strategy: str = "uniform"
) -> List[int]:
    """
    Generates indices for subsampling frames from a video clip.

    Args:
        total_frames: Total number of frames in the video.
        max_frames: Maximum number of frames to keep.
        strategy: Subsampling strategy. 'uniform' selects evenly spaced frames.

    Returns:
        List of frame indices to keep.
    """
    if total_frames <= max_frames:
        return list(range(total_frames))

    if strategy == "uniform":
        # Select max_frames evenly spaced indices
        indices = np.linspace(0, total_frames - 1, max_frames, dtype=int)
        return indices.tolist()
    else:
        fail_loudly(f"Unknown subsampling strategy: {strategy}")

def generate_temporal_chunks(
    total_frames: int,
    chunk_size: int,
    overlap: int = 0
) -> List[Tuple[int, int]]:
    """
    Generates a list of (start, end) tuples representing temporal chunks.

    Args:
        total_frames: Total number of frames.
        chunk_size: Number of frames per chunk.
        overlap: Number of overlapping frames between chunks.

    Returns:
        List of (start_index, end_index) tuples.
    """
    if chunk_size <= 0:
        fail_loudly("Chunk size must be positive.")
    if overlap < 0:
        fail_loudly("Overlap cannot be negative.")
    if overlap >= chunk_size:
        fail_loudly("Overlap must be less than chunk size.")

    chunks = []
    step = chunk_size - overlap
    start = 0
    while start < total_frames:
        end = min(start + chunk_size, total_frames)
        chunks.append((start, end))
        start += step
        # If we've reached the end, break to avoid empty or duplicate chunks
        if end == total_frames:
            break
    return chunks

def get_processing_plan(
    total_frames: int,
    width: int = DEFAULT_FRAME_WIDTH,
    height: int = DEFAULT_FRAME_HEIGHT,
    target_ram_gb: float = TARGET_MAX_RAM_GB,
    strategy: str = "uniform"
) -> dict:
    """
    Creates a processing plan to ensure memory constraints are met.
    This plan includes subsampling indices if necessary.

    Returns:
        Dictionary containing:
            - 'max_frames': calculated max frames allowed
            - 'subsample_indices': list of indices to process (if subsampling needed)
            - 'is_subsampled': boolean indicating if subsampling was applied
    """
    max_frames = calculate_max_frames(width, height, target_ram_gb)
    is_subsampled = total_frames > max_frames
    subsample_indices = generate_subsample_indices(total_frames, max_frames, strategy) if is_subsampled else list(range(total_frames))

    logger.info(f"Processing Plan: Total frames={total_frames}, Max allowed={max_frames}, Subsampled={is_subsampled}")
    if is_subsampled:
        logger.info(f"Subsampling strategy: {strategy}. Keeping {len(subsample_indices)} frames.")

    return {
        "max_frames": max_frames,
        "subsample_indices": subsample_indices,
        "is_subsampled": is_subsampled
    }
