"""
Integration test for reproducibility (Task T003).

The test re‑runs the reference single‑run configuration using the CLI entry point
``code.main`` and checks two things:

1. The top eigenvalue printed by the run matches the reference value
   2.901642355091 ± 1e‑6.
2. The generated ``single_run_results.json`` file is byte‑identical to a stored
   reference after normalising the ``timestamp`` field (the timestamp is
   deliberately excluded from the comparison).

The reference JSON file is stored at
``data/processed/reference_single_run_results.json``.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from llmxive_toolkit import paths

# Path helpers -------------------------------------------------------------
GENERATED_JSON = paths.data("processed", "single_run_results.json")
REFERENCE_JSON = paths.data("processed", "reference_single_run_results.json")

# Expected top eigenvalue (reference) --------------------------------------
REFERENCE_TOP_EIGEN = 2.901642355091
TOLERANCE = 1e-6

def _run_single_mode() -> str:
    """
    Executes the CLI in ``single`` mode with the reference parameters.
    Returns the captured stdout as a string.
    """
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
    # Run the command from the project root
    result = subprocess.run(
        cmd,
        cwd=paths.root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

def _extract_top_eigenvalue(output: str) -> float:
    """
    The ``code.main`` script prints a line like:
    ``top_eigenvalue=2.901642355091  (reference value ...)``
    This helper extracts the floating‑point number.
    """
    match = re.search(r"top_eigenvalue\s*=\s*([0-9]*\.?[0-9]+)", output)
    if not match:
        raise AssertionError("Could not find top_eigenvalue in CLI output.")
    return float(match.group(1))

def _load_and_normalise(json_path: Path) -> dict:
    """
    Loads a JSON artifact and replaces the ``timestamp`` field (if present)
    with the literal string ``PLACEHOLDER``. The function returns the
    normalised dictionary.
    """
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Recursively replace any key named ``timestamp``.
    def _replace_timestamp(obj):
        if isinstance(obj, dict):
            return {
                k: ("PLACEHOLDER" if k == "timestamp" else _replace_timestamp(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_replace_timestamp(item) for item in obj]
        return obj

    return _replace_timestamp(data)

def test_top_eigenvalue_matches_reference():
    """Assert that the top eigenvalue is within the required tolerance."""
    stdout = _run_single_mode()
    top_val = _extract_top_eigenvalue(stdout)
    assert abs(top_val - REFERENCE_TOP_EIGEN) <= TOLERANCE, (
        f"Top eigenvalue {top_val} differs from reference "
        f"{REFERENCE_TOP_EIGEN} by more than {TOLERANCE}"
    )

def test_single_run_results_json_is_reproducible():
    """
    After the CLI run, ``single_run_results.json`` must be byte‑identical
    to the stored reference (modulo the ``timestamp`` field).
    """
    # Ensure the CLI has been executed – the previous test already did this.
    assert GENERATED_JSON.is_file(), f"Generated file missing: {GENERATED_JSON}"
    assert REFERENCE_JSON.is_file(), f"Reference file missing: {REFERENCE_JSON}"

    generated = _load_and_normalise(GENERATED_JSON)
    reference = _load_and_normalise(REFERENCE_JSON)

    # Compare the two JSON structures after normalisation.
    assert generated == reference, "Generated single_run_results.json does not match the reference."