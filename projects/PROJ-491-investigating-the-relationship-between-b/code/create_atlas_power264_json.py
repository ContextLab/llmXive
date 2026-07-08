"""
create_atlas_power264_json.py

This script fetches the Power 264 functional atlas node coordinates in MNI space
using Nilearn's built‑in dataset loader and writes them to a JSON contract file
located at ``data/contracts/atlas_power264.json``.

The generated JSON has the following structure::

    [
        {"node": 1, "x": -24, "y": -30, "z":  36},
        {"node": 2, "x":  26, "y": -30, "z":  36},
        ...
    ]

Each entry corresponds to a node (1‑based indexing) and its MNI coordinates in
millimetres.  The file can be consumed by downstream preprocessing code that
extracts time‑series from the Power atlas.
"""

import json
import os
from pathlib import Path

# Nilearn is used to fetch the official Power 264 atlas coordinates.
# It is listed as a runtime dependency in ``requirements.txt``.
from nilearn.datasets import fetch_atlas_power_2011

# Project‑wide configuration utilities (ensure directories exist, etc.)
# If the project later adds more helpers to ``config`` they can be imported
# here without changing this script.
try:
    from config import ensure_directories
except Exception:  # pragma: no cover
    # Fallback: a minimal implementation if ``config`` is not yet providing
    # ``ensure_directories``.  This keeps the script runnable in isolation.
    def ensure_directories(*paths: Path) -> None:
        for p in paths:
            p.mkdir(parents=True, exist_ok=True)


def fetch_power264_coordinates() -> list[dict]:
    """
    Retrieve Power 264 node coordinates using Nilearn.

    Returns
    -------
    list[dict]
        A list of dictionaries, each containing the node index (1‑based)
        and its ``x``, ``y``, ``z`` MNI coordinates.
    """
    atlas = fetch_atlas_power_2011()
    # ``coordinates`` is an ``(264, 3)`` NumPy array of (x, y, z) values.
    coords = atlas["coordinates"]
    nodes = []
    for idx, (x, y, z) in enumerate(coords, start=1):
        nodes.append({"node": idx, "x": float(x), "y": float(y), "z": float(z)})
    return nodes


def write_json_contract(nodes: list[dict], output_path: Path) -> None:
    """
    Write the node list to a JSON file with pretty formatting.

    Parameters
    ----------
    nodes : list[dict]
        List of node dictionaries as produced by ``fetch_power264_coordinates``.
    output_path : Path
        Destination path for the JSON contract.
    """
    # Ensure the parent directory exists.
    ensure_directories(output_path.parent)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2, sort_keys=False)
    print(f"Power 264 atlas contract written to {output_path}")


def main() -> None:
    """
    Main entry point.

    The script can be executed directly:
        python code/create_atlas_power264_json.py
    """
    # Define the contract location relative to the repository root.
    contract_path = Path(__file__).resolve().parents[1] / "data" / "contracts" / "atlas_power264.json"

    nodes = fetch_power264_coordinates()
    write_json_contract(nodes, contract_path)


if __name__ == "__main__":
    main()
