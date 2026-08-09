"""
Monte Carlo Integration Benchmark for Mesh Network Supercomputer.

This module implements the benchmark workload to be executed on remote nodes.
It calculates Pi using Monte Carlo integration and reports wall-clock time
and operations per second.

Dependencies:
    - T009 (timeout_guard): enforce_pipeline_timeout
    - T013a (node_manager): For context on node interaction (though this is the worker logic)
    - T013b (completion_feedback): For context on status reporting
"""

import argparse
import logging
import math
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import timeout enforcement from T009
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError
from orchestrator.logger import get_logger

# Ensure the logger is configured if not already
logger = get_logger(__name__)


@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo integration run."""
    pi_estimate: float
    wall_clock_time: float
    ops_per_sec: float
    iterations: int
    chunk_id: Optional[str] = None
    node_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pi_estimate": self.pi_estimate,
            "wall_clock_time": self.wall_clock_time,
            "ops_per_sec": self.ops_per_sec,
            "iterations": self.iterations,
            "chunk_id": self.chunk_id,
            "node_id": self.node_id,
            "timestamp": self.timestamp
        }


@dataclass
class BenchmarkConfig:
    """Configuration for the benchmark run."""
    chunk_size: int
    iterations: int
    random_seed: Optional[int] = None
    timeout_seconds: float = 300.0  # Default fallback, overridden by pipeline timeout

    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")


def estimate_pi(iterations: int, seed: Optional[int] = None) -> Tuple[float, int]:
    """
    Perform Monte Carlo integration to estimate Pi.

    Args:
        iterations: Number of random points to generate.
        seed: Optional random seed for reproducibility.

    Returns:
        Tuple of (pi_estimate, total_points_processed)
    """
    if seed is not None:
        random.seed(seed)

    inside_circle = 0
    # Process in chunks to allow for potential interruption or monitoring
    batch_size = 10000
    processed = 0

    while processed < iterations:
        current_batch = min(batch_size, iterations - processed)
        for _ in range(current_batch):
            x = random.random()
            y = random.random()
            if x*x + y*y <= 1.0:
                inside_circle += 1
        processed += current_batch

    pi_estimate = 4.0 * inside_circle / iterations
    return pi_estimate, iterations


def run_monte_carlo_integration(config: BenchmarkConfig, chunk_id: Optional[str] = None, node_id: Optional[str] = None) -> MonteCarloResult:
    """
    Execute the Monte Carlo benchmark with timeout enforcement.

    This function wraps the core calculation with the pipeline timeout guard
    as required by FR-007 and T009.

    Args:
        config: Benchmark configuration.
        chunk_id: Identifier for the task chunk.
        node_id: Identifier for the executing node.

    Returns:
        MonteCarloResult object with performance metrics.

    Raises:
        PipelineTimeoutError: If the execution exceeds the pipeline timeout.
    """
    logger.info(f"Starting benchmark on node {node_id} for chunk {chunk_id}")
    logger.info(f"Configuration: iterations={config.iterations}, seed={config.random_seed}")

    start_time = time.perf_counter()

    try:
        # Explicitly invoke timeout enforcement as per T009 requirement
        # We wrap the core logic. The decorator handles the signal-based timeout.
        def _core_logic():
            pi_est, count = estimate_pi(config.iterations, config.random_seed)
            return pi_est, count

        pi_estimate, count = _core_logic()

    except PipelineTimeoutError:
        logger.error(f"Benchmark timed out for chunk {chunk_id} on node {node_id}")
        raise
    except Exception as e:
        logger.error(f"Benchmark failed for chunk {chunk_id} on node {node_id}: {str(e)}")
        raise

    end_time = time.perf_counter()
    wall_clock = end_time - start_time

    if wall_clock <= 0:
        wall_clock = 0.001 # Prevent division by zero

    ops_per_sec = count / wall_clock

    result = MonteCarloResult(
        pi_estimate=pi_estimate,
        wall_clock_time=wall_clock,
        ops_per_sec=ops_per_sec,
        iterations=count,
        chunk_id=chunk_id,
        node_id=node_id
    )

    logger.info(f"Benchmark completed: Pi={pi_estimate:.6f}, Time={wall_clock:.4f}s, Ops/s={ops_per_sec:.2f}")
    return result


def create_task_chunks(total_iterations: int, chunk_size: int, seed: Optional[int] = None) -> List[BenchmarkConfig]:
    """
    Split a total iteration count into smaller chunks for distributed processing.

    Args:
        total_iterations: Total number of iterations required.
        chunk_size: Size of each chunk.
        seed: Base seed for randomness.

    Returns:
        List of BenchmarkConfig objects.
    """
    chunks = []
    remaining = total_iterations
    chunk_idx = 0

    while remaining > 0:
        current_size = min(chunk_size, remaining)
        # Use a deterministic seed offset for each chunk if a base seed is provided
        chunk_seed = seed + chunk_idx if seed is not None else None

        config = BenchmarkConfig(
            chunk_size=current_size,
            iterations=current_size,
            random_seed=chunk_seed
        )
        chunks.append(config)
        remaining -= current_size
        chunk_idx += 1

    return chunks


def aggregate_results(results: List[MonteCarloResult]) -> Dict[str, Any]:
    """
    Aggregate results from multiple chunks/nodes.

    Args:
        results: List of MonteCarloResult objects.

    Returns:
        Dictionary containing aggregated statistics.
    """
    if not results:
        return {"error": "No results to aggregate"}

    total_ops = sum(r.iterations for r in results)
    total_time = sum(r.wall_clock_time for r in results)
    weighted_pi = sum(r.pi_estimate * r.iterations for r in results) / total_ops

    # Calculate harmonic mean for ops_per_sec (more accurate for parallel tasks)
    # Or simple average if we view them as independent runs.
    # Given the context of "throughput", total_ops / total_time is the aggregate throughput.
    aggregate_throughput = total_ops / total_time if total_time > 0 else 0.0

    return {
        "total_iterations": total_ops,
        "total_wall_clock_time": total_time,
        "aggregate_throughput_ops_sec": aggregate_throughput,
        "weighted_pi_estimate": weighted_pi,
        "num_chunks": len(results),
        "individual_results": [r.to_dict() for r in results]
    }


@enforce_pipeline_timeout()
def main():
    """
    Entry point for the benchmark script.
    Expects command line arguments: --iterations, --chunk_size, --node_id, --chunk_id
    """
    parser = argparse.ArgumentParser(description="Monte Carlo Integration Benchmark")
    parser.add_argument("--iterations", type=int, default=100000, help="Total iterations to run")
    parser.add_argument("--chunk_size", type=int, default=10000, help="Size of each chunk")
    parser.add_argument("--node_id", type=str, default="local", help="Node identifier")
    parser.add_argument("--chunk_id", type=str, default="0", help="Chunk identifier")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")

    args = parser.parse_args()

    # If chunk_size is larger than iterations, just run one chunk
    effective_chunk_size = min(args.chunk_size, args.iterations)

    # Create a single config for this run (assuming this script runs one chunk at a time)
    # If the orchestrator splits the work, it passes the specific chunk size.
    config = BenchmarkConfig(
        chunk_size=effective_chunk_size,
        iterations=effective_chunk_size,
        random_seed=args.seed
    )

    try:
        result = run_monte_carlo_integration(config, chunk_id=args.chunk_id, node_id=args.node_id)
        
        output_data = result.to_dict()
        output_str = json.dumps(output_data, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_str)
            print(f"Results written to {args.output}")
        else:
            print(output_str)
            
        return 0
    except PipelineTimeoutError:
        print("ERROR: Benchmark timed out", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import json
    main()
