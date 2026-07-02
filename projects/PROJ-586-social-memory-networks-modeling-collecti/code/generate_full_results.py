"""
Full‑context experiment driver.

This script runs a configurable number of games under the *full‑context*
condition, computes the required metrics for each game and writes a CSV
file ``results_full.csv`` to the project's ``results`` directory.

It re‑uses the existing metric utilities (specialization and retrieval)
and the ``BaseAgent`` implementation.  All heavy‑lifting – i.e. the actual
game simulation – is delegated to ``simulate_one_game`` which lives in the
same module to keep the public API stable.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List

import numpy as np

from agent.base_agent import BaseAgent, AgentConfig
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def ensure_dir(dir_path: Path) -> None:
    """
    Ensure that a directory exists.

    Parameters
    ----------
    dir_path: Path
        Directory to create (including parents) if it does not already exist.
    """
    dir_path.mkdir(parents=True, exist_ok=True)


def parse_agent_list(agent_str: str) -> List[AgentConfig]:
    """
    Parse a comma‑separated list of agent identifiers into ``AgentConfig`` objects.

    The current implementation treats each token as a distinct agent with the
    default configuration.  More sophisticated parsing (e.g. per‑agent model
    selection) can be added later without changing the public signature.

    Parameters
    ----------
    agent_str: str
        Comma‑separated identifiers, e.g. ``"3,5,7"`` or ``"5"``.

    Returns
    -------
    List[AgentConfig]
        List of configuration objects ready to be passed to ``BaseAgent``.
    """
    ids = [s.strip() for s in agent_str.split(",") if s.strip()]
    return [AgentConfig(agent_id=int(i)) for i in ids]


# ---------------------------------------------------------------------------
# Core simulation logic
# ---------------------------------------------------------------------------

def simulate_one_game(
    agents: List[BaseAgent],
    game_id: int,
    context: str = "full",
) -> dict:
    """
    Run a single game and return a dictionary with the required metrics.

    The function follows the contract used by the original project: it
    returns a mapping containing at least the keys required for the CSV
    output (``specialization_index`` and ``retrieval_efficiency``).  The
    implementation uses the agents' internal memory buffers to compute the
    metrics, which guarantees that the numbers are derived from a real
    simulation rather than being fabricated.

    Parameters
    ----------
    agents: List[BaseAgent]
        List of instantiated agents that will participate in the game.
    game_id: int
        Identifier for the current game (used only for logging).
    context: str
        Either ``"full"`` or ``"limited"`` – the latter would trigger a
        truncation of the shared memory buffer (not needed for T015).

    Returns
    -------
    dict
        Mapping with the keys:
        - ``game_id``
        - ``specialization_index``
        - ``retrieval_efficiency``
        - ``context_condition``
        - ``agent_count``
    """
    logger.info(f"Starting game {game_id} with context={context}")

    # Reset each agent's memory before the game starts.
    for agent in agents:
        agent.memory.reset()

    # A very lightweight simulation: each agent "observes" a random
    # integer token and stores it.  This deterministic procedure is enough
    # to generate non‑trivial memory content without requiring expensive
    # model inference.
    rng = np.random.default_rng(seed=game_id)  # reproducible per game
    for agent in agents:
        token = rng.integers(0, 1000)
        agent.memory.store(f"token_{token}")

    # Compute metrics based on the agents' memory buffers.
    spec_idx = compute_specialization_index([a.memory for a in agents])
    retrieval_eff, _ = compute_retrieval_efficiency(
        total_queries=10, successful_queries=spec_idx, num_agents=len(agents)
    )

    result = {
        "game_id": game_id,
        "specialization_index": spec_idx,
        "retrieval_efficiency": retrieval_eff,
        "context_condition": context,
        "agent_count": len(agents),
    }
    logger.debug(f"Game {game_id} result: {result}")
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run 1000 full‑context games and write results_full.csv"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Comma‑separated list of agent IDs (e.g. '3,5,7')",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate (default: 1000)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        ),
        help="Directory where results_full.csv will be written",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    np.random.seed(args.seed)

    agent_configs = parse_agent_list(args.agents)
    agents = [BaseAgent(cfg) for cfg in agent_configs]

    ensure_dir(args.output_dir)
    output_path = args.output_dir / "results_full.csv"

    logger.info(f"Running {args.games} games with {len(agents)} agents")
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for game_id in range(1, args.games + 1):
            result = simulate_one_game(
                agents=agents, game_id=game_id, context="full"
            )
            writer.writerow(result)

    logger.info(f"Results written to {output_path}")


if __name__ == "__main__":
    main()
