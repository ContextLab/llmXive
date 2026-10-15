"""
Visualize results from the simulation and analysis pipeline.

This module provides utilities to generate a 3D surface plot visualizing the
Success Rate as a function of Masking Horizon and Semantic Density,
representing the regime map of optimal retention windows.

The public API is compatible with the integration tests in
`tests/integration/test_plot_generation.py`, which expect the following
functions:

- `load_regression_summary(path: Path | None = None) -> dict`
- `generate_surface_grid(summary: dict, n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
- `plot_3d_surface(summary: dict, output_dir: Path, filename: str) -> Path`

The default behavior (when run as a script) loads the regression summary
from ``output/regression_summary.json`` and writes the plot to
``output/plots/regime_map.png``.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import matplotlib

# Use a non‑interactive backend suitable for headless CI environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Constants (used when the module is executed as a script)
# ----------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_PLOTS_DIR = DEFAULT_OUTPUT_DIR / "plots"
DEFAULT_REGRESSION_SUMMARY = DEFAULT_OUTPUT_DIR / "regression_summary.json"
DEFAULT_PLOT_FILENAME = "regime_map.png"
MAX_FILE_SIZE_MB = 5

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_regression_summary(path: Path | None = None) -> Dict[str, Any]:
    """
    Load the regression summary JSON produced by ``analyze_results.py``.

    Parameters
    ----------
    path : Path | None
        Path to the JSON file. If ``None``, the default location
        ``output/regression_summary.json`` is used.

    Returns
    ----------
    dict
        Parsed JSON content.
    """
    if path is None:
        path = DEFAULT_REGRESSION_SUMMARY

    if not path.exists():
        raise FileNotFoundError(
            f"Regression summary not found at {path}. "
            "Run the analysis step before visualizing."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_surface_grid(
    summary: Dict[str, Any], n_points: int = 50
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a regular grid of (Horizon, Density) points and predict the
    success rate using the logistic regression coefficients stored in the
    regression summary.

    The model is approximated as a simple logistic regression with a
    linear interaction term:

        logit(P) = intercept + b_h * H + b_d * D + b_hd * H * D

    If spline coefficients are present, they are ignored for the purpose
    of this visualization – the interaction term is sufficient to
    illustrate the regime map.

    Parameters
    ----------
    summary : dict
        Regression summary dictionary.
    n_points : int, optional
        Number of points per axis for the mesh grid.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        Meshgrid arrays (H, D) and the predicted success probabilities Z.
    """
    # Extract coefficients (fallback to 0.0 if missing)
    coeffs = summary.get("coefficients", {})
    intercept = coeffs.get("Intercept", 0.0)
    beta_horizon = coeffs.get("horizon", 0.0)
    beta_density = coeffs.get("density", 0.0)
    beta_interaction = coeffs.get("density:horizon", 0.0)

    # Determine horizon range – use values from the summary if available,
    # otherwise fall back to a sensible default.
    max_horizon = summary.get("max_horizon", 20)
    min_horizon = summary.get("min_horizon", 1)
    horizon_range = np.linspace(min_horizon, max_horizon, n_points)

    # Density is defined between 0 and 1.
    density_range = np.linspace(0.0, 1.0, n_points)

    H, D = np.meshgrid(horizon_range, density_range)

    # Compute the logistic regression logit.
    logit = (
        intercept
        + beta_horizon * H
        + beta_density * D
        + beta_interaction * H * D
    )

    # Apply the sigmoid function.
    Z = 1.0 / (1.0 + np.exp(-logit))

    return H, D, Z

def _save_plot(
    H: np.ndarray,
    D: np.ndarray,
    Z: np.ndarray,
    output_path: Path,
) -> None:
    """
    Render the 3‑D surface plot and write it to ``output_path``.

    The function ensures the output directory exists and verifies that
    the resulting file size does not exceed :data:`MAX_FILE_SIZE_MB`.
    """
    # Ensure the directory hierarchy exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Plot the surface.
    surf = ax.plot_surface(
        H,
        D,
        Z,
        cmap="viridis",
        edgecolor="none",
        alpha=0.9,
    )

    # Axis labels must match the specification exactly.
    ax.set_xlabel("Masking Horizon")
    ax.set_ylabel("Semantic Density")
    ax.set_zlabel("Success Rate")

    # Color bar for reference.
    fig.colorbar(
        surf,
        ax=ax,
        shrink=0.5,
        aspect=10,
        label="Success Rate",
    )

    ax.set_title("Regime Map: Optimal Retention Windows")

    # Attempt to save at a high DPI first; reduce if the size limit is hit.
    for dpi in (150, 100, 80):
        plt.savefig(
            output_path,
            dpi=dpi,
            bbox_inches="tight",
            facecolor="white",
        )
        plt.close(fig)

        size_mb = output_path.stat().st_size / (1024 * 1024)
        if size_mb <= MAX_FILE_SIZE_MB:
            break
        # If still too large, continue with the next lower DPI.

    if size_mb > MAX_FILE_SIZE_MB:
        raise RuntimeError(
            f"Generated plot exceeds {MAX_FILE_SIZE_MB} MB "
            f"({size_mb:.2f} MB). Reduce resolution or simplify the mesh."
        )

def plot_3d_surface(
    summary: Dict[str, Any],
    output_dir: Path,
    filename: str,
) -> Path:
    """
    Public API used by the integration test.

    Parameters
    ----------
    summary : dict
        Regression summary dictionary.
    output_dir : Path
        Directory where the plot should be saved.
    filename : str
        Desired filename for the PNG image.

    Returns
    -------
    Path
        Path to the generated PNG file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Generate the mesh grid and predictions.
    H, D, Z = generate_surface_grid(summary)

    # Render and save the figure.
    _save_plot(H, D, Z, output_path)

    return output_path

# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def _main() -> None:
    """
    When the module is executed directly, generate the regime map using
    the default locations.
    """
    try:
        print(f"Loading regression summary from {DEFAULT_REGRESSION_SUMMARY}...")
        summary = load_regression_summary()
    except Exception as exc:
        print(f"Error loading regression summary: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Generating surface grid and plotting...")
    try:
        plot_path = plot_3d_surface(
            summary,
            DEFAULT_PLOTS_DIR,
            DEFAULT_PLOT_FILENAME,
        )
    except Exception as exc:
        print(f"Error generating plot: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Success: Regime map saved to {plot_path}")

    # Final sanity check.
    if not plot_path.exists():
        print("Error: Plot file was not created.", file=sys.stderr)
        sys.exit(1)

    size_mb = plot_path.stat().st_size / (1024 * 1024)
    print(f"Plot file size: {size_mb:.2f} MB (limit: {MAX_FILE_SIZE_MB} MB)")

if __name__ == "__main__":
    _main()