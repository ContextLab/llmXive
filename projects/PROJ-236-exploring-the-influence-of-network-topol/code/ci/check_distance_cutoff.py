"""
CI utility to verify that the distance‑cutoff scaling factor defined in the
simulation configuration actually changes the nearest‑neighbour cutoff.
The script exits with a non‑zero status if the scaling factor leaves the
cutoff unchanged (i.e. factor == 1.0), causing the CI pipeline to fail.
"""

import sys
from pathlib import Path

import numpy as np
from ase import io

# Project imports
from generate_networks import nearest_neighbor_distance
from utils.io import load_simulation_config, get_config_value

def find_first_seed_file() -> Path:
    """
    Locate the first atomic seed file (XYZ or POSCAR) under
    ``data/raw/atomic_seeds``.  The function raises ``FileNotFoundError`` if
    no suitable file is found.
    """
    seeds_dir = Path(__file__).resolve().parents[2] / "data" / "raw" / "atomic_seeds"
    for ext in ("*.xyz", "*.POSCAR", "*.poscar"):
        matches = list(seeds_dir.glob(ext))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No atomic seed file found in {seeds_dir}")

def check_cutoff_scaling() -> bool:
    """
    Returns ``True`` if the configured cutoff scaling factor changes the
    nearest‑neighbour distance, ``False`` otherwise.
    """
    # Load configuration – the helper returns a dict‑like object.
    config = load_simulation_config()
    factor = float(get_config_value(config, "cutoff_factor"))

    # Determine the reference nearest‑neighbour distance.
    seed_path = find_first_seed_file()
    nn_distance = nearest_neighbor_distance(seed_path)

    # Compute the scaled cutoff.
    scaled_cutoff = factor * nn_distance

    # If the scaled cutoff is (within tolerance) equal to the original,
    # the scaling factor is ineffective and should cause CI failure.
    return not np.isclose(scaled_cutoff, nn_distance)

def main() -> None:
    """
    Entry‑point used by the CI runner.
    """
    if not check_cutoff_scaling():
        print(
            "[CI] Distance‑cutoff verification failed: scaling factor does not "
            "modify the nearest‑neighbour distance.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("[CI] Distance‑cutoff verification passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
