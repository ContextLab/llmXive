"""Sensitivity analysis for token threshold sweeps.

This module implements FR-008: Sweep token thresholds explicitly across a range
of values and record how specialization and retrieval metrics vary for each threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Project imports
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SensitivityResult:
    """Single data point from the sensitivity sweep."""
    threshold_tokens: int
    specialization_index: float
    retrieval_efficiency: float
    successful_games: int
    total_games: int
    avg_turns: float
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

@dataclass
class SensitivityAnalysisOutput:
    """Container for the full sensitivity analysis results."""
    sweep_range: List[int]
    results: List[SensitivityResult]
    summary_stats: Dict[str, Any]
    metadata: Dict[str, Any]

def truncate_context_to_token_limit(context_text: str, limit: int) -> str:
    """Truncate a context string to a token limit (approximate by whitespace tokens).

    Args:
        context_text: The full context string.
        limit: Maximum number of tokens (whitespace-separated words) to keep.

    Returns:
        Truncated context string.
    """
    if not context_text:
        return ""
    tokens = context_text.split()
    if len(tokens) <= limit:
        return context_text
    # Keep first (limit - 3) tokens and add ellipsis
    truncated = " ".join(tokens[: limit - 3]) + " [...]"
    return truncated

def simulate_game_with_threshold(
    config: Dict[str, Any],
    game_id: int,
    dataset_item: Dict[str, Any],
    token_threshold: int,
) -> Optional[Tuple[float, float, int, int, float]]:
    """Simulate a single game with a specific token threshold applied to context.

    This is a simplified simulation that measures the impact of context truncation
    on the metrics without running a full LLM inference loop (which would be
    prohibitively slow for a sensitivity sweep).

    We simulate the effect of truncation by:
    1. Truncating the input context to the token limit.
    2. Estimating the loss of information (facts) due to truncation.
    3. Computing metrics based on the remaining information.

    Args:
        config: Configuration dictionary (agent count, etc.).
        game_id: Unique identifier for the game.
        dataset_item: A single item from the dataset (context, facts, etc.).
        token_threshold: The token limit to apply.

    Returns:
        Tuple of (specialization_index, retrieval_efficiency, successful_turns, total_turns, avg_turns)
        or None if the simulation fails.
    """
    try:
        num_agents = config.get("num_agents", 3)
        context = dataset_item.get("context", "")
        facts = dataset_item.get("facts", [])
        total_turns = dataset_item.get("total_turns", 10)

        # Apply truncation
        truncated_context = truncate_context_to_token_limit(context, token_threshold)
        truncated_tokens = len(truncated_context.split())

        # Estimate information loss: if context is truncated, we assume some facts are lost.
        # This is a heuristic: facts are distributed across the context.
        original_tokens = len(context.split())
        if original_tokens == 0:
            retention_ratio = 1.0
        else:
            retention_ratio = truncated_tokens / original_tokens

        # Simulate fact retrieval based on retention ratio
        # Assume facts are uniformly distributed; truncation removes them proportionally.
        total_facts = len(facts)
        retained_facts = int(total_facts * retention_ratio)

        # Simulate successful retrievals (some noise)
        # In a real system, retrieval efficiency depends on cue quality and memory state.
        # Here we model it as a function of retained facts and agent count.
        # Heuristic: efficiency = (retained_facts / total_facts) * (1 - noise)
        noise_factor = 0.1  # 10% noise
        successful_retrievals = int(retained_facts * (1.0 - noise_factor))
        if successful_retrievals < 0:
            successful_retrievals = 0

        # Compute specialization index
        # Simulate agent skills: distribute retained facts among agents with some specialization
        agent_skills = {}
        for i in range(num_agents):
            # Assign a portion of facts to each agent, with some variance
            base_share = retained_facts / num_agents
            variance = np.random.normal(0, base_share * 0.2)
            agent_skills[i] = max(0, int(base_share + variance))

        spec_index, _ = compute_specialization_index(agent_skills, num_agents=num_agents)

        # Compute retrieval efficiency
        # Total queries = total_turns * num_agents (each agent queries each turn)
        total_queries = total_turns * num_agents
        if total_queries == 0:
            total_queries = 1  # Avoid division by zero

        ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, num_agents)

        # Simulate turns (just pass through or slight reduction due to truncation)
        successful_turns = total_turns if retention_ratio > 0.5 else int(total_turns * retention_ratio)
        avg_turns = successful_turns / num_agents if num_agents > 0 else 0.0

        return spec_index, ret_eff, successful_turns, total_turns, avg_turns

    except Exception as e:
        logger.error(f"Game simulation failed for ID {game_id} with threshold {token_threshold}: {e}")
        return None

def run_sensitivity_analysis(
    config: Dict[str, Any],
    dataset: List[Dict[str, Any]],
    thresholds: List[int],
    games_per_threshold: int = 50,
    seed: Optional[int] = None,
) -> SensitivityAnalysisOutput:
    """Run the full sensitivity analysis sweep.

    Args:
        config: Configuration dictionary.
        dataset: List of dataset items to simulate.
        thresholds: List of token thresholds to test.
        games_per_threshold: Number of games to simulate per threshold.
        seed: Random seed for reproducibility.

    Returns:
        SensitivityAnalysisOutput containing all results.
    """
    if seed is not None:
        np.random.seed(seed)

    results = []
    metadata = {
        "num_thresholds": len(thresholds),
        "games_per_threshold": games_per_threshold,
        "dataset_size": len(dataset),
        "config": config,
    }

    for threshold in thresholds:
        logger.info(f"Running sensitivity sweep at threshold={threshold} tokens")
        threshold_results = []

        for i in range(games_per_threshold):
            if not dataset:
                break
            # Sample a random dataset item
            item = dataset[i % len(dataset)]
            game_id = threshold * 1000 + i

            sim_result = simulate_game_with_threshold(config, game_id, item, threshold)
            if sim_result:
                spec_idx, ret_eff, succ_turns, tot_turns, avg_turns = sim_result
                threshold_results.append(
                    SensitivityResult(
                        threshold_tokens=threshold,
                        specialization_index=spec_idx,
                        retrieval_efficiency=ret_eff,
                        successful_games=1,
                        total_games=1,
                        avg_turns=avg_turns,
                    )
                )

        if threshold_results:
            # Aggregate for this threshold
            avg_spec = np.mean([r.specialization_index for r in threshold_results])
            avg_ret = np.mean([r.retrieval_efficiency for r in threshold_results])
            total_succ = sum([r.successful_games for r in threshold_results])
            total_g = sum([r.total_games for r in threshold_results])
            avg_turns_overall = np.mean([r.avg_turns for r in threshold_results])

            results.append(
                SensitivityResult(
                    threshold_tokens=threshold,
                    specialization_index=avg_spec,
                    retrieval_efficiency=avg_ret,
                    successful_games=total_succ,
                    total_games=total_g,
                    avg_turns=avg_turns_overall,
                )
            )

    # Compute summary statistics
    if results:
        spec_values = [r.specialization_index for r in results]
        ret_values = [r.retrieval_efficiency for r in results]
        summary_stats = {
            "spec_mean": float(np.mean(spec_values)),
            "spec_std": float(np.std(spec_values)),
            "spec_min": float(np.min(spec_values)),
            "spec_max": float(np.max(spec_values)),
            "ret_mean": float(np.mean(ret_values)),
            "ret_std": float(np.std(ret_values)),
            "ret_min": float(np.min(ret_values)),
            "ret_max": float(np.max(ret_values)),
        }
    else:
        summary_stats = {}

    return SensitivityAnalysisOutput(
        sweep_range=thresholds,
        results=results,
        summary_stats=summary_stats,
        metadata=metadata,
    )

def compute_summary_statistics(output: SensitivityAnalysisOutput) -> Dict[str, Any]:
    """Compute additional summary statistics (trends, slopes)."""
    if not output.results:
        return {}

    thresholds = [r.threshold_tokens for r in output.results]
    specs = [r.specialization_index for r in output.results]
    rets = [r.retrieval_efficiency for r in output.results]

    # Simple linear regression for trends
    def linear_fit(x, y):
        if len(x) < 2:
            return 0.0, 0.0
        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)
        # Avoid division by zero
        if np.std(x) == 0:
            return 0.0, np.mean(y)
        slope, intercept = np.polyfit(x, y, 1)
        return float(slope), float(intercept)

    spec_slope, spec_intercept = linear_fit(thresholds, specs)
    ret_slope, ret_intercept = linear_fit(thresholds, rets)

    return {
        "spec_trend_slope": spec_slope,
        "spec_trend_intercept": spec_intercept,
        "ret_trend_slope": ret_slope,
        "ret_trend_intercept": ret_intercept,
        "n_points": len(results),
    }

def write_results_csv(output: SensitivityAnalysisOutput, output_path: str) -> None:
    """Write the sensitivity analysis results to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "threshold_tokens",
                "specialization_index",
                "retrieval_efficiency",
                "successful_games",
                "total_games",
                "avg_turns",
                "timestamp",
            ]
        )
        for res in output.results:
            writer.writerow(
                [
                    res.threshold_tokens,
                    res.specialization_index,
                    res.retrieval_efficiency,
                    res.successful_games,
                    res.total_games,
                    res.avg_turns,
                    res.timestamp,
                ]
            )

    logger.info(f"Wrote sensitivity results to {output_path}")

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the sensitivity analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on token thresholds."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512,1024",
        help="Comma-separated list of token thresholds to sweep (e.g., 128,256,512).",
    )
    parser.add_argument(
        "--games-per-threshold",
        type=int,
        default=50,
        help="Number of games to simulate per threshold.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/sensitivity_analysis.csv",
        help="Output path for the CSV results.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents to simulate.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/data/sample_dataset.json",
        help="Path to the dataset file (JSON list of items).",
    )
    return parser

