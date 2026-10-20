"""
Integration test for seed consistency.

This test runs the full analysis pipeline twice with the same configuration
(identical N, primes, and random seed) and asserts that the generated
``ResidueDataset`` files (`data/raw/residues_{prime}_{N}.json`) are byte‑identical
between the two runs. The test uses a small ``N`` to keep execution time short.
"""

import subprocess
import sys
import json
import filecmp
from pathlib import Path

# Helper to run the pipeline with given arguments.
def run_pipeline(N: int, primes: list[int], seed: int) -> None:
    """
    Execute ``code/run_analysis.py`` via ``python -m code.run_analysis`` with
    the supplied arguments. Raises ``RuntimeError`` if the subprocess fails.
    """
    # Build the command line arguments.
    primes_arg = ",".join(str(p) for p in primes)
    cmd = [
        sys.executable,
        "-m",
        "code.run_analysis",
        "--N",
        str(N),
        "--primes",
        primes_arg,
        "--seed",
        str(seed),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Pipeline failed (exit {result.returncode}). "
            f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
        )

def test_residue_files_are_byte_identical():
    """
    Run the analysis twice with the same configuration and verify that the
    raw residue JSON files are identical byte‑for‑byte.
    """
    # Small parameters for a quick test.
    N = 30
    primes = [3, 5]
    seed = 12345

    # Ensure a clean start: remove any leftover files from previous runs.
    for p in primes:
        path = Path("data/raw") / f"residues_{p}_{N}.json"
        if path.is_file():
            path.unlink()

    # First run.
    run_pipeline(N, primes, seed)

    # Capture the contents of the generated files after the first run.
    first_contents = {}
    for p in primes:
        file_path = Path("data/raw") / f"residues_{p}_{N}.json"
        assert file_path.is_file(), f"Expected file {file_path} not found after first run"
        with file_path.open("rb") as f:
            first_contents[p] = f.read()

    # Second run (same configuration).
    run_pipeline(N, primes, seed)

    # Verify that the files exist after the second run and compare byte‑wise.
    for p in primes:
        file_path = Path("data/raw") / f"residues_{p}_{N}.json"
        assert file_path.is_file(), f"Expected file {file_path} not found after second run"
        with file_path.open("rb") as f:
            second_content = f.read()
        assert (
            first_contents[p] == second_content
        ), f"Residue file for prime {p} differs between runs despite identical configuration"

    # Cleanup: remove the generated files to keep the repository tidy.
    for p in primes:
        (Path("data/raw") / f"residues_{p}_{N}.json").unlink(missing_ok=True)
    # Optionally remove any other artefacts the pipeline may have created
    # (statistical results, plots, etc.) for the small N used here.
    for p in primes:
        (Path("data/processed") / f"stats_{p}_{N}.json").unlink(missing_ok=True)
        (Path("results/plots") / f"bar_{p}_{N}.png").unlink(missing_ok=True)
        (Path("results/plots") / f"qq_{p}_{N}.png").unlink(missing_ok=True)
        (Path("results/reports") / f"flag_{p}_{N}.json").unlink(missing_ok=True)