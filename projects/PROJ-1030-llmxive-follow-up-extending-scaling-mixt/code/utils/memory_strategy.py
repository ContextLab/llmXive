import json
import os
import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from .memory_manager import (
    estimate_frame_memory,
    calculate_max_frames,
    generate_subsample_indices,
    generate_temporal_chunks,
    get_processing_plan
)
from .logging_config import get_logger

logger = get_logger(__name__)

# Constants for memory constraints (FR-006: 7 GB limit)
MAX_RAM_GB = 7.0
MAX_RAM_MB = MAX_RAM_GB * 1024
SAFETY_FACTOR = 0.8  # Keep usage at 80% of limit to prevent OOM spikes
SAFE_MAX_RAM_MB = MAX_RAM_MB * SAFETY_FACTOR

# Thresholds for strategy selection
# If a clip has more than this many frames, we MUST chunk temporally regardless of subsampling
TEMPORAL_CHUNK_THRESHOLD = 120  # Frames
# If a clip is short but still large, we subsample
SUBSAMPLE_THRESHOLD = 30  # Frames

def estimate_clip_memory(num_frames: int, frame_height: int = 224, frame_width: int = 224, channels: int = 3) -> float:
    """
    Estimate memory usage in MB for loading a video clip into memory for processing.
    Assumes float32 tensors (4 bytes per value).
    """
    # Calculate raw pixel data size: H * W * C * 4 bytes
    frame_size_bytes = frame_height * frame_width * channels * 4
    total_bytes = num_frames * frame_size_bytes
    total_mb = total_bytes / (1024 * 1024)
    
    # Add overhead for model weights and intermediate activations (conservative estimate)
    # LingBot-Video / DiT models can be large. We add a fixed overhead buffer.
    model_overhead_mb = 2048.0  # 2 GB buffer for model + activations
    
    return total_mb + model_overhead_mb

def determine_strategy(num_frames: int, frame_height: int = 224, frame_width: int = 224, channels: int = 3) -> Dict[str, Any]:
    """
    Determine the optimal memory management strategy for a given clip.
    
    Returns a dictionary containing:
    - 'strategy': 'none', 'subsample', or 'chunk'
    - 'target_frames': number of frames to process in one go
    - 'chunk_indices': list of tuples (start, end) if chunking, else None
    - 'subsample_indices': list of indices if subsampling, else None
    """
    estimated_memory = estimate_clip_memory(num_frames, frame_height, frame_width, channels)
    
    strategy = {
        'strategy': 'none',
        'target_frames': num_frames,
        'chunk_indices': None,
        'subsample_indices': None,
        'estimated_memory_mb': estimated_memory
    }
    
    if estimated_memory <= SAFE_MAX_RAM_MB:
        # Safe to process whole clip
        logger.info(f"Clip with {num_frames} frames fits in memory ({estimated_memory:.2f} MB). No strategy needed.")
        return strategy
    
    # If we are here, we need to reduce memory usage
    # Priority 1: Temporal Chunking for very long clips
    if num_frames > TEMPORAL_CHUNK_THRESHOLD:
        logger.info(f"Clip with {num_frames} frames exceeds temporal threshold. Using temporal chunking.")
        chunks = generate_temporal_chunks(num_frames, target_chunk_size=TEMPORAL_CHUNK_THRESHOLD)
        # Estimate memory per chunk
        chunk_size = TEMPORAL_CHUNK_THRESHOLD
        chunk_memory = estimate_clip_memory(chunk_size, frame_height, frame_width, channels)
        
        strategy['strategy'] = 'chunk'
        strategy['target_frames'] = chunk_size
        strategy['chunk_indices'] = chunks
        strategy['estimated_memory_mb'] = chunk_memory
        return strategy
    
    # Priority 2: Subsampling for moderately long clips
    logger.info(f"Clip with {num_frames} frames requires subsampling.")
    # Calculate how many frames we can safely hold
    max_safe_frames = calculate_max_frames(SAFE_MAX_RAM_MB, frame_height, frame_width, channels)
    
    if max_safe_frames < 1:
        # Fallback to a minimal number, though this might still be tight
        max_safe_frames = 10
    
    # Ensure we don't undersample too aggressively if the clip is already short
    target_frames = min(num_frames, max_safe_frames)
    
    subsample_indices = generate_subsample_indices(num_frames, target_frames)
    
    strategy['strategy'] = 'subsample'
    strategy['target_frames'] = target_frames
    strategy['subsample_indices'] = subsample_indices.tolist()
    
    # Re-estimate memory with target frames
    strategy['estimated_memory_mb'] = estimate_clip_memory(target_frames, frame_height, frame_width, channels)
    
    return strategy

def apply_strategy(strategy: Dict[str, Any], frames: np.ndarray) -> List[np.ndarray]:
    """
    Apply the determined strategy to a numpy array of frames.
    Returns a list of processed segments (either subsampled frames or chunks).
    """
    if strategy['strategy'] == 'none':
        return [frames]
    
    if strategy['strategy'] == 'subsample':
        indices = strategy['subsample_indices']
        logger.debug(f"Subsampling frames to indices: {indices}")
        return [frames[indices]]
    
    if strategy['strategy'] == 'chunk':
        chunks = strategy['chunk_indices']
        result = []
        for start, end in chunks:
            chunk = frames[start:end]
            result.append(chunk)
            logger.debug(f"Chunking frames from {start} to {end}")
        return result
    
    raise ValueError(f"Unknown strategy: {strategy['strategy']}")

def save_chunking_config(config: Dict[str, Any], output_path: str):
    """
    Save the chunking configuration to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Chunking config saved to {output_path}")

def generate_memory_log_entry(clip_id: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a log entry for memory usage based on the applied strategy.
    """
    return {
        'clip_id': clip_id,
        'strategy': strategy['strategy'],
        'original_frames': strategy.get('original_frames', 0), # Should be passed in context
        'processed_frames': strategy['target_frames'],
        'estimated_memory_mb': strategy['estimated_memory_mb'],
        'timestamp': int(time.time())
    }

def main():
    """
    Main entry point for testing the memory strategy module.
    This is primarily for manual verification or integration tests.
    """
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Test memory strategy")
    parser.add_argument("--frames", type=int, default=500, help="Number of frames to simulate")
    parser.add_argument("--output", type=str, default="data/processed/chunking_config.json", help="Output config path")
    args = parser.parse_args()
    
    # Simulate a clip
    clip_id = "test_clip_001"
    num_frames = args.frames
    frame_h, frame_w, ch = 224, 224, 3
    
    strategy = determine_strategy(num_frames, frame_h, frame_w, ch)
    strategy['original_frames'] = num_frames
    
    # Save config
    save_chunking_config(strategy, args.output)
    
    # Generate log entry
    log_entry = generate_memory_log_entry(clip_id, strategy)
    print(f"Strategy for {num_frames} frames: {strategy['strategy']}")
    print(f"Log entry: {log_entry}")

if __name__ == "__main__":
    main()
