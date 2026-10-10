"""
Run the primary simulation sweep (full domain) and verify that the
generated simulation output contains at least 2,500 replicate records
(5 heterogeneity levels × 500 replicates per level).

This script is intended to be invoked by the quickstart or CI as:
    python code/run_primary_sweep.py

It calls the existing pipeline entry point `code/main.py` with the
appropriate arguments, then checks the resulting JSON file and writes
a concise summary artifact.
"""

import json
import pathlib
import subprocess
import sys

# Paths relative to the project root
MAIN_SCRIPT = pathlib.Path("code/main.py")
SIMULATION_OUTPUT = pathlib.Path("data/results/simulation_raw.json")
SUMMARY_OUTPUT = pathlib.Path("data/results/run_summary.json")

# Expected number of replicates (5 levels × 500 replicates)
MIN_REPLICATES = 5 * 500  # 2,500


def run_pipeline() -> None:
    """Execute the main pipeline in full mode."""
    # Use the same Python interpreter that is running this script.
    subprocess.check_call(
        [
            sys.executable,
            str(MAIN_SCRIPT),
            "--mode",
            "full",
            "--seed",
            "42",
        ],
        # Ensure any failure in the pipeline aborts this script.
    )


def verify_output() -> int:
    """Load the simulation JSON and return the number of replicates."""
    if not SIMULATION_OUTPUT.is_file():
        raise FileNotFoundError(f"Simulation output not found at {SIMULATION_OUTPUT}")

    with SIMULATION_OUTPUT.open("r", encoding="utf-8") as f:
        data = json.load(f)

    replicates = data.get("replicates")
    if replicates is None:
        raise KeyError("Missing 'replicates' key in simulation output JSON.")

    count = len(replicates)
    if count < MIN_REPLICATES:
        raise RuntimeError(
            f"Insufficient replicates generated: {count} (minimum required {MIN_REPLICATES})."
        )
    return count


def write_summary(count: int) -> None:
    """Write a tiny JSON summary file for downstream verification."""
    summary = {
        "replicate_count": count,
        "minimum_required": MIN_REPLICATES,
        "status": "ok" if count >= MIN_REPLICATES else "insufficient",
    }
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> int:
    """Orchestrate the sweep, verification, and summary creation."""
    run_pipeline()
    count = verify_output()
    write_summary(count)
    print(f"Primary sweep completed successfully: {count} replicates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())