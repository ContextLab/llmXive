"""
analysis/create_full_metrics.py
------------------------------

A thin wrapper that exists for historical reasons – the original pipeline
invoked a separate script to generate ``full_metrics.csv``.  The core
functionality now lives in :pymod:`analysis.correlations`.  This wrapper
simply forwards to that implementation so that any external callers that
still import ``create_full_metrics.main`` continue to work.
"""

import logging
from pathlib import Path

from analysis.correlations import (
    load_metrics_data,
    load_pca_scores,
    merge_metrics_and_pca_scores,
)

def merge_and_save_full_metrics() -> None:
    """
    Load the required inputs, merge them, and persist the combined CSV.
    This function mirrors the behaviour of ``analysis.correlations.main``
    but is kept separate to preserve the original public API.
    """
    logging.basicConfig(level=logging.INFO)
    metrics = load_metrics_data()
    pca_scores = load_pca_scores()
    merge_metrics_and_pca_scores(metrics, pca_scores)

def main() -> None:
    """
    Command‑line entry point used by ``code/main.py`` (if the older
    ``create_full_metrics`` step is still referenced).  It simply calls the
    wrapper defined above.
    """
    logging.info("Running legacy full‑metrics generation script")
    merge_and_save_full_metrics()

if __name__ == "__main__":
    main()