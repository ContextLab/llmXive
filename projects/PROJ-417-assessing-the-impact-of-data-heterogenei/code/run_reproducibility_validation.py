"""
Reproducibility validation script for the heterogeneity impact pipeline.

This script performs the following steps:
1. Executes the full simulation and analysis pipeline (`code/main.py`) in
   full mode with a deterministic seed.
2. Computes SHA‑256 checksums for every file produced under
   `data/results/`.
3. Writes the checksum mapping to `state/artifact_hashes.yaml`.

The script is intended to be invoked by the CI or by a developer
performing a final reproducibility check. It exits with status 0 on
success and a non‑zero status on any failure (e.g., pipeline crash,
checksum generation error).
"""

import subprocess
import sys
from pathlib import Path

# Import the checksum utilities from the existing module.
# The module `generate_checksums` provides `main()` which writes the
# checksum file to `state/artifact_hashes.yaml`.
from generate_checksums import main as generate_checksums_main

def run_full_pipeline() -> None:
    """
    Run the main pipeline in full mode.

    The pipeline is expected to:
    - Load or generate the base dataset (real Cochrane data or the verified
      synthetic fallback).
    - Perform the primary simulation sweep (5 τ² levels × ≥500 replicates).
    - Estimate effects with Fixed‑Effects, DerSimonian‑Laird, and REML.
    - Compute metrics, aggregate results, generate plots, and produce the
      final report.

    Any failure in the subprocess will raise a CalledProcessError,
    causing the script to exit with a non‑zero status.
    """
    cmd = [
        sys.executable,
        "code/main.py",
        "--mode",
        "full",
        "--seed",
        "42",
    ]
    # Using `check=True` ensures an exception on non‑zero exit code.
    subprocess.run(cmd, check=True)

def main() -> int:
    """
    Entry point for the reproducibility validation.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        # Step 1: run the full pipeline.
        print("=== Running full pipeline (T001 → T010) ===")
        run_full_pipeline()
        print("=== Pipeline completed successfully ===")

        # Step 2: generate SHA‑256 checksums for all result artifacts.
        print("=== Generating SHA‑256 checksums for data/results/ ===")
        generate_checksums_main()
        print("=== Checksums written to state/artifact_hashes.yaml ===")

        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Pipeline execution failed (returncode={e.returncode})", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: Unexpected exception during reproducibility validation: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())