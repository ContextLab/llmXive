"""Test that ``code/03_compute_graph_metrics.py`` runs without error
and produces the expected output file.

The test does not assert on metric values – they depend on the real
dataset – but it verifies that the script finishes within a reasonable
time (under 5 minutes on the CI runner) and that the output CSV exists
with the correct header columns.
"""

import time
from pathlib import Path

import pytest

from code import __main__ as compute_module  # noqa: F401  (import for side‑effects)

def test_compute_graph_metrics_produces_csv(tmp_path: Path, monkeypatch):
    # Arrange: ensure the script sees the project root correctly
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    output_path = project_root / "data" / "processed" / "graph_metrics.csv"
    if output_path.is_file():
        output_path.unlink()

    # Act: run the script's main function and time it
    start = time.time()
    from code import _03_compute_graph_metrics as cg  # type: ignore
    cg.main()
    elapsed = time.time() - start

    # Assert: file exists and has the expected header
    assert output_path.is_file(), "graph_metrics.csv was not created"
    with output_path.open(newline="", encoding="utf-8") as f:
        header = f.readline().strip()
    expected_header = (
        "subject_id,degree_mean,global_efficiency,clustering_coefficient,"
        "average_shortest_path"
    )
    assert header == expected_header, f"Unexpected CSV header: {header}"
    # The performance requirement for this test environment is generous;
    # we only check that it finishes in a few minutes.
    assert elapsed < 300, f"Computation took too long: {elapsed:.1f}s"