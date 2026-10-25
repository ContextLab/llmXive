"""
generate_base_template.py

Generate a deterministic synthetic base meta‑analysis template.

This script creates a CSV file with exactly 20 rows and the columns:
    study_id, effect, se, n

It is used by task T001 to provide a reproducible base dataset for
downstream simulation steps.  The output path can be overridden via the
``--out`` argument; otherwise it defaults to
``data/processed/base_template.csv`` inside the project.

Usage
-----
python code/scripts/generate_base_template.py --out data/processed/base_template.csv
"""
import argparse
import csv
from pathlib import Path
from typing import List

import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
DEFAULT_OUT = paths.data("processed", "base_template.csv")
DEFAULT_SEED = 42
N_STUDIES = 20
DEFAULT_SAMPLE_SIZE = 30  # Fixed sample size for each study

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _generate_study_data(seed: int) -> List[dict]:
    """Generate deterministic synthetic study‑level data.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    List[dict]
        List of dictionaries with keys ``study_id``, ``effect``,
        ``se`` and ``n``.
    """
    rng = np.random.default_rng(seed)

    # Effect sizes from a standard normal distribution
    effects = rng.normal(loc=0.0, scale=1.0, size=N_STUDIES)

    # Standard errors – ensure positivity; use a half‑normal
    # distribution (abs of normal) with mean ~0.1 and sd ~0.05
    ses_raw = rng.normal(loc=0.1, scale=0.05, size=N_STUDIES)
    ses = np.abs(ses_raw)
    # Avoid zeros (which would break downstream calculations)
    ses[ses == 0] = 1e-6

    studies = []
    for i, (eff, se) in enumerate(zip(effects, ses), start=1):
        studies.append(
            {
                "study_id": f"study_{i}",
                "effect": float(eff),
                "se": float(se),
                "n": DEFAULT_SAMPLE_SIZE,
            }
        )
    return studies

def _write_csv(studies: List[dict], out_path: Path) -> None:
    """Write the list of study dictionaries to a CSV file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["study_id", "effect", "se", "n"]
    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in studies:
            writer.writerow(row)

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic base meta‑analysis template."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility (default: %(default)s).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(DEFAULT_OUT),
        help=(
            "Output CSV path (relative to project root or absolute). "
            f"Defaults to '{DEFAULT_OUT}'."
        ),
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    out_path = Path(args.out)

    # Resolve relative paths against the project root
    if not out_path.is_absolute():
        out_path = paths.root / out_path

    log.info("Generating deterministic synthetic base template with seed %d", args.seed)
    studies = _generate_study_data(args.seed)
    _write_csv(studies, out_path)
    log.info("Wrote %d studies to %s", len(studies), out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())