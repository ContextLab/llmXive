import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Executes quickstart.sh, asserts exit code 0, and verifies
    data/processed/merged_data.csv exists.
    """
    project_root = Path(__file__).resolve().parents[2]
    quickstart_script = project_root / "quickstart.sh"
    expected_output = project_root / "data" / "processed" / "merged_data.csv"

    if not quickstart_script.exists():
        print(f"ERROR: quickstart.sh not found at {quickstart_script}")
        return 1

    print(f"Executing {quickstart_script}...")
    try:
        result = subprocess.run(
            ["bash", str(quickstart_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ERROR: quickstart.sh failed with exit code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return 1
        
        print("quickstart.sh executed successfully.")

    except FileNotFoundError:
        print("ERROR: bash executable not found.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to execute quickstart.sh: {e}")
        return 1

    if not expected_output.exists():
        print(f"ERROR: Expected output file not found: {expected_output}")
        return 1

    print(f"SUCCESS: Verified {expected_output} exists.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
