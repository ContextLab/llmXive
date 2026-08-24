"""Implementation of full metrics generation for US2.

This module merges the outputs of the PCA step (``pca_loadings.csv`` and
``factor_scores.csv``) with the aggregated network metrics (``aggregated_metrics.csv``)
to produce ``full_metrics.csv`` with the schema required by the specification:

``subject_id, modularity, global_efficiency, pc_mean, wmd_mean,
pca_factor_1, pca_factor_2``

The module re‑uses the existing PCA utilities defined in
``code/analysis/pca_utils.py`` so that the earlier task *T023a* (PCA
computation) remains the single source of truth for those outputs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

# Re‑use the PCA pipeline implementation that already writes the PCA
# artifacts.  Importing it here keeps the dependency graph simple and
# guarantees that the PCA step is executed before we attempt to merge the
# results.
from .pca_utils import run_pca_pipeline

# ----------------------------------------------------------------------
# Logging – the project uses a tolerant reproducibility logger defined in
# ``code/logging_config.py``.  ``get_logger`` returns a singleton that
# works with any call signature.
# ----------------------------------------------------------------------
from code.logging_config import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file and raise a clear error if the file is missing."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    logger.info("reading_csv", path=str(path))
    return pd.read_csv(path)

def _write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("wrote_csv", path=str(path), rows=len(df))

# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def generate_full_metrics(
    analysis_dir: Path = Path("data/analysis")
) -> Path:
    """
    Generate ``full_metrics.csv`` by merging the aggregated network metrics
    with the PCA factor scores.

    Parameters
    ----------
    analysis_dir :
        Directory containing the intermediate CSV artefacts produced by
        previous tasks (default: ``data/analysis``).

    Returns
    -------
    Path
        Path to the written ``full_metrics.csv`` file.
    """
    logger.info("generate_full_metrics_start", analysis_dir=str(analysis_dir))

    # Expected input file names
    aggregated_path = analysis_dir / "aggregated_metrics.csv"
    factor_scores_path = analysis_dir / "factor_scores.csv"

    # Ensure the required inputs exist; if not, run the PCA pipeline which
    # will also generate ``factor_scores.csv``.
    if not aggregated_path.is_file():
        raise FileNotFoundError(
            f"Aggregated metrics file missing: {aggregated_path}"
        )

    # ``run_pca_pipeline`` reads ``aggregated_metrics.csv`` and writes the
    # PCA artefacts.  It is safe to call it even if the artefacts already
    # exist – the function overwrites them with the same deterministic
    # results.
    run_pca_pipeline(analysis_dir=analysis_dir)

    # Load the required data frames
    aggregated_df = _read_csv(aggregated_path)
    factor_scores_df = _read_csv(factor_scores_path)

    # Verify that both data frames contain a ``subject_id`` column.
    for df, name in [(aggregated_df, "aggregated_metrics"), (factor_scores_df, "factor_scores")]:
        if "subject_id" not in df.columns:
            raise KeyError(
                f"'{name}.csv' must contain a 'subject_id' column; columns found: {list(df.columns)}"
            )

    # Merge on ``subject_id`` – a left join preserves all subjects that have
    # network metrics (the PCA step always produces a factor row for each of
    # those subjects).
    full_df = pd.merge(
        aggregated_df,
        factor_scores_df,
        on="subject_id",
        how="left",
        validate="one_to_one",
    )

    # The specification requires the following column order.  If any column
    # is missing we raise an informative error so the pipeline fails loudly
    # rather than producing a malformed file.
    required_columns = [
        "subject_id",
        "modularity",
        "global_efficiency",
        "pc_mean",
        "wmd_mean",
        "pca_factor_1",
        "pca_factor_2",
    ]

    missing = [col for col in required_columns if col not in full_df.columns]
    if missing:
        raise KeyError(
            f"The following required columns are missing after merge: {missing}"
        )

    # Re‑order columns exactly as required.
    full_df = full_df[required_columns]

    # Write the final CSV.
    output_path = analysis_dir / "full_metrics.csv"
    _write_csv(full_df, output_path)

    logger.info("generate_full_metrics_complete", output_path=str(output_path))
    return output_path

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def _parse_cli() -> Tuple[Path]:
    """Parse a minimal CLI – the script can be called with an optional
    ``--analysis-dir`` argument.  Using ``argparse`` keeps the interface
    consistent with the rest of the project."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create full_metrics.csv by merging aggregated network metrics "
        "with PCA factor scores."
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("data/analysis"),
        help="Directory containing the intermediate CSV artefacts (default: data/analysis).",
    )
    args = parser.parse_args()
    return (args.analysis_dir,)

def main() -> None:
    """Entry point used by the run‑book and by the higher‑level pipeline."""
    analysis_dir, = _parse_cli()
    try:
        generate_full_metrics(analysis_dir=analysis_dir)
    except Exception as exc:
        logger.error("full_metrics_generation_failed", error=str(exc))
        raise

if __name__ == "__main__":
    # When the module is executed directly, run the main entry point.
    main()