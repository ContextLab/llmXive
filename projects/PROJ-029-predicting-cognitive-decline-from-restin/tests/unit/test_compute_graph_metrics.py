"""Unit test for the graph‑metric computation script.

The test ensures that the script can be imported and that the ``main``
function runs without raising an exception when the input files are
minimal (an empty eligible‑subjects list).  It also checks that the
expected output CSV is created and contains the correct header.
"""

import os
import csv
from pathlib import Path

import pytest

# Import the module under test
from code import _03_compute_graph_metrics as compute_metrics  # noqa: F401

@pytest.fixture
def empty_eligible_file(tmp_path):
    """Create an empty ``eligible_subjects.csv`` file."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    eligible_path = processed_dir / "eligible_subjects.csv"
    # Write only the header (or leave empty – the script treats any row as a subject)
    eligible_path.write_text("")
    # Patch the Path used by the script to point to this temporary location
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)

def test_main_creates_header_only_csv(empty_eligible_file):
    """Running ``main`` with no subjects should produce a CSV with only a header."""
    # Ensure no previous output exists
    output_path = Path("data/processed/graph_metrics.csv")
    if output_path.is_file():
        output_path.unlink()

    # Run the main function
    compute_metrics.main()

    # Verify the output file exists
    assert output_path.is_file(), "graph_metrics.csv was not created"

    # Verify the header row matches expectations
    with output_path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    expected_header = [
        "subject_id",
        "mean_degree",
        "global_efficiency",
        "clustering_coefficient",
        "average_shortest_path_length",
    ]
    assert rows, "Output CSV is empty"
    assert rows[0] == expected_header, "Header row does not match expected schema"
    # No additional rows should be present
    assert len(rows) == 1, "Expected only header row when no subjects are eligible"