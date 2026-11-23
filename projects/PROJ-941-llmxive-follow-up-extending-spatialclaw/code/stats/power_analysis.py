"""
Power Analysis & Budget Validation Module.

Calculates the required sample size (N) for statistical power and validates
it against the allocated time budget (SC-004).

This module reads parameters from `data/power_config.yaml` and outputs
`results/analysis/power_analysis_summary.json`.
"""
import json
import os
import logging
import math
from typing import Dict, Any, Optional
from scipy.stats import norm
import yaml

# Project imports
from data.loader import load_dataset_stream

logger = logging.getLogger(__name__)

# Configuration paths
POWER_CONFIG_PATH = "data/power_config.yaml"
OUTPUT_PATH = "results/analysis/power_analysis_summary.json"

# Default fallbacks if config is missing or incomplete
DEFAULT_BETA = 0.20  # 80% power
DEFAULT_ALPHA = 0.05  # 5% significance
DEFAULT_EFFECT_SIZE = 0.5  # Medium effect size (Cohen's d) assumption
DEFAULT_TIME_PER_SAMPLE_MS = 5000  # Conservative estimate: 5 seconds per sample
BUDGET_SECONDS = 300  # Hard limit from project constraints
BUDGET_MS = BUDGET_SECONDS * 1000

def load_power_config(config_path: str = POWER_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load power analysis parameters from YAML config.
    Raises FileNotFoundError if config is missing.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Power config not found at {config_path}. "
                                "Run T035a to generate data/power_config.yaml first.")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required keys
    required_keys = ['effect_size', 'power', 'alpha']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key '{key}' in {config_path}")
    
    # Derive beta from power
    config['beta'] = 1.0 - config['power']
    return config

def estimate_effect_size_from_pilot(pilot_data: Optional[list] = None) -> float:
    """
    Estimate effect size from pilot data if available.
    Falls back to config value or DEFAULT_EFFECT_SIZE if no pilot data is provided.
    """
    if pilot_data and len(pilot_data) > 1:
        # Simple heuristic: standard deviation of differences / pooled std dev
        # For now, return a conservative medium effect size to avoid over-optimism
        logger.warning("Pilot data detected, but using conservative default effect size for safety.")
        return DEFAULT_EFFECT_SIZE
    return DEFAULT_EFFECT_SIZE

def calculate_sample_size(effect_size: float, alpha: float = DEFAULT_ALPHA, beta: float = DEFAULT_BETA) -> int:
    """
    Calculate required sample size N for a paired t-test (or Wilcoxon)
    given effect size, alpha, and beta.

    Formula for two-sided test:
    N = 2 * ((Z_alpha/2 + Z_beta) / effect_size)^2
    """
    if effect_size <= 0:
        raise ValueError("Effect size must be positive")
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(math.ceil(n))

def validate_budget(n_samples: int, time_per_sample_ms: float, budget_ms: int = BUDGET_MS) -> Dict[str, Any]:
    """
    Validate if the calculated sample size fits within the time budget.
    Returns a decision object.
    """
    estimated_total_time_ms = n_samples * time_per_sample_ms
    fits = estimated_total_time_ms <= budget_ms

    decision = {
        "n_samples_calculated": n_samples,
        "estimated_time_ms": estimated_total_time_ms,
        "budget_ms": budget_ms,
        "fits_budget": fits,
        "recommendation": "Proceed" if fits else "Reduce N or Optimize",
        "action_taken": None,
        "final_n": n_samples
    }

    if not fits:
        # Strategy: Reduce N to fit budget, acknowledging reduced power
        # Calculate max N that fits budget
        max_n = int(budget_ms / time_per_sample_ms)
        if max_n < 5:
            logger.error("Budget too small for even minimal sample size (N=5).")
            decision["recommendation"] = "Budget Insufficient"
            decision["action_taken"] = "Cannot proceed with valid statistics."
            decision["final_n"] = 0
        else:
            decision["recommendation"] = "Budget constrained"
            decision["action_taken"] = f"Reduced N from {n_samples} to {max_n} to fit budget."
            decision["final_n"] = max_n
            decision["warning"] = f"Power reduced. With N={max_n}, power may be < {1-beta}."
    
    return decision

def run_power_analysis() -> Dict[str, Any]:
    """
    Main entry point for power analysis.
    1. Loads parameters from data/power_config.yaml.
    2. Calculates N.
    3. Validates against budget.
    4. Writes report to results/analysis/power_analysis_summary.json.
    """
    logger.info("Starting Power Analysis & Budget Validation...")

    # 1. Load configuration
    try:
        config = load_power_config()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        raise

    effect_size = config['effect_size']
    alpha = config['alpha']
    power = config['power']
    beta = config['beta']

    # 2. Calculate Sample Size
    n_required = calculate_sample_size(effect_size, alpha, beta)
    logger.info(f"Calculated required sample size N: {n_required} "
                f"(Effect size: {effect_size}, Power: {power}, Alpha: {alpha})")

    # 3. Validate Budget
    validation_result = validate_budget(n_required, DEFAULT_TIME_PER_SAMPLE_MS)

    # 4. Construct Report
    report = {
        "task_id": "T035b",
        "analysis_type": "Power Analysis & Budget Validation",
        "used_parameters": {
            "alpha": alpha,
            "beta": beta,
            "power": power,
            "effect_size": effect_size,
            "budget_seconds": BUDGET_SECONDS
        },
        "n_required": validation_result["n_samples_calculated"],
        "estimated_runtime": validation_result["estimated_time_ms"] / 1000.0,  # Convert to seconds
        "budget_status": "within_budget" if validation_result["fits_budget"] else "exceeded",
        "action_taken": validation_result["action_taken"],
        "final_n": validation_result["final_n"],
        "recommendation": validation_result["recommendation"],
        "status": "completed" if validation_result["final_n"] > 0 else "failed"
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write report
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Power analysis report written to: {OUTPUT_PATH}")
    return report

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    report = run_power_analysis()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
