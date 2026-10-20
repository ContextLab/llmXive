"""
Monte‑Carlo benchmark utilities.

This file already existed and is used by the CLI.  No changes are needed
for T016, but it is included here to ensure the import path remains
consistent after the task modifications.
"""

import math
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError

@dataclass
class BenchmarkConfig:
    chunk_size: int
    iterations: int
    random_seed: Optional[int] = None

    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")

@dataclass
class MonteCarloResult:
    pi_estimate: float
    wall_clock_time: float
    ops_per_sec: float
    iterations: int
    chunk_id: str
    node_id: str

    def to_dict(self):
        return {
            "pi_estimate": self.pi_estimate,
            "wall_clock_time": self.wall_clock_time,
            "ops_per_sec": self.ops_per_sec,
            "iterations": self.iterations,
            "chunk_id": self.chunk_id,
            "node_id": self.node_id,
            "timestamp": time.time(),
        }

def estimate_pi(iterations: int, seed: Optional[int] = None) -> Tuple[float, int]:
    """
    Estimate π using the Monte‑Carlo method.

    Returns a tuple ``(pi_estimate, points_used)``.
    """
    if seed is not None:
        random.seed(seed)
    inside = 0
    for _ in range(iterations):
        x, y = random.random(), random.random()
        if x * x + y * y <= 1.0:
            inside += 1
    pi_est = 4.0 * inside / iterations
    return pi_est, iterations

@enforce_pipeline_timeout(300)  # default hard timeout for a single benchmark
def run_monte_carlo_integration(config: BenchmarkConfig, chunk_id: Optional[str] = None,
                                node_id: Optional[str] = None) -> MonteCarloResult:
    """
    Execute the Monte‑Carlo benchmark with timeout enforcement.

    ``config`` supplies the number of iterations and optional random seed.
    """
    start = time.perf_counter()
    pi, _ = estimate_pi(config.iterations, seed=config.random_seed)
    end = time.perf_counter()
    duration = end - start
    ops_per_sec = config.iterations / duration if duration > 0 else 0.0

    return MonteCarloResult(
        pi_estimate=pi,
        wall_clock_time=duration,
        ops_per_sec=ops_per_sec,
        iterations=config.iterations,
        chunk_id=chunk_id or "chunk_unknown",
        node_id=node_id or "node_unknown"
    )

def create_task_chunks(total_iterations: int, chunk_size: int,
                       seed: Optional[int] = None) -> List[BenchmarkConfig]:
    """
    Split ``total_iterations`` into chunks of size ``chunk_size``.
    Returns a list of ``BenchmarkConfig`` objects.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    chunks = []
    remaining = total_iterations
    while remaining > 0:
        cur = min(chunk_size, remaining)
        cfg = BenchmarkConfig(chunk_size=chunk_size, iterations=cur, random_seed=seed)
        chunks.append(cfg)
        remaining -= cur
    return chunks

def aggregate_results(results: List[MonteCarloResult]) -> dict:
    """
    Aggregate a list of ``MonteCarloResult`` objects.
    Returns a dictionary with total iterations, total wall‑clock time,
    and aggregate throughput (ops per second).
    """
    if not results:
        return {"error": "No results to aggregate"}

    total_iterations = sum(r.iterations for r in results)
    total_wall_clock = sum(r.wall_clock_time for r in results)
    aggregate_throughput = total_iterations / total_wall_clock if total_wall_clock > 0 else 0.0

    return {
        "total_iterations": total_iterations,
        "total_wall_clock_time": total_wall_clock,
        "aggregate_throughput_ops_sec": aggregate_throughput,
    }

def main():
    """
    Simple CLI entry point for manual testing.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    cfg = BenchmarkConfig(chunk_size=args.chunk_size,
                          iterations=args.iterations,
                          random_seed=args.seed)
    result = run_monte_carlo_integration(cfg, chunk_id="demo", node_id="local")
    print("Result:", result.to_dict())

if __name__ == "__main__":
    main()