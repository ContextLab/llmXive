import json
import math
import random
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from utils.heuristics import calculate_composite_density

# Configuration constants for the heuristic solver
ALPHA = 2.0  # Scaling factor for the logistic function
THRESHOLD = 0.5  # Critical density threshold

def sigmoid(x: float) -> float:
    """Compute the sigmoid function."""
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    else:
        # Numerical stability for large negative x
        exp_x = math.exp(x)
        return exp_x / (1 + exp_x)

def heuristic_solver_success(density: float, alpha: float = ALPHA, threshold: float = THRESHOLD) -> bool:
    """
    Determine if the agent successfully retrieves evidence based on density.
    Uses the logistic function P(retrieval) = sigmoid(alpha * (density - threshold)).
    """
    prob = sigmoid(alpha * (density - threshold))
    return random.random() < prob

def check_evidence_visibility(critical_evidence_turn_index: int, current_turn: int, retention_horizon: int) -> bool:
    """
    Check if the critical evidence is within the current retention horizon.
    Returns True if the evidence is visible (i.e., not masked).
    """
    # The evidence is visible if the current turn is within [evidence_turn, evidence_turn + horizon - 1]
    # But typically, at turn T, we look back `horizon` turns.
    # Logic: Is the evidence turn index >= (current_turn - retention_horizon + 1)?
    # And obviously evidence_turn <= current_turn.
    if critical_evidence_turn_index > current_turn:
        return False
    start_of_window = current_turn - retention_horizon + 1
    return critical_evidence_turn_index >= start_of_window

def run_simulation(trajectories: List[Dict[str, Any]], retention_horizons: List[int]) -> List[Dict[str, Any]]:
    """
    Run the simulation for a list of trajectories and a list of retention horizons.
    Returns a list of results for each (trajectory, horizon) pair.
    """
    results = []
    for traj in trajectories:
        text = traj.get("text", "")
        density = traj.get("density", 0.0)
        evidence_turn = traj.get("critical_evidence_turn_index", -1)
        
        # Calculate density if not provided (using the utility)
        if density is None or density == 0.0:
            # Fallback to utility calculation if needed, though trajectories should have it
            # Assuming text is available
            if text:
                density = calculate_composite_density(text)
            else:
                density = 0.0

        for horizon in retention_horizons:
            # Determine if agent succeeds probabilistically based on density
            agent_success = heuristic_solver_success(density)
            
            # Check if evidence is visible given the horizon
            # We assume simulation runs at the final turn of the trajectory for this check
            # Or we can iterate turns. The task implies a final success check.
            # Based on T013: "1 if (critical_evidence_turn_index >= current_turn - retention_horizon + 1) AND (agent_heuristic_success = true)"
            # We assume current_turn is the last turn index of the trajectory.
            # If the trajectory has N turns, indices are 0..N-1.
            # Let's assume the simulation runs at the end (turn = N-1).
            # However, to be robust, let's assume the input trajectory has a 'total_turns' or we derive it.
            # If not, we assume the evidence turn is the last relevant event, and we check if it's in the window of the last turn.
            # Let's assume the "current turn" for the check is the turn index of the evidence itself? 
            # No, the logic is: At the end of the search (or at turn T), did we retain the evidence?
            # If evidence is at turn E, and we are at turn T, we retain it if E >= T - H + 1.
            # Let's assume T is the length of the trajectory (or max index).
            # If 'total_turns' is not in traj, we can't calculate T exactly without parsing text.
            # Assumption: The input JSON from T011 includes 'total_turns' or we assume the check happens at the turn of the evidence?
            # Re-reading T013: "Verify... failure when horizon < 5 for high-density evidence".
            # Let's assume the simulation runs until the end of the trajectory.
            # If the trajectory doesn't specify total turns, we might assume the evidence turn is the last one?
            # No, evidence can be earlier.
            # Let's assume the trajectory object has a 'total_turns' field added by T011.
            total_turns = traj.get("total_turns", evidence_turn + 1) 
            # If total_turns is not provided, default to evidence_turn + 1 (meaning evidence is the last thing)
            # But if evidence is early, this logic changes.
            # Let's assume the standard case: The agent runs for `total_turns` steps.
            current_turn = total_turns - 1 # 0-indexed last turn
            
            visibility = check_evidence_visibility(evidence_turn, current_turn, horizon)
            
            final_success = 1 if (visibility and agent_success) else 0
            
            results.append({
                "trajectory_id": traj.get("id", "unknown"),
                "density": density,
                "retention_horizon": horizon,
                "evidence_turn": evidence_turn,
                "total_turns": total_turns,
                "visibility": visibility,
                "agent_success": agent_success,
                "final_success": final_success
            })
    return results

def main():
    """
    Main entry point for the simulation.
    Implements streaming approach to write results to data/processed/ immediately after each batch.
    """
    # Paths
    input_path = Path("data/raw/trajectories.json")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration
    batch_size = 50  # Process 50 trajectories at a time to manage RAM
    retention_horizons = list(range(1, 11)) # Test horizons 1 to 10
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)
    
    # Load all trajectories (assuming they fit in memory, or we could stream the JSON if it was NDJSON)
    # For JSON array, we load once. If the file is too large, we'd need a streaming JSON parser.
    # Given the constraint "manage RAM", we assume the input is large but fits in RAM, 
    # but we stream the *results* to disk to avoid accumulating a huge result list.
    print(f"Loading trajectories from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        trajectories = json.load(f)
    
    print(f"Loaded {len(trajectories)} trajectories.")
    
    output_file = output_dir / "simulation_results.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # Process in batches
        for i in range(0, len(trajectories), batch_size):
            batch = trajectories[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1} (rows {i} to {min(i+batch_size, len(trajectories))-1})...")
            
            batch_results = run_simulation(batch, retention_horizons)
            
            # Stream results immediately to disk
            for res in batch_results:
                out_f.write(json.dumps(res) + '\n')
            
            # Optional: Clear batch to free memory (though batch is small)
            del batch
            del batch_results
    
    print(f"Simulation complete. Results written to {output_file}")

if __name__ == "__main__":
    main()