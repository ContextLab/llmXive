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
from .logging_config import get_logger, fail_loudly

logger = get_logger(__name__)

# Constants for memory limits (FR-006: 7 GB RAM limit)
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
# Threshold to switch between subsampling and chunking (in frames)
SUBSAMPLE_THRESHOLD_FRAMES = 300
CHUNK_SIZE_FRAMES = 256

def estimate_clip_memory(num_frames: int, frame_height: int = 224, frame_width: int = 224, channels: int = 3) -> float:
    """
    Estimate memory usage for processing a video clip.
    Returns memory in MB.
    
    Args:
        num_frames: Number of frames in the clip
        frame_height: Height of frames (default 224)
        frame_width: Width of frames (default 224)
        channels: Number of channels (default 3 for RGB)
        
    Returns:
        Estimated memory usage in MB
    """
    # Estimate per-frame memory (float32: 4 bytes per pixel)
    bytes_per_pixel = 4
    frame_size_bytes = frame_height * frame_width * channels * bytes_per_pixel
    total_bytes = num_frames * frame_size_bytes
    return total_bytes / (1024 * 1024)

def determine_strategy(clip_duration_seconds: float, fps: float, clip_id: str) -> Dict[str, Any]:
    """
    Determine whether to use subsampling or temporal chunking based on clip properties.
    
    Strategy:
    - Short clips (under threshold): Use frame subsampling to reduce memory
    - Long clips (over threshold): Use temporal chunking to split into manageable segments
    
    Args:
        clip_duration_seconds: Duration of the clip in seconds
        fps: Frames per second of the video
        clip_id: Identifier for the clip (for logging)
        
    Returns:
        Dictionary containing the strategy decision and parameters
    """
    total_frames = int(clip_duration_seconds * fps)
    estimated_memory = estimate_clip_memory(total_frames)
    
    logger.info(f"Clip {clip_id}: {total_frames} frames, est. memory: {estimated_memory:.2f} MB")
    
    if estimated_memory > MEMORY_LIMIT_MB:
        # Force chunking if even the full clip exceeds memory limit
        strategy = "chunk"
        logger.warning(f"Clip {clip_id} exceeds memory limit ({estimated_memory:.2f} MB > {MEMORY_LIMIT_MB} MB). Using chunking.")
    elif total_frames > SUBSAMPLE_THRESHOLD_FRAMES:
        # Long clip: use temporal chunking
        strategy = "chunk"
        logger.info(f"Clip {clip_id}: Long clip ({total_frames} frames). Using temporal chunking.")
    else:
        # Short clip: use subsampling
        strategy = "subsample"
        logger.info(f"Clip {clip_id}: Short clip ({total_frames} frames). Using frame subsampling.")
    
    return {
        "clip_id": clip_id,
        "strategy": strategy,
        "total_frames": total_frames,
        "estimated_memory_mb": estimated_memory,
        "fps": fps,
        "duration_seconds": clip_duration_seconds
    }

def apply_strategy(strategy_info: Dict[str, Any], frame_height: int = 224, frame_width: int = 224) -> Dict[str, Any]:
    """
    Apply the determined strategy to generate processing plan.
    
    Args:
        strategy_info: Dictionary from determine_strategy
        frame_height: Height of frames
        frame_width: Width of frames
        
    Returns:
        Processing plan with frame indices or chunks
    """
    clip_id = strategy_info["clip_id"]
    strategy = strategy_info["strategy"]
    total_frames = strategy_info["total_frames"]
    fps = strategy_info["fps"]
    duration = strategy_info["duration_seconds"]
    
    result = {
        "clip_id": clip_id,
        "strategy": strategy,
        "total_frames": total_frames,
        "fps": fps,
        "duration_seconds": duration
    }
    
    if strategy == "subsample":
        # Calculate subsampling rate to keep memory under limit
        max_frames = calculate_max_frames(MEMORY_LIMIT_MB, frame_height, frame_width)
        subsample_rate = max(1, math.ceil(total_frames / max_frames))
        subsample_indices = generate_subsample_indices(total_frames, subsample_rate)
        
        result["subsample_rate"] = subsample_rate
        result["original_frames"] = total_frames
        result["processed_frames"] = len(subsample_indices)
        result["frame_indices"] = subsample_indices.tolist()
        result["chunk_boundaries"] = []
        
        logger.info(f"Clip {clip_id}: Subsampled from {total_frames} to {len(subsample_indices)} frames (rate: {subsample_rate})")
        
    elif strategy == "chunk":
        # Split into temporal chunks
        chunks = generate_temporal_chunks(total_frames, CHUNK_SIZE_FRAMES)
        
        result["chunk_size"] = CHUNK_SIZE_FRAMES
        result["num_chunks"] = len(chunks)
        result["chunk_boundaries"] = [(int(start), int(end)) for start, end in chunks]
        result["frame_indices"] = []  # Will be generated per chunk during processing
        
        logger.info(f"Clip {clip_id}: Split into {len(chunks)} chunks of ~{CHUNK_SIZE_FRAMES} frames each")
    
    else:
        fail_loudly(f"Unknown strategy: {strategy}")
    
    return result

