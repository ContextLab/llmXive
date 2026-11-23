# This helper script simply invokes the finalization step of the data ingestion pipeline.
# It is executed by the verification harness to ensure that the FR‑011 simulated‑data
# branch runs without error and produces the required artifacts.
import subprocess
import sys

if __name__ == "__main__":
    # Run the ingestion script with the --finalize flag
    result = subprocess.run(
        [sys.executable, "code/01_data_ingestion.py", "--finalize"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)