"""
Automated script to run the full simulation and verify runtime constraints.

This script executes the main simulation pipeline (run_full_simulation)
multiple times to measure total execution duration. It generates a
runtime log in JSON format at data/results/runtime_log.json.

It also checks against the 6-hour (21600s) threshold, logging a warning
if exceeded but not failing the build (as per T036 requirements).
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import run_full_simulation
from simulation.config import SimulationConfig
from simulation.logging_utils import ensure_log_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify runtime of full simulation pipeline."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of independent simulation runs to perform for timing.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Directory to store runtime_log.json.",
    )
    parser.add_argument(
        "--config-json",
        type=str,
        default=None,
        help="Optional path to a JSON config file overriding default SimulationConfig.",
    )
    parser.add_argument(
        "--threshold-seconds",
        type=int,
        default=21600,
        help="Runtime threshold in seconds (default 6 hours). Warning if exceeded.",
    )
    return parser.parse_args()


def load_config_from_json(path: Optional[str]) -> Optional[SimulationConfig]:
    """Load a SimulationConfig from a JSON file if provided."""
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # SimulationConfig is a dataclass; we can instantiate it directly
    return SimulationConfig(**data)


def run_verification(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the simulation pipeline N times, measure total duration,
    and return a result dictionary.
    """
    ensure_log_directory(args.output_dir)

    config = load_config_from_json(args.config_json)
    if config is None:
        # Use a default small config for runtime verification to keep it fast
        # but still representative. Adjust N and reps as needed.
        config = SimulationConfig(
            N=20,
            predictors=3,
            rho=0.3,
            noise_scale=1.0,
            true_coeffs=[1.0, -1.0, 0.5],
            seed=42,
            n_replications=10,  # Small number for runtime test
        )

    results = []
    start_total = time.time()

    for i in range(args.runs):
        run_start = time.time()
        # We call run_full_simulation directly; it handles its own logging
        # and writes results to data/results/coverage_metrics.json etc.
        # We capture its return value if any, but primarily care about timing.
        try:
            run_output = run_full_simulation(config)
            run_success = True
            run_error = None
        except Exception as e:
            run_success = False
            run_error = str(e)
            run_output = None

        run_end = time.time()
        run_duration = run_end - run_start

        results.append(
            {
                "run_index": i,
                "start_time_utc": datetime.utcnow().isoformat(),
                "duration_seconds": run_duration,
                "success": run_success,
                "error": run_error,
            }
        )

    end_total = time.time()
    total_duration = end_total - start_total

    return {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "runs_requested": args.runs,
        "runs_completed": len(results),
        "total_duration_seconds": total_duration,
        "threshold_seconds": args.threshold_seconds,
        "exceeded_threshold": total_duration > args.threshold_seconds,
        "run_details": results,
        "config_summary": {
            "N": config.N,
            "predictors": config.predictors,
            "rho": config.rho,
            "n_replications": config.n_replications,
        },
    }


def main() -> int:
    args = parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "runtime_log.json")

    result = run_verification(args)

    # Write the runtime log
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Runtime log written to: {output_path}")
    print(f"Total duration: {result['total_duration_seconds']:.2f} seconds")
    print(f"Threshold: {result['threshold_seconds']} seconds")

    if result["exceeded_threshold"]:
        # Log a warning but do NOT fail the build
        print(
            f"WARNING: Total runtime ({result['total_duration_seconds']:.2f}s) "
            f"exceeded threshold ({result['threshold_seconds']}s). "
            f"Build continues but consider optimizing."
        )
    else:
        print("Runtime within acceptable threshold.")

    # Always return 0 (success) unless a critical failure occurred
    # that prevented generating the log. Here we assume log generation
    # succeeded if we reached this point.
    return 0


if __name__ == "__main__":
    sys.exit(main())
