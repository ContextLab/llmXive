"""Execute the US1 pipeline (Correlation only) with timing and adjusted results.

This script orchestrates the following stages:
  1. Ingest validation (T001)
  2. Pre‑processing (T002)
  3. Per‑patient slope computation (T003)
  4. Covariate‑adjusted Spearman correlation (T004, partial=True)

It expects the raw input files to be present at the default locations
``data/raw/ppmi_asv.csv`` (or ``open_asv.csv``) and
``data/raw/ppmi_clinical.parquet`` (or ``open_clinical.parquet``).  The
script does **not** fabricate any data; it simply wires together the
existing pipeline modules.  All outputs are written under the project
hierarchy as defined by the specification.

Runtime for each stage is recorded in ``results/runtime_log.txt`` and the
total wall‑clock time is checked against the 6 h budget.
"""
from __future__ import annotations

import logging
import time
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

def _log_stage(log_path: Path, name: str, seconds: float) -> None:
    """Append a stage timing entry to the runtime log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{name}: {seconds:.2f} seconds\n")

def main() -> int:
    """Execute the US1 pipeline and return an exit code."""
    # ------------------------------------------------------------------
    # 1) Determine raw data locations (default PPMI filenames or open‑data
    #    alternatives).  This mirrors the behaviour of the full pipeline
    #    entry point.
    # ------------------------------------------------------------------
    try:
        asv_path, clinical_path = _determine_input_paths()
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 1

    # Prepare runtime log.
    runtime_log = paths.results("runtime_log.txt")
    # Ensure a fresh log.
    if runtime_log.is_file():
        runtime_log.unlink()

    total_start = time.time()

    # ------------------------------------------------------------------
    # 2) Ingest validation – writes a JSON validation report next to the
    #    raw files.  The function returns an exit code; we forward any
    #    non‑zero value.
    # ------------------------------------------------------------------
    ingest_start = time.time()
    validation_report = paths.data("raw", "ingest_validation.json")
    rc = ingest.main(asv_path, clinical_path, validation_report)
    ingest_elapsed = time.time() - ingest_start
    _log_stage(runtime_log, "Ingest", ingest_elapsed)
    if rc != 0:
        logger.error("Ingest validation failed (rc=%s).", rc)
        return rc

    # ------------------------------------------------------------------
    # 3) Pre‑processing – produces ``filtered_samples.parquet`` and
    #    ``clr_abundances.parquet`` under ``data/processed``.
    # ------------------------------------------------------------------
    preprocess_start = time.time()
    processed_dir = paths.data("processed")
    preprocess.run_preprocess(
        asv_path,
        clinical_path,
        out_dir=processed_dir,
        max_taxa=100,  # enforce FR‑010 guard
    )
    _log_stage(runtime_log, "Preprocess", time.time() - preprocess_start)

    # ------------------------------------------------------------------
    # 4) Slope computation – writes per‑patient taxon slopes and outcome
    #    slopes.
    # ------------------------------------------------------------------
    slopes_start = time.time()
    clr_path = processed_dir / "clr_abundances.parquet"
    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        clr_path,
        clinical_path,
    )
    _log_stage(runtime_log, "Slope computation", time.time() - slopes_start)
    logger.info(
        "Slope files created: %s (taxa) , %s (outcome)",
        taxon_slopes_path,
        outcome_slopes_path,
    )

    # ------------------------------------------------------------------
    # 5) Correlation – covariate‑adjusted (partial) Spearman.
    #    The function returns the path to the primary results CSV and the
    #    adjusted results CSV.
    # ------------------------------------------------------------------
    corr_start = time.time()
    results_path, adj_path = correlation.run_correlation(
        partial=True,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    _log_stage(runtime_log, "Correlation (partial)", time.time() - corr_start)
    logger.info("Correlation results written to %s (adjusted: %s)", results_path, adj_path)

    # ------------------------------------------------------------------
    # 6) Final budget check.
    # ------------------------------------------------------------------
    total_elapsed = time.time() - total_start
    # Append total time entry.
    _log_stage(runtime_log, "Total", total_elapsed)
    if total_elapsed > 6 * 60 * 60:
        logger.error(
            "Total pipeline runtime %.2f seconds exceeds the 6‑hour budget.",
            total_elapsed,
        )
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
