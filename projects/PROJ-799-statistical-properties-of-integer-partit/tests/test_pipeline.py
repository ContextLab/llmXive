import os
import sys
import time
import pytest
import subprocess
from pathlib import Path

# Ensure code directory is in path for imports if running as module,
# though we primarily invoke scripts via subprocess for accurate timing.
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
data_dir = project_root / "data"
processed_dir = data_dir / "processed"
sys.path.insert(0, str(code_dir))

# Import the visualization module to verify existence and basic loadability
# This is a lightweight check before the heavy execution test.
try:
    import visualize_results
except ImportError as e:
    # If the module doesn't exist or can't be imported, the test will fail naturally
    # during the subprocess call, but we note it here for clarity.
    pass

@pytest.mark.timeout(3600)  # 1 hour = 3600 seconds
def test_us3_time_budget():
    """
    T010d: Verify that the visualization phase (US3) completes within 1 hour (3600 seconds).

    US3 consists of:
    1. Cross-Validation (part of code/regression_model.py, specifically perform_cross_validation)
    2. Visualization (code/visualize_results.py)

    This test executes the visualization script (which assumes model results exist from US2)
    and measures total time. SC-004 specifies a total pipeline budget of 6 hours, with US1
    taking 1.5h, US2 taking 3.5h, leaving 1h for US3.

    Prerequisites:
    - data/processed/model_results.json must exist (produced by US2/T024)
    - data/processed/features.csv must exist (produced by US2/T016a)

    Note: If prerequisites are missing, the script will fail, which is the correct behavior
    as US3 cannot run without US2 output. The time budget test is valid only if the script
    actually runs.
    """
    start_time = time.time()

    # Step 1: Ensure prerequisite data exists (fail fast if not)
    model_results_path = processed_dir / "model_results.json"
    features_path = processed_dir / "features.csv"

    if not model_results_path.exists():
        raise FileNotFoundError(
            f"US3 prerequisite missing: {model_results_path}. "
            "US2 (regression_model.py) must be completed first."
        )

    if not features_path.exists():
        raise FileNotFoundError(
            f"US3 prerequisite missing: {features_path}. "
            "US2 (feature_engineering.py) must be completed first."
        )

    # Step 2: Execute Visualization Script
    viz_script = code_dir / "visualize_results.py"
    if not viz_script.exists():
        raise FileNotFoundError(f"Visualization script not found: {viz_script}")

    print(f"Starting visualization phase at {time.strftime('%H:%M:%S')}...")
    print(f"Prerequisites verified: {model_results_path.exists()}, {features_path.exists()}")

    viz_process = subprocess.run(
        [sys.executable, str(viz_script)],
        cwd=str(code_dir),
        capture_output=True,
        text=True
    )

    if viz_process.returncode != 0:
        print(f"Visualization failed:\nSTDOUT: {viz_process.stdout}\nSTDERR: {viz_process.stderr}")
        raise RuntimeError(f"Visualization script failed with code {viz_process.returncode}")

    total_time = time.time() - start_time
    print(f"Visualization completed in {total_time:.2f} seconds.")
    print(f"Total US3 execution time: {total_time:.2f} seconds (limit: 3600 seconds)")

    # The @pytest.mark.timeout decorator enforces the 3600s limit.
    # If we reach here, the limit was not exceeded.
    assert total_time < 3600, f"US3 phase exceeded time budget: {total_time:.2f}s > 3600s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])