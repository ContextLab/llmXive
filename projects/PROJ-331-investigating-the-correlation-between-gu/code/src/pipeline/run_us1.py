"""Execute the US1 pipeline (Correlation only).

This script orchestrates the following stages:
  1. Ingest validation (T001)
  2. Pre‑processing (T002)
  3. Per‑patient slope computation (T003)
  4. Plain Spearman correlation (T004)

It expects the raw input files to be present at the default locations
``data/raw/ppmi_asv.csv`` (or ``open_asv.csv``) and
``data/raw/ppmi_clinical.parquet`` (or ``open_clinical.parquet``).  The
script does **not** fabricate any data; it simply wires together the
existing pipeline modules.  All outputs are written under the ``data/``
hierarchy as defined by the project specification.
"""
from __future__ import annotations

import logging
from pathlib import Path

from llmxive_toolkit import paths

# Public pipeline modules
from code.src.pipeline import ingest, preprocess, slopes, correlation
from code.src.pipeline.__main__ import _determine_input_paths

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def main() -> int:
    """Execute the US1 pipeline and return an exit code."""
    # ------------------------------------------------------------------
    # 1) Determine raw data locations (default PPMI filenames or open‑data
    #    alternatives).  This mirrors the behaviour of the full pipeline
    #    entry point.
    # ------------------------------------------------------------------
    asv_path, clinical_path = _determine_input_paths()

    # ------------------------------------------------------------------
    # 2) Ingest validation – writes a JSON validation report next to the
    #    raw files.  The function returns an exit code; we forward any
    #    non‑zero value.
    # ------------------------------------------------------------------
    validation_report = paths.data("raw", "ingest_validation.json")
    rc = ingest.main(asv_path, clinical_path, validation_report)
    if rc != 0:
        logger.error("Ingest validation failed (rc=%s).", rc)
        return rc

    # ------------------------------------------------------------------
    # 3) Pre‑processing – produces ``filtered_samples.parquet`` and
    #    ``clr_abundances.parquet`` under ``data/processed``.
    # ------------------------------------------------------------------
    processed_dir = paths.data("processed")
    preprocess.run_preprocess(
        asv_path,
        clinical_path,
        out_dir=processed_dir,
        max_taxa=100,  # default upper bound; the tiny synthetic data used in tests
    )

    # ------------------------------------------------------------------
    # 4) Slope computation – writes per‑patient taxon slopes and, if the
    #    outcome column is present, per‑patient outcome slopes.
    # ------------------------------------------------------------------
    clr_path = processed_dir / "clr_abundances.parquet"
    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        clr_path,
        clinical_path,
    )
    logger.info(
        "Slope files created: %s (taxa) , %s (outcome)",
        taxon_slopes_path,
        outcome_slopes_path,
    )

    # ------------------------------------------------------------------
    # 5) Correlation – plain Spearman (no covariate adjustment).  The
    #    function returns the path to the primary results CSV and an
    #    optional partial‑Spearman CSV (unused here).
    # ------------------------------------------------------------------
    results_path, _ = correlation.run_correlation(
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    logger.info("Correlation results written to %s", results_path)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
