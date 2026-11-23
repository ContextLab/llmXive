import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Project imports
from config import get_path, get_seed, get_simulation_config
from logging_config import setup_logging

# Ensure the analysis module is importable if run as a script
if __name__ == "__main__":
    # Add project root to path if needed
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found or invalid."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def calculate_token_reduction(baseline_tokens: float, critic_tokens: float) -> float:
    """
    Calculate the percentage of tokens saved by the Meta-Critic compared to the baseline.
    Formula: ((Baseline - Critic) / Baseline) * 100
    """
    if baseline_tokens <= 0:
        logger.warning("Baseline token count is non-positive, cannot calculate reduction.")
        return 0.0
    return ((baseline_tokens - critic_tokens) / baseline_tokens) * 100

def calculate_effect_size(group_a: list, group_b: list) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    d = (mean_a - mean_b) / pooled_std
    """
    import numpy as np

    if not group_a or not group_b:
        logger.warning("Empty groups provided for effect size calculation.")
        return 0.0

    arr_a = np.array(group_a)
    arr_b = np.array(group_b)

    mean_a = np.mean(arr_a)
    mean_b = np.mean(arr_b)

    std_a = np.std(arr_a, ddof=1)
    std_b = np.std(arr_b, ddof=1)

    n_a = len(arr_a)
    n_b = len(arr_b)

    if n_a < 2 and n_b < 2:
        logger.warning("Insufficient data points to calculate pooled standard deviation.")
        return 0.0

    # Pooled standard deviation
    pooled_var = ((n_a - 1) * (std_a ** 2) + (n_b - 1) * (std_b ** 2)) / (n_a + n_b - 2)
    if pooled_var <= 0:
        logger.warning("Pooled variance is non-positive, effect size undefined.")
        return 0.0

    pooled_std = np.sqrt(pooled_var)

    return (mean_a - mean_b) / pooled_std

def main():
    """
    Main entry point to generate the baseline comparison report.
    Reads simulation results from data/results/simulation_results.json (or similar)
    and writes data/results/baseline_comparison.json.
    """
    # Paths
    config = get_path("results_dir")
    results_dir = Path(config)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Input: Simulation results containing both conditions
    # Expected structure: { "meta_critic": [...], "full_context": [...] }
    # Or separate files if the simulation framework outputs them separately.
    # Assuming a consolidated simulation output based on T022/T020.5 context.
    input_file = results_dir / "simulation_results.json"
    output_file = results_dir / "baseline_comparison.json"

    if not input_file.exists():
        # Fallback: try to find specific files if consolidated one doesn't exist yet
        # But per spec, we expect the simulation to produce a comparison source.
        logger.error(f"Input simulation results file not found: {input_file}")
        # Attempt to create a minimal error report if data is missing
        error_report = {
            "status": "failed",
            "reason": "Input simulation results file missing",
            "expected_input": str(input_file)
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2)
        return

    data = load_json_safe(input_file)
    if not data:
        logger.error("Failed to load or parse simulation results.")
        return

    # Extract metrics. Assuming the simulation output structure:
    # {
    #   "meta_critic": { "total_tokens": X, "latency": Y, "abstentions": Z, "token_list": [...] },
    #   "full_context": { "total_tokens": A, "latency": B, "abstentions": C, "token_list": [...] }
    # }
    # If the keys are different, we adapt. Based on T022, we expect specific metrics.

    meta_critic_data = data.get("meta_critic", {})
    full_context_data = data.get("full_context", {})

    # Calculate derived metrics
    mc_tokens = meta_critic_data.get("total_tokens", 0)
    fc_tokens = full_context_data.get("total_tokens", 0)

    mc_latency = meta_critic_data.get("total_latency", 0)
    fc_latency = full_context_data.get("total_latency", 0)

    mc_abstentions = meta_critic_data.get("abstention_count", 0)
    fc_abstentions = full_context_data.get("abstention_count", 0) # Should be 0 for full context baseline

    # Token reduction
    token_reduction_pct = calculate_token_reduction(fc_tokens, mc_tokens)

    # Effect size (Cohen's d) on token consumption
    # We need lists of per-task token usage for this.
    mc_token_list = meta_critic_data.get("per_task_tokens", [])
    fc_token_list = full_context_data.get("per_task_tokens", [])

    cohen_d = calculate_effect_size(fc_token_list, mc_token_list)

    # Compile the report
    report = {
        "meta_critic": {
            "total_tokens": mc_tokens,
            "total_latency_seconds": mc_latency,
            "abstention_count": mc_abstentions,
            "avg_tokens_per_task": mc_tokens / len(meta_critic_data.get("per_task_tokens", [1])) if meta_critic_data.get("per_task_tokens") else 0
        },
        "full_context": {
            "total_tokens": fc_tokens,
            "total_latency_seconds": fc_latency,
            "abstention_count": fc_abstentions,
            "avg_tokens_per_task": fc_tokens / len(full_context_data.get("per_task_tokens", [1])) if full_context_data.get("per_task_tokens") else 0
        },
        "comparison": {
            "token_reduction_percentage": round(token_reduction_pct, 2),
            "cohen_d_effect_size": round(cohen_d, 4),
            "latency_difference_seconds": round(mc_latency - fc_latency, 2),
            "success_criteria_met": {
                "token_reduction_ge_40": token_reduction_pct >= 40,
                "cohen_d_ge_0_5": abs(cohen_d) >= 0.5,
                "overall": (token_reduction_pct >= 40) or (abs(cohen_d) >= 0.5)
            }
        },
        "generated_at": str(Path(__file__).parent) # Or use datetime if needed, but keeping it simple
    }

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Baseline comparison report generated: {output_file}")
    print(f"Report written to {output_file}")

if __name__ == "__main__":
    main()
