"""
Main entry point for the BES (Bidirectional Evolutionary Search) experiment.
Orchestrates the comparison between Symbolic-guided BES and Neural-verifier Baseline.
"""
import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Project imports based on API surface
from config import load_config, save_config, get_experiment_id, initialize_experiment
from utils.seed import set_seed, get_seed
from utils.logger import setup_logging, log, log_experiment_entry
from dataset.generator import PuzzleGenerator, PuzzleType
from dataset.verifier import verify_solution, SolutionResult
from bes.population import Population, Individual
from bes.forward_step import ForwardStep
from bes.backward_step import BackwardStep, BackwardStepResult
from symbolic.parser import PuzzleParser
from symbolic.planner import SymbolicPlanner
from analysis.metrics import ExperimentMetrics, calculate_metrics_from_logs, save_metrics_to_csv
from analysis.stats import two_proportion_z_test, ZTestResult
from exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR

@dataclass
class BESRunResult:
    """Container for the results of a single BES run (Symbolic or Neural)."""
    run_type: str  # 'symbolic' or 'neural_baseline'
    experiment_id: str
    population_size: int
    generations: int
    total_puzzles: int
    successful_puzzles: int
    success_rate: float
    total_time_seconds: float
    avg_time_per_puzzle_seconds: float
    log_path: str
    metrics_path: str

