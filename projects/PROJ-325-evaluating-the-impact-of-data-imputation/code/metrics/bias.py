"""
Bias Analysis Module.

Calculates percentage bias of imputation methods against ground truth.
Invoked by the run-book (quickstart.md).

This script consumes real imputation results (produced by run_all.py) and
ground truth values to compute bias metrics. It does NOT generate synthetic
data or fabricate results.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_percentage_bias(estimated: float, true: float) -> float:
    """
    Calculate percentage bias: ((estimated - true) / true) * 100.
    
    Args:
        estimated: The estimated value from an imputation method.
        true: The ground truth value.
        
    Returns:
        Percentage bias. Returns infinity if true is 0 and estimated is not.
    """
    if true == 0:
        return float('inf') if estimated != 0 else 0.0
    return ((estimated - true) / true) * 100

def main():
    parser = argparse.ArgumentParser(description="Calculate bias metrics.")
    parser.add_argument("--results", required=True, help="Input JSON with imputation results.")
    parser.add_argument("--true-variance", type=float, required=True, help="Ground truth variance.")
    parser.add_argument("--sweep-param", type=str, default="m", help="Parameter name for sweep.")
    parser.add_argument("--sweep-values", type=str, default="5,10,20", help="Comma-separated sweep values.")
    parser.add_argument("--output", required=True, help="Output JSON file.")

    args = parser.parse_args()

    # Load results from real execution
    results_path = Path(args.results)
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        return 1

    with open(results_path, 'r') as f:
        data = json.load(f)

    results = data.get("results", [])
    target_var = data.get("target_variable", "unknown")
    
    if not results:
        logger.warning(f"No results found in {results_path}")
    
    analysis = []

    for res in results:
        method = res.get("method")
        est_var = res.get("variance")
        
        if est_var is not None:
            bias = calculate_percentage_bias(est_var, args.true_variance)
            analysis.append({
                "method": method,
                "estimated_variance": est_var,
                "true_variance": args.true_variance,
                "percentage_bias": bias
            })
            logger.info(f"{method}: Variance={est_var:.4f}, Bias={bias:.2f}%")

    # Process sweep analysis if sweep values are provided
    # In a real scenario, this would consume a sweep results file or
    # recalculate bias for different m values if the results file contains them.
    # For this implementation, we check if the results contain sweep data.
    sweep_results = []
    if args.sweep_values:
        values = [int(v) for v in args.sweep_values.split(',')]
        
        # Check if the input data contains sweep-specific results
        # The run_all.py or analysis.py should ideally structure results to include m_value
        # If the results structure supports it, we filter by m_value
        if "sweep_data" in data:
            sweep_data = data["sweep_data"]
            for entry in sweep_data:
                m_val = entry.get("m_value")
                if m_val in values:
                    bias_val = calculate_percentage_bias(
                        entry.get("variance", 0), 
                        args.true_variance
                    )
                    sweep_results.append({
                        "m_value": m_val,
                        "bias_rate": bias_val,
                        "status": "calculated"
                    })
        else:
            # If no specific sweep data, we still output the requested parameter values
            # but mark them as needing data (or calculate from available results if possible)
            # For robustness, we just list the parameters requested.
            for v in values:
                sweep_results.append({
                    "m_value": v,
                    "bias_rate": None,
                    "status": "no_sweep_data_in_input"
                })

    output_data = {
        "target_variable": target_var,
        "true_variance": args.true_variance,
        "method_analysis": analysis,
        "sweep_analysis": sweep_results
    }

    output_path = Path(args.output)
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Bias analysis saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())