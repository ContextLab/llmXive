import os
import sys
import tempfile
import pytest
from pathlib import Path
import numpy as np
import ase
from ase import Atoms
from ase.io import write

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.services.topology_extractor import extract_topology, calculate_rdf, determine_cutoff

@pytest.fixture
def temp_trajectory_dir():
    """Create a temporary directory with test trajectory files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Create a small amorphous silicon-like structure
    # 100 atoms, random positions (simplified for testing)
    np.random.seed(42)
    positions = np.random.rand(100, 3) * 5.0  # 5x5x5 box
    symbols = ['Si'] * 100

    atoms = Atoms(symbols=symbols, positions=positions, cell=[5.0, 5.0, 5.0], pbc=True)

    # Write multiple frames
    trajectory_path = temp_path / "test_trajectory.xyz"
    with open(trajectory_path, 'w') as f:
        for i in range(5):
            atoms.set_positions(positions + np.random.rand(100, 3) * 0.1)
            write(f, atoms, format='xyz', append=True)

    yield temp_path

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_streaming_extraction(temp_trajectory_dir):
    """Test that topology extraction works with streaming logic."""
    input_path = temp_trajectory_dir / "test_trajectory.xyz"
    output_path = temp_trajectory_dir / "output.csv"

    # Run extraction with a small sample limit to simulate large file handling
    result = extract_topology(
        trajectory_path=input_path,
        output_path=output_path,
        sample_limit=2
    )

    assert result["status"] == "success"
    assert result["frames_processed"] == 2
    assert result["total_atoms"] == 200  # 100 atoms * 2 frames
    assert output_path.exists()

    # Verify output content
    import csv
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 200
        assert "atom_id" in rows[0]
        assert "coord_num" in rows[0]
        assert "angle_var" in rows[0]
        assert "is_valid" in rows[0]

def test_rdf_calculation():
    """Test RDF calculation with a known structure."""
    # Create a simple cubic lattice
    atoms = Atoms(
        symbols=['Si'] * 8,
        positions=[
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]
        ],
        cell=[2.0, 2.0, 2.0],
        pbc=True
    )

    r, g_r = calculate_rdf(atoms, cutoff=2.0)

    assert len(r) > 0
    assert len(g_r) > 0
    assert np.all(g_r >= 0)

def test_cutoff_determination():
    """Test cutoff determination from RDF."""
    # Create a structure with a clear first peak
    atoms = Atoms(
        symbols=['Si'] * 10,
        positions=np.random.rand(10, 3) * 3.0,
        cell=[5.0, 5.0, 5.0],
        pbc=True
    )

    r, g_r = calculate_rdf(atoms, cutoff=5.0)

    if len(r) > 0:
        cutoff = determine_cutoff(r, g_r)
        assert 2.0 < cutoff < 4.0, f"Cutoff {cutoff} out of expected range"

def test_large_file_simulation(temp_trajectory_dir):
    """Simulate large file handling with chunking."""
    input_path = temp_trajectory_dir / "test_trajectory.xyz"
    output_path = temp_trajectory_dir / "output_large.csv"

    # Use a small chunk size to test streaming logic
    result = extract_topology(
        trajectory_path=input_path,
        output_path=output_path,
        chunk_size=50,  # Small chunks to force multiple reads
        sample_limit=3
    )

    assert result["status"] == "success"
    assert result["frames_processed"] == 3
    assert output_path.exists()

def test_anomaly_flagging(temp_trajectory_dir):
    """Test that high coordination numbers are flagged."""
    # Create a structure with artificially high coordination
    # by placing atoms very close together
    positions = np.array([
        [0, 0, 0],
        [0.1, 0, 0],
        [-0.1, 0, 0],
        [0, 0.1, 0],
        [0, -0.1, 0],
        [0, 0, 0.1],
        [0, 0, -0.1],
        [0.1, 0.1, 0.1]  # 8th neighbor very close
    ])

    atoms = Atoms(
        symbols=['Si'] * 8,
        positions=positions,
        cell=[2.0, 2.0, 2.0],
        pbc=True
    )

    temp_path = temp_trajectory_dir
    trajectory_path = temp_path / "anomaly_test.xyz"
    output_path = temp_path / "anomaly_output.csv"

    write(trajectory_path, atoms, format='xyz')

    result = extract_topology(
        trajectory_path=trajectory_path,
        output_path=output_path,
        rdf_override=2.5  # High cutoff to catch all neighbors
    )

    assert result["status"] == "success"
    assert result["anomalies_flagged"] > 0  # At least one atom should have coordination > 6

    # Verify in output
    import csv
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row["is_valid"] == "True":
                assert float(row["coord_num"]) > 6