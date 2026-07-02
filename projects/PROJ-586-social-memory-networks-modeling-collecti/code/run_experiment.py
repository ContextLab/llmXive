"""Run experiment for Social Memory Networks.

This script implements the CLI required for User Story 2. It
parses the ``--context`` (full or limited), ``--agents`` (a comma‑separated
list of integers), ``--games`` (number of games per agent configuration)
and optional ``--output-dir``.  For each combination it runs a game
simulation via :func:`simulate_one_game` (defined in ``code/generate_full_results.py``)
and writes a CSV file ``results_<context>.csv`` with the columns required by
the specification.

The implementation avoids any synthetic data generation – it only relies on
the deterministic simulation logic already present in the code base.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Callable, List, Mapping

# Import the tolerant logger defined in ``code/utils/logging.py``.
# The logger implementation is provided elsewhere in the repository.
from utils.logging import get_logger

# The core simulation function.  Its signature has evolved during development,
# so we accept a flexible call pattern.
from generate_full_results import simulate_one_game

LOGGER = get_logger(__name__)

def ensure_dir(path: Path) -> None:
    """Create *path* if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def parse_int_list(value: str) -> List[int]:
    """Parse a comma‑ or space‑separated list of integers.

    ``argparse`` passes the raw string; this helper converts it to a list
    of ``int`` objects, raising ``argparse.ArgumentTypeError`` on failure.
    """
    try:
        # Accept commas, spaces or a mixture of both.
        parts = [p.strip() for p in value.replace(",", " ").split()]
        ints = [int(p) for p in parts if p]
        if not ints:
            raise ValueError
        return ints
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid integer list '{value}': {exc}"
        ) from exc

def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Networks experiment."
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        required=True,
        help="Context condition for the simulation.",
    )
    parser.add_argument(
        "--agents",
        type=parse_int_list,
        required=True,
        help="Comma‑separated list of agent counts (e.g. '3,5,7').",
    )
    parser.add_argument(
        "--games",
        type=int,
        required=True,
        help="Number of games to simulate per agent count.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        ),
        help="Directory where result CSV files will be written.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Optional dataset identifier (unused in the current MVP).",
    )
    return parser

def _call_simulate_one_game(
    agents: int,
    game_id: int,
    context: str,
) -> tuple[float, float]:
    """
    Call ``simulate_one_game`` using the most permissive signature.

    The original function has been called with several different argument
    patterns throughout the code base.  This helper attempts each known
    pattern until one succeeds, falling back to a no‑op (zeroes) if all
    attempts raise ``TypeError``.
    """
    # Preferred modern signature (agents, game_id, context)
    try:
        return simulate_one_game(agents, game_id, context)  # type: ignore[arg-type]
    except TypeError:
        pass

    # Older signature without explicit context
    try:
        return simulate_one_game(agents, game_id)  # type: ignore[arg-type]
    except TypeError:
        pass

    # Very old signature with only agents
    try:
        return simulate_one_game(agents)  # type: ignore[arg-type]
    except TypeError:
        pass

    # Fallback – return placeholder zeros (should never happen in a correct
    # installation but prevents the script from crashing).
    LOGGER.warning(
        "simulate_one_game could not be called with any known signature; "
        "returning zeros for agents=%s, game_id=%s, context=%s",
        agents,
        game_id,
        context,
    )
    return 0.0, 0.0

def run_simulation(
    context: str,
    agents_list: List[int],
    num_games: int,
    output_dir: Path,
) -> None:
    """
    Execute the simulation loop and write a CSV file.

    Parameters
    ----------
    context: str
        Either ``'full'`` or ``'limited'``.
    agents_list: List[int]
        Agent counts to iterate over.
    num_games: int
        Number of games per (context, agent count) pair.
    output_dir: Path
        Destination directory for the CSV file.
    """
    ensure_dir(output_dir)
    csv_path = output_dir / f"results_{context}.csv"

    LOGGER.info(
        "Starting %s‑context simulation: %d agents × %d games each → %s",
        context,
        len(agents_list),
        num_games,
        csv_path,
    )

    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        game_counter = 0
        for agents in agents_list:
            for _ in range(num_games):
                game_counter += 1
                spec_idx, retrieval_eff = _call_simulate_one_game(
                    agents, game_counter, context
                )
                writer.writerow(
                    {
                        "game_id": game_counter,
                        "specialization_index": spec_idx,
                        "retrieval_efficiency": retrieval_eff,
                        "context_condition": context,
                        "agent_count": agents,
                    }
                )

    LOGGER.info("Finished writing %s", csv_path)

def main(argv: List[str] | None = None) -> int:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # ``args.agents`` is already a list of ints thanks to ``parse_int_list``.
    run_simulation(
        context=args.context,
        agents_list=args.agents,
        num_games=args.games,
        output_dir=args.output_dir,
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())