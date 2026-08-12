"""
Main BES Loop Orchestrator for llmXive Project.

This module implements the main evolutionary search loop, orchestrating:
1. Forward Step: LLM-based trajectory recombination/generation.
2. Backward Step: Symbolic planner sub-goal decomposition.
3. Population Management: Selection and replacement strategies.
4. Logging: Comprehensive JSON logging of all transitions and metrics.
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import load_config, initialize_experiment, get_experiment_id
from code.utils.seed import set_seed, get_seed
from code.utils.logger import log, log_experiment_entry
from code.dataset.verifier import verify_solution, SolutionResult, ErrorCodes
from code.dataset.generator import PuzzleInstance
from code.dataset.generate_dataset import generate_checksum
from code.symbolic.parser import parse_dataset_file, PuzzleParser
from code.symbolic.planner import SymbolicPlanner, SubGoalStatus, DecompositionResult
from code.bes.forward_step import ForwardStep, ForwardStepError
from code.bes.backward_step import BackwardStep, BackwardStepResult, BackwardStepError
from code.bes.population import Population
from code.exceptions import BaseResearchException, PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR

@dataclass
class BESRunResult:
    """Container for the results of a single BES execution run."""
    experiment_id: str
    total_generations: int
    population_size: int
    success_rate: float
    total_time_seconds: float
    avg_verifier_time_ms: float
    total_puzzles_processed: int
    log_file_path: str
    population_history: List[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BESOrchestrator:
    """
    Orchestrates the Bidirectional Evolutionary Search (BES) loop.
    """

    def __init__(self, config_path: str, data_dir: str, output_dir: str):
        self.config = load_config(config_path)
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.puzzle_parser = PuzzleParser()
        self.symbolic_planner = SymbolicPlanner()
        self.forward_step = ForwardStep(self.config)
        self.population_manager = Population(self.config)

        # Load dataset
        self.dataset_path = self.data_dir / "raw" / "puzzles.json"
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}. Run T013 first.")
        
        self.puzzles = parse_dataset_file(self.dataset_path)
        self.experiment_id = get_experiment_id()
        
        # Initialize logging for this run
        self.log_file = self.output_dir / f"bes_run_{self.experiment_id}.log"
        self.run_log = []

    def _log_transition(self, step_type: str, data: Dict[str, Any]):
        """Helper to log a transition event."""
        entry = {
            "timestamp": time.time(),
            "step": step_type,
            "data": data
        }
        self.run_log.append(entry)
        log(f"[BES] {step_type}: {json.dumps(data)}")

    def run_generation(self, generation_id: int, current_population: Population) -> Population:
        """
        Executes a single generation of the BES loop.
        
        1. Backward Step: Symbolic planner decomposes current best solutions into sub-goals.
        2. Forward Step: LLM generates new trajectories guided by sub-goals.
        3. Verification: New solutions are verified.
        4. Selection: Population is updated based on fitness.
        """
        start_time = time.time()
        
        # 1. Backward Step: Analyze current population to generate sub-goals
        # We pick the top K individuals for analysis to avoid excessive computation
        top_k = min(5, len(current_population))
        top_individuals = current_population.get_top_k(top_k)
        
        sub_goals = []
        backward_results = []
        
        for idx, individual in enumerate(top_individuals):
            puzzle_id = individual["puzzle_id"]
            current_solution = individual.get("solution", "")
            
            try:
                # Parse the puzzle constraints
                puzzle_constraints = self.puzzle_parser.get_constraints_by_id(puzzle_id, self.puzzles)
                
                # Run symbolic planner
                decomposition = self.symbolic_planner.decompose(
                    puzzle_constraints, 
                    current_solution
                )
                
                sub_goals.extend(decomposition.sub_goals)
                backward_results.append({
                    "puzzle_id": puzzle_id,
                    "status": decomposition.status.value,
                    "sub_goal_count": len(decomposition.sub_goals)
                })
                
            except (PARSE_FAILURE, CONTRADICTION_DETECTED) as e:
                self._log_transition("BACKWARD_STEP_FAILURE", {
                    "puzzle_id": puzzle_id,
                    "error_type": type(e).__name__,
                    "message": str(e)
                })
                backward_results.append({
                    "puzzle_id": puzzle_id,
                    "status": "FAILURE",
                    "error": str(e)
                })
            except Exception as e:
                self._log_transition("BACKWARD_STEP_ERROR", {
                    "puzzle_id": puzzle_id,
                    "error": str(e)
                })
                backward_results.append({
                    "puzzle_id": puzzle_id,
                    "status": "ERROR",
                    "error": str(e)
                })

        self._log_transition("BACKWARD_STEP_COMPLETE", {
            "generation": generation_id,
            "individuals_analyzed": len(top_individuals),
            "total_sub_goals": len(sub_goals),
            "results": backward_results
        })

        # 2. Forward Step: Generate new candidates using LLM and sub-goals
        new_candidates = []
        forward_results = []
        
        try:
            candidates, details = self.forward_step.generate(
                sub_goals,
                self.puzzles,
                num_candidates=self.config.get("population_size", 10)
            )
            new_candidates = candidates
            forward_results = details
        except ForwardStepError as e:
            self._log_transition("FORWARD_STEP_ERROR", {
                "generation": generation_id,
                "error": str(e)
            })
            # Continue with empty candidates if forward step fails
            new_candidates = []
        
        self._log_transition("FORWARD_STEP_COMPLETE", {
            "generation": generation_id,
            "candidates_generated": len(new_candidates),
            "details": forward_results
        })

        # 3. Verification: Verify new candidates
        verified_count = 0
        verifier_times = []
        
        for candidate in new_candidates:
            puzzle_id = candidate["puzzle_id"]
            solution = candidate["solution"]
            
            # Find the full puzzle instance for verification
            puzzle_instance = None
            for p in self.puzzles:
                if p["id"] == puzzle_id:
                    puzzle_instance = p
                    break
            
            if not puzzle_instance:
                self._log_transition("VERIFICATION_SKIP", {
                    "puzzle_id": puzzle_id,
                    "reason": "Puzzle not found in dataset"
                })
                continue

            start_verifier = time.time()
            try:
                result = verify_solution(puzzle_instance, solution)
                end_verifier = time.time()
                verifier_times.append((end_verifier - start_verifier) * 1000) # ms
                
                candidate["verification_result"] = result
                candidate["verified"] = result.success
                candidate["verifier_time_ms"] = (end_verifier - start_verifier) * 1000
                
                if result.success:
                    verified_count += 1
                    
                self._log_transition("VERIFICATION", {
                    "puzzle_id": puzzle_id,
                    "success": result.success,
                    "error_code": result.error_code.value if result.error_code else None,
                    "time_ms": candidate["verifier_time_ms"]
                })
                
            except VERIFIER_ERROR as e:
                self._log_transition("VERIFICATION_ERROR", {
                    "puzzle_id": puzzle_id,
                    "error": str(e)
                })
                candidate["verified"] = False
                candidate["verification_result"] = None
            except Exception as e:
                self._log_transition("VERIFICATION_UNEXPECTED_ERROR", {
                    "puzzle_id": puzzle_id,
                    "error": str(e)
                })
                candidate["verified"] = False
                candidate["verification_result"] = None

        self._log_transition("VERIFICATION_COMPLETE", {
            "generation": generation_id,
            "total_candidates": len(new_candidates),
            "verified_count": verified_count,
            "avg_verifier_time_ms": sum(verifier_times) / len(verifier_times) if verifier_times else 0
        })

        # 4. Selection: Update population
        # Add verified candidates to the population
        for candidate in new_candidates:
            if candidate.get("verified", False):
                current_population.add(candidate)
        
        # Perform selection to maintain population size
        current_population.select()

        end_time = time.time()
        self._log_transition("GENERATION_COMPLETE", {
            "generation": generation_id,
            "duration_seconds": end_time - start_time,
            "population_size": len(current_population),
            "verified_candidates": verified_count
        })

        return current_population

    def run(self) -> BESRunResult:
        """
        Executes the full BES experiment.
        """
        log_experiment_entry({
            "experiment_id": self.experiment_id,
            "type": "BES_RUN",
            "config": self.config,
            "dataset_path": str(self.dataset_path)
        })

        total_time_start = time.time()
        total_puzzles = 0
        all_verifier_times = []
        population_history = []

        # Initialize population
        current_population = self.population_manager.initialize(self.puzzles)
        
        generations = self.config.get("generations", 10)
        population_size = self.config.get("population_size", 10)

        log(f"Starting BES run: {generations} generations, pop size {population_size}")

        for gen in range(generations):
            log(f"--- Generation {gen + 1}/{generations} ---")
            current_population = self.run_generation(gen, current_population)
            
            # Record population snapshot
            snapshot = {
                "generation": gen,
                "size": len(current_population),
                "best_fitness": current_population.get_best_fitness()
            }
            population_history.append(snapshot)

            # Count unique puzzles processed in this generation
            # (Simplified: assuming each candidate is a unique puzzle attempt)
            # In a real scenario, we'd track unique puzzle IDs processed
            
        total_time_end = time.time()
        total_duration = total_time_end - total_time_start

        # Calculate final metrics
        final_population = current_population
        successful_solutions = [ind for ind in final_population if ind.get("verified", False)]
        success_rate = len(successful_solutions) / len(final_population) if final_population else 0.0

        # Collect verifier times from the last generation's log if available
        # For simplicity, we estimate based on the run log
        # A more robust implementation would aggregate all verifier times during the run
        avg_verifier_time = 0.0 
        for entry in self.run_log:
            if entry["step"] == "VERIFICATION" and "time_ms" in entry["data"]:
                all_verifier_times.append(entry["data"]["time_ms"])
        
        if all_verifier_times:
            avg_verifier_time = sum(all_verifier_times) / len(all_verifier_times)

        # Write run log to file
        with open(self.log_file, 'w') as f:
            json.dump(self.run_log, f, indent=2)

        result = BESRunResult(
            experiment_id=self.experiment_id,
            total_generations=generations,
            population_size=population_size,
            success_rate=success_rate,
            total_time_seconds=total_duration,
            avg_verifier_time_ms=avg_verifier_time,
            total_puzzles_processed=len(successful_solutions),
            log_file_path=str(self.log_file),
            population_history=population_history
        )

        log(f"BES Run Complete. Success Rate: {success_rate:.2f}, Total Time: {total_duration:.2f}s")
        return result

def main():
    """
    Entry point for the BES loop.
    Usage: python code/main.py [--config <path>] [--data <path>] [--output <path>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run the BES Evolutionary Loop")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--data", type=str, default="data", help="Path to data directory")
    parser.add_argument("--output", type=str, default="data/processed", help="Path to output directory")
    args = parser.parse_args()

    # Ensure paths are relative to project root if not absolute
    if not os.path.isabs(args.config):
        args.config = str(PROJECT_ROOT / args.config)
    if not os.path.isabs(args.data):
        args.data = str(PROJECT_ROOT / args.data)
    if not os.path.isabs(args.output):
        args.output = str(PROJECT_ROOT / args.output)

    try:
        orchestrator = BESOrchestrator(
            config_path=args.config,
            data_dir=args.data,
            output_dir=args.output
        )
        result = orchestrator.run()
        
        # Save result summary to JSON
        result_path = Path(args.output) / f"bes_result_{result.experiment_id}.json"
        with open(result_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"Results saved to {result_path}")
        print(f"Experiment ID: {result.experiment_id}")
        print(f"Success Rate: {result.success_rate:.4f}")
        print(f"Total Time: {result.total_time_seconds:.2f}s")
        
    except FileNotFoundError as e:
        print(f"Configuration or Data Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error during BES execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()