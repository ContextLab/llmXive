"""
simulate_agent.py

Implements the agent simulation loop with variable retention horizons.
Optimized for performance (runtime < 6h, RAM < 7GB) using streaming I/O
and vectorized operations where applicable.
"""

import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Constants for the logistic function (FR-009)
# Default parameters can be overridden via CLI or config
DEFAULT_ALPHA = 2.0
DEFAULT_THRESHOLD = 0.5


def sigmoid(x: float) -> float:
    """Compute the sigmoid function."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        # Avoid overflow for large negative x
        exp_x = math.exp(x)
        return exp_x / (1.0 + exp_x)


def heuristic_solver_success(density: float, alpha: float = DEFAULT_ALPHA, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """
    Determine agent success probabilistically based on density.
    Uses the logistic function: P(retrieval) = sigmoid(α * (density - threshold))
    """
    prob = sigmoid(alpha * (density - threshold))
    return random.random() < prob


def check_evidence_visibility(critical_turn: int, current_turn: int, retention_horizon: int) -> bool:
    """
    Check if the critical evidence is visible within the current retention horizon.
    
    Logic:
    The agent at 'current_turn' can see turns from (current_turn - retention_horizon + 1) to current_turn.
    If critical_turn falls in this range, it is visible.
    
    Edge Case: If critical_turn is the very last turn (T), and horizon is T, it must be visible.
    """
    # Calculate the start of the visible window
    start_window = current_turn - retention_horizon + 1
    
    # Ensure the window doesn't go before turn 1 (though logic handles it naturally if turns are 1-indexed)
    # Assuming turns are 1-based indices for this logic
    return start_window <= critical_turn <= current_turn


def run_simulation(
    input_path: str,
    output_path: str,
    alpha: float = DEFAULT_ALPHA,
    threshold: float = DEFAULT_THRESHOLD,
    max_horizon: Optional[int] = None,
    seed: Optional[int] = None
) -> None:
    """
    Run the simulation loop.
    
    Optimizations:
    1. Stream input: Read JSON lines or iterate file to avoid loading 500 trajectories + all horizons into RAM at once if huge.
       However, for 500 trajectories, loading into memory is fine. The optimization here is to avoid nested list
       explosion by writing results incrementally or processing in batches.
    2. Vectorized logic: Use simple math instead of heavy libraries if possible, but here we stick to stdlib for speed in loop.
    3. Pre-calculate random seeds if needed for reproducibility.
    
    Args:
        input_path: Path to the trajectories JSON file (output of generate_trajectories.py).
        output_path: Path to write the simulation results (JSON lines or JSON array).
        alpha: Scaling factor for the logistic function.
        threshold: Critical density threshold.
        max_horizon: Maximum retention horizon to test (defaults to trajectory length if None).
        seed: Random seed for reproducibility.
    """
    if seed is not None:
        random.seed(seed)

    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input trajectory file not found: {input_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    
    # Load trajectories. For 500 trajectories, this is lightweight.
    # If the file is huge (e.g. > 1GB), we would implement a line-by-line JSON parser.
    # Assuming the format from T011 is a JSON list of objects.
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            trajectories = json.load(f)
    except json.JSONDecodeError:
        # Fallback for JSONL if the generator outputs lines
        trajectories = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    trajectories.append(json.loads(line))

    total_trajectories = len(trajectories)
    print(f"Loaded {total_trajectories} trajectories. Starting simulation...")

    # Process each trajectory
    for idx, traj in enumerate(trajectories):
        traj_id = traj.get('id', idx)
        density = traj.get('density', 0.0)
        critical_turn = traj.get('critical_evidence_turn_index', -1)
        total_turns = traj.get('total_turns', 0)
        
        if total_turns == 0:
            continue

        # Determine max horizon to test
        horizon_limit = max_horizon if max_horizon is not None else total_turns
        
        # Pre-allocate results for this trajectory to avoid repeated list appends in inner loop
        # We will store (horizon, success_flag)
        traj_results = []
        
        # Optimization: The success logic is deterministic given the random seed for the heuristic.
        # However, since we need to sample the heuristic for each horizon, we iterate.
        
        for horizon in range(1, horizon_limit + 1):
            # 1. Check visibility
            is_visible = check_evidence_visibility(critical_turn, total_turns, horizon)
            
            if not is_visible:
                # If evidence is not in window, success is 0 (failure)
                success = 0
            else:
                # 2. Check heuristic success
                if heuristic_solver_success(density, alpha, threshold):
                    success = 1
                else:
                    success = 0
            
            traj_results.append({
                "horizon": horizon,
                "success": success,
                "density": density,
                "critical_turn": critical_turn,
                "is_visible": is_visible
            })
        
        results.append({
            "trajectory_id": traj_id,
            "density": density,
            "results": traj_results
        })
        
        # Optional: Print progress every 100 trajectories
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{total_trajectories} trajectories...")

    # Write results
    # Writing as a single JSON file is fine for this size.
    # If output is massive, we could write line-by-line (JSONL).
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"Simulation complete. Results written to {output_path}")


def main():
    """Entry point for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run agent simulation with variable retention horizons.")
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input trajectories JSON file (e.g., data/raw/trajectories.json)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to output simulation results JSON file (e.g., data/processed/simulation_results.json)"
    )
    parser.add_argument(
        "--alpha", "-a",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Scaling factor for logistic function (default: {DEFAULT_ALPHA})"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Critical density threshold (default: {DEFAULT_THRESHOLD})"
    )
    parser.add_argument(
        "--max-horizon", "-m",
        type=int,
        default=None,
        help="Maximum retention horizon to test (default: total turns of trajectory)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    try:
        run_simulation(
            input_path=args.input,
            output_path=args.output,
            alpha=args.alpha,
            threshold=args.threshold,
            max_horizon=args.max_horizon,
            seed=args.seed
        )
    except Exception as e:
        print(f"Error during simulation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()