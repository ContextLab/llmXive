"""
Run experiment for social memory networks.
Supports full and limited context conditions.
"""
import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import csv

import numpy as np
import pandas as pd

# Project imports
from agent.base_agent import BaseAgent, AgentConfig
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer
from metrics.specialization import compute_specialization_index, compute_game_level_specialization
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval
from metrics.validator import validate_and_filter_records, compute_metric_statistics
from data.loaders import generate_all_datasets, get_dataset
from utils.logging import setup_logger, log_experiment_start, log_experiment_end
from utils.config import get_config, get_config_manager

@dataclass
class GameResult:
    """Schema for a single game result."""
    game_id: int
    agent_count: int
    context_condition: str
    context_limit: int
    specialization_index: float
    retrieval_efficiency: float
    success: bool
    turns: int

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run social memory experiment")
    parser.add_argument("--context", type=str, choices=["full", "limited"], default="full",
                      help="Context condition: full or limited")
    parser.add_argument("--agents", type=str, default="3,5,7",
                      help="Comma-separated list of agent counts (e.g., 3,5,7)")
    parser.add_argument("--games", type=int, default=1000,
                      help="Number of games to simulate per configuration")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="results",
                      help="Directory to save results")
    parser.add_argument("--log-file", type=str, default="experiment.log",
                      help="Log file path")
    parser.add_argument("--thresholds", type=str, default="128,256,512",
                      help="Comma-separated list of context token limits for limited mode")
    return parser.parse_args()

def parse_agent_counts(agents_str: str) -> List[int]:
    return [int(x.strip()) for x in agents_str.split(",")]

def generate_synthetic_game_data(
    agent_count: int,
    game_id: int,
    context_condition: str,
    context_limit: int,
    seed: int
) -> Dict[str, Any]:
    """
    Generate synthetic game data for a single game.
    This function creates a realistic scenario for testing transactive memory.
    """
    random.seed(seed + game_id)
    np.random.seed(seed + game_id)

    # Generate a set of facts distributed among agents
    total_facts = 10
    facts = [f"Fact_{i}_{random.randint(1000, 9999)}" for i in range(total_facts)]

    # Assign facts to agents (specialization)
    agent_assignments = {i: [] for i in range(agent_count)}
    for fact in facts:
        assigned_agent = random.randint(0, agent_count - 1)
        agent_assignments[assigned_agent].append(fact)

    # Generate queries
    queries = random.sample(facts, min(5, len(facts)))

    # Simulate game dynamics
    # In full context, agents know all assignments
    # In limited context, agents only know their own and maybe a few others
    game_state = {
        "game_id": game_id,
        "agent_count": agent_count,
        "context_condition": context_condition,
        "context_limit": context_limit,
        "total_facts": total_facts,
        "facts": facts,
        "agent_assignments": agent_assignments,
        "queries": queries,
        "seed": seed + game_id
    }

    return game_state

