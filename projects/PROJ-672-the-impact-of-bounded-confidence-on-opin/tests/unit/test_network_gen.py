"""
Unit tests for the network generation script (T005).

The tests verify:
1. Exactly 50 edge‑list files are created per topology.
2. The summary CSV exists and contains 50 rows.
3. Every generated network reports node_count == 500.
4. The CSV conforms to the JSON schema (basic column check).
"""

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Helper to locate the topology directory
def _topology_dir(topology: str):
    return paths.data("raw", "networks", topology)


@pytest.mark.parametrize("topology", ["ER", "BA", "WS"])
def test_generated_files_exist(topology):
    # Edge‑list files
    edgelist_files = list(_topology_dir(topology).glob("*.edgelist"))
    assert len(edgelist_files) == 50, f"Expected 50 .edgelist files for {topology}"

    # CSV summary
    csv_path = paths.data("raw", "networks", f"{topology}_metadata.csv")
    assert csv_path.is_file(), f"Missing summary CSV for {topology}"

    df = pd.read_csv(csv_path)
    assert len(df) == 50, f"CSV should have 50 rows for {topology}"
    # Basic schema validation – required columns
    required_cols = {"topology", "seed", "node_count", "edge_count"}
    assert required_cols.issubset(df.columns), "CSV missing required columns"

    # Node count check
    assert (df["node_count"] == 500).all(), "All networks must have 500 nodes"