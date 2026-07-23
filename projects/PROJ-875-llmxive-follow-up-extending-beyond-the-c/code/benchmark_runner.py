"""
Benchmark Runner for Text Agent.
Orchestrates execution of N game instances, measures timing, and validates constraints.
"""
import os
import sys
import json
import time
import argparse
import logging
from typing import List, Dict, Any, Optional

# Import from local project modules
from agent_loop import TextAgent, AgentConfig, log_discarded_run
from config_loader import load_seeds_config, get_seeds
from logger import setup_logger, configure_global_logging, get_logger
from resource_monitor import ResourceMonitor

# Constants
MAX_RUN_TIME_HOURS = 6.0
MAX_STEPS_PER_RUN = 500  # Hard limit from T026
DEFAULT_SEEDS_FILE = "config/seeds.yaml"
DEFAULT_OUTPUT_FILE = "results/benchmark_log.json"

class BenchmarkRunner:
    """
    Orchestrates the benchmark execution for the Text Agent.
    Handles resource monitoring, timing, and result aggregation.
    """

    def __init__(self, seeds: List[int], output_path: str, max_time_hours: float = MAX_RUN_TIME_HOURS):
        self.seeds = seeds
        self.output_path = output_path
        self.max_time_hours = max_time_hours
        self.logger = get_logger("benchmark_runner")
        self.results: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.total_time_seconds: float = 0.0

    def run_single_instance(self, seed: int) -> Dict[str, Any]:
        """
        Executes a single game instance for the given seed.
        Returns a result dictionary with timing, status, and metrics.
        """
        run_start = time.time()
        resource_monitor = ResourceMonitor(run_id=f"benchmark_{seed}")

        self.logger.info(f"Starting benchmark run for seed: {seed}")

        try:
            # Initialize Agent
            agent_config = AgentConfig(seed=seed, max_steps=MAX_STEPS_PER_RUN)
            agent = TextAgent(agent_config)

            # Start resource monitoring
            resource_monitor.start()

            # Run the agent loop
            # The agent_loop.py main function or run method should handle the logic
            # Assuming TextAgent has a run() method that returns status and mental_map
            # Based on T024, we expect JSON output with action and mental_map
            # We need to adapt to the actual interface. Assuming a run method exists.
            
            # NOTE: Since agent_loop.py is provided as an interface, we assume the 
            # TextAgent class has a 'run' method that executes the logic.
            # If the interface is different (e.g., a function), we adapt here.
            
            run_status = agent.run() 
            
            # Stop resource monitoring
            resource_monitor.stop()
            resource_metrics = resource_monitor.get_summary()

            run_end = time.time()
            duration_seconds = run_end - run_start

            result = {
                "seed": seed,
                "status": run_status.get("status", "unknown"),
                "duration_seconds": duration_seconds,
                "mental_map": run_status.get("mental_map", ""),
                "actions_count": len(run_status.get("actions", [])),
                "resource_metrics": resource_metrics,
                "timed_out": run_status.get("status") == "timeout" or duration_seconds > (MAX_STEPS_PER_RUN * 1.0), # Simplified timeout check
                "error": run_status.get("error")
            }

            self.logger.info(f"Completed run for seed {seed}: status={result['status']}, duration={duration_seconds:.2f}s")

        except Exception as e:
            run_end = time.time()
            duration_seconds = run_end - run_start
            self.logger.error(f"Failed run for seed {seed}: {str(e)}", exc_info=True)
            
            result = {
                "seed": seed,
                "status": "error",
                "duration_seconds": duration_seconds,
                "mental_map": "",
                "actions_count": 0,
                "resource_metrics": {},
                "timed_out": False,
                "error": str(e)
            }

            # Log discarded run if applicable
            if result["status"] in ["error", "timeout", "nan_detected", "oom"]:
                log_discarded_run(seed, result["status"], str(result.get("error", "Unknown error")))

        return result

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Runs the full benchmark suite.
        """
        self.start_time = time.time()
        self.logger.info(f"Starting benchmark with {len(self.seeds)} seeds")

        for seed in self.seeds:
            # Check total time budget
            elapsed = time.time() - self.start_time
            if elapsed > (self.max_time_hours * 3600):
                self.logger.warning(f"Total time budget ({self.max_time_hours}h) exceeded. Stopping.")
                break

            result = self.run_single_instance(seed)
            self.results.append(result)

        self.total_time_seconds = time.time() - self.start_time
        total_time_hours = self.total_time_seconds / 3600.0

        # Calculate summary
        passed_count = sum(1 for r in self.results if r["status"] == "success")
        total_count = len(self.results)
        passed = passed_count == total_count and total_time_hours < self.max_time_hours

        summary = {
            "total_seeds": total_count,
            "passed_count": passed_count,
            "failed_count": total_count - passed_count,
            "total_time_hours": total_time_hours,
            "passed": passed,
            "results": self.results
        }

        self.logger.info(f"Benchmark completed. Total time: {total_time_hours:.2f}h. Passed: {passed}")

        return summary

    def save_results(self, summary: Dict[str, Any]):
        """
        Saves the benchmark results to the specified output path.
        """
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"Results saved to {self.output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run Text Agent Benchmark")
    parser.add_argument("--seeds", type=str, default=DEFAULT_SEEDS_FILE,
                        help="Path to seeds config file (YAML)")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_FILE,
                        help="Output path for benchmark log (JSON)")
    parser.add_argument("--max-time-hours", type=float, default=MAX_RUN_TIME_HOURS,
                        help=f"Maximum total time in hours (default: {MAX_RUN_TIME_HOURS})")
    parser.add_argument("--log-level", type=str, default="INFO",
                        help="Logging level (DEBUG, INFO, WARNING, ERROR)")

    args = parser.parse_args()

    # Configure logging
    configure_global_logging(level=args.log_level)
    logger = get_logger("benchmark_runner")

    # Load seeds
    try:
        load_seeds_config(args.seeds)
        seeds = get_seeds()
        if not seeds:
            logger.error("No seeds found in config file.")
            sys.exit(1)
        logger.info(f"Loaded {len(seeds)} seeds from {args.seeds}")
    except Exception as e:
        logger.error(f"Failed to load seeds config: {e}")
        sys.exit(1)

    # Run benchmark
    runner = BenchmarkRunner(seeds, args.output, args.max_time_hours)
    summary = runner.run_benchmark()
    runner.save_results(summary)

    if summary["passed"]:
        logger.info("BENCHMARK PASSED")
        sys.exit(0)
    else:
        logger.warning("BENCHMARK FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
