"""
Deterministic synthetic baseline generator for ABot-AgentOS v1.0 simulation.

This module provides a fallback mechanism to generate deterministic synthetic
task traces and success metrics when the real ABot-AgentOS v1.0 baseline
cannot be acquired (private repo, complex dependencies, etc.).

LIMITATIONS:
- This is a synthetic generator, not a real neural baseline.
- Success rates are probabilistic based on task complexity, not learned behavior.
- Latency values are simulated, not measured from actual inference.
- Memory usage is estimated, not monitored from a running process.
- Results should be treated as placeholders for pipeline validation only.
- NOT suitable for final scientific conclusions about neural vs symbolic performance.

Usage:
    from mock_baseline import run_baseline_simulation
    results = run_baseline_simulation(task_traces, seed=42)
"""

import json
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing project configuration
try:
    from config import RANDOM_SEED
except ImportError:
    # Fallback if config not available in current context
    RANDOM_SEED = 42

@dataclass
class BaselineResult:
    """Result from a single baseline execution."""
    task_id: str
    success: bool
    latency_ms: float
    memory_mb: float
    steps_taken: int
    error_type: Optional[str] = None

@dataclass
class BaselineReport:
    """Aggregated report from baseline simulation."""
    total_tasks: int
    successful_tasks: int
    success_rate: float
    avg_latency_ms: float
    avg_memory_mb: float
    avg_steps: int
    error_distribution: Dict[str, int]
    seed_used: int
    is_synthetic: bool = True

def _determine_success(task_trace: Dict[str, Any], rng: random.Random) -> tuple[bool, Optional[str]]:
    """
    Determine synthetic success based on task complexity.
    
    This is a heuristic simulation:
    - Tasks with more steps have lower success probability
    - Tasks with complex object interactions are harder
    - Random noise is added to simulate stochastic behavior
    """
    steps = len(task_trace.get("steps", []))
    complexity_score = steps * 0.1  # Base complexity per step
    
    # Add interaction complexity
    interactions = sum(1 for step in task_trace.get("steps", []) 
                     if any(key in step for key in ["put", "take", "open", "close"]))
    complexity_score += interactions * 0.15
    
    # Base success probability with decay
    base_success = 0.95
    decay = 0.05 * min(complexity_score, 3.0)  # Cap decay at 15%
    success_prob = max(0.60, base_success - decay)
    
    if rng.random() < success_prob:
        return True, None
    else:
        # Categorize failure type
        failure_types = ["navigation_error", "object_interaction_failure", "planning_error"]
        weights = [0.4, 0.35, 0.25]
        error_type = rng.choices(failure_types, weights=weights)[0]
        return False, error_type

def _simulate_latency(task_trace: Dict[str, Any], rng: random.Random) -> float:
    """Simulate inference latency in milliseconds."""
    steps = len(task_trace.get("steps", []))
    base_latency = 50.0  # Base overhead
    step_latency = 10.0  # Per-step inference cost
    noise = rng.gauss(0, 5.0)
    return max(20.0, base_latency + (steps * step_latency) + noise)

def _simulate_memory(task_trace: Dict[str, Any], rng: random.Random) -> float:
    """Simulate memory usage in MB."""
    steps = len(task_trace.get("steps", []))
    base_memory = 200.0
    step_memory = 2.5
    noise = rng.gauss(0, 10.0)
    return max(150.0, base_memory + (steps * step_memory) + noise)

def run_baseline_simulation(
    task_traces: List[Dict[str, Any]],
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> BaselineReport:
    """
    Run deterministic synthetic baseline simulation on task traces.
    
    Args:
        task_traces: List of task trace dictionaries from ALFWorld
        seed: Random seed for reproducibility (uses config.RANDOM_SEED if None)
        output_path: Optional path to write JSON report
      
    Returns:
        BaselineReport with aggregated metrics
    """
    effective_seed = seed if seed is not None else RANDOM_SEED
    rng = random.Random(effective_seed)
    
    results: List[BaselineResult] = []
    error_counts: Dict[str, int] = {}
    
    for trace in task_traces:
        task_id = trace.get("task_id", f"task_{len(results)}")
        
        success, error_type = _determine_success(trace, rng)
        latency = _simulate_latency(trace, rng)
        memory = _simulate_memory(trace, rng)
        steps = len(trace.get("steps", []))
        
        result = BaselineResult(
            task_id=task_id,
            success=success,
            latency_ms=round(latency, 2),
            memory_mb=round(memory, 2),
            steps_taken=steps,
            error_type=error_type
        )
        results.append(result)
        
        if error_type:
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    # Calculate aggregated metrics
    successful = [r for r in results if r.success]
    total = len(results)
    success_count = len(successful)
    
    report = BaselineReport(
        total_tasks=total,
        successful_tasks=success_count,
        success_rate=round(success_count / total, 4) if total > 0 else 0.0,
        avg_latency_ms=round(sum(r.latency_ms for r in results) / total, 2) if total > 0 else 0.0,
        avg_memory_mb=round(sum(r.memory_mb for r in results) / total, 2) if total > 0 else 0.0,
        avg_steps=round(sum(r.steps_taken for r in results) / total, 2) if total > 0 else 0.0,
        error_distribution=error_counts,
        seed_used=effective_seed,
        is_synthetic=True
    )
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2)
    
    return report

def generate_mock_traces(num_traces: int = 10, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generate deterministic mock task traces for testing.
    
    This creates synthetic ALFWorld-style traces with varying complexity.
    """
    effective_seed = seed if seed is not None else RANDOM_SEED
    rng = random.Random(effective_seed)
    
    objects = ["apple", "bowl", "cup", "countertop", "drawer", "fridge", "microwave", "plate", "sink", "stove"]
    actions = ["go to", "open", "close", "take", "put", "clean", "heat", "cool"]
    
    traces = []
    for i in range(num_traces):
        num_steps = rng.randint(3, 15)
        steps = []
        current_location = rng.choice(objects)
        
        for _ in range(num_steps):
            action = rng.choice(actions)
            target = rng.choice(objects)
            if action in ["go to", "take", "put"]:
                step = {"action": action, "target": target, "location": current_location}
            else:
                step = {"action": action, "target": target}
            
            steps.append(step)
            if action == "go to":
                current_location = target
        
        traces.append({
            "task_id": f"mock_task_{i:03d}",
            "steps": steps,
            "goal": f"Find and manipulate {rng.choice(objects)}",
            "environment": "kitchen"
        })
    
    return traces

def main():
    """Main entry point for standalone execution."""
    print("Generating mock task traces...")
    mock_traces = generate_mock_traces(num_traces=20, seed=RANDOM_SEED)
    
    print(f"Running baseline simulation on {len(mock_traces)} traces...")
    report = run_baseline_simulation(
        mock_traces,
        seed=RANDOM_SEED,
        output_path=Path("data/results/mock_baseline_report.json")
    )
    
    print("\n=== Mock Baseline Report ===")
    print(f"Total Tasks: {report.total_tasks}")
    print(f"Success Rate: {report.success_rate:.2%}")
    print(f"Avg Latency: {report.avg_latency_ms:.2f} ms")
    print(f"Avg Memory: {report.avg_memory_mb:.2f} MB")
    print(f"Avg Steps: {report.avg_steps:.2f}")
    print(f"Error Distribution: {report.error_distribution}")
    print(f"Seed Used: {report.seed_used}")
    print(f"SYNTHETIC: {report.is_synthetic}")
    print("\nReport saved to: data/results/mock_baseline_report.json")
    
    return report

if __name__ == "__main__":
    main()
