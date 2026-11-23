"""
Monte Carlo Integration Benchmark Worker.

This script performs a Monte Carlo estimation of Pi (π) to serve as a
compute-bound benchmark for the mesh network supercomputer.

It is designed to be runnable via CLI and accepts parameters for:
- Number of samples (granularity)
- Output file path for results
- Run ID for correlation with orchestration logs

The worker calculates the ratio of points falling inside a unit circle
quadrant to the total points in a unit square, scaling by 4 to estimate π.
"""
import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Project imports based on API surface
from orchestrator.models import TaskStatus, ExecutionStatus
from orchestrator.logger import get_logger, init_logger
from orchestrator.config import load_config

# Ensure the parent directory is in the path for imports if run as script
# This handles the case where the script is run directly without package installation
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = get_logger(__name__)

def estimate_pi(num_samples: int, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Monte Carlo integration to estimate Pi.
    
    Args:
        num_samples: Number of random points to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing the estimate, number of samples, and error metrics.
    """
    if seed is not None:
        random.seed(seed)
    
    start_time = time.perf_counter()
    inside_circle = 0
    
    # Perform the integration
    for _ in range(num_samples):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            inside_circle += 1
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    pi_estimate = 4.0 * inside_circle / num_samples
    actual_pi = math.pi
    error = abs(pi_estimate - actual_pi)
    relative_error = error / actual_pi
    
    return {
        "pi_estimate": pi_estimate,
        "num_samples": num_samples,
        "inside_circle": inside_circle,
        "elapsed_seconds": elapsed,
        "absolute_error": error,
        "relative_error": relative_error,
        "status": "success"
    }

def run_benchmark(
    num_samples: int,
    output_path: str,
    run_id: str,
    node_id: str = "local",
    seed: Optional[int] = None
) -> bool:
    """
    Execute the benchmark and write results to disk.
    
    Args:
        num_samples: Number of Monte Carlo samples.
        output_path: Path to the output JSON file.
        run_id: Unique identifier for this execution run.
        node_id: Identifier of the node performing the work.
        seed: Random seed.
        
    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Starting Monte Carlo benchmark: {num_samples} samples on node {node_id}")
    
    try:
        result = estimate_pi(num_samples, seed=seed)
        
        # Construct the final result payload matching ExecutionRun expectations
        payload = {
            "run_id": run_id,
            "node_id": node_id,
            "task_type": "monte_carlo_pi",
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": {
                "num_samples": num_samples,
                "seed": seed
            },
            "metrics": result,
            "status": TaskStatus.COMPLETED.value
        }
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results to disk
        with open(output_file, 'w') as f:
            json.dump(payload, f, indent=2)
        
        logger.info(f"Benchmark completed successfully. Output written to {output_path}")
        logger.info(f"Estimate: {result['pi_estimate']:.6f} (Error: {result['relative_error']:.2e})")
        
        return True
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        # Write a failure record
        failure_payload = {
            "run_id": run_id,
            "node_id": node_id,
            "task_type": "monte_carlo_pi",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "status": TaskStatus.FAILED.value
        }
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(failure_payload, f, indent=2)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Monte Carlo Integration Benchmark Worker for Mesh Network"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=1000000,
        help="Number of Monte Carlo samples to generate (default: 1000000)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/raw/monte_carlo_results.json",
        help="Path to output results JSON file"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Unique run ID for correlation (defaults to timestamp)"
    )
    parser.add_argument(
        "--node-id",
        type=str,
        default="local_worker",
        help="Identifier of the node executing this task"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Initialize logger if not already done
    # In a real orchestration context, this might be passed in
    if not logger.handlers:
        init_logger()
    
    run_id = args.run_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    
    success = run_benchmark(
        num_samples=args.samples,
        output_path=args.output,
        run_id=run_id,
        node_id=args.node_id,
        seed=args.seed
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
