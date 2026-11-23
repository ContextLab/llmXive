"""
Simple visualisation script for eigenstate probability densities.
Implements the ``visualize`` mode expected by the quickstart guide.
Produces a PNG plot of |ψ_i|² versus site index for a single eigenstate
near the band centre.
"""
import argparse
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian

logger = logging.getLogger(__name__)


def _load_pr_dataset() -> list:
    """
    Helper to load the PR dataset – needed to locate the eigenvector
    corresponding to the requested realisation.
    """
    path = Path("data/processed/pr_raw_multiL.json")
    if not path.is_file():
        logger.error("PR dataset not found; run the full analysis first.")
        raise FileNotFoundError(path)
    with open(path, "r") as f:
        return json.load(f)


def _select_record(
    records: list, L: int, W: float, realization: int
) -> dict:
    """
    Return the first record matching the supplied identifiers.
    """
    for rec in records:
        if (
            rec["L"] == L
            and abs(rec["W"] - W) < 1e-12
            and rec["realization_index"] == realization
        ):
            return rec
    raise ValueError("Requested record not found in the dataset.")


def plot_eigenstate(
    L: int,
    W: float,
    realization: int,
    output_path: Path,
) -> None:
    """
    Generate a probability‑density plot for a single eigenstate.
    """
    # Regenerate the Hamiltonian to obtain the eigenvectors.
    seed = get_config()["SEED"] + realization
    H = generate_hamiltonian(L, W, seed=seed, realization_index=realization)

    # Diagonalise (dense is fine for the modest sizes used for visualisation).
    energies, vecs = np.linalg.eigh(H)
    # Pick the eigenstate closest to zero energy.
    idx = np.argmin(np.abs(energies))
    psi = np.abs(vecs[:, idx]) ** 2

    plt.figure(figsize=(6, 4))
    plt.plot(np.arange(L), psi, marker="o", markersize=3, linestyle="-")
    plt.title(f"Eigenstate probability density (L={L}, W={W})")
    plt.xlabel("Site index")
    plt.ylabel(r"$|\psi_i|^2$")
    plt.grid(True, which="both", ls="--", lw=0.5)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved eigenstate visualisation to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Eigenstate visualisation")
    parser.add_argument("--L", type=int, required=True, help="System size")
    parser.add_argument("--W", type=float, required=True, help="Disorder width")
    parser.add_argument(
        "--realization", type=int, required=True, help="Realisation index"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path for the PNG output"
    )
    args = parser.parse_args()

    out_path = Path(args.output)
    plot_eigenstate(args.L, args.W, args.realization, out_path)


if __name__ == "__main__":
    main()
