"""
Helper script to run the Plan‑Primary analysis and write its results to
data/model_fits_plan.json. This script is a thin wrapper around the
`analysis.py` module's CLI, ensuring the expected output file is generated
during the pipeline execution.
"""
import subprocess
import sys

def main():
    cmd = [
        sys.executable,
        "code/analysis.py",
        "--task", "plan",
        "--input", "data/density_measurements_plan.csv",
        "--output", "data/model_fits_plan.json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running analysis:", result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    else:
        print("Plan‑Primary analysis completed successfully.")
        print(result.stdout)

if __name__ == "__main__":
    main()