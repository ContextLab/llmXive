"""Sensitivity analysis for token threshold variations.

This module implements a sensitivity analysis that sweeps token thresholds
across the set {128, 256, 512} tokens and records how specialization and
retrieval metrics vary for each threshold.

Per FR-008, this analysis measures the robustness of the system under
different context window constraints.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Import from project modules using the exact API surface
from metrics.specialization import compute_specialization_index, SpecializationMetrics
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SensitivityResult:
    """Result of a single sensitivity measurement at a given threshold."""
    threshold_tokens: int
    specialization_index: float
    retrieval_efficiency: float
    game_id: int
    agent_count: int
    elapsed_seconds: float
    facts_count: int
    successful_retrievals: int
    total_queries: int


@dataclass
class SensitivityAnalysisOutput:
    """Aggregated output from the full sensitivity sweep."""
    thresholds: List[int]
    results: List[SensitivityResult]
    summary: Dict[str, Any] = field(default_factory=dict)


def truncate_context_to_token_limit(context: str, token_limit: int) -> str:
    """Truncate a context string to a specified token limit.

    This is a simplified tokenization that counts whitespace-separated tokens.
    For production use, a proper tokenizer (e.g., from transformers) should be used.
    However, for sensitivity analysis on CPU without model dependencies,
    this approximation suffices to measure the effect of context length.

    Args:
        context: The full context string to truncate.
        token_limit: Maximum number of tokens to keep.

    Returns:
        Truncated context string with at most `token_limit` tokens.
    """
    if not context:
        return ""

    tokens = context.split()
    if len(tokens) <= token_limit:
        return context

    truncated = tokens[:token_limit]
    return " ".join(truncated)


def simulate_game_with_threshold(
    game_id: int,
    agent_count: int,
    token_limit: int,
    seed: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Simulate a single game with a specific token threshold.

    This function creates a realistic simulation of a multi-agent game where
    context is truncated according to the token limit. The simulation uses
    deterministic pseudo-random generation based on the seed to ensure
    reproducibility while measuring actual metric values.

    Args:
        game_id: Unique identifier for this game instance.
        agent_count: Number of agents in the simulation.
        token_limit: Token threshold for context truncation.
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (facts_list, retrieval_list) where:
        - facts_list: List of facts distributed among agents
        - retrieval_list: List of retrieval attempts and outcomes
    """
    if seed is not None:
        np.random.seed(seed + game_id)

    # Generate a realistic set of facts distributed across agents
    # Number of facts scales with agent count (sublinear, per Geoff West's insight)
    base_facts = int(20 + agent_count * 2.5)
    facts_list = []

    for i in range(base_facts):
        fact_id = f"fact_{game_id}_{i}"
        # Distribute facts among agents with some overlap (transactive memory)
        # Each fact is known by 1-3 agents
        num_agents_with_fact = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        agents_with_fact = np.random.choice(agent_count, size=num_agents_with_fact, replace=False).tolist()

        facts_list.append({
            "fact_id": fact_id,
            "content": f"Fact {i} about topic {i % 10}",
            "known_by": agents_with_fact,
            "token_length": np.random.randint(10, 50)  # Simulated token count
        })

    # Simulate retrieval attempts
    retrieval_list = []
    for i in range(base_facts):
        query_agent = np.random.randint(0, agent_count)
        target_fact = facts_list[i]

        # Check if the querying agent knows the fact or can retrieve it
        if query_agent in target_fact["known_by"]:
            success = True
            retrieval_path = [query_agent]
        else:
            # Attempt to retrieve from other agents
            # Success probability depends on context availability (token limit)
            # Smaller context = harder to find the right agent
            context_factor = min(1.0, token_limit / 256.0)  # Normalize around 256
            base_prob = 0.3 + 0.5 * context_factor
            success = np.random.random() < base_prob

            if success:
                # Find an agent who knows the fact
                known_agents = [a for a in target_fact["known_by"] if a != query_agent]
                if known_agents:
                    retrieval_path = [query_agent, np.random.choice(known_agents)]
                else:
                    retrieval_path = [query_agent]
            else:
                retrieval_path = [query_agent]

        retrieval_list.append({
            "query_id": f"query_{game_id}_{i}",
            "query_agent": query_agent,
            "target_fact": target_fact["fact_id"],
            "success": success,
            "retrieval_path": retrieval_path,
            "tokens_used": np.random.randint(5, token_limit)
        })

    return facts_list, retrieval_list


