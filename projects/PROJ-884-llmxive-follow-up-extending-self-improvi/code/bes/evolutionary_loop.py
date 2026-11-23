"""
Evolutionary Loop for Bidirectional Evolutionary Search (BES).
Orchestrates the forward (LLM) and backward (Symbolic) steps.
Handles exclusion of instances with CONTRADICTION_DETECTED or PARSE_FAILURE.
"""
import json
import os
import sys
import time
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Import from project API surface
from code.bes.forward_step import ForwardStep, ForwardStepResult
from code.bes.backward_step import BackwardStep, BackwardStepResult, BackwardStepError
from code.bes.population import Population, Individual, PopulationStats, SelectionMethod
from code.bes.mutation_operator import MutationOperator
from code.bes.crossover_operator import CrossoverOperator
from code.bes.fitness_evaluator import FitnessEvaluator
from code.bes.termination_condition import TerminationCondition
from code.bes.config import BESConfig, get_default_config
from code.symbolic.planner import SymbolicPlanner, SubGoalStatus, DecompositionResult
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent
from code.exceptions import CONTRADICTION_DETECTED, PARSE_FAILURE, VERIFIER_ERROR
from code.utils.seed import set_seed, get_seed
from code.utils.logger import log_experiment_entry

@dataclass
class EvolutionaryRunResult:
    """Result container for a single evolutionary loop execution."""
    experiment_id: str
    total_generations: int
    final_population_stats: Optional[PopulationStats]
    best_individual: Optional[Individual]
    success_rate: float
    exclusions: List[Dict[str, Any]]
    run_time_seconds: float
    timestamp: str

