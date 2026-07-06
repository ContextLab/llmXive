"""
Memory monitoring script to validate the 4GB peak memory target.

This script can be run independently to monitor memory usage during
pipeline execution and ensure compliance with the memory target.
"""
import subprocess
import sys
import time
import psutil
import os
from pathlib import Path
import logging

from config import get_config
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

MAX_MEMORY_GB = 4.0
CHECK_INTERVAL_SECONDS = 1.0

def get_process_memory_gb(pid: int) -> float:
    """Get current memory usage of a process in GB."""
    try:
        process = psutil.Process(pid)
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except psutil.NoSuchProcess:
        return 0.0

def run_pipeline_with_monitoring():
    """Run the main pipeline while monitoring memory usage."""
    logger.info(f"Starting pipeline with memory monitoring (limit: {MAX_MEMORY_GB}GB)")
    
    # Start the pipeline process
    pipeline_script = Path(__file__).parent / "main.py"
    process = subprocess.Popen(
        [sys.executable, str(pipeline_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    peak_memory_gb = 0.0
    start_time = time.time()
    
    while process.poll() is None:
        current_memory = get_process_memory_gb(process.pid)
        peak_memory_gb = max(peak_memory_gb, current_memory)
        
        elapsed = time.time() - start_time
        status = f"Elapsed: {elapsed:.1f}s, Current: {current_memory:.2f}GB, Peak: {peak_memory_gb:.2f}GB"
        
        if current_memory > MAX_MEMORY_GB * 0.9:
            logger.warning(f"HIGH MEMORY: {status}")
        elif current_memory > MAX_MEMORY_GB:
            logger.error(f"MEMORY EXCEEDED: {status}")
            process.terminate()
            return False
        else:
            logger.info(status)
        
        time.sleep(CHECK_INTERVAL_SECONDS)
    
    # Get final memory
    final_memory = get_process_memory_gb(process.pid)
    peak_memory_gb = max(peak_memory_gb, final_memory)
    
    # Wait for process to complete
    stdout, stderr = process.communicate()
    
    logger.info(f"Pipeline completed. Peak memory: {peak_memory_gb:.2f}GB")
    
    if peak_memory_gb > MAX_MEMORY_GB:
        logger.error(f"Memory limit exceeded: {peak_memory_gb:.2f}GB > {MAX_MEMORY_GB}GB")
        return False
    else:
        logger.info(f"Memory target met: {peak_memory_gb:.2f}GB <= {MAX_MEMORY_GB}GB")
        return True

def main():
    """Main entry point for memory monitoring."""
    config = get_config()
    setup_logging(config)
    
    success = run_pipeline_with_monitoring()
    
    if success:
        logger.info("Memory monitoring: PASSED")
        return 0
    else:
        logger.error("Memory monitoring: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
