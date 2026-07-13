"""
generate_full_metrics.py
-------------------------

This script merges the individual network metric columns (produced by the
earlier analysis steps) with the PCA factor scores and writes the combined
DataFrame to ``data/analysis/full_metrics.csv``.

The implementation relies on the public functions already defined in
``code/analysis/correlations.py``:

* ``load_metrics_data`` – loads the raw metric DataFrame.
* ``run_pca_analysis`` – loads the PCA factor scores DataFrame.
* ``merge_metrics_and_pca_scores`` – merges the two tables on the subject
  identifier.

The script is deliberately lightweight and does **not** generate any
synthetic data; it works on the real outputs produced by the preceding
pipeline stages.
"""

import logging
from pathlib import Path

import pandas as pd

# Import the public helpers from the existing correlations module.
# These functions are guaranteed to exist according to the project API
# surface description.
from analysis.correlations import (
    load_metrics_data,
    run_pca_analysis,
    merge_metrics_and_pca_scores,
)

__all__ = ["merge_and_save_full_metrics", "main"]

# Configure a simple logger for this script.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def merge_and_save_full_metrics(
    output_path: Path = Path("data/analysis/full_metrics.csv"),
) -> pd.DataFrame:
    """
    Load the raw metric table and the PCA factor‑score table, merge them,
    and persist the result.

    Parameters
    ----------
    output_path : pathlib.Path, optional
        Destination CSV file.  The parent directory is created if it does
        not already exist.

    Returns
    -------
    pandas.DataFrame
        The merged DataFrame that was written to ``output_path``.
    """
    logger.info("Loading raw network metrics...")
    metrics_df = load_metrics_data()
    logger.info(f"Raw metrics shape: {metrics_df.shape}")

    logger.info("Loading PCA factor scores...")
    pca_scores_df = run_pca_analysis()
    logger.info(f"PCA scores shape: {pca_scores_df.shape}")

    logger.info("Merging metrics with PCA scores...")
    full_df = merge_metrics_and_pca_scores(metrics_df, pca_scores_df)
    logger.info(f"Merged DataFrame shape: {full_df.shape}")

    # Ensure the output directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving merged DataFrame to {output_path}")
    full_df.to_csv(output_path, index=False)
    logger.info("Full metrics file written successfully.")
    return full_df


def main() -> None:
    """
    Entry point for ``python -m code.analysis.generate_full_metrics``.
    """
    try:
        merge_and_save_full_metrics()
    except Exception as exc:
        logger.exception("Failed to generate full_metrics.csv: %s", exc)
        raise


if __name__ == "__main__":
    main()
