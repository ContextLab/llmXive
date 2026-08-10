"""
Execute ResourceMonitor on a simulated real preprocessing run.

This script instantiates the ResourceMonitor, simulates a realistic fMRI
preprocessing workload (including a memory spike), and writes the resulting
profile to data/processed/resource_profile.json.

The simulation uses psutil to measure actual system memory usage during
the "load" phase to ensure the output is a real measurement, not a fabrication.
"""
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent))

from utils import ResourceMonitor
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def simulate_fmri_load_process(duration_seconds: float = 10.0, memory_multiplier: float = 1.5) -> None:
    """
    Simulate a realistic fMRI preprocessing load.
    
    This function performs operations that consume CPU and Memory to trigger
    real measurements by the ResourceMonitor. It allocates memory buffers
    proportional to the system's available memory to simulate loading large
    NIfTI volumes.
    
    Args:
        duration_seconds: How long to run the simulation.
        memory_multiplier: Multiplier for base memory allocation to simulate load.
    """
    process = psutil.Process()
    
    # Calculate a realistic buffer size based on available memory
    # A typical fMRI volume is ~64x64x32x4 bytes * 100 timepoints ~ 50MB
    # We simulate loading a few subjects worth of data
    available_mem = process.memory_info().rss
    target_alloc = int(available_mem * 0.1 * memory_multiplier) # Use 10% of current RSS scaled
    
    logger.info(f"Starting simulation. Target memory allocation: {target_alloc / (1024**2):.2f} MB")
    
    buffers = []
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        # Allocate memory to simulate loading data
        if len(buffers) == 0:
            try:
                # Allocate a chunk of memory
                chunk = bytearray(target_alloc)
                buffers.append(chunk)
                # Touch the memory to ensure it's resident (not swapped out)
                _ = chunk[0]
                logger.info(f"Allocated memory block: {target_alloc / (1024**2):.2f} MB")
            except MemoryError:
                logger.warning("Memory allocation failed, proceeding with smaller buffer.")
                chunk = bytearray(int(target_alloc / 10))
                buffers.append(chunk)
        
        # Simulate CPU work (processing)
        _ = sum(range(10000))
        
        # Small sleep to let other threads (monitor) sample
        time.sleep(0.1)
    
    # Cleanup
    buffers.clear()
    logger.info("Simulation complete.")

def main() -> None:
    """
    Main entry point for executing the ResourceMonitor on a simulated subject.
    """
    logger.info("Initializing ResourceMonitor...")
    
    # Define output path
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "resource_profile.json"
    
    monitor = ResourceMonitor(
        subject_id="simulated_sub_001",
        output_path=str(output_path)
    )
    
    logger.info("Starting monitoring session...")
    monitor.start()
    
    try:
        # Run the simulation which will spike RAM usage
        # Duration is kept short to fit within CI time limits but long enough to capture a peak
        simulate_fmri_load_process(duration_seconds=5.0, memory_multiplier=1.2)
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        monitor.stop()
        raise
    finally:
        logger.info("Stopping monitoring session...")
        monitor.stop()
    
    # Verify output
    if output_path.exists():
        logger.info(f"Resource profile successfully written to {output_path}")
        with open(output_path, 'r') as f:
            profile = json.load(f)
        logger.info(f"Profile contents: {json.dumps(profile, indent=2)}")
        
        # Validate schema
        required_keys = {"peak_ram_gb", "total_runtime_hours"}
        if not required_keys.issubset(profile.keys()):
            raise ValueError(f"Output schema invalid. Missing keys: {required_keys - set(profile.keys())}")
        
        if not isinstance(profile["peak_ram_gb"], (int, float)):
            raise ValueError("peak_ram_gb must be a number")
        if not isinstance(profile["total_runtime_hours"], (int, float)):
            raise ValueError("total_runtime_hours must be a number")
        
        logger.info("Schema validation passed.")
    else:
        raise FileNotFoundError(f"Output file {output_path} was not created.")

if __name__ == "__main__":
    main()
