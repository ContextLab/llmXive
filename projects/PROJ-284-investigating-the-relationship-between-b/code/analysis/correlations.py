"""Implementation of full metrics generation and Benjamini-Hochberg FDR correction for US2.

This module merges the outputs of the PCA step (``pca_loadings.csv`` and
``factor_scores.csv``) with the aggregated network metrics (``aggregated_metrics.csv``)
to produce ``full_metrics.csv`` and then applies FDR correction to the
correlation results (``correlation_results.csv``), writing ``fdr_corrected_results.csv``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
from statsmodels.stats.multitest import multipletests

# Re‑use the PCA pipeline implementation that already writes the PCA
# artefacts.  Importing it here keeps the dependency graph simple and
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
    logger.log("reading_csv", path=str(path))
    return pd.read_csv(path)

def _write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.log("wrote_csv", path=str(path), rows=len(df))

# ----------------------------------------------------------------------
# Core functionality – full metrics generation
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
    logger.log("generate_full_metrics_start", analysis_dir=str(analysis_dir))

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

    # The specification requires the following column order.
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

    logger.log("generate_full_metrics_complete", output_path=str(output_path))
    return output_path

# ----------------------------------------------------------------------
# Benjamini-Hochberg FDR correction
# ----------------------------------------------------------------------
def apply_fdr_correction(
    analysis_dir: Path = Path("data/analysis"),
    pvalue_column: str = "p",
    qvalue_column: str = "q",
    significance_column: str = "significant",
    alpha: float = 0.05,
) -> Path:
    """
    Apply Benjamini‑Hochberg FDR correction to the set of p‑values produced
    by the correlation step and write a CSV that includes corrected q‑values
    and a boolean ``significant`` flag.

    The function expects a CSV named ``correlation_results.csv`` (produced by
    task T024) in ``analysis_dir`` with at least the columns ``metric_name``
    and the p‑value column (default ``p``).  It writes
    ``fdr_corrected_results.csv`` to the same directory.

    Parameters
    ----------
    analysis_dir : Path
        Directory containing ``correlation_results.csv`` and where the
        corrected file will be written.
    pvalue_column : str, optional
        Name of the column containing raw p‑values. Default ``"p"``.
    qvalue_column : str, optional
        Name of the column to store the corrected q‑values. Default ``"q"``.
    significance_column : str, optional
        Name of the Boolean column indicating significance after correction.
        Default ``"significant"``.
    alpha : float, optional
        FDR threshold. Default ``0.05``.

    Returns
    -------
    Path
        Path to the written ``fdr_corrected_results.csv`` file.
    """
    logger.log("apply_fdr_correction_start", analysis_dir=str(analysis_dir))

    corr_path = analysis_dir / "correlation_results.csv"
    if not corr_path.is_file():
        raise FileNotFoundError(f"Correlation results file not found: {corr_path}")

    df = _read_csv(corr_path)

    if pvalue_column not in df.columns:
        raise KeyError(f"Column '{pvalue_column}' not found in correlation results.")

    # Perform Benjamini‑Hochberg correction
    pvals = df[pvalue_column].values
    _, qvals, _, _ = multipletests(pvals, alpha=alpha, method="fdr_bh")
    df[qvalue_column] = qvals
    df[significance_column] = df[qvalue_column] < alpha

    # Preserve original column order, appending the new ones at the end.
    output_path = analysis_dir / "fdr_corrected_results.csv"
    _write_csv(df, output_path)

    logger.log(
        "apply_fdr_correction_complete",
        output_path=str(output_path),
        total_tests=int(len(pvals)),
        significant=int(df[significance_column].sum()),
    )
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
        description=(
            "Create ``full_metrics.csv`` by merging aggregated network metrics "
            "with PCA factor scores and apply Benjamini‑Hochberg FDR correction "
            "to correlation results."
        )
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
        apply_fdr_correction(analysis_dir=analysis_dir)
    except Exception as exc:
        logger.log("full_metrics_or_fdr_failed", error=str(exc))
        raise

if __name__ == "__main__":
    # When the module is executed directly, run the main entry point.
    main()