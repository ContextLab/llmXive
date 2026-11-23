"""
Heat‑map visualisation for Möbius autocorrelation results.

For each interval length ``L`` in {1000, 10000, 100000} the script
reads ``data/processed/autocorr_stats.csv`` and produces a PNG
heat‑map ``outputs/figures/heatmap_L{L}.png`` showing autocorrelation
values (colour) as a function of lag (x‑axis) and interval start
(y‑axis).  The zero line (autocorrelation = 0) is drawn as a white
horizontal line and the 95 % confidence band from the permutation
null distribution is shaded.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INPUT_CSV = pathlib.Path("data/processed/autocorr_stats.csv")
OUTPUT_DIR = pathlib.Path("outputs/figures")
L_VALUES = [1000, 10000, 100000]

# ----------------------------------------------------------------------


def _ensure_parent_dir(p: pathlib.Path) -> None:
    """Create the parent directory of *p* if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _plot_heatmap_for_L(df: pd.DataFrame, L: int) -> None:
    """Create and save a heat‑map for a specific interval length.

    Parameters
    ----------
    df : pandas.DataFrame
        Sub‑frame containing only rows with the given ``L``.
    L : int
        Interval length.
    """
    # Pivot so rows = interval_start, columns = lag, values = autocorrelation
    pivot = df.pivot(index="interval_start", columns="lag", values="autocorrelation")
    if pivot.empty:
        print(f"[WARN] No data for L={L}; skipping heat‑map.", file=sys.stderr)
        return

    # Prepare the figure.
    plt.figure(figsize=(10, 8))
    cmap = plt.get_cmap("RdBu_r")
    im = plt.imshow(
        pivot,
        aspect="auto",
        origin="lower",
        cmap=cmap,
        vmin=-1,
        vmax=1,
    )
    plt.colorbar(im, label="Autocorrelation")
    plt.title(f"Autocorrelation heat‑map (L = {L})")
    plt.xlabel("Lag $h$")
    plt.ylabel("Interval start $k$")

    # Draw the zero‑line across all lags.
    plt.axhline(y=-0.5, color="white", linewidth=1.5)  # baseline at 0 autocorr

    # Shade the 95 % confidence band (ci_lower / ci_upper).
    # We compute the band per lag across all intervals.
    ci_lower = df.groupby("lag")["ci_lower"].mean()
    ci_upper = df.groupby("lag")["ci_upper"].mean()
    lags = ci_lower.index.values
    # Create a semi‑transparent polygon covering the band.
    plt.fill_between(
        lags,
        ci_lower,
        ci_upper,
        color="gray",
        alpha=0.3,
        label="95 % CI (permutations)",
    )
    plt.legend(loc="upper right")

    # Save the figure.
    out_path = OUTPUT_DIR / f"heatmap_L{L}.png"
    _ensure_parent_dir(out_path)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved heat‑map for L={L} to {out_path}")


def main() -> None:
    """Generate heat‑maps for all required interval lengths."""
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(f"Required CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    for L in L_VALUES:
        sub_df = df[df["interval_length"] == L]
        _plot_heatmap_for_L(sub_df, L)


if __name__ == "__main__":
    main()