class BESOrchestrator:
    """
    Orchestrates the full experiment: running Symbolic BES and Neural Baseline,
    collecting metrics, and performing statistical analysis.
    """

    def __init__(self, config_path: str = "code/config.yaml"):
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.seed = self.config.get("seed", 42)
        set_seed(self.seed)
        
        # Setup logging
        log_dir = Path("data/processed")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / f"experiment_{get_experiment_id()}.log"
        setup_logging(self.log_path)

        # Initialize components
        self.puzzle_generator = PuzzleGenerator()
        self.verifier = None # Loaded per puzzle
        self.forward_step = ForwardStep(self.config)
        self.symbolic_planner = SymbolicPlanner()
        self.parser = PuzzleParser()
        
        # Results storage
        self.results: List[BESRunResult] = []
        self.log_entries: List[Dict[str, Any]] = []

    def _run_single_bes_loop(self, run_type: str, puzzles: List[Dict[str, Any]]) -> BESRunResult:
        """
        Executes the BES loop for a specific configuration (Symbolic or Neural).
        """
        start_time = time.time()
        population_size = self.config.get("population_size", 20)
        generations = self.config.get("generations", 50)
        
        log(f"Starting {run_type} BES loop with {len(puzzles)} puzzles.")
        
        successes = 0
        puzzle_durations = []
        
        for idx, puzzle in enumerate(puzzles):
            puzzle_start = time.time()
            
            # Initialize population for this puzzle
            population = Population(
                size=population_size,
                puzzle=puzzle,
                seed=get_seed()
            )
            
            solved = False
            best_individual = None
            
            for gen in range(generations):
                if solved:
                    break
                
                # Forward Step (LLM Trajectory Generation)
                # Note: In Neural Baseline, backward step is also neural (simulated here by random/verifier check)
                # In Symbolic, backward step uses planner.
                
                # 1. Evaluate current population
                for ind in population.individuals:
                    if not ind.fitness_evaluated:
                        result = verify_solution(puzzle, ind.solution)
                        ind.fitness = 1.0 if result.is_valid else 0.0
                        ind.fitness_evaluated = True
                        if result.is_valid:
                            solved = True
                            best_individual = ind
                            break
                
                if solved:
                    successes += 1
                    break
                
                # 2. Backward Step / Selection
                if run_type == "symbolic":
                    # Use symbolic planner to guide backward step
                    try:
                        subgoals = self.symbolic_planner.decompose(puzzle)
                        population.evolve_backward(subgoals)
                    except (PARSE_FAILURE, CONTRADICTION_DETECTED) as e:
                        log(f"Symbolic planner failed for puzzle {puzzle['id']}: {e}. Falling back to random.")
                        population.evolve_backward(None) # Fallback to random mutation
                else:
                    # Neural Baseline: Standard evolutionary step without symbolic guidance
                    population.evolve_backward(None)
                
                # 3. Forward Step (Recombination/Generation)
                population.evolve_forward(self.forward_step)
                
                # 4. Elitism / Replacement
                population.replace()
                
                # Log generation progress occasionally
                if gen % 10 == 0:
                    log(f"Gen {gen} | Pop Fitness: {population.avg_fitness:.4f}")

            puzzle_end = time.time()
            puzzle_durations.append(puzzle_end - puzzle_start)
            
            if not solved:
                log(f"Puzzle {puzzle['id']} not solved within {generations} generations.")

        total_time = time.time() - start_time
        avg_time = total_time / len(puzzles) if puzzles else 0.0
        success_rate = successes / len(puzzles) if puzzles else 0.0

        # Save logs
        log_entry = {
            "run_type": run_type,
            "timestamp": time.time(),
            "total_time": total_time,
            "successes": successes,
            "total": len(puzzles),
            "success_rate": success_rate,
            "avg_time_per_puzzle": avg_time
        }
        self.log_entries.append(log_entry)
        
        # Write detailed log to file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return BESRunResult(
            run_type=run_type,
            experiment_id=get_experiment_id(),
            population_size=population_size,
            generations=generations,
            total_puzzles=len(puzzles),
            successful_puzzles=successes,
            success_rate=success_rate,
            total_time_seconds=total_time,
            avg_time_per_puzzle_seconds=avg_time,
            log_path=str(self.log_path),
            metrics_path="" # Will be set later
        )

    def run_experiment(self):
        """
        Runs the full experiment: Symbolic vs Neural Baseline.
        """
        log("Initializing full experiment.")
        
        # Load or generate dataset
        data_path = Path("data/raw/puzzles.json")
        if not data_path.exists():
            log("Dataset not found. Generating a small set for the experiment.")
            # Generate a deterministic small set for the experiment run
            self.puzzle_generator.generate(
                output_path=data_path,
                count=10,
                difficulty_range=(10, 50) # Small complexity for demo
            )
        
        # Load puzzles
        with open(data_path, "r") as f:
            puzzles = json.load(f)
        
        if not puzzles:
            raise ValueError("No puzzles loaded. Experiment cannot proceed.")

        log(f"Loaded {len(puzzles)} puzzles.")

        # Run Symbolic BES
        log("=== Starting Symbolic BES Run ===")
        symbolic_result = self._run_single_bes_loop("symbolic", puzzles)
        self.results.append(symbolic_result)
        
        # Run Neural Baseline BES
        log("=== Starting Neural Baseline BES Run ===")
        neural_result = self._run_single_bes_loop("neural_baseline", puzzles)
        self.results.append(neural_result)

        # Calculate Metrics
        metrics = ExperimentMetrics()
        for res in self.results:
            metrics.add_run(res)
        
        # Save metrics to CSV
        metrics_path = Path("data/processed/metrics.csv")
        metrics.save_to_csv(metrics_path)
        
        # Update results with metrics path
        for res in self.results:
            res.metrics_path = str(metrics_path)

        # Statistical Analysis
        if len(self.results) == 2:
            s_res = next(r for r in self.results if r.run_type == "symbolic")
            n_res = next(r for r in self.results if r.run_type == "neural_baseline")
            
            z_test_result = two_proportion_z_test(
                successes_1=s_res.successful_puzzles,
                n1=s_res.total_puzzles,
                successes_2=n_res.successful_puzzles,
                n2=n_res.total_puzzles
            )
            
            log(f"Z-Test Result: p-value = {z_test_result.p_value:.4f}, significant = {z_test_result.is_significant}")
            
            # Append to log
            with open(self.log_path, "a") as f:
                f.write(json.dumps({
                    "analysis": "z_test",
                    "p_value": z_test_result.p_value,
                    "is_significant": z_test_result.is_significant,
                    "symbolic_rate": s_res.success_rate,
                    "neural_rate": n_res.success_rate
                }) + "\n")

        log("Experiment complete.")
        return self.results

def main():
    """Entry point for the script."""
    try:
        orchestrator = BESOrchestrator()
        results = orchestrator.run_experiment()
        
        print("\n=== Experiment Summary ===")
        for r in results:
            print(f"{r.run_type}: Success Rate = {r.success_rate:.2%} ({r.successful_puzzles}/{r.total_puzzles}), "
                  f"Avg Time = {r.avg_time_per_puzzle_seconds:.2f}s")
        
        print(f"\nResults saved to: {results[0].metrics_path}")
        print(f"Logs saved to: {results[0].log_path}")
        
    except Exception as e:
        log(f"Experiment failed with error: {e}", level=logging.ERROR)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()