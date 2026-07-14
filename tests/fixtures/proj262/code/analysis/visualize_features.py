"""visualize_features.py
-----------------------
Generate visualizations of feature importance maps for representative molecules.

The script reads ``results/attributions.json`` (produced by the attribution
pipeline) which is expected to contain a list of entries.  Each entry must
include at least the following keys:

* ``molecule_id`` – a unique identifier for the molecule (any hashable type)
* ``coordinates`` – a list of ``[x, y, z]`` triples for each atom
* ``atom_importances`` – a list of float importance values for each atom
  (same length as ``coordinates``)

For each selected molecule a 3‑D scatter plot is created where the colour
encodes the importance of each atom.  The plot is saved as a PNG file in
``results/figures/feature_importance_<molecule_id>.png``.

The script can be invoked from the command line:

    python code/analysis/visualize_features.py [--num-samples N]

``--num-samples`` limits the number of molecules visualised (default: 5).
If the JSON file or required fields are missing the script logs a warning
and continues with the next entry.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D projection)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_attributions(attributions_path: Path) -> List[Dict[str, Any]]:
    """Load the attributions JSON file.

    Parameters
    ----------
    attributions_path: Path
        Path to the JSON file.

    Returns
    -------
    List[Dict[str, Any]]
        The list of attribution records.
    """
    if not attributions_path.is_file():
        logger.error("Attributions file not found: %s", attributions_path)
        return []

    try:
        with attributions_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON file %s: %s", attributions_path, exc)
        return []

    if not isinstance(data, list):
        logger.error("Expected a list of attributions in %s", attributions_path)
        return []

    return data


def validate_entry(entry: Dict[str, Any]) -> bool:
    """Check that a single attribution entry contains the required fields."""
    required = {"molecule_id", "coordinates", "atom_importances"}
    missing = required - entry.keys()
    if missing:
        logger.warning("Entry missing required keys %s – skipping.", missing)
        return False

    coords = entry["coordinates"]
    importances = entry["atom_importances"]
    if not (isinstance(coords, list) and isinstance(importances, list)):
        logger.warning("Coordinates or importances are not lists – skipping.")
        return False
    if len(coords) != len(importances):
        logger.warning(
            "Length mismatch between coordinates (%d) and importances (%d) – skipping.",
            len(coords),
            len(importances),
        )
        return False
    return True


def plot_importance(
    molecule_id: Any,
    coordinates: List[List[float]],
    importances: List[float],
    output_path: Path,
) -> None:
    """Create a 3‑D scatter plot where colour indicates atom importance.

    Parameters
    ----------
    molecule_id: Any
        Identifier used only for logging.
    coordinates: List[List[float]]
        List of ``[x, y, z]`` triples.
    importances: List[float]
        Importance values for each atom.
    output_path: Path
        Destination PNG file.
    """
    xs, ys, zs = zip(*coordinates)  # type: ignore[arg-type]

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(
        xs,
        ys,
        zs,
        c=importances,
        cmap="viridis",
        s=60,
        edgecolor="k",
        depthshade=True,
    )
    ax.set_title(f"Feature Importance – Molecule {molecule_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    fig.colorbar(sc, ax=ax, label="Importance")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Saved feature‑importance plot for %s to %s", molecule_id, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualize atom‑wise feature importance for representative molecules."
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=5,
        help="Maximum number of molecules to visualise (default: 5).",
    )
    args = parser.parse_args()

    # Resolve project‑root relative paths
    project_root = Path(__file__).resolve().parents[2]  # <repo>/code/analysis -> <repo>
    attributions_file = project_root / "results" / "attributions.json"
    figures_dir = project_root / "results" / "figures"

    attributions = load_attributions(attributions_file)
    if not attributions:
        logger.error("No attributions to process – exiting.")
        return

    processed = 0
    for entry in attributions:
        if processed >= args.num_samples:
            break
        if not validate_entry(entry):
            continue

        molecule_id = entry["molecule_id"]
        coords = entry["coordinates"]
        importances = entry["atom_importances"]

        # Normalise importance values for colour mapping
        if all(v == 0 for v in importances):
            norm_importances = importances
        else:
            min_imp, max_imp = min(importances), max(importances)
            range_imp = max_imp - min_imp if max_imp != min_imp else 1.0
            norm_importances = [(v - min_imp) / range_imp for v in importances]

        out_file = figures_dir / f"feature_importance_{molecule_id}.png"
        plot_importance(molecule_id, coords, norm_importances, out_file)
        processed += 1

    if processed == 0:
        logger.warning("No valid attribution entries were found.")
    else:
        logger.info("Generated visualisations for %d molecule(s).", processed)


if __name__ == "__main__":
    main()
