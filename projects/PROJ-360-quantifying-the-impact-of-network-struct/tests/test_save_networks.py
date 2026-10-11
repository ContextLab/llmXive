"""
test_save_networks.py

Basic integration test for the ``save_networks.py`` script.

The test creates a temporary CIF file (using a minimal crystal structure
from pymatgen) in a temporary input directory, runs the script, and
checks that a corresponding pickle file is produced in the output
directory.

This test does not require network access; it uses a tiny synthetic
structure that is valid for graph construction.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from pymatgen.core import Structure, Lattice, Site

# Helper to create a minimal CIF file that ``construct_network`` can parse.
def create_minimal_cif(path: Path, material_id: str) -> None:
    # Simple cubic structure with two atoms (NaCl prototype) – sufficient for
    # bond detection and graph creation.
    lattice = Lattice.cubic(5.64)
    species = ["Na", "Cl"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    struct = Structure(lattice, species, coords)
    struct.to(filename=str(path), fmt="cif")

@pytest.fixture
def temp_dirs(tmp_path: Path):
    """Create temporary input and output directories."""
    input_dir = tmp_path / "raw_cif"
    output_dir = tmp_path / "networks"
    input_dir.mkdir()
    output_dir.mkdir()
    yield input_dir, output_dir
    # Cleanup handled by pytest's tmp_path fixture.

def test_save_networks_creates_pickle(temp_dirs):
    input_dir, output_dir = temp_dirs

    # Create a single minimal CIF file.
    material_id = "testmaterial"
    cif_path = input_dir / f"{material_id}.cif"
    create_minimal_cif(cif_path, material_id)

    # Execute the script via subprocess (the same way the quickstart runs it).
    script_path = Path("code/save_networks.py")
    result = subprocess.run(
        [
            "python",
            str(script_path),
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    # Ensure the script exited successfully.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the expected pickle file exists.
    expected_pickle = output_dir / f"{material_id}.pkl"
    assert expected_pickle.is_file(), "Pickle file was not created."

    # Optional sanity check: load the pickle and confirm it is a NetworkX graph.
    import pickle

    with expected_pickle.open("rb") as f:
        graph = pickle.load(f)

    # The graph should have at least two nodes (the two atoms).
    assert hasattr(graph, "number_of_nodes")
    assert graph.number_of_nodes() >= 2