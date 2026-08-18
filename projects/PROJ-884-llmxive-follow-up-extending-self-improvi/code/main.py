"""
Main BES (Bidirectional Evolutionary Search) Loop Orchestrator.

Orchestrates the forward (LLM) and backward (Symbolic) steps across
the full complexity scaling range (N=10..500) to generate data for analysis.
"""
import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Import from existing API surface
from config import load_config, get_experiment_id, initialize_experiment
from utils.seed import set_seed, get_seed
from utils.logger import setup_logging, log, log_experiment_entry
from dataset.verifier import PuzzleVerifier, SolutionResult, ErrorCodes
from dataset.generator import PuzzleGenerator, PuzzleInstance
from bes.forward_step import ForwardStep, ForwardStepResult
from bes.backward_step import BackwardStep, BackwardStepResult
from bes.population import Population, Individual
from symbolic.planner import SymbolicPlanner
from exceptions import BaseResearchException, PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR

@dataclass
class BESRunResult:
    """Container for the results of a single BES run."""
    experiment_id: str
    puzzle_id: str
    complexity_n: int
    population_size: int
    generations: int
    success: bool
    final_score: float
    total_time_seconds: float
    forward_calls: int
    backward_calls: int
    failure_reasons: List[str] = field(default_factory=list)
    log_entries: List[Dict[str, Any]] = field(default_factory=list)

