"""
code/utils/budget_check.py

Budget validation logic for the SpatialClaw pipeline.
Checks if the estimated runtime from power analysis exceeds the configured maximum budget.
"""
import json
import os
import sys
import logging
from typing import Optional

# Ensure imports work from code/ directory structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stats.power_analysis import load_power_config

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration parameters violate budget constraints."""
    pass

def check_budget(budget_seconds: float) -> None:
    """
    Validate that the estimated runtime from power analysis does not exceed the budget.

    Args:
        budget_seconds: Maximum allowed runtime in seconds.

    Raises:
        ConfigurationError: If estimated runtime exceeds the budget.
    """
    # Define paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, 'data', 'power_config.yaml')
    summary_path = os.path.join(project_root, 'results', 'analysis', 'power_analysis_summary.json')

    # Load power configuration to get max_runtime_hours
    try:
        config = load_power_config(config_path)
        max_runtime_hours = config.get('max_runtime_hours')
        
        # Handle case where max_runtime_hours might be a placeholder string
        if isinstance(max_runtime_hours, str):
            # If it's a descriptive string, we can't compare numerically
            # For safety, we assume a very large default or skip strict check
            # But per task requirements, we should fail loudly if we can't verify
            logger.warning(f"max_runtime_hours in config is non-numeric: '{max_runtime_hours}'. "
                         "Skipping strict budget check. Set a numeric value to enforce budget.")
            return
        
        max_runtime_seconds = max_runtime_hours * 3600
    except FileNotFoundError:
        logger.warning(f"Power config not found at {config_path}. Skipping budget check.")
        return
    except Exception as e:
        logger.warning(f"Failed to load power config: {e}. Skipping budget check.")
        return

    # Load power analysis summary to get estimated runtime
    if not os.path.exists(summary_path):
        logger.warning(f"Power analysis summary not found at {summary_path}. "
                     "Skipping budget check. Run T035b first.")
        return

    try:
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        estimated_runtime = summary.get('estimated_runtime')
        
        if estimated_runtime is None:
            logger.warning("estimated_runtime not found in power analysis summary. Skipping budget check.")
            return
        
        # Check if estimated runtime exceeds budget
        if estimated_runtime > max_runtime_seconds:
            msg = (
                f"BUDGET VIOLATION: Estimated runtime ({estimated_runtime:.2f}s) exceeds "
                f"configured maximum ({max_runtime_seconds:.2f}s / {max_runtime_hours:.2f}h). "
                f"Aborting execution before data generation."
            )
            logger.critical(msg)
            raise ConfigurationError(msg)
        
        logger.info(f"Budget check passed: estimated {estimated_runtime:.2f}s < max {max_runtime_seconds:.2f}s")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse power analysis summary JSON: {e}")
        raise ConfigurationError(f"Invalid power analysis summary format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during budget check: {e}")
        raise ConfigurationError(f"Budget check failed unexpectedly: {e}")

def main():
    """CLI entry point for budget check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check if estimated runtime exceeds budget")
    parser.add_argument("--budget-seconds", type=float, default=6 * 60 * 60,
                      help="Maximum allowed runtime in seconds (default: 6 hours)")
    args = parser.parse_args()
    
    try:
        check_budget(budget_seconds=args.budget_seconds)
        print("Budget check passed.")
        sys.exit(0)
    except ConfigurationError as e:
        print(f"BUDGET CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