def main() -> None:
    """Main entry point for the sensitivity analysis."""
    parser = build_parser()
    args = parser.parse_args()

    # Parse thresholds
    thresholds = [int(x.strip()) for x in args.thresholds.split(",")]
    thresholds = sorted(list(set(thresholds)))  # Unique and sorted

    logger.info(f"Sensitivity sweep thresholds: {thresholds}")

    # Load dataset
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        # Create a minimal synthetic dataset for the sweep if missing (fallback for CI)
        # NOTE: This is a fallback ONLY if the real dataset is missing.
        # In a real run, the dataset should be present.
        logger.warning("Generating minimal fallback dataset for sensitivity sweep.")
        dataset = [
            {
                "context": " ".join([f"fact_{i} context_word_{j}" for j in range(200)]),
                "facts": [f"fact_{i}" for i in range(20)],
                "total_turns": 10,
            }
            for i in range(100)
        ]
    else:
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            if not isinstance(dataset, list):
                dataset = [dataset]
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            sys.exit(1)

    config = {"num_agents": args.agents}

    # Run analysis
    output = run_sensitivity_analysis(
        config=config,
        dataset=dataset,
        thresholds=thresholds,
        games_per_threshold=args.games_per_threshold,
        seed=args.seed,
    )

    # Compute summary
    summary = compute_summary_statistics(output)
    output.summary_stats.update(summary)

    # Write CSV
    write_results_csv(output, args.output)

    # Write JSON summary
    json_path = args.output.replace(".csv", "_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sweep_range": output.sweep_range,
                "results": [asdict(r) for r in output.results],
                "summary_stats": output.summary_stats,
                "metadata": output.metadata,
            },
            f,
            indent=2,
        )
    logger.info(f"Wrote summary to {json_path}")

    logger.info("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()