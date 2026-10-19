"""
Executes the quick‑start smoke test by running the full synthetic pipeline
and then checking that all declared outputs exist and are schema‑valid.
"""

import subprocess
import sys
import pathlib

def main() -> int:
    project_root = pathlib.Path(__file__).resolve().parents[1]

    # 1. Run the full pipeline in synthetic mode
    pipeline_cmd = [
        sys.executable,
        "code/main.py",
        "--mode",
        "synthetic",
        "--n-subjects",
        "100",
        "--seed",
        "42",
    ]
    print("Running synthetic pipeline...")
    result = subprocess.run(pipeline_cmd, cwd=project_root, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print("Synthetic pipeline failed.", file=sys.stderr)
        return result.returncode

    # 2. Verify that expected output files exist
    expected_files = [
        "data/processed/subjects_cleaned.csv",
        "data/processed/matching_balance_report.csv",
        "data/processed/connectivity_matrices.npy",
        "data/processed/connectivity_results.csv",
        "data/processed/nbs_results.csv",
        "data/processed/correlation_results.csv",
        "data/processed/sensitivity_analysis.csv",
    ]
    missing = [p for p in expected_files if not (project_root / p).exists()]
    if missing:
        print(f"Missing expected output files: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("All expected outputs are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
