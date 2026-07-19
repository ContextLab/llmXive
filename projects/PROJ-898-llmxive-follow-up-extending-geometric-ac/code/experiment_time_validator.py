"""
Experiment Time Validator and Budget Enforcer.

This module implements the logic to calculate total experiment time based on
configuration parameters and enforce the 6-hour CI limit defined in SC-005.
It includes logic to ABORT trials that would exceed the budget.

Dependencies:
- code/config.py: For loading experiment parameters (timeout_limits, trial_count, etc.)
- code/utils.py: For logging setup and deterministic seeding
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple

# Import from project API surface
from config import load_config, ExperimentConfig
from utils import setup_logging, set_deterministic_seed

# Constants
CI_TIME_LIMIT_HOURS = 6
CI_TIME_LIMIT_SECONDS = CI_TIME_LIMIT_HOURS * 3600
PER_STEP_TIME_LIMIT_SECONDS = 300  # From FR-004 assumption

@dataclass
class BudgetResult:
    """Result of the budget validation check."""
    is_within_budget: bool
    estimated_total_seconds: float
    remaining_seconds: float
    max_trials_allowed: int
    trials_to_abort: int
    message: str

class ExperimentTimeValidator:
    """
    Validates experiment execution time against CI limits and enforces budget caps.
    """

    def __init__(self, config_path: str = "code/config.yaml"):
        """
        Initialize the validator with configuration.

        Args:
            config_path: Path to the configuration YAML file.
        """
        self.logger = setup_logging("ExperimentTimeValidator")
        self.config_path = config_path
        self.config: Optional[ExperimentConfig] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            raw_config = load_config(self.config_path)
            # Extract experiment config section
            self.config = ExperimentConfig(
                trial_count=raw_config.get('experiment', {}).get('trial_count', 50),
                timeout_limits=raw_config.get('solver', {}).get('timeout_limits', 300),
                seed=raw_config.get('experiment', {}).get('seed', 42),
                topology_counts=raw_config.get('topology', {}).get('topology_counts', [])
            )
            self.logger.info(f"Loaded configuration: trial_count={self.config.trial_count}, "
                           f"timeout_limits={self.config.timeout_limits}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def calculate_total_experiment_time(self, 
                                      per_step_time: Optional[float] = None,
                                      steps_per_trial: Optional[int] = None) -> Tuple[float, int]:
        """
        Calculate total expected experiment time.

        Args:
            per_step_time: Average time per solver step in seconds. If None, uses config timeout.
            steps_per_trial: Number of steps per trial. If None, assumes 1 step per trial for estimation.

        Returns:
            Tuple of (total_time_seconds, total_steps)
        """
        if per_step_time is None:
            # Use the configured timeout as a conservative estimate
            per_step_time = float(self.config.timeout_limits)
        
        if steps_per_trial is None:
            # Default assumption: 1 step per trial for basic estimation
            # In a real scenario, this would be determined by the simulation length
            steps_per_trial = 1

        total_steps = self.config.trial_count * steps_per_trial
        total_time = per_step_time * total_steps

        return total_time, total_steps

    def validate_against_ci_limit(self, 
                                per_step_time: Optional[float] = None,
                                steps_per_trial: Optional[int] = None) -> BudgetResult:
        """
        Validate total experiment time against the 6-hour CI limit.

        Args:
            per_step_time: Average time per solver step in seconds.
            steps_per_trial: Number of steps per trial.

        Returns:
            BudgetResult with validation details and abort recommendations.
        """
        total_time, total_steps = self.calculate_total_experiment_time(
            per_step_time, steps_per_trial
        )

        is_within_budget = total_time <= CI_TIME_LIMIT_SECONDS
        remaining_seconds = max(0.0, CI_TIME_LIMIT_SECONDS - total_time)

        # Calculate how many trials we can actually run within budget
        if per_step_time is None:
            per_step_time = float(self.config.timeout_limits)
        
        if steps_per_trial is None:
            steps_per_trial = 1

        max_trials_allowed = int(CI_TIME_LIMIT_SECONDS / (per_step_time * steps_per_trial))
        trials_to_abort = max(0, self.config.trial_count - max_trials_allowed)

        if is_within_budget:
            message = (f"Experiment is within budget. "
                     f"Estimated total time: {total_time:.2f}s ({total_time/3600:.2f}h). "
                     f"Remaining budget: {remaining_seconds:.2f}s ({remaining_seconds/3600:.2f}h).")
        else:
            message = (f"Experiment EXCEEDS budget by {total_time - CI_TIME_LIMIT_SECONDS:.2f}s. "
                     f"Must abort {trials_to_abort} trials to stay within 6-hour limit.")

        return BudgetResult(
            is_within_budget=is_within_budget,
            estimated_total_seconds=total_time,
            remaining_seconds=remaining_seconds,
            max_trials_allowed=max_trials_allowed,
            trials_to_abort=trials_to_abort,
            message=message
        )

    def enforce_budget(self, 
                     current_trial: int,
                     per_step_time: Optional[float] = None,
                     steps_per_trial: Optional[int] = None) -> bool:
        """
        Check if the current trial should be aborted to stay within budget.

        This method is called before starting a trial to determine if there is
        enough time remaining in the 6-hour window.

        Args:
            current_trial: The current trial number (0-indexed).
            per_step_time: Average time per solver step in seconds.
            steps_per_trial: Number of steps per trial.

        Returns:
            True if the trial should proceed, False if it should be aborted.
        """
        if per_step_time is None:
            per_step_time = float(self.config.timeout_limits)
        
        if steps_per_trial is None:
            steps_per_trial = 1

        # Calculate remaining trials
        remaining_trials = self.config.trial_count - current_trial
        estimated_remaining_time = remaining_trials * per_step_time * steps_per_trial

        # Estimate time already spent (simplified - in real use, track actual elapsed time)
        # For this implementation, we assume we're checking at the start of the experiment
        # In a real pipeline, you would pass actual elapsed time
        estimated_total_time = self.config.trial_count * per_step_time * steps_per_trial
        
        # If total time exceeds limit, calculate how many trials we can actually run
        max_trials_allowed = int(CI_TIME_LIMIT_SECONDS / (per_step_time * steps_per_trial))
        
        if current_trial >= max_trials_allowed:
            self.logger.warning(f"Trial {current_trial} aborted: Would exceed 6-hour CI limit. "
                              f"Max trials allowed: {max_trials_allowed}")
            return False

        return True

    def get_abort_recommendation(self, 
                               per_step_time: Optional[float] = None,
                               steps_per_trial: Optional[int] = None) -> str:
        """
        Generate a human-readable recommendation for trial aborts.

        Args:
            per_step_time: Average time per solver step in seconds.
            steps_per_trial: Number of steps per trial.

        Returns:
            Formatted string with abort recommendations.
        """
        result = self.validate_against_ci_limit(per_step_time, steps_per_trial)
        
        if result.is_within_budget:
            return f"✅ {result.message}"
        else:
            return (f"⚠️  {result.message}\n"
                  f"   → Recommendation: Reduce trial count from {self.config.trial_count} "
                  f"to {result.max_trials_allowed} trials.\n"
                  f"   → Trials to skip/abort: {result.trials_to_abort}")

def main():
    """
    Main entry point for the experiment time validator.
    
    This script:
    1. Loads configuration from code/config.yaml
    2. Calculates total experiment time based on current settings
    3. Validates against the 6-hour CI limit
    4. Reports abort recommendations if budget would be exceeded
    
    Usage:
        python code/experiment_time_validator.py
    """
    logger = setup_logging("main")
    logger.info("Starting Experiment Time Validator")
    
    try:
        validator = ExperimentTimeValidator("code/config.yaml")
        
        # Calculate and validate
        result = validator.validate_against_ci_limit()
        
        logger.info("=" * 60)
        logger.info("EXPERIMENT TIME VALIDATION REPORT")
        logger.info("=" * 60)
        logger.info(f"Configuration: {validator.config_path}")
        logger.info(f"Trial count: {validator.config.trial_count}")
        logger.info(f"Timeout limit per step: {validator.config.timeout_limits}s")
        logger.info(f"CI Time limit: {CI_TIME_LIMIT_HOURS} hours ({CI_TIME_LIMIT_SECONDS}s)")
        logger.info("-" * 60)
        logger.info(f"Estimated total time: {result.estimated_total_seconds:.2f}s "
                   f"({result.estimated_total_seconds/3600:.2f}h)")
        logger.info(f"Within budget: {'YES' if result.is_within_budget else 'NO'}")
        logger.info(f"Remaining budget: {result.remaining_seconds:.2f}s")
        logger.info("-" * 60)
        logger.info(f"Max trials allowed: {result.max_trials_allowed}")
        logger.info(f"Trials to abort: {result.trials_to_abort}")
        logger.info("=" * 60)
        logger.info(result.message)
        logger.info("=" * 60)
        
        # If budget is exceeded, output abort recommendation
        if not result.is_within_budget:
            logger.warning("⚠️  BUDGET EXCEEDED - TRIALS MUST BE ABORTED")
            logger.warning(validator.get_abort_recommendation())
            sys.exit(1)  # Exit with error code to signal budget violation
        
        logger.info("✅ Experiment time validation PASSED")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
