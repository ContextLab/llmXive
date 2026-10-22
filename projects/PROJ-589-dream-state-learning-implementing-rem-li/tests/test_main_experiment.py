"""
Integration test for ``code/main.py`` – ensures that the orchestrator creates
the expected JSON result files for each seed and regime.
"""

import json
from pathlib import Path

def test_experiment_result_files_exist():
    # The orchestrator should have been executed prior to this test.
    results_dir = Path("data/results")
    for seed in range(0, 5):
        wake_path = results_dir / f"experiment_result_seed{seed}_wake_dream.json"
        baseline_path = results_dir / f"experiment_result_seed{seed}_baseline.json"
        assert wake_path.is_file(), f"Missing wake/dream result for seed {seed}"
        assert baseline_path.is_file(), f"Missing baseline result for seed {seed}"

        # Verify that the JSON conforms to the expected schema fields.
        for path in (wake_path, baseline_path):
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
                assert key in data, f"{key} missing in {path}"