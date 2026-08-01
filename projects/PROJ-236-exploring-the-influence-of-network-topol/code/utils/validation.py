"""
utils.validation
-----------------

Physical Stability Filter utilities.

This module provides functions to assess the physical stability of atomic
structures (e.g., XYZ or POSCAR files) based on simple geometric criteria:

* All inter‑atomic distances must be larger than ``cutoff_factor`` times a
  reference nearest‑neighbor distance (median of per‑atom nearest distances).
* No two atoms may occupy the same position (distance exactly zero).

The functions are deliberately lightweight and rely only on the ASE
(Atomic Simulation Environment) package, which is already declared as a
project dependency.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import numpy as np
from ase import Atoms
from ase.io import read, write

__all__ = [
    "is_structure_stable",
    "filter_stable_structures",
]


def _compute_reference_nn_distance(atoms: Atoms) -> float:
    """
    Compute a reference nearest‑neighbor distance for a set of atoms.

    The reference is defined as the median of each atom's nearest‑neighbor
    distance (excluding the atom itself). Using the median makes the metric
    robust against a few anomalously short or long bonds that may be present
    in disordered structures.

    Parameters
    ----------
    atoms: Atoms
        ASE Atoms object containing the atomic positions.

    Returns
    -------
    float
        Median nearest‑neighbor distance (Å).
    """
    positions = atoms.get_positions()
    # Compute full pairwise distance matrix
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dists = np.linalg.norm(diff, axis=-1)

    # Mask the diagonal (self‑distances) by setting them to np.inf
    np.fill_diagonal(dists, np.inf)

    # Minimum distance for each atom (its nearest neighbour)
    min_per_atom = np.min(dists, axis=1)

    # Median of those minima is the reference distance
    reference = float(np.median(min_per_atom))
    return reference


def is_structure_stable(
    filepath: str | Path,
    cutoff_factor: float = 0.8,
) -> bool:
    """
    Determine whether an atomic structure satisfies the physical stability
    filter.

    The filter checks two conditions:

    1. No pair of atoms is closer than ``cutoff_factor`` × *reference_nn*,
       where *reference_nn* is the median nearest‑neighbor distance.
    2. No pair of atoms occupies exactly the same coordinates (zero distance).

    Parameters
    ----------
    filepath: str or Path
        Path to an atomic structure file readable by ASE (e.g., XYZ, POSCAR).
    cutoff_factor: float, optional
        Multiplicative factor applied to the reference nearest‑neighbor distance.
        Default is 0.8, matching the specification.

    Returns
    -------
    bool
        ``True`` if the structure passes the filter, ``False`` otherwise.
    """
    atoms = read(filepath)  # ASE automatically detects format
    if not isinstance(atoms, Atoms):
        raise TypeError(f"File {filepath} did not produce an ASE Atoms object.")

    positions = atoms.get_positions()
    if positions.shape[0] < 2:
        # A single atom cannot be judged for bond distances – consider it stable.
        return True

    # Compute pairwise distances
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dists = np.linalg.norm(diff, axis=-1)

    # Check for exact overlaps (zero distance)
    if np.any(np.isclose(dists + np.eye(dists.shape[0]), 0.0)):
        return False

    # Reference nearest‑neighbor distance
    reference_nn = _compute_reference_nn_distance(atoms)

    # Apply the cutoff
    min_allowed = cutoff_factor * reference_nn

    # Mask diagonal and check if any distance is below the threshold
    np.fill_diagonal(dists, np.inf)
    if np.any(dists < min_allowed):
        return False

    return True


def filter_stable_structures(
    input_dir: str | Path,
    output_dir: str | Path,
    cutoff_factor: float = 0.8,
) -> List[Path]:
    """
    Scan a directory of atomic seed files, retain only those that satisfy the
    physical stability filter, and copy them to an output directory.

    Parameters
    ----------
    input_dir: str or Path
        Directory containing atomic seed files (e.g., XYZ, POSCAR).
    output_dir: str or Path
        Destination directory for structures that pass the filter.
    cutoff_factor: float, optional
        Factor used in the stability check (default 0.8).

    Returns
    -------
    List[Path]
        List of paths (within ``output_dir``) of the structures that were
        copied because they passed the filter.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    passed: List[Path] = []

    for file_path in input_path.iterdir():
        if file_path.is_file():
            try:
                stable = is_structure_stable(file_path, cutoff_factor=cutoff_factor)
            except Exception as exc:
                # If the file cannot be parsed, treat it as unstable and continue.
                # Raising would abort the entire filtering step, which is not
                # desirable for batch processing.
                continue

            if stable:
                dest = output_path / file_path.name
                shutil.copy2(file_path, dest)
                passed.append(dest)

    return passed