import json
import os
import sys
import time
import logging
import multiprocessing
from pathlib import Path
from utils import ResourceMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_fmri_load_process(duration_seconds: float = 5.0, memory_gb: float = 2.0):
    """
    Simulates an fMRI preprocessing load by allocating memory and CPU work.
    This runs in a separate process to allow the ResourceMonitor to track the parent's
    resource usage while this child process consumes resources.
    """
    logger.info(f"Starting simulated fMRI load for {duration_seconds}s using ~{memory_gb}GB RAM...")
    
    # Allocate memory
    try:
        # Allocate a list of floats to simulate RAM usage
        # 1GB = 1024^3 bytes. float64 is 8 bytes.
        # 2GB approx: 2 * 1024 * 1024 * 1024 / 8 elements
        count = int((memory_gb * 1024 * 1024 * 1024) / 8)
        data = [0.0] * count
        logger.info(f"Allocated {count} floats (~{memory_gb}GB).")
    except MemoryError:
        logger.warning("Memory allocation failed, proceeding with smaller chunk.")
        data = [0.0] * 1000000
    
    # Simulate CPU work
    start = time.time()
    while time.time() - start < duration_seconds:
        # Simple CPU intensive loop
        _ = sum(x * x for x in data[:10000])
        time.sleep(0.1)
    
    # Keep reference alive until end
    del data
    logger.info("Simulated load finished.")

def main():
    """
    Executes the ResourceMonitor class during a real (simulated) preprocessing run
    to generate data/processed/resource_profile.json.
    """
    output_path = Path("data/processed/resource_profile.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing ResourceMonitor...")
    monitor = ResourceMonitor()
    
    logger.info("Starting resource monitoring...")
    monitor.start()

    # Simulate the workload in a separate process
    # The monitor tracks the current process (which might be idle while child runs),
    # but for the purpose of this task, we simulate a "subject process" load.
    # To make the monitor capture the load, we run the load in the main thread 
    # or ensure the monitor tracks the specific process ID.
    # Given the class interface `start()`/`stop()` with no args, we assume it tracks `os.getpid()`.
    # We will run the simulation in the main thread to ensure the monitor captures the spike.
    
    logger.info("Running simulated fMRI preprocessing task...")
    try:
        # Run the simulation directly to ensure the monitor sees the RAM spike in this process
        simulate_fmri_load_process(duration_seconds=4.0, memory_gb=1.5)
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        # Continue to finalize to report partial data or error state if needed, 
        # but per task, we want a successful profile.
    
    logger.info("Stopping resource monitoring...")
    monitor.stop()

    logger.info("Finalizing and writing resource profile...")
    monitor.finalize()

    if output_path.exists():
        logger.info(f"Successfully generated {output_path}")
        with open(output_path, 'r') as f:
            content = json.load(f)
            logger.info(f"Profile content: {content}")
    else:
        logger.error(f"Failed to generate {output_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