def save_chunking_config(config: Dict[str, Any], output_path: str) -> None:
    """
    Save the chunking configuration to a JSON file.
    
    Args:
        config: Dictionary containing all strategy configurations
        output_path: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Chunking config saved to {output_path}")

def generate_memory_log_entry(clip_id: str, strategy: str, memory_usage_mb: float, success: bool = True) -> Dict[str, Any]:
    """
    Generate a memory log entry for a clip processing operation.
    
    Args:
        clip_id: Identifier for the clip
        strategy: Strategy used (subsample or chunk)
        memory_usage_mb: Peak memory usage in MB
        success: Whether the operation was successful
        
    Returns:
        Dictionary containing the log entry
    """
    return {
        "clip_id": clip_id,
        "strategy": strategy,
        "memory_usage_mb": round(memory_usage_mb, 2),
        "success": success,
        "timestamp": os.popen("date -u +'%Y-%m-%dT%H:%M:%SZ'").read().strip()
    }

def main():
    """
    Main function to demonstrate and test the memory strategy logic.
    This generates a sample chunking config and memory log for validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Strategy Configuration Generator")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for artifacts")
    parser.add_argument("--clip-duration", type=float, default=10.0, help="Sample clip duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--clip-id", type=str, default="sample_clip_001", help="Sample clip ID")
    args = parser.parse_args()
    
    # Determine strategy for sample clip
    strategy_info = determine_strategy(args.clip_duration, args.fps, args.clip_id)
    processing_plan = apply_strategy(strategy_info)
    
    # Create chunking config with sample data
    chunking_config = {
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "subsample_threshold_frames": SUBSAMPLE_THRESHOLD_FRAMES,
        "chunk_size_frames": CHUNK_SIZE_FRAMES,
        "strategies": [processing_plan]
    }
    
    # Save chunking config
    output_path = os.path.join(args.output_dir, "chunking_config.json")
    save_chunking_config(chunking_config, output_path)
    
    # Generate sample memory log entry
    sample_memory_usage = estimate_clip_memory(processing_plan.get("processed_frames", processing_plan["total_frames"]))
    memory_entry = generate_memory_log_entry(
        args.clip_id,
        processing_plan["strategy"],
        sample_memory_usage,
        success=True
    )
    
    # Save memory log (append mode for future entries)
    memory_log_path = os.path.join(args.output_dir, "memory_log.json")
    memory_log = [memory_entry]
    
    # If file exists, load existing entries
    if os.path.exists(memory_log_path):
        try:
            with open(memory_log_path, 'r') as f:
                existing_log = json.load(f)
                if isinstance(existing_log, list):
                    memory_log = existing_log + memory_log
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing memory log: {e}. Starting fresh.")
    
    os.makedirs(args.output_dir, exist_ok=True)
    with open(memory_log_path, 'w') as f:
        json.dump(memory_log, f, indent=2)
    
    logger.info(f"Memory log saved to {memory_log_path}")
    logger.info("Strategy determination complete. Artifacts generated successfully.")
    
    return 0

if __name__ == "__main__":
    exit(main())
