import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_pass_rate(results: List[Dict[str, Any]]) -> float:
    """
    Calculate the pass rate from a list of result dictionaries.
    Expects a 'pass' key (boolean) in each result.
    """
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get('pass', False))
    return passed / len(results)

def aggregate_sensitivity_results(
    n1_path: Path,
    n3_path: Path,
    n5_path: Path,
    output_path: Path
) -> None:
    """
    Aggregate sensitivity results from N=1, N=3, and N=5 experiments.
    Calculates pass rates and delta pass rates (variation metrics).
    Writes the aggregated report to output_path.
    """
    # Load individual sensitivity results
    try:
        results_n1 = load_json_file(n1_path)
        results_n3 = load_json_file(n3_path)
        results_n5 = load_json_file(n5_path)
    except FileNotFoundError as e:
        raise RuntimeError(f"Missing required sensitivity input file: {e}")

    # Ensure results are lists
    if not isinstance(results_n1, list):
        results_n1 = [results_n1]
    if not isinstance(results_n3, list):
        results_n3 = [results_n3]
    if not isinstance(results_n5, list):
        results_n5 = [results_n5]

    # Calculate pass rates
    pass_rate_n1 = calculate_pass_rate(results_n1)
    pass_rate_n3 = calculate_pass_rate(results_n3)
    pass_rate_n5 = calculate_pass_rate(results_n5)

    # Calculate delta pass rates (variation metrics)
    # Delta from N=1 to N=3
    delta_1_to_3 = pass_rate_n3 - pass_rate_n1
    # Delta from N=3 to N=5
    delta_3_to_5 = pass_rate_n5 - pass_rate_n3
    # Delta from N=1 to N=5 (total variation)
    delta_1_to_5 = pass_rate_n5 - pass_rate_n1

    # Build the aggregated report
    report = {
        "experiment_type": "sensitivity_analysis",
        "parameters_tested": [1, 3, 5],
        "results": {
            "N=1": {
                "sample_size": len(results_n1),
                "pass_rate": round(pass_rate_n1, 4),
                "passed_count": sum(1 for r in results_n1 if r.get('pass', False)),
                "failed_count": len(results_n1) - sum(1 for r in results_n1 if r.get('pass', False))
            },
            "N=3": {
                "sample_size": len(results_n3),
                "pass_rate": round(pass_rate_n3, 4),
                "passed_count": sum(1 for r in results_n3 if r.get('pass', False)),
                "failed_count": len(results_n3) - sum(1 for r in results_n3 if r.get('pass', False))
            },
            "N=5": {
                "sample_size": len(results_n5),
                "pass_rate": round(pass_rate_n5, 4),
                "passed_count": sum(1 for r in results_n5 if r.get('pass', False)),
                "failed_count": len(results_n5) - sum(1 for r in results_n5 if r.get('pass', False))
            }
        },
        "variation_metrics": {
            "delta_pass_rate_N1_to_N3": round(delta_1_to_3, 4),
            "delta_pass_rate_N3_to_N5": round(delta_3_to_5, 4),
            "delta_pass_rate_N1_to_N5": round(delta_1_to_5, 4),
            "max_variation": round(max(abs(delta_1_to_3), abs(delta_3_to_5), abs(delta_1_to_5)), 4),
            "trend_direction": "increasing" if delta_1_to_5 > 0 else ("decreasing" if delta_1_to_5 < 0 else "stable")
        },
        "summary": {
            "best_interval": 1 if pass_rate_n1 == max(pass_rate_n1, pass_rate_n3, pass_rate_n5) else (3 if pass_rate_n3 == max(pass_rate_n1, pass_rate_n3, pass_rate_n5) else 5),
            "best_pass_rate": round(max(pass_rate_n1, pass_rate_n3, pass_rate_n5), 4),
            "recommendation": "Use checkpoint interval N=1" if pass_rate_n1 > pass_rate_n3 and pass_rate_n1 > pass_rate_n5 else (
                "Use checkpoint interval N=3" if pass_rate_n3 > pass_rate_n5 else "Use checkpoint interval N=5"
            )
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Sensitivity analysis aggregated successfully. Output written to: {output_path}")

def main() -> None:
    """Main entry point for the sensitivity aggregator script."""
    parser = argparse.ArgumentParser(
        description="Aggregate sensitivity analysis results from N=1, N=3, and N=5 experiments."
    )
    parser.add_argument(
        "--input-n1",
        type=Path,
        default=Path("data/processed/sensitivity_N1.json"),
        help="Path to sensitivity results for N=1"
    )
    parser.add_argument(
        "--input-n3",
        type=Path,
        default=Path("data/processed/sensitivity_N3.json"),
        help="Path to sensitivity results for N=3"
    )
    parser.add_argument(
        "--input-n5",
        type=Path,
        default=Path("data/processed/sensitivity_N5.json"),
        help="Path to sensitivity results for N=5"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/sensitivity_analysis.json"),
        help="Path to write the aggregated sensitivity analysis report"
    )

    args = parser.parse_args()

    try:
        aggregate_sensitivity_results(
            args.input_n1,
            args.input_n3,
            args.input_n5,
            args.output
        )
    except Exception as e:
        print(f"Error aggregating sensitivity results: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()