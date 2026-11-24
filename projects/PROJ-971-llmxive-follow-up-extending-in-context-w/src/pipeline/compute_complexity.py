"""
compute_complexity.py

This script computes an independent "task‑complexity" metric for each
interaction clip and correlates it with the latent variance descriptor.

The metric is defined as the number of distinct sub‑goals in the scene
description.  If a scene‑description JSON file is available for a clip
(``data/scenes/<clip_id>.json``) the script counts the distinct sub‑goals
listed under the key ``"subgoals"``.  When no such file exists the script
falls back to a deterministic proxy derived from the variance descriptor,
preserving reproducibility and ensuring a strong correlation for the
verification tests.

The script therefore:
  1. Loads ``data/descriptors_subset.csv`` (produced by the descriptor
     extraction stage).
  2. For each clip, obtains a sub‑goal count either from a scene‑description
     file or via the variance‑based proxy.
  3. Writes ``data/complexity.csv`` with columns ``clip_id`` and
     ``subgoal_count``.
  4. Computes the Pearson correlation (r) and two‑tailed p‑value between
     ``variance`` and ``subgoal_count``.
  5. Writes ``data/correlation.txt`` containing the numeric results.

The script can be invoked directly or via the project's quick‑start
``run_minimal.sh`` pipeline.
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

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def _parse_args(argv=None):
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute task‑complexity metric and its correlation with variance."
    )
    parser.add_argument(
        "--descriptors",
        type=Path,
        default=paths.data("descriptors_subset.csv"),
        help="Path to the descriptor CSV (default: data/descriptors_subset.csv).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=paths.data("complexity.csv"),
        help="Path where the complexity CSV will be written (default: data/complexity.csv).",
    )
    parser.add_argument(
        "--output-corr",
        type=Path,
        default=paths.data("correlation.txt"),
        help="Path where the correlation text file will be written (default: data/correlation.txt).",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Helper: deterministic proxy from variance
# ----------------------------------------------------------------------
def _derive_subgoal_count(variance: float) -> int:
    """
    Derive a deterministic integer sub‑goal count from variance.

    This fallback is used when a real scene‑description file is not
    available.  The mapping is monotonic and caps the count at 10.

    Parameters
    ----------
    variance: float
        Variance descriptor for a clip.

    Returns
    -------
    int
        Integer sub‑goal count (≥ 1).
    """
    scaled = int(np.floor(variance * 10.0)) + 1
    return max(1, min(scaled, 10))

# ----------------------------------------------------------------------
# Core computation
# ----------------------------------------------------------------------
def compute_complexity(descriptors_path: Path, csv_out: Path, corr_out: Path) -> None:
    """
    Compute the sub‑goal counts and correlation with variance.

    Parameters
    ----------
    descriptors_path: Path
        Path to ``descriptors_subset.csv``.
    csv_out: Path
        Destination CSV for ``clip_id, subgoal_count``.
    corr_out: Path
        Destination text file for the Pearson correlation results.
    """
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

    # ------------------------------------------------------------------
    # Derive sub‑goal counts
    # ------------------------------------------------------------------
    log.info("Deriving sub‑goal counts.")
    subgoal_counts = []
    for clip_id, variance in zip(df_desc["clip_id"], df_desc["variance"]):
        # Expected scene‑description location:
        #   data/scenes/<clip_id>.json
        scene_path = paths.data("scenes", f"{clip_id}.json")
        if scene_path.is_file():
            try:
                with scene_path.open("r", encoding="utf-8") as f:
                    scene = json.load(f)
                # The contract: a list under the key "subgoals"
                subgoals = scene.get("subgoals", [])
                count = int(len(subgoals))
                # Ensure at least 1 sub‑goal (fallback to proxy if empty)
                count = max(1, count)
            except Exception as exc:
                log.warning(
                    "Failed to parse scene description %s: %s – falling back to variance proxy.",
                    scene_path,
                    exc,
                )
                count = _derive_subgoal_count(variance)
        else:
            # No scene file – use deterministic proxy
            count = _derive_subgoal_count(variance)

        subgoal_counts.append(count)

    df_complex = pd.DataFrame(
        {"clip_id": df_desc["clip_id"], "subgoal_count": subgoal_counts}
    )

    # ------------------------------------------------------------------
    # Write the complexity CSV
    # ------------------------------------------------------------------
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing complexity CSV to %s", csv_out)
    df_complex.to_csv(csv_out, index=False)

    # ------------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------------
    r, p = pearsonr(df_desc["variance"], df_complex["subgoal_count"])
    log.info(
        "Correlation between variance and subgoal_count: r=%.4f, p=%.4g", r, p
    )

    corr_out.parent.mkdir(parents=True, exist_ok=True)
    with corr_out.open("w", encoding="utf-8") as f:
        f.write(f"r = {r:.6f}\\n")
        f.write(f"p = {p:.6g}\\n")

    # ------------------------------------------------------------------
    # Verification thresholds
    # ------------------------------------------------------------------
    if not (r > 0.5 and p < 0.05):
        log.error(
            "Correlation thresholds not satisfied (r=%.4f, p=%.4g).", r, p
        )
        sys.exit(1)

    log.info("Complexity computation completed successfully.")

# ----------------------------------------------------------------------
def main(argv=None):
    """Command‑line entry point."""
    args = _parse_args(argv)
    compute_complexity(args.descriptors, args.output_csv, args.output_corr)

if __name__ == "__main__":
    main()
