"""
BES Main Entry Point
--------------------

This script provides a minimal, reproducible pilot execution of the
Bidirectional Evolutionary Search (BES) framework.  It is invoked by the
quick‑start command:

    python -m code.bes.main --pilot

The pilot run uses a tiny synthetic puzzle, runs a configurable number of
generations, and writes two JSON‑Lines files to the standard output
location:

* ``data/processed/pilot/attempts.jsonl`` – one line per individual
  (id, genotype, fitness, generation).
* ``data/processed/pilot/evaluations.jsonl`` – one line per generation
  with summary statistics (generation, best_fitness, avg_fitness,
  diversity_score, elite_count).

The implementation relies only on the existing BES components
(``Population``, ``ForwardStep``, ``BackwardStep`` and ``BESConfig``) and
the ``llmxive_toolkit`` path helpers for deterministic file placement.
All heavy‑weight components (e.g., the LLM model) are loaded lazily; for
the pilot we skip the forward‑step entirely to keep runtime well under the
CI limits.

The script is deliberately lightweight and side‑effect free when
imported – the evolutionary loop runs **only** when the module is executed
as ``__main__`` or when the ``run_pilot`` function is called explicitly.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List

# Project‑local imports
from code.bes.population import Population
from code.bes.forward_step import ForwardStep  # noqa: F401 (imported for completeness)
from code.bes.backward_step import BackwardStep  # noqa: F401
from code.bes.config import BESConfig

# Toolkit helpers for deterministic paths
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_jsonl(path: Path, records: List[Dict]) -> None:
    """
    Write a list of dictionaries to *path* as JSON‑Lines.
    The parent directory is created automatically.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f)
            f.write("\n")
    log.info(f"Wrote {len(records)} records to {path}")

def _create_dummy_puzzle() -> Dict:
    """
    Return a minimal puzzle definition sufficient for the symbolic planner.
    The exact fields are not important for the pilot – they only need to be
    JSON‑serialisable and contain an ``id``.
    """
    return {
        "id": "pilot_puzzle_001",
        "type": "logic",
        "constraints": ["A != B", "B != C"],
        "initial_state": {"A": None, "B": None, "C": None},
        "target_state": {"A": 1, "B": 2, "C": 3}
    }

def run_pilot(generations: int = 3,
              population_size: int = 10,
              output_dir: Path = None) -> None:
    """
    Execute a tiny BES pilot run.

    Parameters
    ----------
    generations : int
        Number of evolutionary generations to simulate.
    population_size : int
        Size of the initial random population.
    output_dir : pathlib.Path, optional
        Directory under ``data/processed`` where pilot artefacts are stored.
        If ``None`` the default pilot directory is used.
    """
    # Resolve output locations
    if output_dir is None:
        output_dir = paths.data("processed", "pilot")
    attempts_path = output_dir / "attempts.jsonl"
    evaluations_path = output_dir / "evaluations.jsonl"

    # ------------------------------------------------------------------
    # 1. Load configuration (defaults are fine for the pilot)
    # ------------------------------------------------------------------
    try:
        config = BESConfig()  # uses built‑in defaults
    except Exception as exc:
        log.error(f"Failed to initialise BESConfig: {exc}")
        sys.exit(1)

    # Override population size for the pilot
    config.population_size = population_size

    # ------------------------------------------------------------------
    # 2. Initialise population with a dummy puzzle
    # ------------------------------------------------------------------
    puzzle = _create_dummy_puzzle()
    pop = Population(config)
    pop.initialize_random(puzzle)

    # ------------------------------------------------------------------
    # 3. Run the evolutionary loop
    # ------------------------------------------------------------------
    attempts_records: List[Dict] = []
    evaluations_records: List[Dict] = []

    for gen in range(1, generations + 1):
        start = time.time()
        # In the pilot we do **not** invoke the forward/backward steps;
        # the population evolves purely via selection, crossover and
        # mutation (which are deterministic/random but cheap).
        stats = pop.evolve_generation(puzzle)
        elapsed = time.time() - start

        # Record per‑individual data
        for ind in pop.individuals:
            attempts_records.append({
                "generation": gen,
                "individual_id": ind.id,
                "fitness": ind.fitness,
                "genotype": ind.genotype,
                "metadata": ind.metadata,
                "is_elite": ind.is_elite
            })

        # Record generation‑level summary
        evaluations_records.append({
            "generation": gen,
            "best_fitness": stats.max_fitness,
            "avg_fitness": stats.avg_fitness,
            "diversity_score": stats.diversity_score,
            "elite_count": stats.elite_count,
            "generation_time_s": elapsed
        })

        log.info(
            f"Generation {gen}: best={stats.max_fitness:.4f}, "
            f"avg={stats.avg_fitness:.4f}, elites={stats.elite_count}"
        )

    # ------------------------------------------------------------------
    # 4. Persist results
    # ------------------------------------------------------------------
    _write_jsonl(attempts_path, attempts_records)
    _write_jsonl(evaluations_path, evaluations_records)

    log.info("Pilot BES run completed successfully.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pilot execution of the Bidirectional Evolutionary Search (BES)."
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=3,
        help="Number of generations to run (default: 3)"
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=10,
        help="Population size for the pilot run (default: 10)"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run in pilot mode (default when script is executed directly)"
    )
    args = parser.parse_args()

    if args.pilot:
        run_pilot(generations=args.generations, population_size=args.pop_size)
    else:
        # If the script is invoked without ``--pilot`` we still perform a
        # minimal run so that ``python -m code.bes.main`` never exits with
        # an error code.
        log.info("Running default pilot (no explicit --pilot flag).")
        run_pilot()

if __name__ == "__main__":
    # When executed as a module ``python -m code.bes.main`` the
    # ``__name__`` is ``code.bes.main``; we still want the same behaviour
    # as a direct script execution.
    main()