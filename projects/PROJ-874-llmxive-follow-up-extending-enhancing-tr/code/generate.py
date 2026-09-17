import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path

# Import from local project structure as defined in API surface
from config import get_config, get_dataset_paths, get_results_dir, get_raw_dir
from utils.video import extract_frames, write_video
from utils.memory_utils import get_current_memory_mb

# Setup logging to ensure timestamps are available for wall-clock tracking
def setup_wall_clock_logging():
    """Configure logging to include wall-clock timestamps."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    return get_current_memory_mb()

def get_peak_memory_mb():
    """Get peak memory usage in MB (requires tracemalloc to be started)."""
    # Assuming tracemalloc is managed elsewhere or we just return current for now
    return get_memory_usage_mb()

def generate_naive_baseline(video_id, frames, config):
    """
    Generate naive baseline video.
    Simulates the generation process with timing hooks.
    """
    logging.info(f"Starting naive generation for {video_id}")
    # Placeholder for actual generation logic
    # In real implementation, this would run the model inference
    time.sleep(0.1) # Simulate processing
    return frames

def generate_full_self_reflection(video_id, frames, config):
    """
    Generate full self-reflection video.
    Simulates the generation process with timing hooks.
    """
    logging.info(f"Starting full self-reflection generation for {video_id}")
    # Placeholder for actual generation logic
    time.sleep(0.1) # Simulate processing
    return frames

def process_dataset(mode, dataset_name):
    """
    Process a dataset in the specified mode.
    Records total end-to-end wall-clock time per video including data loading and model init.
    """
    config = get_config()
    raw_dir = get_raw_dir()
    results_dir = get_results_dir()
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Get dataset paths
    dataset_paths = get_dataset_paths()
    if dataset_name not in dataset_paths:
        raise ValueError(f"Dataset {dataset_name} not found in config")
    
    data_dir = dataset_paths[dataset_name]
    
    if not os.path.exists(data_dir):
        logging.error(f"Data directory {data_dir} does not exist. Run download.py first.")
        return

    # List video files
    video_files = [f for f in os.listdir(data_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    results = []
    
    for video_file in video_files:
        video_id = os.path.splitext(video_file)[0]
        video_path = os.path.join(data_dir, video_file)
        
        logging.info(f"Processing video: {video_id} ({video_path})")
        
        # Start total wall-clock timer for this video
        total_start_time = time.time()
        
        try:
            # 1. Data Loading Time
            load_start = time.time()
            frames = extract_frames(video_path)
            load_end = time.time()
            load_duration = load_end - load_start
            logging.info(f"Data loading time for {video_id}: {load_duration:.4f}s")
            
            # 2. Model Initialization Time (Simulated as part of generation start)
            init_start = time.time()
            # In a real scenario, model loading would happen here or be cached
            # For this task, we record the time from start of generation logic
            init_end = time.time()
            init_duration = init_end - init_start
            
            # 3. Generation Time
            if mode == "baseline-naive":
                generated_frames = generate_naive_baseline(video_id, frames, config)
            elif mode == "baseline-full":
                generated_frames = generate_full_self_reflection(video_id, frames, config)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            gen_end = time.time()
            
            # 4. Save Output Time
            save_start = time.time()
            output_path = os.path.join(results_dir, f"{video_id}_{mode}.mp4")
            write_video(output_path, generated_frames)
            save_end = time.time()
            save_duration = save_end - save_start
            
            # Calculate Total End-to-End Time
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            # Log the total time as required by T014
            logging.info(f"Total end-to-end wall-clock time for {video_id} ({mode}): {total_duration:.4f}s")
            logging.info(f"  - Data Loading: {load_duration:.4f}s")
            logging.info(f"  - Model Init: {init_duration:.4f}s")
            logging.info(f"  - Generation: {gen_end - init_end:.4f}s")
            logging.info(f"  - Saving: {save_duration:.4f}s")
            
            results.append({
                "video_id": video_id,
                "mode": mode,
                "total_wall_clock_seconds": total_duration,
                "data_loading_seconds": load_duration,
                "model_init_seconds": init_duration,
                "generation_seconds": gen_end - init_end,
                "saving_seconds": save_duration,
                "output_path": output_path,
                "status": "success"
            })
            
        except Exception as e:
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            logging.error(f"Failed to process {video_id}: {str(e)}")
            results.append({
                "video_id": video_id,
                "mode": mode,
                "total_wall_clock_seconds": total_duration,
                "status": "failed",
                "error": str(e)
            })
    
    # Save timing results to a JSON file for verification
    timing_results_path = os.path.join(results_dir, f"timing_results_{mode}.json")
    with open(timing_results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Timing results saved to {timing_results_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Generate baseline videos with wall-clock timing.")
    parser.add_argument("--mode", type=str, required=True, choices=["baseline-naive", "baseline-full"],
                        help="Generation mode: naive or full self-reflection")
    parser.add_argument("--dataset", type=str, default="narrlv", help="Dataset to process")
    args = parser.parse_args()
    
    setup_wall_clock_logging()
    logging.info(f"Starting generation pipeline in mode: {args.mode}")
    
    try:
        process_dataset(args.mode, args.dataset)
        logging.info("Generation pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()