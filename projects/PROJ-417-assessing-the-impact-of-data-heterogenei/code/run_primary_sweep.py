"""
Run the primary simulation sweep (full domain) and verify that the
output contains at least 2 500 simulation replicates.

This script is used for task T006. It invokes the main pipeline
(`code/main.py`) with the arguments required for the full sweep:
- mode: full
- seed: 42 (deterministic)

After the pipeline finishes, the script checks that
`data/results/simulation_raw.json` exists and that it contains the
expected number of replicate records (≥ 5 levels × 500 replicates = 2 500).
If any of these conditions are not met, the script raises an error
so the task executor can report a failure.
"""

import sys
from pathlib import Path
import json

# Import the pipeline entry point.  The import works because the
# repository root is added to `sys.path` by `code/main.py` itself,
# but we also make sure it is importable here.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import main as pipeline_main


def run_pipeline() -> None:
    """Execute the pipeline with the full‑sweep configuration."""
    # Prepare a fake argv that mimics the CLI call.
    sys.argv = [
        "code/main.py",
        "--mode",
        "full",
        "--seed",
        "42",
    ]

    exit_code = pipeline_main()
    if exit_code != 0:
        raise RuntimeError(f"Pipeline exited with non‑zero code {exit_code}")


def verify_output() -> None:
    """Check that the simulation output file exists and has enough records."""
    sim_path = Path("data/results") / "simulation_raw.json"
    if not sim_path.is_file():
        raise FileNotFoundError(f"Expected simulation output not found: {sim_path}")

    with sim_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    replicates = data.get("replicates")
    if not isinstance(replicates, list):
        raise ValueError("Simulation JSON does not contain a 'replicates' list.")

    expected_min = 5 * 500  # 5 τ² levels × 500 replicates each
    actual = len(replicates)
    if actual < expected_min:
        raise ValueError(
            f"Simulation contains {actual} replicates; "
            f"expected at least {expected_min}."
        )
    # Optionally, write a tiny log confirming success.
    log_path = Path("data/results") / "run_summary.json"
    summary = {
        "status": "primary_sweep_completed",
        "replicates": actual,
        "required_minimum": expected_min,
    }
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> int:
    """Entry point for the task runner."""
    try:
        run_pipeline()
        verify_output()
    except Exception as exc:
        # Propagate the exception so the executor records a failure.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Primary simulation sweep completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())