"""
Demo script to verify logging infrastructure for T010.

This script demonstrates the logging of coherence_score, diversity_score,
and step_latency at regular intervals during a simulated run.
"""
import sys
import time
import random
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging_config import create_metrics_logger

def run_demo_simulation(num_steps: int = 10, interval: int = 2):
    """
    Run a demo simulation that logs metrics at specified intervals.
    
    Args:
        num_steps: Number of simulation steps to run
        interval: Log metrics every N steps
    """
    # Create logger with output to data/logs/demo_metrics.json
    logger = create_metrics_logger(log_file="data/logs/demo_metrics.json")
    
    logger.logger.info("Starting demo simulation with logging infrastructure verification")
    
    for step in range(1, num_steps + 1):
        # Simulate step execution
        start_time = time.time()
        
        # Simulate some computation
        time.sleep(0.01)  # Small delay to simulate work
        
        # Calculate metrics (simulated values for demo)
        coherence_score = 0.7 + random.uniform(-0.1, 0.1)
        diversity_score = 0.6 + random.uniform(-0.1, 0.1)
        step_latency = time.time() - start_time
        
        # Log metrics at specified intervals
        if step % interval == 0 or step == num_steps:
            logger.log_step_metrics(
                step=step,
                coherence_score=coherence_score,
                diversity_score=diversity_score,
                step_latency=step_latency,
                additional_metrics={
                    "demo_mode": True,
                    "iteration": step
                }
            )
            logger.flush_buffer()
    
    logger.logger.info("Demo simulation completed successfully")
    logger.logger.info(f"Total metrics logged: {num_steps // interval + 1}")
    logger.logger.info("Check data/logs/demo_metrics.json for output")

if __name__ == "__main__":
    run_demo_simulation(num_steps=10, interval=2)
