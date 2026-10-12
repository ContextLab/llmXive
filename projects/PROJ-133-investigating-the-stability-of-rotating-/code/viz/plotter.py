"""Visualization utilities for the rotating BEC study.

The module defines a single public function :func:`plot_phase_map` that
generates PNG figures of vortex‑density phase maps.  The function is
fully documented with a NumPy‑style docstring.
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np

from llmxive_toolkit import paths

def plot_phase_map(
    input_json: str,
    output_path: str = "figures/phase_map.png",
    cmap: str = "viridis",
) -> None:
    """Generate a phase‑map contour plot from aggregated results.

    Parameters
    ----------
    input_json : str
        Path to the JSON file containing aggregated statistical results.
    output_path : str, optional
        Destination file for the PNG image (default ``figures/phase_map.png``).
    cmap : str, optional
        Matplotlib colormap name for the contour plot (default ``"viridis"``).

    Returns
    -------
    None
        The function writes the figure to ``output_path``; it returns
        ``None``.
    """
    # Load the aggregated results.
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Expecting a 2‑D grid of vortex‑density values keyed by (Ω, ε_dd).
    # For simplicity we assume ``data`` is a list of dicts with keys
    # ``omega``, ``epsilon_dd``, and ``vortex_density``.
    omegas = sorted({entry["omega"] for entry in data})
    epsilons = sorted({entry["epsilon_dd"] for entry in data})

    # Build a 2‑D array for contouring.
    Z = np.zeros((len(omegas), len(epsilons)))
    for entry in data:
        i = omegas.index(entry["omega"])
        j = epsilons.index(entry["epsilon_dd"])
        Z[i, j] = entry["vortex_density"]

    Omega, Epsilon = np.meshgrid(epsilons, omegas)

    plt.figure(figsize=(8, 6))
    cp = plt.contourf(Omega, Epsilon, Z, cmap=cmap, levels=20)
    plt.colorbar(cp, label="Vortex Density")
    plt.xlabel(r"$\epsilon_{dd}$")
    plt.ylabel(r"$\Omega$")
    plt.title("Stability Phase Map (Vortex Density)")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