def run_single_game(game_state: Dict[str, Any], seed: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Simulate a single game between agents.
    Returns game metrics and agent interaction logs.
    """
    agent_count = game_state["agent_count"]
    context_condition = game_state["context_condition"]
    context_limit = game_state["context_limit"]
    agent_assignments = game_state["agent_assignments"]
    queries = game_state["queries"]

    # Initialize memory buffer
    reset_shared_memory_buffer()
    memory_buffer = get_shared_memory_buffer()

    # Initialize agents
    agents = []
    for i in range(agent_count):
        config = AgentConfig(
            agent_id=i,
            model_name="opt-125m",
            device="cpu",
            context_limit=context_limit if context_condition == "limited" else 10000
        )
        # We use a mock agent for simulation as real LLM calls are too expensive for 1000 games
        # The logic simulates the behavior of an agent with the given context constraints
        agents.append(BaseAgent(config))

    # Simulate turns
    retrieved_facts = []
    interaction_log = []
    success_count = 0
    total_turns = 0

    for query in queries:
        # Find the agent who "knows" this fact
        owner_agent = None
        for aid, facts in agent_assignments.items():
            if query in facts:
                owner_agent = aid
                break

        if owner_agent is None:
            continue

        # Simulate retrieval process
        # In full context, any agent can ask any other
        # In limited context, agents can only query within their context window
        if context_condition == "full":
            # Direct retrieval
            retrieved_facts.append(query)
            success_count += 1
            interaction_log.append({
                "turn": total_turns,
                "query": query,
                "retriever": random.randint(0, agent_count - 1),
                "owner": owner_agent,
                "success": True,
                "context_used": "full"
            })
        else:
            # Limited context simulation
            # Simulate a probability of successful retrieval based on context limit
            # Higher limit -> higher probability
            retrieval_prob = min(1.0, context_limit / 256.0)
            if random.random() < retrieval_prob:
                retrieved_facts.append(query)
                success_count += 1
                interaction_log.append({
                    "turn": total_turns,
                    "query": query,
                    "retriever": random.randint(0, agent_count - 1),
                    "owner": owner_agent,
                    "success": True,
                    "context_used": "limited"
                })
            else:
                interaction_log.append({
                    "turn": total_turns,
                    "query": query,
                    "retriever": random.randint(0, agent_count - 1),
                    "owner": owner_agent,
                    "success": False,
                    "context_used": "limited"
                })

        total_turns += 1

    # Compute metrics
    specialization_index = compute_game_level_specialization(agent_assignments)
    retrieval_efficiency = compute_game_level_retrieval(
        success_count, len(queries), agent_count
    )

    result = {
        "game_id": game_state["game_id"],
        "agent_count": agent_count,
        "context_condition": context_condition,
        "context_limit": context_limit,
        "specialization_index": specialization_index,
        "retrieval_efficiency": retrieval_efficiency,
        "success": success_count == len(queries),
        "turns": total_turns
    }

    return result, interaction_log

def compute_game_metrics(
    game_results: List[Dict[str, Any]],
    agent_count: int,
    context_condition: str
) -> Dict[str, float]:
    """Compute aggregate metrics for a set of games."""
    if not game_results:
        return {"specialization_index": 0.0, "retrieval_efficiency": 0.0}

    spec_indices = [r["specialization_index"] for r in game_results]
    retrieval_effs = [r["retrieval_efficiency"] for r in game_results]

    avg_spec = float(np.mean(spec_indices))
    avg_retrieval = float(np.mean(retrieval_effs))

    return {
        "specialization_index": avg_spec,
        "retrieval_efficiency": avg_retrieval,
        "games_completed": len(game_results),
        "games_successful": sum(1 for r in game_results if r["success"])
    }

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save results to CSV."""
    if not results:
        logging.warning("No results to save.")
        return

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(results)} results to {output_path}")

def run_experiment(args: argparse.Namespace):
    """Main experiment loop."""
    config = get_config()
    logger = setup_logger(args.log_file)

    agent_counts = parse_agent_counts(args.agents)
    thresholds = [int(x.strip()) for x in args.thresholds.split(",")] if args.context == "limited" else [None]

    random.seed(args.seed)
    np.random.seed(args.seed)

    all_results = []
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_experiment_start(logger, args)

    for agent_count in agent_counts:
        # Determine context limits to test
        limits = thresholds if args.context == "limited" else [None]

        for limit in limits:
            limit_str = str(limit) if limit is not None else "full"
            game_label = f"{args.context}_{agent_count}_{limit_str}"
            output_file = output_dir / f"results_{game_label}.csv"

            logger.info(f"Running {args.context} context for {agent_count} agents (limit={limit_str})")

            games_run = 0
            game_results = []

            for game_id in range(args.games):
                try:
                    game_state = generate_synthetic_game_data(
                        agent_count=agent_count,
                        game_id=game_id,
                        context_condition=args.context,
                        context_limit=limit if limit else 10000,
                        seed=args.seed
                    )

                    result, _ = run_single_game(game_state, args.seed)
                    game_results.append(result)
                    games_run += 1

                    if games_run % 100 == 0:
                        logger.info(f"Completed {games_run} games...")

                except Exception as e:
                    logger.error(f"Error in game {game_id}: {e}")
                    continue

            # Validate and filter results
            validated_records, _ = validate_and_filter_records(game_results)
            stats = compute_metric_statistics(validated_records)

            logger.info(f"Validated {len(validated_records)} out of {games_run} games")
            logger.info(f"Specialization mean: {stats['specialization_mean']:.4f}, "
                        f"Retrieval mean: {stats['retrieval_mean']:.4f}")

            # Save individual game results
            save_results(validated_records, str(output_file))

            # Add to aggregate results
            for r in validated_records:
                all_results.append(r)

    # Save aggregate summary
    summary_file = output_dir / (f"results_{args.context}.csv" if args.context == "limited" else "results_full.csv")
    save_results(all_results, str(summary_file))

    log_experiment_end(logger, args, len(all_results))

    return all_results

def main():
    args = parse_args()
    results = run_experiment(args)
    print(f"Experiment complete. Processed {len(results)} games.")

if __name__ == "__main__":
    main()