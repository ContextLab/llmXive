"""Run the correlation pipeline on real input data.

This script orchestrates the pipeline stages up to (and including)
the plain Spearman correlation (no covariate adjustment).  It **does
not** fabricate any data; instead it expects the user‑provided raw
files to be present at the standard locations:

- ``data/raw/ppmi_asv.csv``   or ``data/raw/open_asv.csv``
- ``data/raw/ppmi_clinical.parquet``   or ``data/raw/open_clinical.parquet``

If the files are missing, the ingest validation step will raise a
clear error and the script will exit with a non‑zero status.
"""
from __future__ import annotations

import logging
from pathlib import Path

from llmxive_toolkit import paths

# Pipeline modules
from code.src.pipeline import ingest, preprocess, slopes, correlation
from code.src.pipeline.__main__ import _determine_input_paths

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def main() -> int:
    """Execute the pipeline up to correlation using real data.

    Returns:
        int: Exit code (0 on success, non‑zero on failure).
    """
    # ------------------------------------------------------------------
    # 1) Locate the raw input files (default PPMI names or open‑data
    #    alternatives).  This mirrors the behaviour of the full pipeline.
    # ------------------------------------------------------------------
    asv_path, clinical_path = _determine_input_paths()

    # ------------------------------------------------------------------
    # 2) Validate the inputs.  ingest.main writes a JSON validation
    #    report and copies alternate filenames to the historic defaults.
    # ------------------------------------------------------------------
    validation_report = paths.data("raw", "ingest_validation.json")
    rc = ingest.main(asv_path, clinical_path, validation_report)
    if rc != 0:
        logger.error("Ingest validation failed (rc=%s).", rc)
        return rc

    # ------------------------------------------------------------------
    # 3) Pre‑process the data – produces filtered_samples.parquet and
    #    clr_abundances.parquet under ``data/processed``.
    # ------------------------------------------------------------------
    processed_dir = paths.data("processed")
    preprocess.run_preprocess(
        asv_path,
        clinical_path,
        out_dir=processed_dir,
        max_taxa=100,  # default upper bound; real datasets may be larger.
    )

    # ------------------------------------------------------------------
    # 4) Compute per‑patient slopes for taxa abundances and clinical
    #    outcome.
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
    # 5) Run the plain Spearman correlation (no covariate adjustment).
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