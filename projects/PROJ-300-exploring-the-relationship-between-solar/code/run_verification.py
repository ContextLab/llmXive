"""
Runner script to execute the full verification of T043.
This script ensures all artifacts are generated and valid.
"""
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed with code {e.returncode}")
        return False
    except Exception as e:
        print(f"ERROR: {description} failed with exception: {e}")
        return False

def main():
    print("=" * 50)
    print("T043: Final Review & Verification Runner")
    print("=" * 50)

    # 1. Ensure the pipeline has been run (if not already)
    # We check if the main output exists. If not, we run the main pipeline.
    results_json = PROJECT_ROOT / "results" / "us1_correlation.json"
    if not results_json.exists():
        print("Main output missing. Running main pipeline...")
        # Run the main pipeline with a sample range
        # Note: This might fail if data fetch fails, which is expected if network is restricted.
        # But per task T043, we assume the pipeline *should* have run.
        # If it hasn't, we try to run it to generate the artifacts for verification.
        if not run_command(
            [sys.executable, "code/main.py", "--start", "2023-01-01", "--end", "2023-01-03"],
            "Main Pipeline Execution"
        ):
            print("Pipeline execution failed. Verification cannot proceed without artifacts.")
            return 1

    # 2. Run the verification script
    if not run_command(
        [sys.executable, "code/verify_artifacts.py"],
        "Artifact Verification"
    ):
        return 1

    print("\n✅ T043 Verification Complete: All artifacts match Spec SC-001 to SC-005.")
    return 0

if __name__ == "__main__":
    sys.exit(main())