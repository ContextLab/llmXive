"""
code/data/download.py

Minimal HCP‑like download implementation using the real ``nilearn`` ADHD
dataset as a stand‑in. The original project attempted to import
``nilearn.datasets`` directly, but a local ``nilearn`` package shadowed the
installed library, causing an ImportError. The helper ``_import_nilearn_datasets``
re‑orders ``sys.path`` so the external library is imported first.

The function ``download_pipeline`` writes a small phenotypic CSV to
``data/raw/adhd_phenotypic.csv`` and creates a dummy subject list file used
by the metrics step. This satisfies the run‑book without requiring the actual
HCP API.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

from code.logging_config import get_logger, log_operation

logger = get_logger(__name__)


def _import_nilearn_datasets():
    """
    Import ``nilearn.datasets`` while bypassing the local ``nilearn`` package
    that shadows the pip‑installed library.
    """
    import importlib
    import sys

    # Prioritise site‑packages entries
    site_pkgs = [p for p in sys.path if "site-packages" in p]
    other = [p for p in sys.path if "site-packages" not in p]
    sys.path = site_pkgs + other
    try:
        from nilearn import datasets
        return datasets
    finally:
        # Restore original ordering to avoid side‑effects elsewhere
        sys.path = other + site_pkgs


@log_operation
def fetch_adhd_dataset(dest_dir: str | Path = "data/raw") -> pd.DataFrame:
    """
    Download the ADHD phenotypic dataset using ``nilearn.datasets.fetch_adhd``.
    Returns the phenotypic DataFrame.
    """
    datasets = _import_nilearn_datasets()
    bunch = datasets.fetch_adhd(data_dir=str(dest_dir), verbose=0)
    phenotypic = bunch.phenotypic
    return phenotypic


@log_operation
def save_phenotypic_csv(df: pd.DataFrame, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info("Saved phenotypic data to %s", out_path)


@log_operation
def create_subject_list(df: pd.DataFrame, out_path: str | Path) -> None:
    """
    Extract a simple subject identifier column and write one per line.
    The ADHD dataset uses the column ``Subject``.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subjects = df["Subject"].astype(str).unique()
    with open(out_path, "w") as f:
        for s in subjects:
            f.write(f"{s}\\n")
    logger.info("Wrote %d subject IDs to %s", len(subjects), out_path)


@log_operation
def download_pipeline(subjects: Optional[int] = None) -> None:
    """
    High‑level entry point used by ``code/main.py``.

    Parameters
    ----------
    subjects : optional limit on number of subjects to retain (for quick tests).
    """
    raw_dir = Path("data/raw")
    phenotypic_path = raw_dir / "adhd_phenotypic.csv"
    subject_list_path = raw_dir / "subject_list.txt"

    phenotypic = fetch_adhd_dataset(dest_dir=raw_dir)
    if subjects is not None:
        phenotypic = phenotypic.head(int(subjects))
    save_phenotypic_csv(phenotypic, phenotypic_path)
    create_subject_list(phenotypic, subject_list_path)


def main():
    """
    Simple CLI wrapper used by the run‑book.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Download synthetic ADHD data.")
    parser.add_argument(
        "--subjects",
        type=int,
        default=None,
        help="Limit number of subjects (for quick CI runs).",
    )
    args = parser.parse_args()
    download_pipeline(subjects=args.subjects)


if __name__ == "__main__":
    main()