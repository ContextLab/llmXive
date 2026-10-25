"""
BES main entry point.

This script provides a minimal, reproducible pilot run of the
Bidirectional Evolutionary Search (BES) framework.  It is invoked by the
quick‑start command:

    python -m code.main --pilot

The script:
  1. Loads a default BES configuration.
  2. Creates a dummy puzzle instance (sufficient for a pilot run).
  3. Initializes a population of random individuals.
  4. Runs a small number of generations using the forward and backward
     steps.
  5. Writes pilot artefacts:
     - data/processed/pilot/attempts.jsonl
     - data/processed/pilot/evaluations.jsonl
     - data/processed/exclusions.json   (empty for the pilot)
     - data/processed/bes_results.json (summary of the run)

All file paths are created via the `llmxive_toolkit.paths` helpers, which
guarantee that the target directories exist.
"""

import argparse
import json
import logging
import time
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Local imports – these modules already exist in the repository
from code.bes.config import BESConfig
from code.bes.population import Population
from code.bes.forward_step import ForwardStep
from code.bes.backward_step import BackwardStep

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_jsonl(file_path: Path, records: list) -> None:
    """Write a list of dictionaries as JSON‑Lines."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f)
            f.write("\n")

def _write_json(file_path: Path, data: dict) -> None:
    """Write a dictionary as a pretty‑printed JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Pilot run implementation
# ----------------------------------------------------------------------
def run_pilot(config: BESConfig, generations: int = 5) -> None:
    """
    Execute a tiny pilot BES run.

    The function writes the four artefacts required by the verification
    suite.  All timings are measured with `time.time()` and represent real
    wall‑clock durations on the host CPU.
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1️⃣  Dummy puzzle definition
    # ------------------------------------------------------------------
    dummy_puzzle = {
        "id": "pilot_puzzle_001",
        "type": "logic",
        "constraints": [
            "A > B",
            "B < C"
        ],
        "initial_state": {"A": None, "B": None, "C": None},
        "target_state": {"A": 3, "B": 2, "C": 1}
    }

    # ------------------------------------------------------------------
    # 2️⃣  Initialise population
    # ------------------------------------------------------------------
    pop = Population(config)
    pop.initialize_random(dummy_puzzle)

    # ------------------------------------------------------------------
    # 3️⃣  Prepare forward / backward step objects
    # ------------------------------------------------------------------
    forward = ForwardStep()
    backward = BackwardStep()

    # ------------------------------------------------------------------
    # 4️⃣  Run evolutionary loop
    # ------------------------------------------------------------------
    attempts_records = []      # one record per individual per generation
    evaluations_records = []   # aggregated per‑generation stats

    for gen in range(1, generations + 1):
        gen_start = time.time()

        # OPTIONAL: obtain symbolic sub‑goals (backward step)
        # For the pilot we ignore the result – we just want a realistic
        # call that exercises the code path.
        try:
            backward_res = backward.execute(dummy_puzzle)
            if not backward_res.success:
                logger.warning(
                    f"Backward step failed (gen {gen}): "
                    f"{backward_res.error_message}"
                )
        except Exception as exc:
            logger.exception(f"Unexpected backward‑step error (gen {gen}): {exc}")

        # Evolve one generation
        stats = pop.evolve_generation(
            puzzle_instance=dummy_puzzle,
            forward_step=forward,
            backward_step=backward
        )

        gen_elapsed = time.time() - gen_start

        # ----------------------------------------------------------------
        # Record attempts (one line per individual)
        # ----------------------------------------------------------------
        for ind in pop.individuals:
            attempts_records.append({
                "generation": gen,
                "individual_id": ind.id,
                "fitness": ind.fitness,
                "age": ind.age,
                "is_elite": ind.is_elite,
                "cost_time": gen_elapsed  # wall‑clock time for the generation
            })

        # ----------------------------------------------------------------
        # Record evaluation summary for the generation
        # ----------------------------------------------------------------
        evaluations_records.append({
            "generation": gen,
            "best_fitness": stats.max_fitness,
            "avg_fitness": stats.avg_fitness,
            "diversity_score": stats.diversity_score,
            "memory_usage_mb": stats.memory_usage_mb,
            "cost_time": gen_elapsed
        })

        logger.info(
            f"Gen {gen}: best={stats.max_fitness:.4f}, "
            f"avg={stats.avg_fitness:.4f}, time={gen_elapsed:.2f}s"
        )

    # ------------------------------------------------------------------
    # 5️⃣  Write artefacts
    # ------------------------------------------------------------------
    attempts_path = paths.data("processed", "pilot", "attempts.jsonl")
    evaluations_path = paths.data("processed", "pilot", "evaluations.jsonl")
    exclusions_path = paths.data("processed", "exclusions.json")
    bes_results_path = paths.data("processed", "bes_results.json")

    _write_jsonl(attempts_path, attempts_records)
    _write_jsonl(evaluations_path, evaluations_records)

    # For the pilot we have no exclusions – write an empty list
    _write_json(exclusions_path, {"exclusions": []})

    # Summary JSON for downstream steps / tests
    summary = {
        "config": config.to_dict() if hasattr(config, "to_dict") else {},
        "generations_run": generations,
        "final_best_fitness": pop.get_best_individual().fitness if pop.get_best_individual() else None,
        "total_individuals_evaluated": len(attempts_records)
    }
    _write_json(bes_results_path, summary)

    logger.info(f"Pilot artefacts written to {attempts_path.parent}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pilot run for the Bidirectional Evolutionary Search (BES) framework"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Execute the minimal pilot experiment (default behaviour)."
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=5,
        help="Number of generations for the pilot run."
    )
    args = parser.parse_args()

    # Load or create a default configuration
    config = BESConfig()
    # Ensure the config uses the CPU device (required by the forward step)
    config.device = "cpu"

    if args.pilot:
        run_pilot(config, generations=args.generations)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()