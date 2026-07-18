import cProfile
import pstats
import io
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
import time

from utils.logger import get_logger
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)

PROFILE_OUTPUT_PATH = "data/derived/runtime_profile.json"
MAX_RUNTIME_SECONDS = 900  # 15 minutes

def profile_pipeline_entrypoint(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Profiles a function execution, capturing timing and statistical data.
    Returns a dictionary with total runtime and top 10 slowest calls.
    """
    logger.info(f"Starting profiler for {func.__name__}")
    
    start_time = time.time()
    profiler = cProfile.Profile()
    
    try:
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
    except Exception as e:
        profiler.disable()
        logger.error(f"Pipeline execution failed during profiling: {e}")
        raise e
    
    end_time = time.time()
    total_runtime = end_time - start_time
    
    # Capture stats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions by cumulative time
    
    # Parse top stats for JSON output
    stats_lines = stream.getvalue().split('\n')
    top_functions = []
    for line in stats_lines[3:13]:  # Skip header lines
        if line.strip() and '|' in line:
            top_functions.append(line.strip())
    
    profile_data = {
        "function_name": func.__name__,
        "total_runtime_seconds": round(total_runtime, 3),
        "max_allowed_seconds": MAX_RUNTIME_SECONDS,
        "status": "passed" if total_runtime < MAX_RUNTIME_SECONDS else "failed",
        "top_10_slowest_calls": top_functions
    }
    
    logger.info(f"Pipeline completed in {total_runtime:.3f}s. Status: {profile_data['status']}")
    return profile_data

def save_profile_results(profile_data: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Saves profile results to a JSON file."""
    if output_path is None:
        output_path = PROFILE_OUTPUT_PATH
    
    project_root = get_project_root()
    full_path = project_root / output_path
    ensure_directory(full_path.parent)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2)
    
    logger.info(f"Profile results saved to {full_path}")

def run_profiler(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for running the profiler on the pipeline.
    """
    from main import run_pipeline
    
    profile_data = profile_pipeline_entrypoint(run_pipeline)
    save_profile_results(profile_data, output_path)
    
    if profile_data['status'] == 'failed':
        logger.error(f"Runtime exceeded limit of {MAX_RUNTIME_SECONDS}s. Optimization required.")
        sys.exit(1)
    
    return profile_data

def main():
    """CLI entry point for profiling."""
    import argparse
    parser = argparse.ArgumentParser(description="Profile the meta-analysis pipeline runtime.")
    parser.add_argument('--output', type=str, default=PROFILE_OUTPUT_PATH, 
                        help='Path to save profile results JSON')
    args = parser.parse_args()
    
    try:
        run_profiler(args.output)
        print("Profiling completed successfully.")
    except Exception as e:
        print(f"Profiling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
