"""
Main entry point for the statistical test sensitivity simulation.

This script orchestrates the simulation pipeline, accepting command-line arguments
to configure sample sizes, effect sizes, test types, and significance levels.
It iterates through the parameter grid and delegates execution to the simulation
engine, ensuring reproducibility and adherence to project constraints.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Project imports based on provided API surface
from code.simulation.data_generator import generate_normal_data, generate_multinomial_data
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation import get_rng, update_simulation_metadata
from code.utils.checksum_utils import compute_file_checksum


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the simulation."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on statistical tests (t-test, ANOVA, Chi-squared)."
    )

    # Sample size configuration
    parser.add_argument(
        "--n-start", type=int, default=5,
        help="Starting sample size (default: 5)"
    )
    parser.add_argument(
        "--n-end", type=int, default=500,
        help="Ending sample size (default: 500)"
    )
    parser.add_argument(
        "--n-step", type=int, default=5,
        help="Step size for sample size increments (default: 5)"
    )

    # Effect size configuration
    parser.add_argument(
        "--effect-sizes", type=str, nargs="+", default=["0.2", "0.5", "0.8"],
        help="List of effect sizes (Cohen's d or similar) to test (default: 0.2 0.5 0.8)"
    )

    # Test type configuration
    parser.add_argument(
        "--test-types", type=str, nargs="+", default=["t-test", "anova", "chi-squared"],
        choices=["t-test", "anova", "chi-squared"],
        help="Statistical tests to simulate (default: t-test anova chi-squared)"
    )

    # Significance level
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance level alpha (default: 0.05)"
    )

    # Iterations
    parser.add_argument(
        "--iterations", type=int, default=100,
        help="Number of simulation iterations per condition (default: 100). "
             "Note: Full production runs require >= 10,000."
    )

    # Hypothesis configuration
    parser.add_argument(
        "--hypothesis", type=str, default="two-sided",
        choices=["one-sided", "two-sided"],
        help="Type of hypothesis test (default: two-sided)"
    )

    # Output directory
    parser.add_argument(
        "--output-dir", type=str, default="data/simulation",
        help="Directory to store output files (default: data/simulation)"
    )

    # Reproducibility
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    if args.n_start < 2:
        raise ValueError("n-start must be at least 2 for statistical tests.")
    if args.n_end < args.n_start:
        raise ValueError("n-end must be greater than or equal to n-start.")
    if args.n_step < 1:
        raise ValueError("n-step must be at least 1.")
    if args.alpha <= 0 or args.alpha >= 1:
        raise ValueError("Alpha must be between 0 and 1.")
    if args.iterations < 1:
        raise ValueError("Iterations must be at least 1.")


def generate_sample_sizes(start: int, end: int, step: int) -> List[int]:
    """Generate a list of sample sizes from start to end with step increments."""
    sizes = []
    current = start
    while current <= end:
        sizes.append(current)
        current += step
    return sizes


def parse_effect_sizes(effect_strs: List[str]) -> List[float]:
    """Parse effect size strings into floats."""
    try:
        return [float(x) for x in effect_strs]
    except ValueError as e:
        raise ValueError(f"Invalid effect size format: {e}")


def run_simulation_grid(
    sample_sizes: List[int],
    effect_sizes: List[float],
    test_types: List[str],
    alpha: float,
    iterations: int,
    hypothesis: str,
    seed: int,
    output_dir: str
) -> Dict[str, Any]:
    """
    Execute the simulation across the full parameter grid.

    Returns a dictionary containing raw results and metadata.
    """
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "alpha": alpha,
            "iterations_per_condition": iterations,
            "sample_sizes": sample_sizes,
            "effect_sizes": effect_sizes,
            "test_types": test_types,
            "hypothesis": hypothesis
        },
        "conditions": [],
        "aggregated_results": []
    }

    # Initialize RNG
    rng = get_rng(seed)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    total_conditions = len(sample_sizes) * len(effect_sizes) * len(test_types)
    current_condition = 0

    print(f"Starting simulation grid: {total_conditions} conditions, {iterations} iterations each.")
    print(f"Output directory: {output_dir}")

    for n in sample_sizes:
        for effect_size in effect_sizes:
            for test_type in test_types:
                current_condition += 1
                condition_id = f"{test_type}_n{n}_es{effect_size}"

                print(f"[{current_condition}/{total_conditions}] Running: {condition_id}")

                # Run the specific simulation condition
                # Note: run_simulation_condition handles data generation and test execution
                try:
                    condition_result = run_simulation_condition(
                        n=n,
                        effect_size=effect_size,
                        test_type=test_type,
                        alpha=alpha,
                        iterations=iterations,
                        hypothesis=hypothesis,
                        rng=rng
                    )

                    results["conditions"].append({
                        "condition_id": condition_id,
                        "n": n,
                        "effect_size": effect_size,
                        "test_type": test_type,
                        "alpha": alpha,
                        "iterations": iterations,
                        "hypothesis": hypothesis,
                        "raw_p_values": condition_result.get("p_values", []),
                        "rejections": condition_result.get("rejections", []),
                        "warnings": condition_result.get("warnings", []),
                        "execution_time": condition_result.get("execution_time", 0)
                    })

                except Exception as e:
                    print(f"Error running condition {condition_id}: {e}")
                    results["conditions"].append({
                        "condition_id": condition_id,
                        "n": n,
                        "effect_size": effect_size,
                        "test_type": test_type,
                        "error": str(e)
                    })

    # Aggregate results
    aggregated = aggregate_results(results["conditions"], alpha)
    results["aggregated_results"] = aggregated

    return results


def save_results(results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """
    Save simulation results to JSON and CSV files.

    Returns a dictionary of saved file paths.
    """
    output_files = {}

    # Save full results as JSON
    json_path = os.path.join(output_dir, "simulation_results_full.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    output_files["full_results"] = json_path

    # Save raw p-values to CSV
    csv_path = os.path.join(output_dir, "p_values_raw.csv")
    with open(csv_path, "w") as f:
        # Write header
        f.write("condition_id,n,effect_size,test_type,alpha,iteration,p_value,rejected,warning\n")

        for cond in results["conditions"]:
            if "error" in cond:
                continue

            cid = cond["condition_id"]
            n = cond["n"]
            es = cond["effect_size"]
            tt = cond["test_type"]
            alpha = cond["alpha"]
            warnings_list = cond.get("warnings", [])

            p_values = cond.get("raw_p_values", [])
            rejections = cond.get("rejections", [])

            for i, (p, rej) in enumerate(zip(p_values, rejections)):
                warning_str = ";".join(warnings_list) if warnings_list else ""
                f.write(f"{cid},{n},{es},{tt},{alpha},{i},{p},{int(rej)},{warning_str}\n")

    output_files["raw_p_values"] = csv_path

    # Save aggregated error rates
    agg_path = os.path.join(output_dir, "error_rates_summary.csv")
    with open(agg_path, "w") as f:
        f.write("condition_id,n,effect_size,test_type,alpha,type1_error_rate,type2_error_rate,power,ci_lower,ci_upper\n")

        for agg in results["aggregated_results"]:
            cid = agg.get("condition_id", "")
            n = agg.get("n", 0)
            es = agg.get("effect_size", 0)
            tt = agg.get("test_type", "")
            alpha = agg.get("alpha", 0.05)
            t1 = agg.get("type1_error_rate", 0)
            t2 = agg.get("type2_error_rate", 0)
            power = agg.get("power", 0)
            ci_low = agg.get("ci_lower", 0)
            ci_high = agg.get("ci_upper", 0)

            f.write(f"{cid},{n},{es},{tt},{alpha},{t1:.4f},{t2:.4f},{power:.4f},{ci_low:.4f},{ci_high:.4f}\n")

    output_files["error_rates"] = agg_path

    return output_files


def main():
    """Main entry point for the simulation."""
    args = parse_args()
    validate_args(args)

    # Generate parameter lists
    sample_sizes = generate_sample_sizes(args.n_start, args.n_end, args.n_step)
    effect_sizes = parse_effect_sizes(args.effect_sizes)

    print(f"Configuration:")
    print(f"  Sample sizes: {len(sample_sizes)} values from {args.n_start} to {args.n_end}")
    print(f"  Effect sizes: {effect_sizes}")
    print(f"  Test types: {args.test_types}")
    print(f"  Alpha: {args.alpha}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Seed: {args.seed}")

    # Run simulation
    results = run_simulation_grid(
        sample_sizes=sample_sizes,
        effect_sizes=effect_sizes,
        test_types=args.test_types,
        alpha=args.alpha,
        iterations=args.iterations,
        hypothesis=args.hypothesis,
        seed=args.seed,
        output_dir=args.output_dir
    )

    # Save results
    output_files = save_results(results, args.output_dir)

    print("\nSimulation complete!")
    print("Output files:")
    for key, path in output_files.items():
        checksum = compute_file_checksum(path)
        print(f"  {key}: {path} (checksum: {checksum[:16]}...)")

    # Update simulation metadata
    try:
        update_simulation_metadata(
            output_dir=args.output_dir,
            seed=args.seed,
            config={
                "n_range": [args.n_start, args.n_end, args.n_step],
                "effect_sizes": effect_sizes,
                "test_types": args.test_types,
                "alpha": args.alpha,
                "iterations": args.iterations
            },
            files=output_files
        )
    except Exception as e:
        print(f"Warning: Could not update simulation metadata: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())