class EvolutionaryLoop:
    """
    Orchestrates the BES evolutionary loop.
    """

    def __init__(self, config: BESConfig, output_path: Path):
        self.config = config
        self.output_path = output_path
        self.exclusion_logger = ExclusionLogger(
            exclusion_path=self.config.exclusion_log_path or "data/processed/exclusions.json"
        )
        self.planner = SymbolicPlanner()
        self.forward_step = ForwardStep(model_config=self.config.model_config)
        self.backward_step = BackwardStep(planner=self.planner)
        self.mutation = MutationOperator(grammar=self.config.grammar_path)
        self.crossover = CrossoverOperator()
        self.fitness_evaluator = FitnessEvaluator(verifier_path=self.config.verifier_path)
        self.termination = TerminationCondition(
            max_generations=config.max_generations,
            convergence_threshold=config.convergence_threshold
        )
        self.logger = logging.getLogger(__name__)
        self.exclusions_log: List[Dict[str, Any]] = []

    def _log_exclusion(self, instance_id: str, reason: str, error_code: str, details: Optional[Dict] = None):
        """Log an exclusion event and update the exclusion log."""
        event = ExclusionEvent(
            instance_id=instance_id,
            reason=reason,
            error_code=error_code,
            timestamp=datetime.now().isoformat(),
            details=details or {}
        )
        self.exclusion_logger.log_event(event)
        self.exclusions_log.append(asdict(event))

    def _handle_planner_error(self, instance_id: str, error_code: str):
        """Handle planner errors (CONTRADICTION_DETECTED, PARSE_FAILURE) by excluding the instance."""
        if error_code == CONTRADICTION_DETECTED:
            self._log_exclusion(
                instance_id=instance_id,
                reason="Symbolic planner detected logical contradiction in sub-goals",
                error_code=CONTRADICTION_DETECTED
            )
        elif error_code == PARSE_FAILURE:
            self._log_exclusion(
                instance_id=instance_id,
                reason="Symbolic planner failed to parse puzzle constraints",
                error_code=PARSE_FAILURE
            )
        else:
            self._log_exclusion(
                instance_id=instance_id,
                reason=f"Unexpected planner error: {error_code}",
                error_code=error_code
            )

    def run(self, puzzle_instances: List[Dict[str, Any]]) -> EvolutionaryRunResult:
        """
        Execute the evolutionary loop for the given puzzle instances.

        Args:
            puzzle_instances: List of puzzle instances to solve.

        Returns:
            EvolutionaryRunResult containing final statistics and best individual.
        """
        start_time = time.time()
        self.logger.info(f"Starting evolutionary loop for {len(puzzle_instances)} instances")

        # Initialize population for each instance (or batch if configured)
        # For simplicity, we process one instance at a time in this loop
        # In a real scenario, this might be parallelized or batched
        all_results = []
        total_successes = 0
        processed_count = 0

        for idx, puzzle in enumerate(puzzle_instances):
            instance_id = puzzle.get("metadata", {}).get("source_id", f"puzzle_{idx}")
            self.logger.info(f"Processing instance {idx+1}/{len(puzzle_instances)}: {instance_id}")

            try:
                # Initialize population for this puzzle
                population = Population(
                    size=self.config.population_size,
                    puzzle_instance=puzzle,
                    seed=get_seed() + idx  # Unique seed per instance
                )

                # Evolutionary loop for this instance
                generation = 0
                best_individual = None
                instance_success = False

                while not self.termination.should_terminate(generation, population):
                    generation += 1

                    # Forward Step: LLM generates new candidates
                    forward_result = self.forward_step.step(population, puzzle)
                    population.update_candidates(forward_result.candidates)

                    # Backward Step: Symbolic planner guides evolution
                    try:
                        backward_result = self.backward_step.step(population, puzzle)
                        
                        # Check for planner errors
                        if backward_result.status == CONTRADICTION_DETECTED:
                            self._handle_planner_error(instance_id, CONTRADICTION_DETECTED)
                            instance_success = False
                            break
                        elif backward_result.status == PARSE_FAILURE:
                            self._handle_planner_error(instance_id, PARSE_FAILURE)
                            instance_success = False
                            break

                        # Apply symbolic guidance to population
                        population.apply_symbolic_guidance(backward_result.sub_goals)
                        
                    except BackwardStepError as e:
                        self.logger.warning(f"Backward step error for {instance_id}: {e}")
                        # Continue with forward step only if backward fails
                        pass

                    # Selection
                    selected = population.select(SelectionMethod.TOURNAMENT, k=4)

                    # Crossover
                    offspring = self.crossover.recombine(selected, population)

                    # Mutation
                    mutated = self.mutation.mutate(offspring, mutation_rate=self.config.mutation_rate)

                    # Evaluate fitness
                    fitness_scores = self.fitness_evaluator.evaluate(mutated, puzzle)
                    population.update_fitness(fitness_scores)

                    # Elitism: keep best individual
                    best = population.get_best()
                    if best is not None:
                        if best_individual is None or best.fitness > best_individual.fitness:
                            best_individual = best

                    # Check for success (fitness threshold)
                    if best_individual and best_individual.fitness >= self.config.success_threshold:
                        instance_success = True
                        total_successes += 1
                        self.logger.info(f"Instance {instance_id} solved at generation {generation}")
                        break

                    # Log progress
                    if generation % 10 == 0:
                        self.logger.info(f"Generation {generation} - Best fitness: {best_individual.fitness if best_individual else 0}")

                if not instance_success and best_individual is not None:
                    self.logger.warning(f"Instance {instance_id} not solved after {generation} generations")

                all_results.append({
                    "instance_id": instance_id,
                    "generations": generation,
                    "success": instance_success,
                    "best_fitness": best_individual.fitness if best_individual else 0
                })

            except Exception as e:
                self.logger.error(f"Error processing instance {instance_id}: {e}", exc_info=True)
                self._log_exclusion(
                    instance_id=instance_id,
                    reason=f"Unexpected error during evolutionary loop: {str(e)}",
                    error_code="RUNTIME_ERROR",
                    details={"error_type": type(e).__name__}
                )

        # Calculate final statistics
        total_time = time.time() - start_time
        success_rate = total_successes / len(puzzle_instances) if puzzle_instances else 0.0

        # Save results
        result_path = self.output_path
        result_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_data = {
            "experiment_id": self.config.experiment_id,
            "total_instances": len(puzzle_instances),
            "successful_instances": total_successes,
            "success_rate": success_rate,
            "total_time_seconds": total_time,
            "results": all_results,
            "exclusions": self.exclusions_log,
            "timestamp": datetime.now().isoformat()
        }

        with open(result_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        self.logger.info(f"Evolutionary loop completed. Results saved to {result_path}")

        # Create final result object
        return EvolutionaryRunResult(
            experiment_id=self.config.experiment_id,
            total_generations=generation if 'generation' in locals() else 0,
            final_population_stats=population.get_stats() if 'population' in locals() else None,
            best_individual=best_individual,
            success_rate=success_rate,
            exclusions=self.exclusions_log,
            run_time_seconds=total_time,
            timestamp=datetime.now().isoformat()
        )

def main():
    """Main entry point for the evolutionary loop."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the BES evolutionary loop")
    parser.add_argument("--config", type=str, default="code/bes/config.py", help="Path to config file")
    parser.add_argument("--input", type=str, required=True, help="Path to input puzzles JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output results JSON file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set seed
    set_seed(args.seed)

    # Load config
    config = get_default_config()
    
    # Override with command line args if provided
    if args.config and os.path.exists(args.config):
        # In a real implementation, we would load from the config file
        pass

    # Load puzzles
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        puzzles = json.load(f)

    # Ensure puzzles is a list
    if isinstance(puzzles, dict) and "puzzles" in puzzles:
        puzzles = puzzles["puzzles"]
    elif not isinstance(puzzles, list):
        puzzles = [puzzles]

    # Run evolutionary loop
    loop = EvolutionaryLoop(config, Path(args.output))
    result = loop.run(puzzles)

    # Print summary
    print(f"Evolutionary Loop Complete")
    print(f"Success Rate: {result.success_rate:.2%}")
    print(f"Exclusions: {len(result.exclusions)}")
    print(f"Run Time: {result.run_time_seconds:.2f}s")

if __name__ == "__main__":
    main()