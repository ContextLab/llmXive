"""
CLI Entry point for running simulations with strict limits.
"""
import argparse
import json
import sys
import os
import time
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.sim.eco_director import EcoDirector
from src.sim.neural_baseline import NeuralBaseline
from src.data_models import SimulationRun

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run llmXive simulation")
    parser.add_argument("--steps", type=int, default=100, help="Number of steps")
    parser.add_argument("--memory-limit", type=int, default=2000, help="Memory limit in MB")
    parser.add_argument("--time-limit", type=int, default=3600, help="Time limit in seconds")
    parser.add_argument("--output", type=str, default="data/output.json", help="Output file path")
    return parser.parse_args()

def main():
    args = parse_args()
    
    logger.info(f"Starting simulation with {args.steps} steps")
    
    # Initialize Eco-Director
    director = EcoDirector(
        params={"type": "eco"},
        memory_limit_mb=args.memory_limit,
        time_limit_sec=args.time_limit
    )
    
    result: SimulationRun = director.run(steps=args.steps)
    
    # Log status
    status_log = {
        "status": result.status,
        "duration": result.duration,
        "steps_completed": len(result.metrics),
        "error": result.error
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w") as f:
        json.dump(status_log, f, indent=2)
    
    logger.info(f"Simulation finished. Status: {result.status}")
    print(json.dumps(status_log, indent=2))

if __name__ == "__main__":
    main()
