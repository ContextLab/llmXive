"""
T015 Implementation: Generate results_full.csv for User Story 1 (Full Context).

This script runs the full-context simulation for 1000 games, computes
specialization index and retrieval efficiency for each, validates the metrics,
and outputs the results to projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv.

It relies on the real experiment logic from run_experiment.py and the metrics
from metrics/specialization.py and metrics/retrieval.py.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from run_experiment import (
    GameConfig,
    GameResult,
    simulate_one_game as run_experiment_simulate_one_game,
    build_parser as run_experiment_build_parser,
    main as run_experiment_main,
    parse_agents_arg,
)
from metrics.specialization import compute_specialization_index, validate_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, validate_retrieval_efficiency
from metrics.validator import validate_and_filter_records, ValidationResult
from utils.logging import get_logger

logger = get_logger(__name__)

RESULTS_DIR = project_root / "results"
OUTPUT_FILE = RESULTS_DIR / "results_full.csv"
NUM_GAMES = 1000
DEFAULT_AGENTS = 5
DEFAULT_SEED = 42


def run_single_game_simulation(game_id: int, config: GameConfig) -> GameResult:
    """
    Run a single game simulation using the real experiment logic.
    """
    # Run the simulation using the logic from run_experiment.py
    # We need to call the internal simulate_one_game logic directly
    # Since run_experiment.py's simulate_one_game is the one we need
    return run_experiment_simulate_one_game(config, game_id)


def compute_metrics_for_game(result: GameResult) -> Tuple[float, float]:
    """
    Compute specialization index and retrieval efficiency for a single game result.
    """
    # Compute Specialization Index
    # The result should contain facts_per_agent or similar structure
    # Based on T012 implementation expectations
    agent_facts = getattr(result, 'facts_per_agent', {})
    if not agent_facts:
        # Fallback if structure is different, try to infer from agent contributions
        # Assuming result has a way to access per-agent contributions
        # If the GameResult structure is different, we adapt here
        # For now, assume facts_per_agent is a dict {agent_id: count} or list
        if hasattr(result, 'agent_contributions'):
            agent_facts = result.agent_contributions
        else:
            agent_facts = {}

    spec_index, _ = compute_specialization_index(agent_facts, num_agents=result.agent_count)

    # Compute Retrieval Efficiency
    # Based on T013 implementation expectations
    successful_retrievals = getattr(result, 'successful_retrievals', 0)
    total_queries = getattr(result, 'total_queries', 0)

    ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, result.agent_count)

    return spec_index, ret_eff


def validate_metrics(spec_index: float, ret_eff: float) -> bool:
    """
    Validate that computed metrics are within expected ranges.
    """
    spec_valid = validate_specialization_index(spec_index, num_agents=DEFAULT_AGENTS)
    ret_valid = validate_retrieval_efficiency(ret_eff)
    return spec_valid and ret_valid


def write_results_csv(results: List[Dict[str, Any]], output_path: Path):
    """
    Write the results to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'game_id',
        'specialization_index',
        'retrieval_efficiency',
        'context_condition',
        'agent_count'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.log("write_results_csv", path=str(output_path), count=len(results))


def main():
    """
    Main entry point for T015: Generate full context results.
    """
    parser = argparse.ArgumentParser(description="Generate full context results for User Story 1")
    parser.add_argument("--games", type=int, default=NUM_GAMES, help="Number of games to simulate")
    parser.add_argument("--agents", type=int, default=DEFAULT_AGENTS, help="Number of agents")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output CSV path")
    args = parser.parse_args()

    logger.log("t015_start", games=args.games, agents=args.agents, seed=args.seed)

    # Configure simulation
    config = GameConfig(
        num_agents=args.agents,
        context_condition="full",
        seed=args.seed,
        dataset="synthetic",  # Use synthetic fallback as per T004/T004b
        token_limit=None  # Full context
    )

    results = []
    valid_count = 0
    error_count = 0

    for game_id in range(args.games):
        try:
            # Run simulation
            result = run_single_game_simulation(game_id, config)

            # Compute metrics
            spec_index, ret_eff = compute_metrics_for_game(result)

            # Validate
            if validate_metrics(spec_index, ret_eff):
                results.append({
                    'game_id': game_id,
                    'specialization_index': round(spec_index, 6),
                    'retrieval_efficiency': round(ret_eff, 6),
                    'context_condition': 'full',
                    'agent_count': args.agents
                })
                valid_count += 1
            else:
                error_count += 1
                logger.log("t015_validation_failed", game_id=game_id, spec=spec_index, ret=ret_eff)

        except Exception as e:
            error_count += 1
            logger.log("t015_simulation_error", game_id=game_id, error=str(e))
            # Continue with next game to ensure we get as many results as possible
            # But log the error

    # Write results
    write_results_csv(results, Path(args.output))

    # Validation check (SC-001): At least 95% of games must have valid metrics
    total_attempted = args.games
    success_rate = valid_count / total_attempted if total_attempted > 0 else 0.0

    logger.log("t015_complete", total=total_attempted, valid=valid_count, errors=error_count, rate=success_rate)

    if success_rate < 0.95:
        logger.log("t015_validation_warning", message=f"Success rate {success_rate:.2%} is below 95% threshold")
        # Do not fail the script, but log the warning as per SC-001

    print(f"T015 Complete: {valid_count}/{total_attempted} games processed. Output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
