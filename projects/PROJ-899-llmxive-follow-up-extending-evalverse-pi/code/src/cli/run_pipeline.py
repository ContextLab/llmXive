import os
import sys
import time
import json
import psutil
import traceback
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from src.data.preprocess import batch_process_clips
from src.utils import get_logger, ensure_directories, read_csv
from src.config import get_processed_data_dir, get_project_root

# Configure logging
logger = get_logger(__name__)

def get_memory_usage_mb(process: psutil.Process) -> float:
    """
    Get current memory usage of the process in MB.
    
    Args:
        process: psutil Process object
        
    Returns:
        Memory usage in megabytes
    """
    try:
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert bytes to MB
    except Exception as e:
        logger.warning(f"Failed to get memory usage: {e}")
        return 0.0

def get_sample_clips(input_file: Path, n_samples: int = 100) -> List[Dict[str, Any]]:
    """
    Load a sample of clips from the input scores file for profiling.
    
    Args:
        input_file: Path to data/processed/scores.csv
        n_samples: Number of clips to sample
        
    Returns:
        List of clip dictionaries
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    df = read_csv(str(input_file))
    
    # Sample rows
    if len(df) > n_samples:
        sample_df = df.sample(n=n_samples, random_state=42)
    else:
        sample_df = df
        
    # Convert to list of dicts
    clips = sample_df.to_dict(orient='records')
    logger.info(f"Loaded {len(clips)} clips for batch processing")
    return clips

def process_batch_clips(clips: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, Any]:
    """
    Process a batch of clips and aggregate timing/memory statistics.
    
    Args:
        clips: List of clip dictionaries
        batch_size: Number of clips to process in each batch
        
    Returns:
        Dictionary with aggregated statistics
    """
    if not clips:
        logger.warning("No clips to process")
        return {
            "total_clips": 0,
            "successful_clips": 0,
            "failed_clips": 0,
            "total_time_sec": 0.0,
            "mean_time_per_clip_sec": 0.0,
            "peak_memory_mb": 0.0
        }
    
    process = psutil.Process(os.getpid())
    initial_memory = get_memory_usage_mb(process)
    peak_memory = initial_memory
    
    total_time = 0.0
    successful = 0
    failed = 0
    
    start_time = time.time()
    
    # Process clips
    for i, clip in enumerate(clips):
        clip_start = time.time()
        clip_id = clip.get('clip_id', f'clip_{i}')
        
        try:
            # Extract features for this clip
            # Note: batch_process_clips expects a list, we process one at a time
            result = batch_process_clips([clip])
            
            clip_time = time.time() - clip_start
            total_time += clip_time
            successful += 1
            
            # Track peak memory
            current_memory = get_memory_usage_mb(process)
            if current_memory > peak_memory:
                peak_memory = current_memory
                
        except Exception as e:
            logger.error(f"Failed to process clip {clip_id}: {e}")
            failed += 1
            # Continue processing remaining clips
            continue
        
        # Log progress every batch_size clips
        if (i + 1) % batch_size == 0:
            logger.info(f"Processed {i + 1}/{len(clips)} clips")
    
    total_time = time.time() - start_time
    
    stats = {
        "total_clips": len(clips),
        "successful_clips": successful,
        "failed_clips": failed,
        "total_time_sec": round(total_time, 3),
        "mean_time_per_clip_sec": round(total_time / len(clips), 4) if len(clips) > 0 else 0.0,
        "peak_memory_mb": round(peak_memory, 2),
        "initial_memory_mb": round(initial_memory, 2)
    }
    
    logger.info(f"Batch processing complete: {stats}")
    return stats

def main():
    """
    Main entry point for batch processing pipeline.
    
    Reads from data/processed/scores.csv and writes batch stats to
    data/processed/batch_stats.json
    """
    logger.info("Starting batch processing pipeline for T022")
    
    # Get paths
    project_root = get_project_root()
    processed_dir = get_processed_data_dir()
    input_file = processed_dir / "scores.csv"
    output_file = processed_dir / "batch_stats.json"
    
    # Ensure directories exist
    ensure_directories([processed_dir])
    
    # Check input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T042 has run and created data/processed/scores.csv")
        sys.exit(1)
    
    # Load sample clips
    try:
        clips = get_sample_clips(input_file, n_samples=50)  # Process 50 clips for timing
    except Exception as e:
        logger.error(f"Failed to load clips: {e}")
        sys.exit(1)
    
    # Process batch
    try:
        stats = process_batch_clips(clips, batch_size=10)
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Write output
    try:
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Successfully wrote batch stats to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        sys.exit(1)
    
    logger.info("Batch processing pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
