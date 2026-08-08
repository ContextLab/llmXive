"""
Monte Carlo Integration Benchmark for Mesh Network Nodes.

This module implements a Monte Carlo integration workload (estimating Pi)
that can be executed on remote nodes to measure throughput and wall-clock time.
It explicitly enforces the pipeline timeout as required by T009.
"""

import logging
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field
import math

# Import timeout enforcement from T009
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError
from orchestrator.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo integration run."""
    iterations: int
    points_inside: int
    points_total: int
    pi_estimate: float
    wall_clock_time: float
    ops_per_sec: float
    node_id: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iterations": self.iterations,
            "points_inside": self.points_inside,
            "points_total": self.points_total,
            "pi_estimate": self.pi_estimate,
            "wall_clock_time": self.wall_clock_time,
            "ops_per_sec": self.ops_per_sec,
            "node_id": self.node_id,
            "timestamp": self.timestamp
        }


@dataclass
class BenchmarkConfig:
    """Configuration for the benchmark run."""
    chunk_size: int = 10000
    iterations: int = 100000
    timeout_seconds: float = 300.0  # Default to 5 minutes
    node_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_size": self.chunk_size,
            "iterations": self.iterations,
            "timeout_seconds": self.timeout_seconds,
            "node_id": self.node_id
        }


def estimate_pi(iterations: int, seed: Optional[int] = None) -> Tuple[int, int]:
    """
    Perform Monte Carlo estimation of Pi.

    Args:
        iterations: Number of random points to generate.
        seed: Optional random seed for reproducibility.

    Returns:
        Tuple of (points_inside, points_total)
    """
    if seed is not None:
        random.seed(seed)

    inside = 0
    for _ in range(iterations):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            inside += 1

    return inside, iterations


def run_monte_carlo_integration(config: BenchmarkConfig) -> MonteCarloResult:
    """
    Run the Monte Carlo benchmark with timeout enforcement.

    This function wraps the actual benchmark logic and enforces the
    pipeline timeout as required by T009.

    Args:
        config: Benchmark configuration.

    Returns:
        MonteCarloResult containing performance metrics.

    Raises:
        PipelineTimeoutError: If the benchmark exceeds the timeout limit.
    """
    logger.info(f"Starting Monte Carlo benchmark with {config.iterations} iterations "
                f"on node {config.node_id or 'local'}")

    start_time = time.time()
    
    try:
        # Run the actual computation
        points_inside, points_total = estimate_pi(
            iterations=config.iterations,
            seed=42  # Fixed seed for reproducibility across runs
        )
        
        end_time = time.time()
        wall_clock_time = end_time - start_time
        
        # Calculate metrics
        pi_estimate = 4.0 * points_inside / points_total if points_total > 0 else 0.0
        ops_per_sec = points_total / wall_clock_time if wall_clock_time > 0 else 0.0
        
        result = MonteCarloResult(
            iterations=points_total,
            points_inside=points_inside,
            points_total=points_total,
            pi_estimate=pi_estimate,
            wall_clock_time=wall_clock_time,
            ops_per_sec=ops_per_sec,
            node_id=config.node_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
        logger.info(f"Benchmark completed: Pi={pi_estimate:.6f}, "
                    f"Time={wall_clock_time:.3f}s, "
                    f"Throughput={ops_per_sec:.0f} ops/sec")
                    
        return result
        
    except PipelineTimeoutError:
        logger.error(f"Benchmark timed out after {config.timeout_seconds} seconds")
        raise


def create_task_chunks(total_iterations: int, chunk_size: int) -> List[int]:
    """
    Divide total iterations into manageable chunks.
    
    Args:
        total_iterations: Total number of iterations to distribute.
        chunk_size: Size of each chunk.
        
    Returns:
        List of chunk sizes that sum to total_iterations.
    """
    chunks = []
    remaining = total_iterations
    
    while remaining > 0:
        current_chunk = min(chunk_size, remaining)
        chunks.append(current_chunk)
        remaining -= current_chunk
        
    return chunks


def aggregate_results(results: List[MonteCarloResult]) -> Dict[str, Any]:
    """
    Aggregate results from multiple benchmark runs.
    
    Args:
        results: List of MonteCarloResult objects.
        
    Returns:
        Dictionary containing aggregated statistics.
    """
    if not results:
        return {"error": "No results to aggregate"}
        
    total_iterations = sum(r.iterations for r in results)
    total_inside = sum(r.points_inside for r in results)
    total_time = sum(r.wall_clock_time for r in results)
    
    avg_pi = 4.0 * total_inside / total_iterations if total_iterations > 0 else 0.0
    avg_throughput = total_iterations / total_time if total_time > 0 else 0.0
    
    return {
        "total_iterations": total_iterations,
        "total_inside": total_inside,
        "total_time": total_time,
        "combined_pi_estimate": avg_pi,
        "combined_throughput": avg_throughput,
        "run_count": len(results),
        "individual_results": [r.to_dict() for r in results]
    }


@enforce_pipeline_timeout()
def main():
    """
    Main entry point for the benchmark.
    
    This function is decorated with enforce_pipeline_timeout() to ensure
    the entire benchmark execution respects the pipeline timeout limit.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Monte Carlo Integration Benchmark")
    parser.add_argument("--chunk-size", type=int, default=10000,
                      help="Size of each iteration chunk")
    parser.add_argument("--iterations", type=int, default=100000,
                      help="Total number of iterations")
    parser.add_argument("--timeout", type=float, default=300.0,
                      help="Timeout in seconds")
    parser.add_argument("--node-id", type=str, default=None,
                      help="Node identifier for distributed runs")
    parser.add_argument("--output", type=str, default=None,
                      help="Output file path for results")
                      
    args = parser.parse_args()
    
    config = BenchmarkConfig(
        chunk_size=args.chunk_size,
        iterations=args.iterations,
        timeout_seconds=args.timeout,
        node_id=args.node_id
    )
    
    try:
        result = run_monte_carlo_integration(config)
        
        output_data = result.to_dict()
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Results written to {args.output}")
        else:
            print(json.dumps(output_data, indent=2))
            
        return result
        
    except PipelineTimeoutError as e:
        logger.error(f"Benchmark failed due to timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"Benchmark failed with unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()