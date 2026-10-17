"""
Integration test for Task T003: Run the single‑run analysis and confirm reproducibility.

This test executes the CLI entry point (`code.main`) with the exact arguments
required by the specification, then checks that:

1. The top eigenvalue matches the reference value within 1e‑6 absolute tolerance.
2. The JSON result file `data/processed/single_run_results.json` exists and is well‑formed.
3. The log file `data/logs/single_run.log` has been created.
4. A checksum entry for the raw matrix file is present in `data/checksums.yaml`.

The test is deliberately simple and deterministic: the random seed is fixed
(`seed=42`), and the raw matrix file is either loaded from cache or regenerated
in a reproducible way by the implementation in `code/main.py`.
"""

import json
import math
import pathlib
import subprocess
import sys

import yaml


def test_single_run_reproducibility():
    """
    Run the single‑run CLI and verify the output artifacts.
    """
    # Define the command as specified in the quickstart / T002 description.
    cmd = [
        sys.executable,
        "-m",
        "code.main",
        "--mode",
        "single",
        "--N",
        "1000",
        "--seed",
        "42",
        "--theta",
        "2.5",
        "--k",
        "1",
        "--pattern",
        "diagonal",
    ]

    # Execute the command; raise if it fails.
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    # Basic sanity check that the process wrote something to stdout/stderr.
    assert result.stdout is not None  # noqa: S101
    assert result.stderr is not None  # noqa: S101

    # 1. Load the JSON result and check the top eigenvalue.
    json_path = pathlib.Path("data/processed/single_run_results.json")
    assert json_path.is_file(), f"Result JSON not found at {json_path}"

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON should contain an ``eigenvalues`` list with at least one entry.
    eigenvalues = data.get("eigenvalues")
    assert isinstance(eigenvalues, list) and len(eigenvalues) > 0, "Missing eigenvalues in JSON"

    top_val = eigenvalues[0].get("value")
    assert isinstance(top_val, (float, int)), "Top eigenvalue is not numeric"

    # Reference value from the specification (to 1e‑6 absolute tolerance).
    reference_val = 2.901642355090901
    assert math.isclose(
        top_val,
        reference_val,
        rel_tol=0.0,
        abs_tol=1e-6,
    ), f"Top eigenvalue {top_val} differs from reference {reference_val}"

    # 2. Verify that the log file was created.
    log_path = pathlib.Path("data/logs/single_run.log")
    assert log_path.is_file(), f"Log file not found at {log_path}"

    # 3. Verify that a checksum entry for the raw matrix exists.
    checksum_path = pathlib.Path("data/checksums.yaml")
    assert checksum_path.is_file(), f"Checksum file not found at {checksum_path}"

    with checksum_path.open("r", encoding="utf-8") as f:
        checksums = yaml.safe_load(f) or {}

    matrix_name = "matrix_N1000_seed42.npy"
    assert matrix_name in checksums, f"Checksum entry for {matrix_name} missing"

    # Optional sanity: the checksum entry should contain the expected keys.
    expected_keys = {"sha256", "N", "seed", "generated_at"}
    assert expected_keys.issubset(set(checksums[matrix_name].keys())), (
        f"Checksum entry for {matrix_name} missing required keys"
    )