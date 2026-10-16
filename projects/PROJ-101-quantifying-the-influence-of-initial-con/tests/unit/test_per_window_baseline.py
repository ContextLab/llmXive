"""
Unit test for the per‑window baseline computation (Task T017).

The test checks that, for each system dimension ``N`` defined in the project
configuration, a JSON file ``baseline_per_window_{N}.json`` exists in the
``data/processed`` directory, that it contains an entry for every required
window size, and that each entry reports ``status == "valid"`` (i.e. the
convergence error is below the 5 % threshold).
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test – this also triggers the computation when
# the test suite is executed.
from analysis.per_window_baseline import main as compute_baselines

@pytest.fixture(scope="module")
def baseline_data():
    """
    Run the baseline computation once for the whole test module and return
    the mapping ``N -> list[record]``.
    """
    return compute_baselines()

def _expected_window_sizes():
    """
    Retrieve the list of window sizes used by the project.  The module
    ``analysis.per_window_baseline`` uses the same configuration, so we
    import it to avoid duplication.
    """
    from analysis.per_window_baseline import WINDOW_SIZES
    return WINDOW_SIZES

@pytest.mark.parametrize("N", [3, 5])  # matches the default N_VALUES
def test_json_file_exists_and_structure(N, baseline_data):
    # Verify that the JSON file was written.
    json_path: Path = paths.data("processed", f"baseline_per_window_{N}.json")
    assert json_path.is_file(), f"Missing baseline file for N={N}"

    # Load the file and compare with the in‑memory result from the fixture.
    with json_path.open("r", encoding="utf-8") as fp:
        file_contents = json.load(fp)

    # The in‑memory dict produced by the script should match the file.
    assert baseline_data[N] == file_contents, "In‑memory result differs from file"

    # Ensure every required window size is present.
    required_windows = set(_expected_window_sizes())
    present_windows = {entry["window_size"] for entry in file_contents}
    assert required_windows == present_windows, (
        f"Window size mismatch for N={N}: expected {required_windows}, got {present_windows}"
    )

    # All entries must be marked as valid (error < 5 %).
    for entry in file_contents:
        assert entry["status"] == "valid", (
            f"Baseline for N={N}, T={entry['window_size']} did not meet the <5 % error criterion"
        )