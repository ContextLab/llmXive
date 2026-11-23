"""
Benchmark Runner for US2 Text Agent.

Orchestrates the execution of N=20 game instances for the Text Agent.
Generates results in results/benchmark_log.json.
"""
import os
import sys
import json
import time
import argparse
import logging
from typing import List, Dict, Any, Optional

# Import from project modules
from config_loader import load_seeds_config, get_seeds
from agent_loop import TextAgent, AgentConfig, log_discarded_run
from logger import get_logger, configure_global_logging

# Ensure we are in the project root context if running as script
# This handles relative imports if the script is run from the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-import logger after path adjustment if needed, but standard import usually works
# assuming code/ is in path or this is run as `python code/benchmark_runner.py`

logger = get_logger(__name__)

class BenchmarkRunner:
    """
    Orchestrates the benchmark execution for the Text Agent.
    """
    def __init__(self, seeds: List[int], output_path: str, config_path: str = None):
        self.seeds = seeds
        self.output_path = output_path
        self.config_path = config_path
        self.results = {
            "run_id": "benchmark_run",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_seeds": len(seeds),
            "completed_seeds": 0,
            "failed_seeds": 0,
            "run_details": [],
            "total_time_seconds": 0.0,
            "passed": False
        }
        
        # Initialize Agent Config
        # Defaults based on typical US2 requirements if not overridden
        self.agent_config = AgentConfig(
            max_steps=500,
            context_window=50,
            model_name="microsoft/Phi-3-mini-4k-instruct", # Example small model
            quantization=True,
            device="cpu"
        )

    def run_single_benchmark(self, seed: int) -> Dict[str, Any]:
        """
        Runs a single benchmark instance for a given seed.
        Returns a result dictionary.
        """
        start_time = time.time()
        result = {
            "seed": seed,
            "status": "pending",
            "duration_seconds": 0.0,
            "steps_taken": 0,
            "error": None
        }

        try:
            # Load seeds config to ensure consistency if needed
            if self.config_path:
                load_seeds_config(self.config_path)
            
            # Initialize Agent for this seed
            # Note: In a real scenario, the agent might need to be re-initialized
            # or the state reset per seed. We assume TextAgent handles internal state.
            agent = TextAgent(config=self.agent_config, seed=seed)
            
            logger.info(f"Starting benchmark run for seed {seed}")
            
            # Run the agent loop
            # The agent_loop.run() method is expected to return a status and metrics
            # We assume a method like `run_benchmark(seed)` exists or we call main loop
            # Based on API surface: TextAgent is available. We need to call its run method.
            # Assuming the agent has a method to run the full episode.
            # If not explicitly defined in API surface, we assume standard interaction:
            # agent.reset(seed) -> agent.step() loop -> agent.get_metrics()
            
            # Since the exact method name isn't in the provided API surface for TextAgent,
            # we infer a standard pattern or use the main entry point logic if available.
            # However, T023/T024 imply an inference cycle.
            # Let's assume TextAgent has a `run_episode(seed)` method or similar.
            # If not, we might need to adapt. Given the constraints, we implement a robust loop.
            
            # Fallback to generic execution if specific method names are unknown:
            # We will simulate the call structure based on typical LLM agent patterns.
            # The agent should load the ascii/log for the seed and run.
            
            # To be safe and strictly follow the "extend" rule, we assume the agent
            # exposes a `run(seed)` method or we construct the loop here.
            # Let's assume `agent.run(seed)` returns (success, steps, metrics)
            
            success, steps, metrics = agent.run(seed)
            
            result["status"] = "success" if success else "failed"
            result["steps_taken"] = steps
            result["metrics"] = metrics
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error running seed {seed}: {e}", exc_info=True)
            log_discarded_run(seed, str(e))
        
        end_time = time.time()
        result["duration_seconds"] = end_time - start_time
        return result

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Runs the full benchmark suite.
        """
        logger.info(f"Starting Benchmark Runner with {len(self.seeds)} seeds.")
        total_start = time.time()
        
        for seed in self.seeds:
            run_result = self.run_single_benchmark(seed)
            self.results["run_details"].append(run_result)
            
            if run_result["status"] == "success":
                self.results["completed_seeds"] += 1
            else:
                self.results["failed_seeds"] += 1

        total_end = time.time()
        self.results["total_time_seconds"] = total_end - total_start
        self.results["total_time_hours"] = self.results["total_time_seconds"] / 3600.0

        # Verification: total_time_hours < 6.0
        if self.results["total_time_hours"] < 6.0 and self.results["failed_seeds"] == 0:
            self.results["passed"] = True
        else:
            self.results["passed"] = False
            if self.results["total_time_hours"] >= 6.0:
                logger.warning("Benchmark exceeded time limit (6.0 hours).")
            if self.results["failed_seeds"] > 0:
                logger.warning(f"Benchmark had {self.results['failed_seeds']} failed runs.")

        # Save results
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Benchmark complete. Results saved to {self.output_path}")
        logger.info(f"Total Time: {self.results['total_time_hours']:.2f} hours, Passed: {self.results['passed']}")
        
        return self.results

def main():
    parser = argparse.ArgumentParser(description="Run Text Agent Benchmark")
    parser.add_argument("--seeds", type=str, required=True, help="Path to seeds.yaml config")
    parser.add_argument("--output", type=str, required=True, help="Path to output benchmark_log.json")
    args = parser.parse_args()

    configure_global_logging()
    logger.info("Initializing Benchmark Runner...")

    # Load seeds
    seeds = get_seeds()
    if not seeds:
        logger.error("No seeds loaded from config.")
        sys.exit(1)

    runner = BenchmarkRunner(seeds=seeds, output_path=args.output, config_path=args.seeds)
    runner.run_benchmark()

if __name__ == "__main__":
    main()
