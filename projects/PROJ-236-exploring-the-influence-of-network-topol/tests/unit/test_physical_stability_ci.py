"""
Unit test for the ``code/ci/check_physical_stability.py`` script.

The test ensures that the ``main`` function exits with the correct
status code depending on the proportion of stable structures.

The test creates a temporary ``data/raw/atomic_seeds`` directory with
a small number of synthetic ASE ``Atoms`` objects.  Because the CI
script is required to work on *real* data, the test does **not**
replace the real implementation of ``filter_stable_structures`` – it
uses the actual function from ``utils.validation``.  The synthetic
structures are simple enough to be considered stable by the default
filter (which checks bond‑distance thresholds).  The test then
manipulates one structure to be unstable (by scaling atomic positions
far apart) and verifies that the script exits with a non‑zero code
when the rejection rate exceeds 5 %.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

import pytest
from ase import Atoms

# Import the functions under test
from ci.check_physical_stability import load_seed_structures, main


@pytest.fixture
def temporary_seed_dir(tmp_path: Path):
    """
    Create a temporary ``data/raw/atomic_seeds`` directory populated with
    a few simple ASE ``Atoms`` objects.
    """
    seed_dir = tmp_path / "data" / "raw" / "atomic_seeds"
    seed_dir.mkdir(parents=True)

    # Create three tiny cubic cells – these are trivially stable.
    for i in range(3):
        atoms = Atoms(
            symbols=["Cu"] * 2,
            positions=[[0, 0, 0], [1.8, 0, 0]],  # typical Cu nearest‑neighbor ~2.5 Å
            cell=[5, 5, 5],
        )
        file_path = seed_dir / f"seed_{i}.xyz"
        atoms.write(file_path)

    # Return the path so the test can temporarily patch the default location.
    return seed_dir


def test_load_seed_structures(temporary_seed_dir: Path):
    # Patch the default directory via environment variable or direct call
    seeds = load_seed_structures(seeds_dir=temporary_seed_dir)
    assert len(seeds) == 3
    for atoms in seeds:
        assert isinstance(atoms, Atoms)


def test_main_passes_when_rejection_rate_below_threshold(tmp_path: Path, monkeypatch):
    """
    All seeds are stable → rejection rate = 0 → script should exit with 0.
    """
    seed_dir = tmp_path / "data" / "raw" / "atomic_seeds"
    seed_dir.mkdir(parents=True)

    # Write two stable seeds
    for i in range(2):
        atoms = Atoms(
            symbols=["Cu"] * 2,
            positions=[[0, 0, 0], [2.0, 0, 0]],
            cell=[5, 5, 5],
        )
        atoms.write(seed_dir / f"seed_{i}.xyz")

    # Monkey‑patch the path used by load_seed_structures
    monkeypatch.setattr(
        "ci.check_physical_stability.load_seed_structures",
        lambda seeds_dir=seed_dir: load_seed_structures(seeds_dir=seed_dir),
    )

    # Run the script as a subprocess to capture the exit code
    result = subprocess.run([sys.executable, "-m", "ci.check_physical_stability"], cwd=tmp_path)
    assert result.returncode == 0


def test_main_fails_when_rejection_rate_exceeds_threshold(tmp_path: Path, monkeypatch):
    """
    Create three seeds, make one unstable → rejection rate = 33 % > 5 % → exit 1.
    """
    seed_dir = tmp_path / "data" / "raw" / "atomic_seeds"
    seed_dir.mkdir(parents=True)

    # Two stable seeds
    for i in range(2):
        atoms = Atoms(
            symbols=["Cu"] * 2,
            positions=[[0, 0, 0], [2.0, 0, 0]],
            cell=[5, 5, 5],
        )
        atoms.write(seed_dir / f"stable_{i}.xyz")

    # One deliberately unstable seed (atoms far apart)
    unstable = Atoms(
        symbols=["Cu"] * 2,
        positions=[[0, 0, 0], [10.0, 0, 0]],  # far beyond typical NN distance
        cell=[5, 5, 5],
    )
    unstable.write(seed_dir / "unstable.xyz")

    # Monkey‑patch loader to use our temporary directory
    monkeypatch.setattr(
        "ci.check_physical_stability.load_seed_structures",
        lambda seeds_dir=seed_dir: load_seed_structures(seeds_dir=seed_dir),
    )

    result = subprocess.run([sys.executable, "-m", "ci.check_physical_stability"], cwd=tmp_path)
    assert result.returncode == 1


# The ``if __name__ == '__main__'`` guard in the module allows it to be
# executed directly via ``python -m ci.check_physical_stability``.
# The above subprocess calls rely on that behaviour.