"""
Memory Chunking Module for Feature Extraction Pipeline.

This module provides functions to manage memory usage during video feature extraction
by either subsampling frames (for short clips) or splitting into temporal chunks
(for long clips).
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

import numpy as np

# Import from existing project utilities
# These are defined in code/utils/memory_manager.py as per the API surface
try:
    from code.utils.memory_manager import generate_subsample_indices, generate_temporal_chunks
except ImportError:
    # Fallback for direct execution or different import structure
    # In a real environment, this should be resolved via the package structure
    from utils.memory_manager import generate_subsample_indices, generate_temporal_chunks


logger = logging.getLogger(__name__)


def subsample_frames(
    frames: np.ndarray,
    target_frame_count: int,
    strategy: str = "uniform"
) -> Tuple[np.ndarray, List[int]]:
    """
    Subsample frames from a video clip to reduce memory usage while preserving temporal resolution.

    Args:
        frames: Input frames array of shape (num_frames, height, width, channels)
        target_frame_count: Target number of frames to keep
        strategy: Subsampling strategy ('uniform' or 'center')

    Returns:
        Tuple of (subsampled_frames, list_of_indices)
    """
    if frames is None or len(frames) == 0:
        raise ValueError("Input frames array is empty or None")

    num_frames = len(frames)
    if num_frames <= target_frame_count:
        logger.warning(f"Frame count {num_frames} is already below target {target_frame_count}. Returning original frames.")
        return frames, list(range(num_frames))

    # Generate subsampling indices using the utility function
    indices = generate_subsample_indices(num_frames, target_frame_count, strategy=strategy)

    # Ensure indices are within bounds
    indices = [i for i in indices if 0 <= i < num_frames]

    if len(indices) == 0:
        raise ValueError("Generated subsampling indices are empty")

    # Select frames at the generated indices
    subsampled_frames = frames[indices]

    logger.info(f"Subsampled {num_frames} frames to {len(indices)} frames using {strategy} strategy")

    return subsampled_frames, indices


def chunk_temporal(
    frames: np.ndarray,
    max_frames_per_chunk: int = 30,
    overlap: int = 0
) -> List[np.ndarray]:
    """
    Split a long video clip into temporal chunks to manage memory usage.

    Args:
        frames: Input frames array of shape (num_frames, height, width, channels)
        max_frames_per_chunk: Maximum number of frames per chunk
        overlap: Number of overlapping frames between consecutive chunks

    Returns:
        List of frame arrays, each representing a temporal chunk
    """
    if frames is None or len(frames) == 0:
        raise ValueError("Input frames array is empty or None")

    num_frames = len(frames)
    if num_frames <= max_frames_per_chunk:
        logger.info(f"Frame count {num_frames} is within chunk limit {max_frames_per_chunk}. Returning single chunk.")
        return [frames]

    # Generate temporal chunks using the utility function
    chunk_indices = generate_temporal_chunks(num_frames, max_frames_per_chunk, overlap)

    if len(chunk_indices) == 0:
        raise ValueError("Generated temporal chunks are empty")

    # Extract frames for each chunk
    chunks = []
    for start_idx, end_idx in chunk_indices:
        chunk_frames = frames[start_idx:end_idx]
        chunks.append(chunk_frames)
        logger.debug(f"Created chunk from frame {start_idx} to {end_idx} ({len(chunk_frames)} frames)")

    logger.info(f"Split {num_frames} frames into {len(chunks)} temporal chunks")

    return chunks


def determine_chunking_strategy(
    clip_duration: float,
    fps: float,
    subsample_threshold: float = 5000,
    chunk_threshold: float = 6500
) -> str:
    """
    Determine the appropriate memory management strategy based on clip duration.

    Args:
        clip_duration: Duration of the video clip in seconds
        fps: Frames per second of the video
        subsample_threshold: Threshold (in frames) for subsampling
        chunk_threshold: Threshold (in frames) for temporal chunking

    Returns:
        Strategy string: 'subsample' or 'chunk'
    """
    estimated_frames = int(clip_duration * fps)

    if estimated_frames < subsample_threshold:
        return "subsample"
    elif estimated_frames > chunk_threshold:
        return "chunk"
    else:
        # Default to subsampling for intermediate lengths
        return "subsample"


def save_chunking_config(
    config: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save chunking configuration to a JSON file.

    Args:
        config: Dictionary containing chunking configuration parameters
        output_path: Path to save the configuration file
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path_obj, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Saved chunking configuration to {output_path}")


def load_chunking_config(
    config_path: str
) -> Dict[str, Any]:
    """
    Load chunking configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing chunking configuration parameters
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    logger.info(f"Loaded chunking configuration from {config_path}")
    return config


def apply_memory_strategy(
    frames: np.ndarray,
    strategy: str,
    config: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply the specified memory management strategy to a frame sequence.

    Args:
        frames: Input frames array
        strategy: Strategy to apply ('subsample' or 'chunk')
        config: Configuration dictionary with strategy parameters

    Returns:
        Tuple of (processed_frames or chunks, metadata_dict)
    """
    if strategy == "subsample":
        target_count = int(config.get("frame_subsampling_rate", 0.5) * len(frames))
        target_count = max(1, target_count)  # Ensure at least 1 frame
        processed, indices = subsample_frames(frames, target_count)
        metadata = {
            "strategy": "subsample",
            "original_frames": len(frames),
            "processed_frames": len(processed),
            "indices": indices
        }
        return processed, metadata

    elif strategy == "chunk":
        max_per_chunk = config.get("max_frames_per_chunk", 30)
        overlap = config.get("overlap", 0)
        chunks = chunk_temporal(frames, max_per_chunk, overlap)
        metadata = {
            "strategy": "chunk",
            "original_frames": len(frames),
            "num_chunks": len(chunks),
            "chunk_sizes": [len(c) for c in chunks]
        }
        return chunks, metadata

    else:
        raise ValueError(f"Unknown strategy: {strategy}")
