"""
Helper script to ensure T019a (generate_manifest.py) runs before T019 (run_experiments.py).

This script:
1. Runs generate_manifest.py to create experiment_manifest.csv.
2. Runs run_experiments.py to execute the experiments.

This is a convenience wrapper for the execution stage.
"""
import subprocess
import sys
from pathlib import Path

def run_script(script_name: str, description: str) -> None:
    """Run a Python script and check exit code."""
    print(f"--- Running {description} ---")
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=Path(__file__).parent,
        capture_output=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed with exit code {result.returncode}")
    print(f"--- {description} completed successfully ---")

def main():
    """Orchestrate the experiment pipeline."""
    # Ensure we are in the right directory
    project_root = Path(__file__).resolve().parent.parent
    execution_dir = project_root / "code" / "03_execution"
    
    # Change to execution directory so imports work
    import os
    os.chdir(execution_dir)
    
    # Step 1: Generate manifest
    run_script("generate_manifest.py", "Generate Manifest (T019a)")
    
    # Step 2: Run experiments
    run_script("run_experiments.py", "Run Experiments (T019)")
    
    print("All experiments completed.")

if __name__ == "__main__":
    main()