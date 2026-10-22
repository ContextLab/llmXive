"""
Main BES (Bidirectional Evolutionary Search) Loop Orchestrator.

Provides two modes:
  * Full scaling analysis (default) – iterates N=10..500.
  * Pilot run (`--pilot`) – a single small puzzle to verify the pipeline.

The script can be invoked as a module:
    python -m code.main [options]
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from dataclasses import asdict

# Local imports – use package-relative paths
from code.dataset.generator import PuzzleGenerator, PuzzleInstance
from code.dataset.verifier import PuzzleVerifier, SolutionResult, ErrorCodes
from code.bes.forward_step import ForwardStep
from code.bes.backward_step import BackwardStep
from code.bes.population import Population, Individual
from code.symbolic.planner import SymbolicPlanner
from code.exceptions import BaseResearchException, PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR

# Utility for path creation
from llmxive_toolkit import paths


class BESRunResult:
    """Container for the results of a single BES run."""
    def __init__(
        self,
        experiment_id: str,
        puzzle_id: str,
        complexity_n: int,
        population_size: int,
        generations: int,
        success: bool,
        final_score: float,
        total_time_seconds: float,
        forward_calls: int,
        backward_calls: int,
        failure_reasons: list,
        log_entries: list,
    ):
        self.experiment_id = experiment_id
        self.puzzle_id = puzzle_id
        self.complexity_n = complexity_n
        self.population_size = population_size
        self.generations = generations
        self.success = success
        self.final_score = final_score
        self.total_time_seconds = total_time_seconds
        self.forward_calls = forward_calls
        self.backward_calls = backward_calls
        self.failure_reasons = failure_reasons
        self.log_entries = log_entries

    def asdict(self):
        """Return a plain‑dict representation for JSON serialisation."""
        return {
            "experiment_id": self.experiment_id,
            "puzzle_id": self.puzzle_id,
            "complexity_n": self.complexity_n,
            "population_size": self.population_size,
            "generations": self.generations,
            "success": self.success,
            "final_score": self.final_score,
            "total_time_seconds": self.total_time_seconds,
            "forward_calls": self.forward_calls,
            "backward_calls": self.backward_calls,
            "failure_reasons": self.failure_reasons,
            "log_entries": self.log_entries,
        }


class BESOrchestrator:
    """
    Orchestrates the Bidirectional Evolutionary Search loop.
    
    Coordinates the forward step (LLM) and backward step (Symbolic Planner)
    over a population of solutions for a given puzzle instance.
    """

    def __init__(self, config: dict, seed: int):
        self.config = config
        self.seed = seed
        self.experiment_id = f"run_{int(time.time())}"
        self.logger = logging.getLogger("BESOrchestrator")

        # Forward and backward components
        self.forward_step = ForwardStep(
            model_name=config.get("forward_model", "distilbert-base-uncased"),
            device="cpu",
            temperature=config.get("temperature", 0.7),
        )

        self.backward_step = BackwardStep(
            planner=SymbolicPlanner(),
            verifier=PuzzleVerifier(),
        )

        self.population_size = config.get("population_size", 20)
        self.generations = config.get("generations", 50)

    def run_single_puzzle(self, puzzle: PuzzleInstance) -> BESRunResult:
        """
        Execute the BES loop for a single puzzle instance.
        
        Returns:
            BESRunResult with execution statistics.
        """
        start_time = time.time()
        forward_calls = 0
        backward_calls = 0
        failure_reasons = []
        log_entries = []

        # Initialise a minimal population (using the Population class defined elsewhere)
        population = Population(
            size=self.population_size,
            puzzle=puzzle,
            seed=self.seed,
        )

        best_individual = None
        best_score = -float("inf")

        for gen in range(self.generations):
            # --- Backward step: evaluate current individuals ---
            for ind in population.individuals:
                result = self.backward_step.verify(ind.solution, puzzle)
                if result.is_valid:
                    best_score = 1.0
                    best_individual = ind
                    break
                if result.score > best_score:
                    best_score = result.score
                    best_individual = ind
                if result.error_code:
                    failure_reasons.append(result.error_code.value)

            if best_score >= 1.0:
                # Early exit – solution found
                break

            # --- Forward step: generate new candidates ---
            sub_goals = []
            if best_individual:
                sub_goals = self.backward_step.extract_subgoals(
                    best_individual.solution, puzzle
                )
            new_candidates = self.forward_step.step(
                population=population,
                sub_goals=sub_goals,
                puzzle=puzzle,
            )
            forward_calls += len(new_candidates)

            # --- Backward step: refine candidates ---
            refined = []
            for cand in new_candidates:
                try:
                    refined_cand = self.backward_step.refine(
                        candidate_solution=cand,
                        puzzle=puzzle,
                        sub_goals=sub_goals,
                    )
                    refined.append(refined_cand)
                    backward_calls += 1
                except BaseResearchException as exc:
                    failure_reasons.append(str(type(exc).__name__))

            # Update population with refined candidates
            if refined:
                population.evolve(refined)

        total_time = time.time() - start_time
        success = best_individual is not None and self.backward_step.verify(
            best_individual.solution, puzzle
        ).is_valid
        final_score = best_score if best_score != -float("inf") else 0.0

        return BESRunResult(
            experiment_id=self.experiment_id,
            puzzle_id=puzzle.id,
            complexity_n=puzzle.complexity_n,
            population_size=self.population_size,
            generations=self.generations,
            success=success,
            final_score=final_score,
            total_time_seconds=total_time,
            forward_calls=forward_calls,
            backward_calls=backward_calls,
            failure_reasons=failure_reasons,
            log_entries=log_entries,
        )

    def run_full_scaling_analysis(self, output_dir: Path) -> None:
        """
        Run the full N=10..500 scaling analysis and write a JSONL file.
        
        Args:
            output_dir: Directory where ``bes_scaling_results.jsonl`` will be written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / "bes_scaling_results.jsonl"

        generator = PuzzleGenerator(seed=self.seed)

        with out_file.open("w", encoding="utf-8") as f:
            for n in range(10, 501):
                self.logger.info(f"Processing complexity N={n}")
                puzzle = generator.generate_puzzle(puzzle_type="logic", complexity_n=n)
                result = self.run_single_puzzle(puzzle)
                f.write(json.dumps(result.asdict()) + "\n")

        self.logger.info(f"Full scaling results written to {out_file}")


