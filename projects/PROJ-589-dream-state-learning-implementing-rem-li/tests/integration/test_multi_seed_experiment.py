"""
Integration test for the multi‑seed orchestrator (code/main.py).

The test runs the orchestrator with a tiny configuration (few steps, small
warm‑up) and asserts that the expected JSON result files are created and
conform to the ``experiment_result_schema`` contract.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path helpers
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_SCRIPT = PROJECT_ROOT / "code" / "main.py"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

def run_main(seeds: str, total_steps: int = 5, warmup: int = 2):
    """Execute ``code/main.py`` with the supplied CLI arguments."""
    cmd = [
        sys.executable,
        str(MAIN_SCRIPT),
        f"--seeds={seeds}",
        f"--total_steps={total_steps}",
        f"--warmup={warmup}",
        "--ratio=4:1",
        "--glue_subset=mrpc",
        "--mode=debug",
    ]
    # Run the command and raise on failure
    subprocess.run(cmd, check=True, capture_output=True)

@pytest.mark.parametrize("seed_list", ["0,1", "2,3,4"])
def test_experiment_files_created(seed_list):
    # Ensure a clean results directory
    if RESULTS_DIR.exists():
        for f in RESULTS_DIR.iterdir():
            f.unlink()
    else:
        RESULTS_DIR.mkdir(parents=True)

    # Run the orchestrator
    run_main(seeds=seed_list, total_steps=5, warmup=2)

    # Verify that for each seed we have both wake_dream and baseline JSON files
    seeds = [int(s) for s in seed_list.split(",")]
    for seed in seeds:
        wake_path = RESULTS_DIR / f"experiment_result_seed{seed}_wake_dream.json"
        base_path = RESULTS_DIR / f"experiment_result_seed{seed}_baseline.json"
        assert wake_path.is_file(), f"Missing wake/dream result for seed {seed}"
        assert base_path.is_file(), f"Missing baseline result for seed {seed}"

        # Basic schema validation – check required keys
        for path in (wake_path, base_path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in [
                "seed",
                "run_type",
                "final_accuracy",
                "total_steps",
                "dream_steps",
                "peak_memory_gb",
                "wall_clock_hours",
            ]:
                assert key in data, f"Key {key} missing in {path.name}"
            # run_type must be one of the allowed enum values
            assert data["run_type"] in {"wake_dream", "baseline"}