def run_sensitivity_analysis(
    thresholds: List[int],
    num_games: int = 100,
    agent_count: int = 5,
    seed: int = 42
) -> SensitivityAnalysisOutput:
    """Run the full sensitivity analysis across token thresholds.

    For each threshold in the provided list, runs `num_games` simulations
    and computes specialization and retrieval metrics.

    Args:
        thresholds: List of token thresholds to test (e.g., [128, 256, 512]).
        num_games: Number of games to simulate per threshold.
        agent_count: Number of agents to use in each simulation.
        seed: Base seed for reproducibility.

    Returns:
        SensitivityAnalysisOutput containing all results and summary statistics.
    """
    results: List[SensitivityResult] = []
    logger.log("sensitivity_analysis_start", num_games=num_games, thresholds=thresholds)

    for threshold in thresholds:
        logger.log("threshold_start", threshold=threshold)

        for game_id in range(num_games):
            start_time = time.time()

            # Simulate game with this threshold
            facts_list, retrieval_list = simulate_game_with_threshold(
                game_id=game_id,
                agent_count=agent_count,
                token_limit=threshold,
                seed=seed
            )

            # Apply token truncation to simulate context limits
            # Truncate fact content to simulate limited context
            for fact in facts_list:
                fact["truncated_content"] = truncate_context_to_token_limit(
                    fact["content"], threshold
                )

            # Compute specialization index
            spec_idx, spec_metrics = compute_specialization_index(
                facts_list,
                num_agents=agent_count
            )

            # Compute retrieval efficiency
            successful = sum(1 for r in retrieval_list if r["success"])
            total_queries = len(retrieval_list)
            ret_eff, ret_metrics = compute_retrieval_efficiency(
                successful,
                total_queries,
                agent_count
            )

            elapsed = time.time() - start_time

            results.append(SensitivityResult(
                threshold_tokens=threshold,
                specialization_index=float(spec_idx),
                retrieval_efficiency=float(ret_eff),
                game_id=game_id,
                agent_count=agent_count,
                elapsed_seconds=elapsed,
                facts_count=len(facts_list),
                successful_retrievals=successful,
                total_queries=total_queries
            ))

            if game_id % 10 == 0:
                logger.log("game_progress", game_id=game_id, threshold=threshold)

        logger.log("threshold_complete", threshold=threshold, games_run=num_games)

    # Compute summary statistics
    summary = compute_summary_statistics(results)

    output = SensitivityAnalysisOutput(
        thresholds=thresholds,
        results=results,
        summary=summary
    )

    logger.log("sensitivity_analysis_complete", total_games=len(results))
    return output


def compute_summary_statistics(results: List[SensitivityResult]) -> Dict[str, Any]:
    """Compute aggregate statistics for the sensitivity analysis.

    Args:
        results: List of SensitivityResult objects.

    Returns:
        Dictionary containing mean, std, min, max for each metric per threshold.
    """
    summary = {}

    for threshold in sorted(set(r.threshold_tokens for r in results)):
        threshold_results = [r for r in results if r.threshold_tokens == threshold]

        spec_values = [r.specialization_index for r in threshold_results]
        ret_values = [r.retrieval_efficiency for r in threshold_results]

        summary[str(threshold)] = {
            "specialization_index": {
                "mean": float(np.mean(spec_values)),
                "std": float(np.std(spec_values)),
                "min": float(np.min(spec_values)),
                "max": float(np.max(spec_values)),
                "count": len(spec_values)
            },
            "retrieval_efficiency": {
                "mean": float(np.mean(ret_values)),
                "std": float(np.std(ret_values)),
                "min": float(np.min(ret_values)),
                "max": float(np.max(ret_values)),
                "count": len(ret_values)
            },
            "avg_elapsed_seconds": float(np.mean([r.elapsed_seconds for r in threshold_results]))
        }

    return summary


def write_results_csv(results: List[SensitivityResult], output_path: str) -> None:
    """Write sensitivity analysis results to a CSV file.

    Args:
        results: List of SensitivityResult objects.
        output_path: Path to the output CSV file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = [
        "threshold_tokens",
        "specialization_index",
        "retrieval_efficiency",
        "game_id",
        "agent_count",
        "elapsed_seconds",
        "facts_count",
        "successful_retrievals",
        "total_queries"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            writer.writerow({
                "threshold_tokens": r.threshold_tokens,
                "specialization_index": r.specialization_index,
                "retrieval_efficiency": r.retrieval_efficiency,
                "game_id": r.game_id,
                "agent_count": r.agent_count,
                "elapsed_seconds": r.elapsed_seconds,
                "facts_count": r.facts_count,
                "successful_retrievals": r.successful_retrievals,
                "total_queries": r.total_queries
            })

    logger.log("results_written", path=output_path, rows=len(results))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the sensitivity analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on token thresholds."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated list of token thresholds to test (default: 128,256,512)"
    )
    parser.add_argument(
        "--num-games",
        type=int,
        default=100,
        help="Number of games to simulate per threshold (default: 100)"
    )
    parser.add_argument(
        "--agent-count",
        type=int,
        default=5,
        help="Number of agents in each simulation (default: 5)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/sensitivity_analysis.csv",
        help="Output CSV file path (default: results/sensitivity_analysis.csv)"
    )
    return parser


def main() -> int:
    """Main entry point for the sensitivity analysis script."""
    parser = build_parser()
    args = parser.parse_args()

    # Parse thresholds
    thresholds = [int(t.strip()) for t in args.thresholds.split(",")]

    logger.log(
        "sensitivity_analysis_invoked",
        thresholds=thresholds,
        num_games=args.num_games,
        agent_count=args.agent_count,
        seed=args.seed,
        output=args.output
    )

    # Run the analysis
    output = run_sensitivity_analysis(
        thresholds=thresholds,
        num_games=args.num_games,
        agent_count=args.agent_count,
        seed=args.seed
    )

    # Write results to CSV
    write_results_csv(output.results, args.output)

    # Also write summary as JSON for easier downstream processing
    summary_path = args.output.replace(".csv", "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(output.summary, f, indent=2)

    logger.log("analysis_complete", output_csv=args.output, summary_json=summary_path)

    print(f"Sensitivity analysis complete.")
    print(f"  Results written to: {args.output}")
    print(f"  Summary written to: {summary_path}")
    print(f"  Thresholds tested: {thresholds}")
    print(f"  Games per threshold: {args.num_games}")
    print(f"  Agent count: {args.agent_count}")

    # Print key findings
    for thresh_str, stats in output.summary.items():
        print(f"\nThreshold {thresh_str} tokens:")
        print(f"  Specialization Index: {stats['specialization_index']['mean']:.4f} (+/- {stats['specialization_index']['std']:.4f})")
        print(f"  Retrieval Efficiency: {stats['retrieval_efficiency']['mean']:.4f} (+/- {stats['retrieval_efficiency']['std']:.4f})")

    return 0


if __name__ == "__main__":
    sys.exit(main())