class BESOrchestrator:
    """
    Orchestrates the Bidirectional Evolutionary Search loop.
    
    Coordinates the forward step (LLM) and backward step (Symbolic Planner)
    over a population of solutions for a given puzzle instance.
    """
    
    def __init__(self, config: Dict[str, Any], seed: int):
        self.config = config
        self.seed = seed
        self.experiment_id = get_experiment_id()
        self.logger = logging.getLogger("BESOrchestrator")
        
        # Initialize components based on config
        self.forward_step = ForwardStep(
            model_name=config.get('forward_model', 'distilbert-base-uncased'),
            device='cpu',
            temperature=config.get('temperature', 0.7)
        )
        
        self.backward_step = BackwardStep(
            planner=SymbolicPlanner(),
            verifier=PuzzleVerifier()
        )
        
        self.population_size = config.get('population_size', 20)
        self.generations = config.get('generations', 50)
        
        set_seed(seed)

    def run_single_puzzle(self, puzzle: PuzzleInstance) -> BESRunResult:
        """
        Execute the BES loop for a single puzzle instance.
        
        Args:
            puzzle: The puzzle instance to solve.
            
        Returns:
            BESRunResult containing execution statistics and outcome.
        """
        start_time = time.time()
        log_entries = []
        failure_reasons = []
        forward_calls = 0
        backward_calls = 0
        
        self.logger.info(f"Starting BES for puzzle {puzzle.id} (N={puzzle.complexity_n})")
        log_experiment_entry({
            "type": "bes_start",
            "puzzle_id": puzzle.id,
            "complexity": puzzle.complexity_n,
            "population_size": self.population_size,
            "generations": self.generations
        })

        # Initialize population
        population = Population(
            size=self.population_size,
            puzzle=puzzle,
            seed=self.seed
        )
        
        generation_results = []
        
        for gen in range(self.generations):
            gen_start = time.time()
            
            # 1. Evaluate current population
            current_best_score = -1.0
            current_best_individual = None
            
            for ind in population.individuals:
                result = self.backward_step.verify(ind.solution, puzzle)
                if result.is_valid:
                    current_best_score = 1.0
                    current_best_individual = ind
                    break
                else:
                    # Track failure reasons for analysis
                    if result.error_code:
                        failure_reasons.append(result.error_code.value)
                
                if result.score > current_best_score:
                    current_best_score = result.score
                    current_best_individual = ind
            
            # Check for early success
            if current_best_score >= 1.0:
                self.logger.info(f"Solution found at generation {gen}")
                log_experiment_entry({
                    "type": "solution_found",
                    "generation": gen,
                    "puzzle_id": puzzle.id
                })
                break
            
            # 2. Forward Step: Recombine/Generate new candidates guided by sub-goals
            # Extract sub-goals from the best individual or puzzle structure
            sub_goals = []
            if current_best_individual:
                sub_goals = self.backward_step.extract_subgoals(
                    current_best_individual.solution, 
                    puzzle
                )
            
            new_candidates = self.forward_step.step(
                population=population,
                sub_goals=sub_goals,
                puzzle=puzzle
            )
            forward_calls += len(new_candidates)
            
            # 3. Backward Step: Filter and refine candidates
            refined_candidates = []
            for candidate in new_candidates:
                # Attempt to refine using symbolic planner
                try:
                    refined = self.backward_step.refine(
                        candidate_solution=candidate,
                        puzzle=puzzle,
                        sub_goals=sub_goals
                    )
                    if refined.is_valid or refined.score > 0.0:
                        refined_candidates.append(refined)
                        backward_calls += 1
                except BaseResearchException as e:
                    # Log and exclude
                    failure_reasons.append(str(type(e).__name__))
                    log_experiment_entry({
                        "type": "backward_step_failure",
                        "reason": str(e),
                        "generation": gen
                    })
            
            # 4. Update population
            if refined_candidates:
                population.evolve(refined_candidates)
            
            gen_time = time.time() - gen_start
            generation_results.append({
                "generation": gen,
                "best_score": current_best_score,
                "time": gen_time,
                "population_size": len(population.individuals)
            })
            
            log_experiment_entry({
                "type": "generation_complete",
                "generation": gen,
                "best_score": current_best_score,
                "time": gen_time
            })

        total_time = time.time() - start_time
        
        # Final verification
        final_success = False
        final_score = 0.0
        if current_best_individual:
            final_result = self.backward_step.verify(current_best_individual.solution, puzzle)
            final_success = final_result.is_valid
            final_score = final_result.score

        result = BESRunResult(
            experiment_id=self.experiment_id,
            puzzle_id=puzzle.id,
            complexity_n=puzzle.complexity_n,
            population_size=self.population_size,
            generations=self.generations,
            success=final_success,
            final_score=final_score,
            total_time_seconds=total_time,
            forward_calls=forward_calls,
            backward_calls=backward_calls,
            failure_reasons=list(set(failure_reasons)), # Deduplicate
            log_entries=log_entries
        )
        
        self.logger.info(
            f"Finished puzzle {puzzle.id}: Success={final_success}, "
            f"Score={final_score:.4f}, Time={total_time:.2f}s"
        )
        
        return result

    def run_full_scaling_analysis(self, output_path: Path) -> List[BESRunResult]:
        """
        Execute the BES loop across the full complexity scaling range (N=10..500).
        
        Args:
            output_path: Directory path to save results.
            
        Returns:
            List of BESRunResult objects.
        """
        output_path.mkdir(parents=True, exist_ok=True)
        results_file = output_path / "bes_scaling_results.json"
        
        self.logger.info(f"Starting full scaling analysis (N=10..500)")
        log_experiment_entry({
            "type": "scaling_analysis_start",
            "range": "10-500",
            "output_path": str(results_file)
        })

        results = []
        
        # Define complexity range as per task constraint
        # Using a subset for demonstration if 500 is too large for quick testing,
        # but the code supports the full range.
        # To strictly follow "N=10..500", we iterate all integers.
        # For performance in a real run, we might step by 10 or 50.
        # Here we implement the full range as requested.
        n_values = list(range(10, 501))
        
        # Generate or load puzzles for these complexities
        # We use the generator to create puzzles on the fly to ensure real data
        generator = PuzzleGenerator(seed=self.seed)
        
        for n in n_values:
            self.logger.info(f"Processing complexity N={n}")
            
            try:
                # Generate a real puzzle instance
                puzzle = generator.generate_puzzle(
                    puzzle_type="logic",
                    complexity_n=n
                )
                
                # Run BES
                result = self.run_single_puzzle(puzzle)
                results.append(result)
                
                # Save intermediate results to avoid data loss on crash
                with open(results_file, 'w') as f:
                    json.dump([asdict(r) for r in results], f, indent=2)
                    
            except Exception as e:
                self.logger.error(f"Failed to process N={n}: {e}", exc_info=True)
                # Continue to next N to ensure we get data for other complexities
                failure_result = BESRunResult(
                    experiment_id=self.experiment_id,
                    puzzle_id=f"unknown_{n}",
                    complexity_n=n,
                    population_size=self.population_size,
                    generations=self.generations,
                    success=False,
                    final_score=0.0,
                    total_time_seconds=0.0,
                    forward_calls=0,
                    backward_calls=0,
                    failure_reasons=[str(e)]
                )
                results.append(failure_result)
                with open(results_file, 'w') as f:
                    json.dump([asdict(r) for r in results], f, indent=2)

        self.logger.info(f"Scaling analysis complete. Results saved to {results_file}")
        log_experiment_entry({
            "type": "scaling_analysis_complete",
            "total_puzzles": len(results),
            "output_path": str(results_file)
        })

        return results


def main():
    """Entry point for the BES pipeline."""
    # Setup
    config = load_config()
    seed = get_seed()
    setup_logging()
    
    orchestrator = BESOrchestrator(config, seed)
    
    # Determine output path
    output_dir = Path(config.get('output_dir', 'data/processed'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run the full scaling analysis
    results = orchestrator.run_full_scaling_analysis(output_dir)
    
    # Print summary
    success_count = sum(1 for r in results if r.success)
    total_count = len(results)
    print(f"Scaling Analysis Complete: {success_count}/{total_count} successes")
    print(f"Results saved to: {output_dir / 'bes_scaling_results.json'}")

    return results


if __name__ == "__main__":
    main()