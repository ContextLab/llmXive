"""
Unit test for the runtime‑budget estimator (T005).

The test runs the estimator script and verifies that the generated
`runtime_estimate.json` contains the correct fields and values based on the
existing `power_analysis.json` fixture.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the script's main functions
from code.analysis.runtime_estimate import (
    load_power_analysis,
    compute_estimate,
    write_output,
)


def test_runtime_estimate_computation(tmp_path):
    """
    Verify that the estimator computes the correct runtime and status.
    """
    # Load the fixture power analysis (already present in the repo)
    power_data = load_power_analysis()
    N_required = power_data["N_required"]

    # Compute expected values
    expected_seconds = N_required * 60
    expected_exceeds = expected_seconds > 6 * 3600
    expected_status = "infeasible" if expected_exceeds else "feasible"

    # Run the computation function directly
    result = compute_estimate(N_required)

    assert result["estimated_seconds"] == expected_seconds
    assert result["exceeds_budget"] is expected_exceeds
    assert result["status"] == expected_status

    # Write the result to a temporary location and verify JSON structure
    output_path = tmp_path / "runtime_estimate.json"
    # Monkey‑patch the paths.results function to point to our temp file
    original_results = paths.results

    def fake_results(*parts):
        # Return the temporary path when the expected filename is requested
        if parts == ("runtime_estimate.json",):
            return output_path
        return original_results(*parts)

    # Replace the function temporarily
    paths.results = fake_results  # type: ignore

    try:
        write_output(result)
        # Read back the file and compare
        with output_path.open("r", encoding="utf-8") as fp:
            written = json.load(fp)
        assert written == result
    finally:
        # Restore the original function to avoid side effects on other tests
        paths.results = original_results  # type: ignore