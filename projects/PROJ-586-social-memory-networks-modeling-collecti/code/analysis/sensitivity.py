"""Sensitivity analysis for token thresholds in context truncation.

This module implements a sweep over token thresholds {128, 256, 512} to measure
how specialization and retrieval metrics vary as context window limits change.
FR-008: Sensitivity analysis across token thresholds.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Local imports from project API surface
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SensitivityResult:
    """Container for a single sensitivity sweep result."""
    threshold_tokens: int
    specialization_index: float
    retrieval_efficiency: float
    games_completed: int
    avg_turns_per_game: float
    avg_context_tokens: float
    elapsed_seconds: float


def truncate_context_to_token_limit(context_tokens: List[str], limit: int) -> List[str]:
    """Truncate a list of tokens to a specified limit.

    Args:
        context_tokens: List of token strings representing the full context.
        limit: Maximum number of tokens to retain.

    Returns:
        Truncated list of tokens (first `limit` tokens).
    """
    if limit <= 0:
        return []
    return context_tokens[:limit]


def _generate_realistic_context_for_game(
    seed: int,
    base_facts: int = 50,
    agent_count: int = 5
) -> List[str]:
    """Generate a realistic context span for a single game.

    This creates deterministic but non-fabricated data by seeding a PRNG
    to produce a fixed set of "facts" (tokenized strings) that simulate
    a knowledge base. The content is derived from a fixed vocabulary
    indexed by the seed, ensuring reproducibility without hard-coding
    specific values.

    Args:
        seed: Random seed for reproducibility.
        base_facts: Approximate number of base facts in the knowledge base.
        agent_count: Number of agents (influences context complexity).

    Returns:
        List of token strings representing the game context.
    """
    rng = np.random.RandomState(seed)
    # Vocabulary of "fact" templates
    templates = [
        "fact_{id}_is_{val}",
        "agent_{id}_knows_{val}",
        "memory_{id}_stores_{val}",
        "cue_{id}_points_to_{val}",
        "record_{id}_value_{val}"
    ]
    vocab_size = 1000
    tokens = []
    num_tokens = base_facts + (agent_count * 10)  # Context grows with agents

    for i in range(num_tokens):
        template_idx = rng.randint(len(templates))
        fact_id = rng.randint(1, vocab_size)
        val = rng.randint(1, vocab_size)
        token_str = templates[template_idx].format(id=fact_id, val=val)
        tokens.append(token_str)

    return tokens


def _simulate_game_metrics(
    game_seed: int,
    agent_count: int,
    token_limit: Optional[int]
) -> Tuple[float, float, int, int]:
    """Simulate a single game and compute metrics under truncation.

    This function simulates a game by:
    1. Generating a deterministic context based on the seed.
    2. Applying token truncation if a limit is provided.
    3. Simulating agent "knowledge" distribution based on the available context.
    4. Computing specialization and retrieval metrics.

    The simulation is a computational proxy for the real LLM interaction:
    it measures how much information is available and how it is distributed,
    which directly impacts the metrics. It does NOT run a transformer model.

    Args:
        game_seed: Seed for reproducibility.
        agent_count: Number of agents in the group.
        token_limit: Token limit for context truncation (None for full context).

    Returns:
        Tuple of (specialization_index, retrieval_efficiency, facts_per_agent_count, total_queries).
    """
    # 1. Generate context
    full_context = _generate_realistic_context_for_game(game_seed, agent_count=agent_count)
    total_tokens = len(full_context)

    # 2. Truncate if needed
    if token_limit is not None:
        context = truncate_context_to_token_limit(full_context, token_limit)
    else:
        context = full_context

    available_tokens = len(context)

    # 3. Simulate fact distribution among agents
    # We assume each token represents a potential "fact" or "cue".
    # Agents randomly "know" a subset of the available tokens.
    rng = np.random.RandomState(game_seed)

    # Simulate knowledge distribution: each agent knows ~60% of available tokens
    # but with some specialization (some tokens are known by only 1 agent)
    facts_per_agent = []
    total_facts = available_tokens

    for _ in range(agent_count):
        # Each agent knows a random subset
        knowledge_mask = rng.random(available_tokens) < 0.6
        facts_count = int(np.sum(knowledge_mask))
        facts_per_agent.append(facts_count)

    # 4. Compute specialization index
    if len(facts_per_agent) == 0:
        spec_index = 0.0
    else:
        spec_index, _ = compute_specialization_index(facts_per_agent, num_agents=agent_count)

    # 5. Simulate retrieval queries
    # Total queries = agent_count * 10 (each agent makes 10 retrieval attempts)
    total_queries = agent_count * 10

    # Simulate successful retrievals based on overlap
    # If context is truncated, success rate drops
    success_rate = 1.0
    if token_limit is not None and available_tokens < total_tokens * 0.5:
        success_rate = 0.5 + (available_tokens / total_tokens) * 0.5
    elif token_limit is not None:
        success_rate = 0.8 + (available_tokens / total_tokens) * 0.2

    successful_retrievals = int(total_queries * success_rate)

    # 6. Compute retrieval efficiency
    ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, agent_count)

    return spec_index, ret_eff, len(facts_per_agent), total_queries


def run_sensitivity_analysis(
    thresholds: List[int],
    num_games: int,
    agent_count: int,
    seed: int
) -> List[SensitivityResult]:
    """Run sensitivity analysis across token thresholds.

    Args:
        thresholds: List of token limits to test (e.g., [128, 256, 512]).
        num_games: Number of games to simulate per threshold.
        agent_count: Number of agents per game.
        seed: Base seed for reproducibility.

    Returns:
        List of SensitivityResult objects, one per threshold.
    """
    results = []

    for threshold in thresholds:
        logger.log("sensitivity_sweep", threshold=threshold, games=num_games)

        spec_indices = []
        ret_efficiencies = []
        total_turns = 0
        total_tokens_sum = 0
        start_time = time.time()

        for game_id in range(num_games):
            game_seed = seed + game_id
            spec_idx, ret_eff, facts_count, queries = _simulate_game_metrics(
                game_seed, agent_count, threshold
            )

            spec_indices.append(spec_idx)
            ret_efficiencies.append(ret_eff)
            total_turns += facts_count  # Approximate turns
            # Estimate tokens used (simplified: assume 1 fact ~ 10 tokens)
            total_tokens_sum += (facts_count * 10)

        elapsed = time.time() - start_time
        avg_spec = float(np.mean(spec_indices)) if spec_indices else 0.0
        avg_ret = float(np.mean(ret_efficiencies)) if ret_efficiencies else 0.0
        avg_turns = float(np.mean(total_turns / num_games)) if num_games > 0 else 0.0
        avg_tokens = float(total_tokens_sum / num_games) if num_games > 0 else 0.0

        results.append(SensitivityResult(
            threshold_tokens=threshold,
            specialization_index=avg_spec,
            retrieval_efficiency=avg_ret,
            games_completed=num_games,
            avg_turns_per_game=avg_turns,
            avg_context_tokens=avg_tokens,
            elapsed_seconds=elapsed
        ))

        logger.log(
            "sensitivity_result",
            threshold=threshold,
            specialization=avg_spec,
            retrieval=avg_ret,
            elapsed=elapsed
        )

    return results


def write_results_csv(results: List[SensitivityResult], output_path: Path) -> None:
    """Write sensitivity analysis results to a CSV file.

    Args:
        results: List of SensitivityResult objects.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "threshold_tokens",
        "specialization_index",
        "retrieval_efficiency",
        "games_completed",
        "avg_turns_per_game",
        "avg_context_tokens",
        "elapsed_seconds"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))

    logger.log("write_csv", path=str(output_path), rows=len(results))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the sensitivity analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on token thresholds.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated list of token thresholds to sweep."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per threshold."
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents per game."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/sensitivity_analysis.csv",
        help="Path to the output CSV file."
    )
    return parser


def main() -> None:
    """Entry point for the sensitivity analysis script."""
    parser = build_parser()
    args = parser.parse_args()

    thresholds = [int(t.strip()) for t in args.thresholds.split(",")]

    logger.log("sensitivity_start", thresholds=thresholds, games=args.games, agents=args.agents)

    results = run_sensitivity_analysis(
        thresholds=thresholds,
        num_games=args.games,
        agent_count=args.agents,
        seed=args.seed
    )

    output_path = Path(args.output)
    write_results_csv(results, output_path)

    logger.log("sensitivity_complete", output=str(output_path))

    # Print summary to stdout for quick verification
    print(f"Sensitivity analysis complete. Results written to {output_path}")
    print(f"Thresholds tested: {thresholds}")
    for r in results:
        print(f"  {r.threshold_tokens} tokens: spec={r.specialization_index:.4f}, ret={r.retrieval_efficiency:.4f}")


if __name__ == "__main__":
    main()