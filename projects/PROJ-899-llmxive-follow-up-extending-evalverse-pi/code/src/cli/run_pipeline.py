"""
Batch processing logic for User Story 2 (Compute Feasibility Profiling).

Implements logic to process N clips and aggregate timing stats.
This script is designed to run the full feature extraction pipeline on a batch
of clips, measuring CPU time and memory usage for feasibility analysis.

Prerequisites: T012 (Optical Flow), T013 (Audio Features)
"""
import os
import sys
import time
import json
import psutil
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_processed_data_dir, get_raw_data_dir, get_data_root
from src.data.preprocess import batch_process_clips, extract_all_features
from src.utils import setup_logging, get_logger, write_json, read_json
from src.data.models import VideoClip, FeatureVector

# Configure logging
logger = setup_logging()

def get_memory_usage_mb() -> float:
    """Get current memory usage of the current process in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def process_batch_clips(
    clip_ids: List[str],
    raw_data_dir: Path,
    output_dir: Path,
    max_memory_gb: float = 7.0
) -> Dict[str, Any]:
    """
    Process a batch of video clips and aggregate timing stats.
    
    Args:
        clip_ids: List of clip identifiers to process.
        raw_data_dir: Path to the raw data directory.
        output_dir: Path to store processed features and logs.
        max_memory_gb: Maximum allowed memory usage in GB (for safety check).
    
    Returns:
        Dictionary containing aggregated timing and memory statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "total_clips": len(clip_ids),
        "processed_clips": 0,
        "failed_clips": 0,
        "total_time_seconds": 0.0,
        "avg_time_per_clip_seconds": 0.0,
        "peak_memory_mb": 0.0,
        "clip_details": []
    }
    
    initial_memory = get_memory_usage_mb()
    peak_memory = initial_memory
    
    logger.info(f"Starting batch processing of {len(clip_ids)} clips...")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    start_time = time.time()
    
    for i, clip_id in enumerate(clip_ids):
        clip_start = time.time()
        clip_memory_start = get_memory_usage_mb()
        
        try:
            # Check memory before processing
            current_memory = get_memory_usage_mb()
            if current_memory > (max_memory_gb * 1024):
                raise MemoryError(
                    f"Memory usage {current_memory:.2f}MB exceeds limit {max_memory_gb * 1024:.2f}MB"
                )
            
            logger.info(f"Processing clip {i+1}/{len(clip_ids)}: {clip_id}")
            
            # Construct file path
            video_path = raw_data_dir / f"{clip_id}.mp4"
            if not video_path.exists():
                # Try alternative extensions
                for ext in ['.avi', '.mov', '.mkv']:
                    alt_path = raw_data_dir / f"{clip_id}{ext}"
                    if alt_path.exists():
                        video_path = alt_path
                        break
            
            if not video_path.exists():
                logger.warning(f"Video file not found for clip {clip_id}, skipping.")
                results["failed_clips"] += 1
                results["clip_details"].append({
                    "clip_id": clip_id,
                    "status": "failed",
                    "error": "File not found",
                    "time_seconds": 0.0,
                    "memory_mb": 0.0
                })
                continue
            
            # Extract features
            features = extract_all_features(str(video_path), clip_id)
            
            # Save features if successful
            if features is not None:
                # Create processed clip directory
                clip_output_dir = output_dir / clip_id
                clip_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save features to JSON
                features_data = {
                    "clip_id": clip_id,
                    "features": {
                        "optical_flow_magnitude": features.get("optical_flow_magnitude", []),
                        "optical_flow_variance": features.get("optical_flow_variance", []),
                        "hog_density": features.get("hog_density", []),
                        "spectral_centroid": features.get("spectral_centroid", []),
                        "zero_crossing_rate": features.get("zero_crossing_rate", [])
                    }
                }
                
                features_path = clip_output_dir / "features.json"
                with open(features_path, 'w') as f:
                    json.dump(features_data, f, indent=2)
                
                results["processed_clips"] += 1
                
            clip_end = time.time()
            clip_time = clip_end - clip_start
            clip_memory = get_memory_usage_mb()
            
            if clip_memory > peak_memory:
                peak_memory = clip_memory
            
            results["total_time_seconds"] += clip_time
            results["clip_details"].append({
                "clip_id": clip_id,
                "status": "success",
                "time_seconds": round(clip_time, 4),
                "memory_mb": round(clip_memory, 2)
            })
            
        except Exception as e:
            clip_end = time.time()
            clip_time = clip_end - clip_start
            
            logger.error(f"Error processing clip {clip_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            results["failed_clips"] += 1
            results["clip_details"].append({
                "clip_id": clip_id,
                "status": "failed",
                "error": str(e),
                "time_seconds": round(clip_time, 4),
                "memory_mb": round(get_memory_usage_mb(), 2)
            })
    
    total_time = time.time() - start_time
    
    # Calculate aggregates
    if results["processed_clips"] > 0:
        results["avg_time_per_clip_seconds"] = results["total_time_seconds"] / results["processed_clips"]
    
    results["peak_memory_mb"] = round(peak_memory, 2)
    results["total_time_seconds"] = round(total_time, 4)
    
    # Save detailed results
    results_path = output_dir / "batch_processing_results.json"
    write_json(str(results_path), results)
    
    logger.info(f"Batch processing completed. Processed: {results['processed_clips']}, Failed: {results['failed_clips']}")
    logger.info(f"Total time: {results['total_time_seconds']:.2f}s, Avg per clip: {results['avg_time_per_clip_seconds']:.4f}s")
    logger.info(f"Peak memory: {results['peak_memory_mb']:.2f}MB")
    
    return results

def get_sample_clips(raw_data_dir: Path, n: int = 100) -> List[str]:
    """
    Get a sample of N clip IDs from the raw data directory.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        n: Number of clips to sample.
    
    Returns:
        List of clip IDs.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    video_files = list(raw_data_dir.glob("*.mp4")) + list(raw_data_dir.glob("*.avi")) + \
                 list(raw_data_dir.glob("*.mov")) + list(raw_data_dir.glob("*.mkv"))
    
    if len(video_files) == 0:
        raise ValueError(f"No video files found in {raw_data_dir}")
    
    # Limit to n clips
    if len(video_files) > n:
        # For deterministic sampling, sort and take first n
        video_files = sorted(video_files)[:n]
    
    clip_ids = [f.stem for f in video_files]
    logger.info(f"Selected {len(clip_ids)} clips for batch processing")
    return clip_ids

def main(args: Optional[List[str]] = None):
    """
    Main entry point for batch processing pipeline.
    
    Usage:
        python -m src.cli.run_pipeline [--n-clips N] [--output-dir DIR]
    
    Args:
        args: Command line arguments (optional, defaults to sys.argv[1:])
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch processing for feasibility profiling")
    parser.add_argument("--n-clips", type=int, default=100, help="Number of clips to process (default: 100)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results")
    parser.add_argument("--raw-dir", type=str, default=None, help="Override raw data directory")
    
    parsed_args = parser.parse_args(args)
    
    # Get directories
    raw_data_dir = Path(parsed_args.raw_dir) if parsed_args.raw_dir else get_raw_data_dir()
    output_dir = Path(parsed_args.output_dir) if parsed_args.output_dir else get_processed_data_dir() / "batch_profiles"
    
    logger.info(f"Batch Processing Pipeline - User Story 2")
    logger.info(f"Processing {parsed_args.n_clips} clips")
    
    try:
        # Get sample clips
        clip_ids = get_sample_clips(raw_data_dir, n=parsed_args.n_clips)
        
        # Process batch
        results = process_batch_clips(
            clip_ids=clip_ids,
            raw_data_dir=raw_data_dir,
            output_dir=output_dir,
            max_memory_gb=7.0
        )
        
        # Print summary
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Total clips requested: {results['total_clips']}")
        print(f"Successfully processed: {results['processed_clips']}")
        print(f"Failed: {results['failed_clips']}")
        print(f"Total time: {results['total_time_seconds']:.2f} seconds")
        print(f"Average time per clip: {results['avg_time_per_clip_seconds']:.4f} seconds")
        print(f"Peak memory usage: {results['peak_memory_mb']:.2f} MB")
        print("="*60)
        
        # Exit with error if any clips failed
        if results["failed_clips"] > 0:
            logger.warning(f"{results['failed_clips']} clips failed during processing")
            # Note: We don't exit with code 1 here as partial success is acceptable
            # for profiling purposes, but the failures are logged.
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
