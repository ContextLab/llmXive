"""
Unit test for the extended generate_networks script.

It runs the script for a single ER instance and checks that the produced
metadata JSON file contains a ``metrics`` field with the expected
structural metric keys.
"""

import json
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths


def test_generate_network_includes_metrics(tmp_path):
    """
    Execute the network generator for one ER instance and verify that the
    resulting metadata JSON contains the calculated structural metrics.
    """
    # Run the generator script with deterministic arguments.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "code.generate_networks",
            "--topology",
            "ER",
            "--instances",
            "1",
            "--seed",
            "0",
        ],
        check=True,
        cwd=Path.cwd(),
    )

    # Resolve the expected metadata file path.
    metadata_path = paths.data("raw", "networks", "ER", "metadata_ER_0000.json")
    assert metadata_path.is_file(), f"Metadata file not found: {metadata_path}"

    # Load and inspect the JSON content.
    with metadata_path.open("r") as f:
        data = json.load(f)

    # The top‑level keys required by the schema must be present.
    for key in ("topology", "seed", "node_count", "edge_count"):
        assert key in data, f"Missing key '{key}' in metadata"

    # The extended script must add a ``metrics`` dictionary.
    assert "metrics" in data, "Metrics field missing from metadata JSON"

    # Verify that the metrics dictionary contains the expected entries.
    metric_keys = {
        "assortativity",
        "average_path_length",
        "clustering_coefficient",
        "num_nodes",
        "num_edges",
    }
    assert metric_keys.issubset(data["metrics"].keys()), "Incomplete metrics data"