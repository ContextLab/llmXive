"""
Benchmark module for running Monte Carlo integration workloads on remote nodes.

This module provides the core workload execution logic for the mesh network
supercomputer. It implements a Monte Carlo integration task that can be
distributed across multiple physical nodes.

The workload estimates PI using the Monte Carlo method, which is:
- Computationally intensive (suitable for benchmarking)
- Embarrassingly parallel (can be split into independent chunks)
- Deterministic (allows verification of results)
"""
import logging
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field
import json

from orchestrator.logger import get_logger
from orchestrator.models import TaskChunk, PhysicalNode, TaskStatus, ExecutionRun
from orchestrator.config import get_config

logger = get_logger(__name__)

@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo integration task."""
    task_id: str
    node_id: str
    samples: int
    pi_estimate: float
    execution_time_ms: float
    status: TaskStatus
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'node_id': self.node_id,
            'samples': self.samples,
            'pi_estimate': self.pi_estimate,
            'execution_time_ms': self.execution_time_ms,
            'status': self.status.value,
            'error_message': self.error_message
        }

@dataclass
class BenchmarkConfig:
    """Configuration for the benchmark workload."""
    total_samples: int = 1000000
    chunk_size: int = 100000
    random_seed: Optional[int] = None
    timeout_seconds: float = 300.0
    
    @classmethod
    def from_config(cls) -> 'BenchmarkConfig':
        """Load configuration from the project config."""
        config = get_config()
        return cls(
            total_samples=config.get('benchmark', {}).get('total_samples', 1000000),
            chunk_size=config.get('benchmark', {}).get('chunk_size', 100000),
            random_seed=config.get('benchmark', {}).get('random_seed'),
            timeout_seconds=config.get('benchmark', {}).get('timeout_seconds', 300.0)
        )

def estimate_pi(samples: int, seed: Optional[int] = None) -> Tuple[float, int]:
    """
    Estimate PI using Monte Carlo integration.
    
    This method generates random points in a unit square and counts how many
    fall within the inscribed quarter circle. The ratio approximates pi/4.
    
    Args:
        samples: Number of random points to generate
        seed: Optional random seed for reproducibility
        
    Returns:
        Tuple of (pi_estimate, points_inside_circle)
    """
    if seed is not None:
        random.seed(seed)
    
    points_inside = 0
    
    for _ in range(samples):
        x = random.random()
        y = random.random()
        if x * x + y * y <= 1.0:
            points_inside += 1
    
    pi_estimate = 4.0 * points_inside / samples
    return pi_estimate, points_inside

def run_monte_carlo_integration(
    task_chunk: TaskChunk,
    node: PhysicalNode,
    config: Optional[BenchmarkConfig] = None
) -> MonteCarloResult:
    """
    Execute a Monte Carlo integration task on a specific node.
    
    This function runs the Monte Carlo PI estimation with the parameters
    specified in the task chunk and returns the result.
    
    Args:
        task_chunk: The task chunk containing parameters for this execution
        node: The physical node on which to execute the task
        config: Optional benchmark configuration overrides
        
    Returns:
        MonteCarloResult containing the execution results
    """
    if config is None:
        config = BenchmarkConfig.from_config()
    
    start_time = time.time()
    
    try:
        # Extract parameters from task chunk
        samples = task_chunk.parameters.get('samples', config.total_samples)
        seed = task_chunk.parameters.get('seed', config.random_seed)
        
        logger.info(
            f"Executing Monte Carlo task {task_chunk.id} on node {node.id}: "
            f"{samples} samples, seed={seed}"
        )
        
        # Execute the Monte Carlo integration
        pi_estimate, points_inside = estimate_pi(samples, seed)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(
            f"Task {task_chunk.id} completed on node {node.id}: "
            f"PI estimate = {pi_estimate:.6f}, time = {execution_time:.2f}ms"
        )
        
        return MonteCarloResult(
            task_id=task_chunk.id,
            node_id=node.id,
            samples=samples,
            pi_estimate=pi_estimate,
            execution_time_ms=execution_time,
            status=TaskStatus.COMPLETED
        )
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Task {task_chunk.id} failed on node {node.id}: {str(e)}")
        
        return MonteCarloResult(
            task_id=task_chunk.id,
            node_id=node.id,
            samples=task_chunk.parameters.get('samples', config.total_samples),
            pi_estimate=0.0,
            execution_time_ms=execution_time,
            status=TaskStatus.FAILED,
            error_message=str(e)
        )

def create_task_chunks(
    total_samples: int,
    chunk_size: int,
    seed_base: Optional[int] = None
) -> List[TaskChunk]:
    """
    Create a list of task chunks for distributed Monte Carlo integration.
    
    Args:
        total_samples: Total number of samples to process across all chunks
        chunk_size: Number of samples per chunk
        seed_base: Base random seed for reproducibility
        
    Returns:
        List of TaskChunk objects ready for distribution
    """
    chunks = []
    remaining = total_samples
    chunk_idx = 0
    
    while remaining > 0:
        current_chunk_size = min(chunk_size, remaining)
        chunk_id = f"mc_chunk_{chunk_idx:04d}"
        
        parameters = {
            'samples': current_chunk_size,
            'seed': seed_base + chunk_idx if seed_base is not None else None
        }
        
        chunk = TaskChunk(
            id=chunk_id,
            task_type='monte_carlo_pi',
            parameters=parameters,
            status=TaskStatus.PENDING,
            assigned_node_id=None,
            start_time=None,
            end_time=None,
            result=None
        )
        
        chunks.append(chunk)
        remaining -= current_chunk_size
        chunk_idx += 1
    
    logger.info(f"Created {len(chunks)} task chunks for {total_samples} total samples")
    return chunks

def aggregate_results(
    results: List[MonteCarloResult]
) -> Dict[str, Any]:
    """
    Aggregate Monte Carlo results from multiple tasks.
    
    Args:
        results: List of MonteCarloResult objects to aggregate
        
    Returns:
        Dictionary containing aggregated statistics
    """
    if not results:
        return {
            'total_samples': 0,
            'pi_estimate': 0.0,
            'avg_execution_time_ms': 0.0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_time_ms': 0.0
        }
    
    total_samples = sum(r.samples for r in results)
    completed = [r for r in results if r.status == TaskStatus.COMPLETED]
    failed = [r for r in results if r.status == TaskStatus.FAILED]
    
    # Aggregate PI estimates by weighted average
    if completed:
        weighted_sum = sum(r.pi_estimate * r.samples for r in completed)
        total_completed_samples = sum(r.samples for r in completed)
        aggregated_pi = weighted_sum / total_completed_samples if total_completed_samples > 0 else 0.0
    else:
        aggregated_pi = 0.0
    
    avg_time = (
        sum(r.execution_time_ms for r in completed) / len(completed)
        if completed else 0.0
    )
    
    return {
        'total_samples': total_samples,
        'pi_estimate': aggregated_pi,
        'actual_pi': 3.141592653589793,
        'error': abs(aggregated_pi - 3.141592653589793),
        'avg_execution_time_ms': avg_time,
        'completed_tasks': len(completed),
        'failed_tasks': len(failed),
        'total_time_ms': sum(r.execution_time_ms for r in results),
        'results_by_node': {
            r.node_id: [res.to_dict() for res in results if res.node_id == r.node_id]
            for r in results
        }
    }

def main():
    """
    Main entry point for running the benchmark locally for testing.
    
    This function creates task chunks, executes them, and outputs the results
    to a JSON file in the data directory.
    """
    logger.info("Starting Monte Carlo benchmark execution")
    
    # Load configuration
    config = BenchmarkConfig.from_config()
    
    # Create task chunks
    task_chunks = create_task_chunks(
        total_samples=config.total_samples,
        chunk_size=config.chunk_size,
        seed_base=config.random_seed
    )
    
    # Execute tasks (simulating local execution for testing)
    results = []
    for chunk in task_chunks:
        # Create a mock node for local testing
        mock_node = PhysicalNode(
            id='local_test_node',
            hostname='localhost',
            status='active',
            cpu_cores=4,
            memory_gb=8,
            network_bandwidth_mbps=1000,
            last_heartbeat=datetime.now(timezone.utc),
            metrics=None
        )
        
        result = run_monte_carlo_integration(chunk, mock_node, config)
        results.append(result)
    
    # Aggregate results
    aggregated = aggregate_results(results)
    
    # Ensure data directory exists
    data_dir = Path('code/data/raw')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results to file
    output_path = data_dir / 'benchmark_results.json'
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Benchmark results written to {output_path}")
    logger.info(f"PI estimate: {aggregated['pi_estimate']:.6f} (error: {aggregated['error']:.6f})")
    
    return aggregated

if __name__ == '__main__':
    from datetime import datetime, timezone
    main()