def _build_config_from_args(args: argparse.Namespace) -> dict:
    """
    Translate CLI arguments into a configuration dictionary consumed by
    :class:`BESOrchestrator`.
    """
    return {
        "forward_model": "distilbert-base-uncased",
        "temperature": 0.7,
        "population_size": args.pop_size,
        "generations": args.generations,
        "output_dir": args.output_dir,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bidirectional Evolutionary Search orchestrator"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run a minimal pilot experiment (single puzzle, small population).",
    )
    parser.add_argument(
        "--method",
        choices=["symbolic", "neural"],
        default="symbolic",
        help="Select the backward‑step method (currently symbolic is the default).",
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=20,
        help="Population size for the run.",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=10,
        help="Number of generations.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/pilot_result.jsonl",
        help="Path for pilot output (ignored for full scaling run).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory for full scaling results.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("main")

    config = _build_config_from_args(args)

    orchestrator = BESOrchestrator(config=config, seed=args.seed)

    if args.pilot:
        # Pilot mode – generate a single small puzzle (N=10) and run it.
        logger.info("Running pilot experiment...")
        generator = PuzzleGenerator(seed=args.seed)
        pilot_puzzle = generator.generate_puzzle(puzzle_type="logic", complexity_n=10)
        result = orchestrator.run_single_puzzle(pilot_puzzle)

        # Write result to the user‑specified path.
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result.asdict(), f, indent=2)

        logger.info(f"Pilot result written to {output_path}")
    else:
        # Full scaling analysis mode.
        logger.info("Running full scaling analysis (N=10..500)...")
        output_dir = Path(args.output_dir)
        orchestrator.run_full_scaling_analysis(output_dir)


if __name__ == "__main__":
    main()