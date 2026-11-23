"""
Master orchestration script for the Möbius autocorrelation pipeline.

This script runs the full analysis in the required order:
  1. Generate the Möbius sequence (sieve)
  2. Pack the Möbius sequence into a 2‑bit representation (packing)
  3. Sample windows (generate_mobius)
  4. Compute autocorrelations (autocorrelation)
  5. Cross‑validation of autocorrelations (int64 exact)
  6. Build the null distribution (null_distribution)
  7. Apply Benjamini‑Hochberg FDR correction (fdr_correction)
  8. Perform zero‑density sensitivity analysis (sensitivity)
  9. Produce heat‑map visualisations (viz)
  10. Run the Kolmogorov‑Smirnov uniformity test (uniformity_test)

The script can be invoked as a module:
    python -m code.main [--demo]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import the entry‑point functions from the existing modules.
from generate_mobius import main as generate_mobius_main
from sieve import main as sieve_main
from autocorrelation import main as autocorr_main
from cross_validate_autocorrelation import main as cross_validate_main
from null_distribution import main as null_dist_main
from fdr_correction import main as fdr_main
from sensitivity import main as sensitivity_main
from viz import main as viz_main
from uniformity_test import main as uniformity_main
# NEW: packing step
from pack import main as pack_main

# Helper from the llmxive toolkit for path handling
from llmxive_toolkit import paths

def _run_step(step_func, step_name: str) -> None:
    """Execute a pipeline step and abort on failure."""
    try:
        step_func()
    except Exception as exc:
        print(f"[ERROR] Step '{step_name}' failed: {exc}", file=sys.stderr)
        raise

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Möbius autocorrelation pipeline."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick demo (reduced data size).",
    )
    return parser.parse_args()

def _run_demo() -> None:
    """
    Execute a minimal demo pipeline.
    Produces:
      - data/mobius_array.npy
      - data/window_starts.json
      - data/processed/demo_autocorr.csv
      - figures/heatmap_demo.png
    """
    from sieve import compute_mobius
    from autocorrelation import compute_autocorrelation

    # 1. Create a small Möbius array (N = 2000)
    N_DEMO = 2000
    mobius_arr = compute_mobius(N_DEMO)
    mobius_path = paths.data("mobius_array.npy")
    _ensure_parent_dir(mobius_path)
    np.save(mobius_path, mobius_arr)
    print(f"Demo Möbius array saved to {mobius_path}")

    # 2. Write a minimal window index JSON (one window per L)
    window_starts = {
        "1000": [1],
        "10000": [1],
        "100000": [1],
    }
    window_json_path = paths.data("window_starts.json")
    _ensure_parent_dir(window_json_path)
    with window_json_path.open("w", encoding="utf-8") as f:
        json.dump(window_starts, f, indent=2)
    print(f"Demo window starts written to {window_json_path}")

    # 3. Compute a single autocorrelation (L=1000, h=1)
    L_DEMO = 1000
    start_demo = 1
    h_demo = 1
    autocorr_val = compute_autocorrelation(mobius_arr, start_demo, L_DEMO, h_demo)

    demo_csv_path = paths.processed("demo_autocorr.csv")
    _ensure_parent_dir(demo_csv_path)
    df_demo = pd.DataFrame(
        [{
            "window_start": start_demo,
            "L": L_DEMO,
            "h": h_demo,
            "autocorrelation": autocorr_val,
        }]
    )
    df_demo.to_csv(demo_csv_path, index=False)
    print(f"Demo autocorrelation written to {demo_csv_path}")

    # 4. Produce a trivial heat‑map figure
    heat_data = np.array([[autocorr_val]])
    fig_path = paths.figures("heatmap_demo.png")
    _ensure_parent_dir(fig_path)

    plt.switch_backend("Agg")
    plt.figure(figsize=(4, 3))
    plt.imshow(heat_data, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(label="Autocorrelation")
    plt.title("Demo heat‑map (single value)")
    plt.xlabel("Lag $h$")
    plt.ylabel("Window index")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()
    print(f"Demo heat‑map saved to {fig_path}")

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Run the pipeline in the correct order."""
    args = _parse_args()

    if args.demo:
        _run_demo()
        return

    # 1. Compute the raw Möbius array.
    _run_step(sieve_main, "sieve")
    # 2. Pack the Möbius array into its 2‑bit representation.
    _run_step(pack_main, "packing")
    # 3. Generate deterministic window indices.
    _run_step(generate_mobius_main, "window sampling")
    # 4. Compute autocorrelations for all windows.
    _run_step(autocorr_main, "autocorrelation")
    # 5. Cross‑validate FFT results with exact integer arithmetic.
    _run_step(cross_validate_main, "cross-validation")
    # 6. Build the permutation‑null distribution.
    _run_step(null_dist_main, "null distribution")
    # 7. Apply Benjamini‑Hochberg FDR correction.
    _run_step(fdr_main, "FDR correction")
    # 8. Perform zero‑density sensitivity analysis.
    _run_step(sensitivity_main, "sensitivity analysis")
    # 9. Produce visualisations.
    _run_step(viz_main, "visualisation")
    # 10. Run the KS uniformity test.
    _run_step(uniformity_main, "KS uniformity test")

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()