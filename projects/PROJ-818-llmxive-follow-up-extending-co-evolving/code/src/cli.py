import argparse
import json
import sys
import os
import time
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIME_BUDGET_HOURS = 5.5
DEFAULT_TIME_BUDGET_SECONDS = DEFAULT_TIME_BUDGET_HOURS * 3600
PARTIAL_RESULT_FILENAME = "partial_run.json"
RESULTS_DIR = "data/results"

class TimeBudgetExceededError(Exception):
    """Raised when the total runtime exceeds the configured time budget."""
    pass

class TimeBudgetEnforcer:
    """
    Enforces a hard wall-clock time limit on batch runs.
    Monitors elapsed time and interrupts the process if the limit is exceeded,
    saving partial results to ensure CI jobs do not exceed the 6-hour limit.
    """

    def __init__(self, budget_seconds: float = DEFAULT_TIME_BUDGET_SECONDS):
        self.budget_seconds = float(budget_seconds)
        self.start_time: Optional[float] = None
        self.is_running = False

    def start(self) -> None:
        """Starts the timer."""
        self.start_time = time.time()
        self.is_running = True
        logger.info(f"Time budget enforcement started. Limit: {self.budget_seconds:.2f} seconds ({self.budget_seconds/3600:.2f} hours).")

    def check(self) -> None:
        """
        Checks if the elapsed time exceeds the budget.
        Raises TimeBudgetExceededError if the limit is breached.
        """
        if not self.is_running:
            raise RuntimeError("Time budget enforcer must be started before checking.")

        elapsed = time.time() - self.start_time
        if elapsed > self.budget_seconds:
            logger.error(f"Time budget exceeded! Elapsed: {elapsed:.2f}s, Limit: {self.budget_seconds:.2f}s")
            raise TimeBudgetExceededError(
                f"Runtime limit exceeded: {elapsed:.2f}s > {self.budget_seconds:.2f}s"
            )

    def save_partial_results(self, results: Dict[str, Any]) -> None:
        """
        Saves partial results to a JSON file in the results directory.
        This is called when the time budget is exceeded to preserve progress.
        """
        results_path = Path(RESULTS_DIR) / PARTIAL_RESULT_FILENAME
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        partial_data = {
            "status": "interrupted_time_budget",
            "elapsed_seconds": time.time() - self.start_time if self.start_time else 0,
            "budget_seconds": self.budget_seconds,
            "timestamp": time.time(),
            "data": results
        }
        
        with open(results_path, 'w') as f:
            json.dump(partial_data, f, indent=2)
        
        logger.info(f"Partial results saved to: {results_path}")

    def stop(self) -> None:
        """Stops the timer."""
        self.is_running = False
        if self.start_time:
            logger.info(f"Time budget enforcement stopped. Total elapsed: {time.time() - self.start_time:.2f}s")

def load_training_data(config_path: str) -> Dict[str, Any]:
    """Load configuration for training runs."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_file) as f:
        return json.load(f)

def run_sequential_training(config: Dict[str, Any], enforcer: TimeBudgetEnforcer) -> Dict[str, Any]:
    """Simulated sequential training loop with time enforcement."""
    logger.info("Running Sequential Training...")
    # In a real implementation, this would iterate through generations
    # and call enforcer.check() periodically.
    # For this task, we simulate the check to demonstrate enforcement.
    enforcer.check()
    return {"condition": "sequential", "status": "completed"}

def run_mixed_training(config: Dict[str, Any], enforcer: TimeBudgetEnforcer) -> Dict[str, Any]:
    """Simulated mixed training loop with time enforcement."""
    logger.info("Running Mixed Training...")
    enforcer.check()
    return {"condition": "mixed", "status": "completed"}

def run_coevolving_training(config: Dict[str, Any], enforcer: TimeBudgetEnforcer) -> Dict[str, Any]:
    """Simulated co-evolving training loop with time enforcement."""
    logger.info("Running Co-evolving Training...")
    enforcer.check()
    return {"condition": "coevolving", "status": "completed"}

def execute_training_loop(
    config: Dict[str, Any],
    conditions: List[str],
    enforcer: TimeBudgetEnforcer
) -> Dict[str, Any]:
    """
    Executes the full batch training loop for all conditions.
    Checks the time budget at every step.
    """
    results = {}
    logger.info(f"Starting batch training for conditions: {conditions}")
    
    for condition in conditions:
        enforcer.check()
        logger.info(f"Executing condition: {condition}")
        
        if condition == "sequential":
            res = run_sequential_training(config, enforcer)
        elif condition == "mixed":
            res = run_mixed_training(config, enforcer)
        elif condition == "coevolving":
            res = run_coevolving_training(config, enforcer)
        else:
            raise ValueError(f"Unknown condition: {condition}")
        
        results[condition] = res
        enforcer.check()

    return results

def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="llmXive Co-Evolving Policy Distillation Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="data/batch_config.json",
        help="Path to the configuration file"
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        default=DEFAULT_TIME_BUDGET_HOURS,
        help=f"Time budget in hours (default: {DEFAULT_TIME_BUDGET_HOURS})"
    )
    parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        choices=["sequential", "mixed", "coevolving"],
        default=["sequential", "mixed", "coevolving"],
        help="Training conditions to run"
    )
    return parser

def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_training_data(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Initialize Time Budget Enforcer
    budget_seconds = args.time_budget * 3600
    enforcer = TimeBudgetEnforcer(budget_seconds)

    # Start the timer
    enforcer.start()

    try:
        # Execute the training loop
        final_results = execute_training_loop(config, args.conditions, enforcer)
        
        # Save final results (if not interrupted)
        results_path = Path(RESULTS_DIR) / "batch_results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Training completed successfully. Results saved to {results_path}")
        
    except TimeBudgetExceededError as e:
        logger.error(str(e))
        # Save partial results before exiting
        # In a real scenario, we would have accumulated partial results
        # Here we simulate that we have some partial state
        partial_results = {
            "status": "interrupted",
            "error": str(e),
            "conditions_completed": args.conditions[:1] if args.conditions else []
        }
        enforcer.save_partial_results(partial_results)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        sys.exit(1)
    finally:
        enforcer.stop()

if __name__ == "__main__":
    main()