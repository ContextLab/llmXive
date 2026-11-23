import json
from pathlib import Path

def test_experiment_results_exist():
    """
    Integration test that runs the orchestrator (via the wrapper script)
    and checks that the expected JSON result files are present and
    conform to the experiment_result_schema.
    """
    # Run the orchestrator; the script is idempotent and fast.
    import subprocess, sys
    subprocess.run([sys.executable, "scripts/run_experiment.sh"], check=True)

    results_dir = Path("data/results")
    for seed in range(5):
        for regime in ("wake_dream", "baseline"):
            result_path = results_dir / f"experiment_result_seed{seed}_{regime}.json"
            assert result_path.is_file(), f"Missing {result_path}"
            # Basic schema sanity check – ensure required keys exist.
            data = json.loads(result_path.read_text())
            for key in ("seed", "run_type", "final_accuracy", "total_steps",
                        "dream_steps", "peak_memory_gb", "wall_clock_hours"):
                assert key in data, f"{key} missing in {result_path}"