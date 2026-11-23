"""
T015: Generate results_full.csv for full-context simulation.

This script runs a simulation loop for N games (default 200) under the
'full' context condition and outputs a CSV with specialization index
and retrieval efficiency metrics.

Dependencies:
  - T011b: simulate_one_game (game simulation loop)
  - T012: compute_specialization_index
  - T013: compute_retrieval_efficiency
"""
import csv
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from run_experiment import simulate_one_game, GameConfig
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """Run full-context simulation and write results_full.csv."""
    # Determine game count from environment variable
    game_count_env = os.environ.get('SIMULATION_GAME_COUNT', '200')
    try:
        game_count = int(game_count_env)
    except ValueError:
        logger.log("error", operation="invalid_game_count", message=f"Invalid SIMULATION_GAME_COUNT: {game_count_env}, defaulting to 200")
        game_count = 200

    logger.log("info", operation="start_simulation", game_count=game_count, context="full")

    # Ensure output directory exists
    output_dir = project_root / "results"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "results_full.csv"

    # Prepare CSV fields
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count"
    ]

    # Run simulation loop
    results = []
    for i in range(game_count):
        game_id = i + 1

        # Configuration for full-context simulation
        # Using default agent count (e.g., 3 or 5) as per task description
        # We'll use 3 agents as a standard baseline
        agent_count = 3
        config = GameConfig(
            context_condition="full",
            agent_count=agent_count,
            dataset_name="hanabi", # Default dataset
            max_turns=50
        )

        try:
            # Run the simulation for one game
            # simulate_one_game returns (specialization_index, retrieval_efficiency, game_result_obj)
            # based on T011b implementation
            spec_idx, ret_eff, game_result = simulate_one_game(game_id, config)

            # Validate metrics (T012 and T013 should handle this, but double-check)
            if spec_idx is None or ret_eff is None:
                logger.log("warning", operation="skip_game", game_id=game_id, reason="None metrics returned")
                continue

            results.append({
                "game_id": game_id,
                "specialization_index": spec_idx,
                "retrieval_efficiency": ret_eff,
                "context_condition": "full",
                "agent_count": agent_count
            })

            if game_id % 50 == 0:
                logger.log("info", operation="progress", game_id=game_id, total=game_count)

        except Exception as e:
            logger.log("error", operation="game_failure", game_id=game_id, error=str(e))
            # Continue with next game rather than failing the whole run

    # Write results to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.log("info", operation="simulation_complete", output_path=str(output_path), total_games=len(results))
    print(f"Results written to {output_path}")

if __name__ == "__main__":
    main()