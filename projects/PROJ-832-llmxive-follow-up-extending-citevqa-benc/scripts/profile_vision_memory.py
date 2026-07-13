"""
Memory profiling script for visual-only pipeline.

Runs the visual control experiment with memory profiling enabled
to verify that memory usage stays under 7GB.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
import psutil
import numpy as np
from memory_profiler import profile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_control import (
    load_phi3_vision_model,
    get_memory_usage_mb,
    MEMORY_LIMIT_GB,
    main as run_visual_experiment
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@profile
def profile_memory_usage():
    """Profile memory usage during model loading and inference."""
    logger.info("Starting memory profiling...")
    
    # Load model
    model, processor = load_phi3_vision_model()
    
    # Check memory after loading
    memory_after_load = get_memory_usage_mb()
    logger.info(f"Memory after model load: {memory_after_load:.2f} MB ({memory_after_load/1024:.2f} GB)")
    
    # Simulate a few inference steps
    logger.info("Simulating inference steps...")
    for i in range(3):
        current_memory = get_memory_usage_mb()
        logger.info(f"Step {i+1} memory: {current_memory:.2f} MB")
        time.sleep(1)
    
    return memory_after_load

def main():
    """Main profiling function."""
    logger.info("=== Visual Control Memory Profiling ===")
    
    initial_memory = get_memory_usage_mb()
    logger.info(f"Initial memory: {initial_memory:.2f} MB ({initial_memory/1024:.2f} GB)")
    
    try:
        peak_memory = profile_memory_usage()
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        peak_memory = get_memory_usage_mb()
    
    final_memory = get_memory_usage_mb()
    
    # Save profile results
    profile_results = {
        "initial_memory_mb": initial_memory,
        "peak_memory_mb": peak_memory,
        "final_memory_mb": final_memory,
        "peak_memory_gb": peak_memory / 1024,
        "limit_gb": MEMORY_LIMIT_GB,
        "status": "PASS" if peak_memory / 1024 <= MEMORY_LIMIT_GB else "FAIL",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path = Path("data/results/visual_memory_profile_detailed.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(profile_results, f, indent=2)
    
    logger.info(f"Profile results saved to {output_path}")
    logger.info(f"Status: {profile_results['status']}")
    logger.info(f"Peak memory: {profile_results['peak_memory_gb']:.2f} GB (limit: {MEMORY_LIMIT_GB} GB)")
    
    if profile_results['status'] == "FAIL":
        logger.warning("MEMORY LIMIT EXCEEDED - Research blocker flagged")
        print("\n⚠️  RESEARCH BLOCKER: Memory usage exceeds 7GB limit")
        print(f"   Peak memory: {profile_results['peak_memory_gb']:.2f} GB")
        print(f"   Limit: {MEMORY_LIMIT_GB} GB")
        print("\nAction required: Consider model optimization or hardware upgrade.")
    
    return profile_results['status']

if __name__ == "__main__":
    status = main()
    sys.exit(0 if status == "PASS" else 1)
