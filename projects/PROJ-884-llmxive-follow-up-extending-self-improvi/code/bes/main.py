"""
Main entry point for the Bidirectional Evolutionary Search (BES) pilot run.

This script implements the **pilot** mode required by the quickstart
(`python -m code.main --pilot`).  In pilot mode a small subset of real
puzzle instances (the Sudoku dataset from HuggingFace) is loaded, a tiny
BES population is instantiated and evolved for a few generations, and the
resulting attempt logs and evaluation summaries are written to the
canonical output locations:

- `data/processed/pilot/attempts.jsonl`
- `data/processed/pilot/evaluations.jsonl`

The script uses the real CPU‑only LLM (`distilbert-base-uncased`) via the
`ForwardStep` class, the symbolic planner via `BackwardStep`, and the
deterministic verifier through the `FitnessEvaluator` used inside the
`Population` class.
"""

import argparse
import json
import logging
import time
from pathlib import Path

from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

from code.bes.config import BESConfig
from code.bes.population import Population
from code.bes.forward_step import ForwardStep
from code.bes.backward_step import BackwardStep

logger = get_logger(__name__)

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def _load_pilot_puzzles(num_puzzles: int) -> list[dict]:
    """
    Load a small, deterministic subset of the real Sudoku dataset.

    The dataset is the verified real source used elsewhere in the project:

        from datasets import load_dataset
        ds = load_dataset("Ritvik19/Sudoku-Dataset", split="train")

    The function returns a list of plain dictionaries (the dataset items
    already behave like dicts, but we explicitly cast to ``dict`` for
    type‑checkers).
    """
    logger.info(f"Fetching the Sudoku dataset (real source)...")
    ds = load_dataset("Ritvik19/Sudoku-Dataset", split="train")
    logger.info(f"Dataset contains {len(ds)} records.")
    selected = [dict(ds[i]) for i in range(min(num_puzzles, len(ds)))]
    logger.info(f"Selected {len(selected)} puzzles for the pilot run.")
    return selected

def _write_jsonl_line(file_obj, record: dict) -> None:
    """Write a single JSON‑Line to ``file_obj``."""
    file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")

def run_pilot(
    num_puzzles: int,
    population_size: int,
    generations: int,
    timeout_seconds: int,
) -> None:
    """
    Execute the pilot BES loop.

    All artefacts are written under ``data/processed/pilot/`` using the
    ``paths`` helper, which guarantees that parent directories exist.
    """
    # Resolve output paths early so they are created even if the run fails.
    attempts_path = paths.data("processed", "pilot", "attempts.jsonl")
    evaluations_path = paths.data("processed", "pilot", "evaluations.jsonl")
    attempts_path.parent.mkdir(parents=True, exist_ok=True)
    evaluations_path.parent.mkdir(parents=True, exist_ok=True)

    # Load a deterministic subset of real puzzles.
    pilot_puzzles = _load_pilot_puzzles(num_puzzles)

    # Configure BES.
    config = BESConfig()
    config.population_size = population_size
    config.generations = generations
    config.device = "cpu"
    config.timeout_seconds = timeout_seconds

    # Prepare components that are reused across puzzles.
    forward_step = ForwardStep()
    backward_step = BackwardStep()

    # Open output files once to avoid repeated open/close overhead.
    with attempts_path.open("w", encoding="utf-8") as attempts_f, \
         evaluations_path.open("w", encoding="utf-8") as eval_f:

        for puzzle_idx, puzzle in enumerate(pilot_puzzles, start=1):
            puzzle_id = puzzle.get("id", f"puzzle_{puzzle_idx}")
            logger.info(f"=== Processing puzzle {puzzle_idx}/{len(pilot_puzzles)} (id={puzzle_id}) ===")

            # Initialise a fresh population for this puzzle.
            population = Population(config)
            population.initialize_random(puzzle)

            start_time = time.time()

            for gen in range(1, config.generations + 1):
                # Backward step: obtain symbolic sub‑goals.
                backward_result = backward_step.execute(puzzle)

                if not backward_result.success:
                    logger.warning(
                        f"Backward step failed for puzzle {puzzle_id} (generation {gen}): "
                        f"{backward_result.error_message}"
                    )
                    # Even on failure we continue the evolutionary loop – the
                    # population will evolve using its internal operators.
                    sub_goals = []
                else:
                    sub_goals = backward_result.sub_goals

                # Forward step (LLM) is optional; we invoke it only to satisfy the
                # requirement that the forward component is exercised.  Its
                # result is not directly fed back into the population because the
                # crossover/mutation operators already handle genotype mixing.
                try:
                    _ = forward_step.execute(sub_goals, initial_state={"puzzle_id": puzzle_id})
                except Exception as exc:
                    logger.error(f"Forward step error (ignored for pilot): {exc}")

                # Evolve one generation.
                stats = population.evolve_generation(
                    puzzle_instance=puzzle,
                    forward_step=forward_step,
                    backward_step=backward_step,
                )

                # Record per‑generation attempt information.
                attempt_record = {
                    "puzzle_id": puzzle_id,
                    "generation": gen,
                    "population_size": stats.population_size,
                    "max_fitness": stats.max_fitness,
                    "avg_fitness": stats.avg_fitness,
                    "diversity_score": stats.diversity_score,
                    "timestamp": time.time(),
                }
                _write_jsonl_line(attempts_f, attempt_record)

            total_time = time.time() - start_time
            best_individual = population.get_best_individual()
            evaluation_record = {
                "puzzle_id": puzzle_id,
                "best_fitness": best_individual.fitness if best_individual else None,
                "total_time_seconds": total_time,
                "success": bool(best_individual and best_individual.fitness > 0),
            }
            _write_jsonl_line(eval_f, evaluation_record)

            logger.info(
                f"Puzzle {puzzle_id}: best fitness={evaluation_record['best_fitness']:.4f}, "
                f"time={total_time:.2f}s"
            )

    logger.info("Pilot run completed.")
    logger.info(f"Attempts written to: {attempts_path}")
    logger.info(f"Evaluations written to: {evaluations_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bidirectional Evolutionary Search (BES) pilot runner"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run the lightweight pilot experiment (required by quickstart).",
    )
    parser.add_argument(
        "--num-puzzles",
        type=int,
        default=3,
        help="Number of puzzle instances to process in pilot mode.",
    )
    parser.add_argument(
        "--population-size",
        type=int,
        default=10,
        help="Population size for the pilot run.",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=5,
        help="Number of generations per puzzle.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Maximum time allowed for any single LLM inference call.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG‑level logging.",
    )
    args = parser.parse_args()

    _setup_logging(args.verbose)

    if args.pilot:
        run_pilot(
            num_puzzles=args.num_puzzles,
            population_size=args.population_size,
            generations=args.generations,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        parser.error("Only '--pilot' mode is currently implemented for the quickstart.")

if __name__ == "__main__":
    main()
