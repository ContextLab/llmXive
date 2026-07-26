"""
Report generation utilities for the Cortical Column LLM project.
Specifically generates the 'cost of biological plausibility' curve.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for file paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ABULATION_RESULTS_PATH = os.path.join(PROJECT_ROOT, 'data', 'results', 'ablation_results.json')
ABULATION_STATS_PATH = os.path.join(PROJECT_ROOT, 'data', 'results', 'ablation_stats.json')
COST_CURVE_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'results', 'cost_curve.json')
COST_CURVE_PNG_PATH = os.path.join(PROJECT_ROOT, 'data', 'results', 'cost_curve.png')


def load_ablation_results() -> Dict[str, Any]:
    """
    Load the ablation study results from JSON.
    Expects schema: { "variants": [ { "name": str, "mae": float, "active_constraints": int }, ... ] }
    """
    if not os.path.exists(ABULATION_RESULTS_PATH):
        raise FileNotFoundError(
            f"Ablation results not found at {ABULATION_RESULTS_PATH}. "
            "Please ensure T026b (run_ablation_study) has been executed."
        )

    with open(ABULATION_RESULTS_PATH, 'r') as f:
        data = json.load(f)

    if 'variants' not in data:
        raise ValueError(f"Invalid ablation results format: missing 'variants' key in {ABULATION_RESULTS_PATH}")

    return data


def load_ablation_stats() -> Dict[str, Any]:
    """
    Load the ablation statistics (t-test results) from JSON.
    Expects schema: { "full_mae": float, "ablated_mae": float, ... }
    """
    if not os.path.exists(ABULATION_STATS_PATH):
        raise FileNotFoundError(
            f"Ablation stats not found at {ABULATION_STATS_PATH}. "
            "Please ensure T031 (compare_ablation_results) has been executed."
        )

    with open(ABULATION_STATS_PATH, 'r') as f:
        return json.load(f)


def count_active_constraints(variant_name: str) -> int:
    """
    Map variant names to the number of active biological constraints.
    Based on T026a definitions:
    - 'full': 3 constraints (Recurrence, Inhibition, Homeostasis)
    - 'no_recurrence': 2 constraints
    - 'no_inhibition': 2 constraints
    - 'no_homeostasis': 2 constraints
    - 'no_recurrence_no_inhibition': 1 constraint
    - 'no_constraints' (or similar): 0 constraints
    """
    name = variant_name.lower()
    if 'full' in name:
        return 3
    if 'no_recurrence' in name and 'no_inhibition' in name and 'no_homeostasis' in name:
        return 0
    if 'no_recurrence' in name and 'no_inhibition' in name:
        return 1
    if 'no_recurrence' in name or 'no_inhibition' in name or 'no_homeostasis' in name:
        return 2
    # Fallback for any other naming convention, assume 3 if not stripped
    return 3


def generate_cost_curve() -> Tuple[Dict[str, Any], str]:
    """
    Generates the 'cost of biological plausibility' curve.
    
    This function:
    1. Loads ablation results.
    2. Maps each variant to (active_constraints, MAE).
    3. Aggregates MAE by constraint count (averaging if multiple variants exist).
    4. Generates a JSON report and a PNG plot.
    
    Returns:
        Tuple of (json_data_dict, png_path)
    """
    logger.info(f"Loading ablation results from {ABULATION_RESULTS_PATH}")
    results_data = load_ablation_results()
    
    variants = results_data.get('variants', [])
    if not variants:
        raise ValueError("No variants found in ablation results.")

    # Aggregate data points: Map constraint_count -> list of MAEs
    constraint_mae_map: Dict[int, List[float]] = {}

    for variant in variants:
        name = variant.get('name', 'unknown')
        mae = variant.get('mae')
        
        if mae is None:
            logger.warning(f"Skipping variant '{name}' due to missing MAE.")
            continue

        constraints = count_active_constraints(name)
        if constraints not in constraint_mae_map:
            constraint_mae_map[constraints] = []
        constraint_mae_map[constraints].append(mae)

    # Calculate averages and prepare data for plotting
    points = []
    for count in sorted(constraint_mae_map.keys()):
        maes = constraint_mae_map[count]
        avg_mae = float(np.mean(maes))
        points.append({
            "active_constraints": count,
            "mean_mae": avg_mae,
            "std_mae": float(np.std(maes)) if len(maes) > 1 else 0.0,
            "n_samples": len(maes)
        })

    if not points:
        raise ValueError("No valid data points generated for cost curve.")

    # Prepare JSON output
    json_output = {
        "description": "Cost of biological plausibility: MAE vs Active Constraints",
        "data_points": points,
        "generated_at": "auto-generated"
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(COST_CURVE_JSON_PATH), exist_ok=True)

    # Write JSON
    with open(COST_CURVE_JSON_PATH, 'w') as f:
        json.dump(json_output, f, indent=2)
    logger.info(f"Saved cost curve JSON to {COST_CURVE_JSON_PATH}")

    # Generate Plot
    x_vals = [p['active_constraints'] for p in points]
    y_vals = [p['mean_mae'] for p in points]
    y_errs = [p['std_mae'] for p in points]

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        x_vals, y_vals, yerr=y_errs, 
        fmt='o-', capsize=5, 
        color='#2c3e50', ecolor='#e74c3c', 
        markersize=8, linewidth=2,
        label='Mean MAE'
    )
    
    plt.title("Cost of Biological Plausibility", fontsize=16, fontweight='bold')
    plt.xlabel("Number of Active Biological Constraints", fontsize=12)
    plt.ylabel("Mean Absolute Error (MAE)", fontsize=12)
    plt.xticks(x_vals)  # Ensure integer ticks
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Add annotations for specific points
    for i, p in enumerate(points):
        plt.annotate(
            f"{p['mean_mae']:.4f}",
            (x_vals[i], y_vals[i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center',
            fontsize=9
        )

    plt.tight_layout()
    plt.savefig(COST_CURVE_PNG_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved cost curve plot to {COST_CURVE_PNG_PATH}")

    return json_output, COST_CURVE_PNG_PATH


def main():
    """
    CLI entry point for generating the cost curve.
    """
    logger.info("Starting cost curve generation...")
    try:
        data, path = generate_cost_curve()
        print(f"Success. Output written to:\n  JSON: {COST_CURVE_JSON_PATH}\n  PNG: {path}")
        return 0
    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception("An unexpected error occurred")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
