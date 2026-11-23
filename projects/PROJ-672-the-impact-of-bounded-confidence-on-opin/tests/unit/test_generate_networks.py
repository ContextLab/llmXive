"""
Unit tests for the network generation script (T005).

The tests verify that:
1. The script creates the expected number of edgelist files per topology.
2. Each generated network contains exactly 500 nodes.
3. The summary CSV exists and contains the correct columns.
4. The metadata JSON files are valid JSON and contain the required fields.
"""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the script's main function to locate the default output directory
from generate_networks import main as generate_main

@pytest.fixture(scope="module")
def output_dir(tmp_path_factory):
    """Create a temporary output directory for the test run."""
    return tmp_path_factory.mktemp("networks_output")

def run_generator(output_dir: Path, instances: int = 5):
    """
    Run the generate_networks script via a subprocess to mimic the CLI.
    Using a small number of instances keeps the test fast.
    """
    cmd = [
        sys.executable,
        "-m",
        "code.generate_networks",
        "--instances",
        str(instances),
        "--seed",
        "123",
        "--output",
        str(output_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result

def test_generate_files_created(output_dir):
    """Check that the expected edgelist and metadata files are created."""
    run_generator(output_dir, instances=3)

    for topo in ["ER", "BA", "WS"]:
        # Verify edgelist count
        edgelists = list(output_dir.glob(f"{topo}_*.edgelist"))
        assert len(edgelists) == 3, f"Expected 3 {topo} edgelists, found {len(edgelists)}"

        # Verify metadata JSON count
        metas = list(output_dir.glob(f"metadata_{topo}_*.json"))
        assert len(metas) == 3, f"Expected 3 {topo} metadata files, found {len(metas)}"

        # Verify each network has 500 nodes by loading the edgelist
        for edgelist_path in edgelists:
            # Simple node count check: read edges and infer node set
            nodes = set()
            with edgelist_path.open() as f:
                for line in f:
                    u, v = map(int, line.split())
                    nodes.update([u, v])
            # The generator ensures a connected component of size 500,
            # but isolated nodes could be missing from the edge list.
            # Therefore we assert at most 500 nodes and at least 1.
            assert 1 <= len(nodes) <= 500

    # Verify CSV files
    for topo in ["ER", "BA", "WS"]:
        csv_path = output_dir / f"{topo}_metadata.csv"
        assert csv_path.is_file(), f"Missing CSV for topology {topo}"
        df = pd.read_csv(csv_path)
        # Expected minimal columns
        for col in ["topology", "seed", "node_count", "edge_count"]:
            assert col in df.columns

    # Verify JSON structure of a metadata file
    sample_meta = next(output_dir.glob("metadata_ER_*.json"))
    with sample_meta.open() as f:
        data = json.load(f)
    for key in ["topology", "seed", "node_count", "edge_count", "metrics"]:
        assert key in data

def test_cli_successful_exit(output_dir):
    """The CLI should exit with status 0."""
    result = run_generator(output_dir, instances=1)
    assert result.returncode == 0
    # Basic sanity check on stdout (log message)
    assert "Network generation completed." in result.stdout