"""
Integration test for verifying the size of the predicted PPI edge list.

The specification (T042) requires that each predicted edge‑list file
``results/predicted_ppi_<species>.tsv`` either contains only the header
line (i.e., zero edges) or at least 10 000 edges. This test scans all such
files in the ``results`` directory and asserts the condition.

The test is deliberately lightweight and uses only the Python standard
library so it can run in any CI environment without additional dependencies.
"""

import csv
from pathlib import Path

def _load_tsv_rows(file_path: Path):
    """Read a TSV file and return a list of rows (including header)."""
    with file_path.open("r", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

def test_predicted_ppi_edge_list_size():
    """
    Verify that each predicted PPI TSV file satisfies the edge‑count policy.

    - The file must exist.
    - It must contain at least a header line.
    - The number of data rows (edges) must be either 0 (header‑only) or
      >= 10 000.
    """
    results_dir = Path("results")
    # Find all predicted PPI edge‑list files.
    edge_files = sorted(results_dir.glob("predicted_ppi_*.tsv"))

    # The pipeline should have produced at least one such file.
    assert edge_files, "No predicted PPI edge‑list files found in 'results/'."

    for edge_file in edge_files:
        rows = _load_tsv_rows(edge_file)
        # Ensure we have at least a header.
        assert rows, f"File {edge_file} is empty."

        header = rows[0]
        # Basic sanity check: header should have at least two columns
        # (e.g., protein_a, protein_b, score, …).
        assert len(header) >= 2, (
            f"Header in {edge_file} appears malformed: {header}"
        )

        edge_count = len(rows) - 1  # exclude header
        # Policy: either no edges (header‑only) or at least 10 000 edges.
        assert (
            edge_count == 0 or edge_count >= 10_000
        ), (
            f"{edge_file} contains {edge_count} edges; expected 0 or >= 10 000."
        )