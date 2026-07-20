"""
Experiment Time Validator (T008b).

Implements the calculation of total experiment time based on:
total_time = per_step_time * steps_per_trial * number_of_trials

It verifies this total against the 6-hour CI limit (SC-005).
If the calculated time exceeds the budget, it ABORTS (exit code 1).
It also calculates the maximum safe number of trials if the current
configuration exceeds the budget.
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple

# Import existing config utilities
from config import load_config, ExperimentConfig
from utils import setup_logging

# Constants
CI_LIMIT_HOURS = 6
CI_LIMIT_SECONDS = CI_LIMIT_HOURS * 3600

@dataclass
class BudgetResult:
    """Holds the result of the budget calculation."""
    per_step_time_seconds: float
    steps_per_trial: int
    planned_trials: int
    total_estimated_time_seconds: float
    total_estimated_time_hours: float
    within_budget: bool
    max_safe_trials: Optional[int]
    budget_exceeded_by_seconds: float

class ExperimentTimeValidator:
    """Validates experiment runtime against the CI budget."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.logger = setup_logging("ExperimentTimeValidator")

    def calculate_total_time(self) -> BudgetResult:
        """
        Calculates total experiment time and checks against the 6-hour limit.

        Formula: total_time = per_step_time * steps_per_trial * number_of_trials
        """
        # Extract parameters from config
        # Note: T007a defines 'timeout_limits' (300s) which acts as per_step_time
        # T007a defines 'trial_count' as number_of_trials
        # We assume a fixed steps_per_trial for this calculation, or derive it.
        # Based on T008a context, per_step_time is the profiling result (max 300s).
        # For the budget check, we use the timeout limit as the worst-case per_step_time.
        
        per_step_time = self.config.solver.timeout_limits  # e.g., 300s
        steps_per_trial = self.config.experiment.steps_per_trial if hasattr(self.config.experiment, 'steps_per_trial') else 100
        number_of_trials = self.config.experiment.trial_count

        total_estimated_time = per_step_time * steps_per_trial * number_of_trials
        total_estimated_hours = total_estimated_time / 3600.0
        within_budget = total_estimated_time <= CI_LIMIT_SECONDS

        max_safe_trials = None
        if not within_budget:
            # Calculate max trials allowed: floor(CI_LIMIT / (per_step * steps))
            denominator = per_step_time * steps_per_trial
            if denominator > 0:
                max_safe_trials = int(CI_LIMIT_SECONDS // denominator)

        return BudgetResult(
            per_step_time_seconds=per_step_time,
            steps_per_trial=steps_per_trial,
            planned_trials=number_of_trials,
            total_estimated_time_seconds=total_estimated_time,
            total_estimated_time_hours=total_estimated_hours,
            within_budget=within_budget,
            max_safe_trials=max_safe_trials,
            budget_exceeded_by_seconds=max(0, total_estimated_time - CI_LIMIT_SECONDS)
        )

    def validate_and_abort(self) -> bool:
        """
        Runs the calculation. If the budget is exceeded, logs the error
        and aborts execution with exit code 1.
        
        Returns:
            True if within budget (execution can proceed).
            False if exceeded (already aborted).
        """
        result = self.calculate_total_time()

        self.logger.info(f"--- Experiment Time Budget Check ---")
        self.logger.info(f"Per-step time (worst-case): {result.per_step_time_seconds:.2f}s")
        self.logger.info(f"Steps per trial: {result.steps_per_trial}")
        self.logger.info(f"Planned trials: {result.planned_trials}")
        self.logger.info(f"Total estimated time: {result.total_estimated_time_hours:.2f} hours ({result.total_estimated_time_seconds:.2f}s)")
        self.logger.info(f"CI Limit (SC-005): {CI_LIMIT_HOURS} hours ({CI_LIMIT_SECONDS}s)")

        if result.within_budget:
            self.logger.info("STATUS: WITHIN BUDGET. Execution can proceed.")
            return True
        else:
            self.logger.error("STATUS: EXCEEDS BUDGET.")
            self.logger.error(f"Exceeded by: {result.budget_exceeded_by_seconds:.2f}s ({result.budget_exceeded_by_seconds/3600:.2f}h)")
            if result.max_safe_trials is not None:
                self.logger.error(f"Maximum safe trial count for this budget: {result.max_safe_trials}")
            self.logger.error("ABORTING execution to enforce hard cap (exit code 1).")
            sys.exit(1)

def main():
    """Entry point for the time validator script."""
    # Setup logging
    logger = setup_logging("main")
    
    try:
        validator = ExperimentTimeValidator()
        success = validator.validate_and_abort()
        if success:
            logger.info("Validation passed. Ready to run experiments.")
            # Return 0 explicitly
            sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()