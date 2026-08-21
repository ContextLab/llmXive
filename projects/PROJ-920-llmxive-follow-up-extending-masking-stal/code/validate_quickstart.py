"""
Script to validate the quickstart.md pipeline execution.

This script runs the full pipeline as described in docs/quickstart.md:
1. Generate trajectories (T011)
2. Simulate agent (T014)
3. Analyze results (T018)
4. Visualize results (T021)

It verifies that all expected output files are created and contain valid data.
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_PLOTS = PROJECT_ROOT / "output" / "plots"
OUTPUT_REGRESSION = PROJECT_ROOT / "output" / "regression_summary.json"
OUTPUT_HYPOTHESIS = PROJECT_ROOT / "output" / "hypothesis_summary.txt"

# Expected outputs
EXPECTED_TRAJECTORIES = DATA_RAW / "trajectories.json"
EXPECTED_SIMULATION_LOG = DATA_PROCESSED / "simulation_results.json"
EXPECTED_PLOT = OUTPUT_PLOTS / "surface_plot.png"

def run_step(name: str, module_path: str, args: List[str]) -> Tuple[bool, str]:
    """Run a pipeline step and return success status and output."""
    cmd = [sys.executable, module_path] + args
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            return False, f"Exit code {result.returncode}:\n{result.stderr}"
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Step timed out"
    except Exception as e:
        return False, str(e)

def validate_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and is non-empty."""
    if not path.exists():
        print(f"❌ Missing: {description} ({path})")
        return False
    if path.stat().st_size == 0:
        print(f"❌ Empty: {description} ({path})")
        return False
    print(f"✅ Found: {description} ({path})")
    return True

def validate_json_structure(path: Path, expected_keys: List[str]) -> bool:
    """Validate that a JSON file has the expected structure."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            if len(data) == 0:
                print(f"⚠️  Warning: {path} is an empty list")
                return True
            # Check first item for keys
            first_item = data[0]
            missing = [k for k in expected_keys if k not in first_item]
            if missing:
                print(f"❌ Missing keys in {path}: {missing}")
                return False
        elif isinstance(data, dict):
            missing = [k for k in expected_keys if k not in data]
            if missing:
                print(f"❌ Missing keys in {path}: {missing}")
                return False
        print(f"✅ Valid JSON structure: {path}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        return False

def main() -> int:
    """Run the full validation pipeline."""
    print("=" * 60)
    print("LLM-Xive Quickstart Validation")
    print("=" * 60)

    # Step 1: Generate Trajectories
    print("\n[1/4] Generating trajectories...")
    success, output = run_step(
        "Generate Trajectories",
        str(PROJECT_ROOT / "code" / "generate_trajectories.py"),
        ["--count", "500", "--seed", "42"]
    )
    if not success:
        print(f"❌ Generation failed: {output}")
        return 1
    print("✅ Generation completed")

    # Validate trajectories
    if not validate_file_exists(EXPECTED_TRAJECTORIES, "Trajectories file"):
        return 1
    if not validate_json_structure(
        EXPECTED_TRAJECTORIES, 
        ["trajectory_id", "turns", "critical_evidence_turn", "density"]
    ):
        return 1

    # Step 2: Simulate Agent
    print("\n[2/4] Simulating agent...")
    success, output = run_step(
        "Simulate Agent",
        str(PROJECT_ROOT / "code" / "simulate_agent.py"),
        ["--input", str(EXPECTED_TRAJECTORIES), "--horizons", "1,2,3,4,5,6,7,8,9,10"]
    )
    if not success:
        print(f"❌ Simulation failed: {output}")
        return 1
    print("✅ Simulation completed")

    # Validate simulation results
    if not validate_file_exists(EXPECTED_SIMULATION_LOG, "Simulation results"):
        return 1
    if not validate_json_structure(
        EXPECTED_SIMULATION_LOG,
        ["trajectory_id", "horizon", "success", "density"]
    ):
        return 1

    # Step 3: Analyze Results
    print("\n[3/4] Analyzing results...")
    success, output = run_step(
        "Analyze Results",
        str(PROJECT_ROOT / "code" / "analyze_results.py"),
        ["--input", str(EXPECTED_SIMULATION_LOG), "--df", "3"]
    )
    if not success:
        print(f"❌ Analysis failed: {output}")
        return 1
    print("✅ Analysis completed")

    # Validate regression summary
    if not validate_file_exists(OUTPUT_REGRESSION, "Regression summary"):
        return 1
    if not validate_json_structure(
        OUTPUT_REGRESSION,
        ["coefficients", "p_values", "interaction_significant"]
    ):
        return 1

    # Validate hypothesis summary
    if not validate_file_exists(OUTPUT_HYPOTHESIS, "Hypothesis summary"):
        return 1
    with open(OUTPUT_HYPOTHESIS, 'r') as f:
        hypothesis_text = f.read()
    if len(hypothesis_text) < 50:
        print(f"❌ Hypothesis summary too short: {hypothesis_text}")
        return 1
    print(f"✅ Hypothesis summary content: {hypothesis_text[:100]}...")

    # Step 4: Visualize Results
    print("\n[4/4] Visualizing results...")
    success, output = run_step(
        "Visualize Results",
        str(PROJECT_ROOT / "code" / "visualize_results.py"),
        ["--input", str(OUTPUT_REGRESSION), "--output", str(EXPECTED_PLOT)]
    )
    if not success:
        print(f"❌ Visualization failed: {output}")
        return 1
    print("✅ Visualization completed")

    # Validate plot
    if not validate_file_exists(EXPECTED_PLOT, "Surface plot"):
        return 1
    plot_size = EXPECTED_PLOT.stat().st_size
    if plot_size > 5 * 1024 * 1024:  # 5 MB
        print(f"⚠️  Warning: Plot file is large ({plot_size / 1024 / 1024:.1f} MB)")
    print(f"✅ Plot size: {plot_size / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("✅ Quickstart validation PASSED")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())