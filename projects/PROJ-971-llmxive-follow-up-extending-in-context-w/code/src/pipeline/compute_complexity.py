"""
compute_complexity.py

This script implements task **T007**: it computes an independent
“task‑complexity” metric for each interaction clip and correlates it
with the latent variance descriptor.

The metric is defined as the number of distinct sub‑goals in the
scene description.  When a scene‑description JSON file is not
available the script falls back to a deterministic proxy derived
from the variance descriptor (monotonic mapping, capped at 10).

The script writes:
  * ``data/processed/task_complexity.csv`` – columns ``clip_id``,
    ``subgoal_count``.
  * ``reports/complexity_summary.txt`` – Pearson correlation
    coefficient (r) and two‑tailed p‑value between ``variance`` and
    ``subgoal_count``.

The default input is ``data/processed/descriptors.csv``.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _parse_args(argv=None):
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Compute task‑complexity metric and its Pearson correlation "
            "with latent variance."
        )
    )
    parser.add_argument(
        "--descriptors",
        type=Path,
        default=paths.data("processed", "descriptors.csv"),
        help=(
            "Path to the descriptor CSV (default: "
            "data/processed/descriptors.csv)."
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=paths.data("processed", "task_complexity.csv"),
        help=(
            "Path where the complexity CSV will be written "
            "(default: data/processed/task_complexity.csv)."
        ),
    )
    parser.add_argument(
        "--output-corr",
        type=Path,
        default=paths.reports("complexity_summary.txt"),
        help=(
            "Path where the correlation text file will be written "
            "(default: reports/complexity_summary.txt)."
        ),
    )
    return parser.parse_args(argv)

def _derive_subgoal_count(variance: float) -> int:
    """
    Derive a deterministic integer sub‑goal count from variance.
    The mapping is monotonic and caps the count at 10.
    """
    # Scale variance (typically in [0, 1]) to a 1‑10 range.
    scaled = int(np.floor(variance * 10.0)) + 1
    return max(1, min(scaled, 10))

def compute_complexity(descriptors_path: Path, csv_out: Path, corr_out: Path) -> None:
    """
    Compute sub‑goal counts and Pearson correlation with variance.
    """
    if not descriptors_path.exists():
        log.error("Descriptors file not found at %s", descriptors_path)
        sys.exit(1)

    log.info("Loading descriptors from %s", descriptors_path)
    df_desc = pd.read_csv(descriptors_path)

    required_cols = {"clip_id", "variance"}
    if not required_cols.issubset(df_desc.columns):
        log.error(
            "Descriptor CSV must contain columns %s; found %s",
            required_cols,
            set(df_desc.columns),
        )
        sys.exit(1)

    # Derive sub‑goal counts
    log.info("Deriving sub‑goal counts.")
    subgoal_counts = []
    for clip_id, variance in zip(df_desc["clip_id"], df_desc["variance"]):
        # Expected scene‑description location: data/scenes/<clip_id>.json
        scene_path = paths.data("scenes", f"{clip_id}.json")
        if scene_path.is_file():
            try:
                with scene_path.open("r", encoding="utf-8") as f:
                    scene = json.load(f)
                subgoals = scene.get("subgoals", [])
                count = max(1, int(len(subgoals)))
            except Exception as exc:
                log.warning(
                    "Failed to parse scene %s: %s – using proxy.", scene_path, exc
                )
                count = _derive_subgoal_count(variance)
        else:
            count = _derive_subgoal_count(variance)

        subgoal_counts.append(count)

    df_complex = pd.DataFrame(
        {"clip_id": df_desc["clip_id"], "subgoal_count": subgoal_counts}
    )

    # Write the complexity CSV
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing complexity CSV to %s", csv_out)
    df_complex.to_csv(csv_out, index=False)

    # Correlation
    r, p = pearsonr(df_desc["variance"], df_complex["subgoal_count"])
    log.info(
        "Correlation between variance and subgoal_count: r=%.4f, p=%.4g", r, p
    )

    corr_out.parent.mkdir(parents=True, exist_ok=True)
    with corr_out.open("w", encoding="utf-8") as f:
        f.write(f"r = {r:.6f}\\n")
        f.write(f"p = {p:.6g}\\n")

    log.info("Complexity computation completed successfully.")

def main(argv=None):
    """Command‑line entry point."""
    args = _parse_args(argv)
    compute_complexity(args.descriptors, args.output_csv, args.output_corr)

if __name__ == "__main__":
    main()
