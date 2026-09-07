"""
T043: Run quickstart.md validation.

Executes the pipeline commands documented in T040 (quickstart.md) and verifies:
1. The pipeline completes successfully (exit code 0).
2. The output file `data/outputs/analysis_result.json` is created.
3. The output file contains valid JSON (verified via `json.tool` logic).
"""
import subprocess
import sys
import json
import os
from pathlib import Path

# Project root relative to this script (assuming code/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "outputs" / "analysis_result.json"
CONFIG_PATH = PROJECT_ROOT / "src" / "config.yaml"
MAIN_SCRIPT = PROJECT_ROOT / "src" / "main.py"

def run_validation():
    print("=== T043: Quickstart Validation ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Config: {CONFIG_PATH}")
    print(f"Output Target: {OUTPUT_PATH}")

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Check if config and main exist
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    if not MAIN_SCRIPT.exists():
        print(f"ERROR: Main script not found at {MAIN_SCRIPT}")
        sys.exit(1)

    # Construct command: python src/main.py --config src/config.yaml
    # We run from project root to match expected paths in the code
    cmd = [
        sys.executable,
        str(MAIN_SCRIPT),
        "--config",
        str(CONFIG_PATH)
    ]

    print(f"Executing: {' '.join(cmd)}")
    print("-" * 40)

    try:
        # Run the pipeline
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Print stdout/stderr to console for visibility
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print(f"ERROR: Pipeline failed with exit code {result.returncode}")
            sys.exit(1)

        print("-" * 40)
        print("Pipeline execution completed successfully.")

    except subprocess.TimeoutExpired:
        print("ERROR: Pipeline execution timed out.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to execute pipeline: {e}")
        sys.exit(1)

    # Verify Output File Existence
    if not OUTPUT_PATH.exists():
        print(f"ERROR: Output file {OUTPUT_PATH} was not created.")
        sys.exit(1)

    print(f"Output file created: {OUTPUT_PATH}")

    # Verify JSON Validity
    try:
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print("ERROR: Output file is empty.")
                sys.exit(1)
            
            # Attempt to parse JSON (equivalent to python -m json.tool)
            data = json.loads(content)
            print("JSON validation: PASSED")
            
            # Basic structure check (optional but good for sanity)
            if not isinstance(data, dict):
                print("WARNING: Root JSON object is not a dictionary.")
            
            print(f"JSON keys found: {list(data.keys())}")

    except json.JSONDecodeError as e:
        print(f"ERROR: Output file is not valid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read/validate output file: {e}")
        sys.exit(1)

    print("\n=== T043 Validation: SUCCESS ===")
    return True

if __name__ == "__main__":
    run_validation()
