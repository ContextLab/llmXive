import os
import sys
import time
import json
import psutil
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project API surface
from src.config import get_project_root, get_data_root, get_raw_data_dir
from src.data.preprocess import batch_process_clips
from src.data.profiles import get_memory_usage_mb, profile_clip_execution, save_profiling_results
from src.utils import get_logger, write_json

logger = get_logger(__name__)


def get_sample_clips(raw_data_dir: Path, n: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve a list of clip metadata from the raw data directory.
    Assumes the dataset structure contains a manifest or list of video files.
    Returns a list of dicts with 'path' and 'id'.
    """
    clips = []
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Look for common manifest files or scan directory
    manifest_path = raw_data_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                clips = data[:n]
            elif isinstance(data, dict) and 'clips' in data:
                clips = data['clips'][:n]
    else:
        # Fallback: scan for video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        files = [f for f in raw_data_dir.iterdir() if f.suffix.lower() in video_extensions]
        files = sorted(files)[:n]
        clips = [{"id": f.stem, "path": str(f)} for f in files]

    if len(clips) == 0:
        raise ValueError(f"No video clips found in {raw_data_dir}")
    
    logger.info(f"Selected {len(clips)} clips for batch processing")
    return clips


def process_batch_clips(
    clips: List[Dict[str, Any]], 
    output_dir: Path,
    profiling_log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process a batch of clips, extracting features and aggregating timing stats.
    
    Args:
        clips: List of clip metadata dicts with 'path' and 'id'.
        output_dir: Directory to write processed features and logs.
        profiling_log_path: Optional path to write detailed profiling logs.
    
    Returns:
        Dictionary containing aggregated timing statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_clips": len(clips),
        "successful_clips": 0,
        "failed_clips": 0,
        "total_time_seconds": 0.0,
        "peak_memory_mb": 0.0,
        "clip_times": [],
        "clip_memory": [],
        "errors": []
    }
    
    start_total = time.time()
    peak_memory = 0.0
    
    for i, clip in enumerate(clips):
        clip_id = clip.get("id", f"clip_{i}")
        clip_path = clip.get("path")
        
        if not clip_path or not os.path.exists(clip_path):
            logger.warning(f"Clip {clip_id} not found at {clip_path}, skipping.")
            stats["failed_clips"] += 1
            stats["errors"].append({"clip_id": clip_id, "error": "File not found"})
            continue
        
        try:
            # Profile individual clip execution
            clip_start = time.time()
            clip_memory_before = get_memory_usage_mb()
            
            # Call the batch processing logic from preprocess
            # Note: batch_process_clips expects a list, we pass single item for profiling
            # We wrap it to get precise timing per clip
            result = batch_process_clips([clip], output_dir)
            
            clip_end = time.time()
            clip_memory_after = get_memory_usage_mb()
            clip_duration = clip_end - clip_start
            clip_peak = max(clip_memory_before, clip_memory_after)
            
            # Update stats
            stats["successful_clips"] += 1
            stats["total_time_seconds"] += clip_duration
            stats["clip_times"].append({
                "clip_id": clip_id,
                "duration_seconds": round(clip_duration, 4)
            })
            stats["clip_memory"].append({
                "clip_id": clip_id,
                "memory_mb": round(clip_peak, 2)
            })
            
            if clip_peak > peak_memory:
                peak_memory = clip_peak
            
            logger.info(f"Processed clip {i+1}/{len(clips)}: {clip_id} "
                        f"({clip_duration:.2f}s, {clip_peak:.2f}MB)")
            
        except Exception as e:
            logger.error(f"Failed to process clip {clip_id}: {str(e)}")
            stats["failed_clips"] += 1
            stats["errors"].append({
                "clip_id": clip_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    end_total = time.time()
    total_duration = end_total - start_total
    
    stats["total_time_seconds"] = round(total_duration, 4)
    stats["peak_memory_mb"] = round(peak_memory, 2)
    stats["avg_time_per_clip"] = round(
        stats["total_time_seconds"] / max(stats["successful_clips"], 1), 4
    )
    
    # Save profiling log if path provided
    if profiling_log_path:
        profiling_log_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(profiling_log_path, stats)
        logger.info(f"Profiling results saved to {profiling_log_path}")
    
    return stats


def main():
    """
    Main entry point for the batch processing pipeline.
    Processes a sample of clips and outputs timing statistics.
    """
    logger.info("Starting batch processing pipeline for US2 timing profiling")
    
    # Get directories
    project_root = get_project_root()
    data_root = get_data_root()
    raw_data_dir = get_raw_data_dir()
    
    # Define output paths
    processed_dir = data_root / "processed"
    state_dir = project_root / "state"
    profiling_log_path = state_dir / "batch_processing_stats.json"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Get sample clips (default 100 for timing test)
    try:
        clips = get_sample_clips(raw_data_dir, n=100)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to get sample clips: {e}")
        sys.exit(1)
    
    # Process batch
    try:
        stats = process_batch_clips(
            clips=clips,
            output_dir=processed_dir,
            profiling_log_path=profiling_log_path
        )
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Output summary
    logger.info("=" * 50)
    logger.info("Batch Processing Summary")
    logger.info("=" * 50)
    logger.info(f"Total clips: {stats['total_clips']}")
    logger.info(f"Successful: {stats['successful_clips']}")
    logger.info(f"Failed: {stats['failed_clips']}")
    logger.info(f"Total time: {stats['total_time_seconds']:.2f} seconds")
    logger.info(f"Avg time/clip: {stats['avg_time_per_clip']:.4f} seconds")
    logger.info(f"Peak memory: {stats['peak_memory_mb']:.2f} MB")
    logger.info("=" * 50)
    
    # Write final stats to state
    write_json(profiling_log_path, stats)
    
    logger.info("Batch processing completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
