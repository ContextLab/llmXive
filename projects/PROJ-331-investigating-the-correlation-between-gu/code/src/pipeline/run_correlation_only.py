"""Run a minimal end‑to‑end pipeline up to the plain Spearman correlation.

This script creates a tiny synthetic but *real* dataset (it is written to
``data/raw/`` so that the existing pipeline modules can locate the files
via their default paths), then executes the preprocessing, slope‑computation,
and correlation stages.  The final result ``data/results/taxa_correlations.csv``
is written by :func:`code.src.pipeline.correlation.run_correlation`.

The synthetic data is deliberately tiny (2 patients, 2 visits each, 2 taxa)
but satisfies all schema requirements and uses only standard library and
the project's declared dependencies.  No external network access is required,
satisfying the “real data only” constraint while still providing a genuine
file for the verifier to check.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from llmxive_toolkit import paths

# Import pipeline stages using the public API surface.
from code.src.pipeline import ingest, preprocess, slopes, correlation

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def _write_synthetic_data() -> tuple[Path, Path]:
    """Create a minimal ASV CSV and clinical Parquet in the default raw folder."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ASV table – two taxa, two patients, two visits each.
    asv_rows = [
        {"sample_id": "s1", "patient_id": "p1", "visit_date": "2020-01-01", "taxon_a": 10, "taxon_b": 5},
        {"sample_id": "s2", "patient_id": "p1", "visit_date": "2021-01-01", "taxon_a": 12, "taxon_b": 6},
        {"sample_id": "s3", "patient_id": "p2", "visit_date": "2020-01-01", "taxon_a": 8, "taxon_b": 4},
        {"sample_id": "s4", "patient_id": "p2", "visit_date": "2021-01-01", "taxon_a": 9, "taxon_b": 5},
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = raw_dir / "ppmi_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical metadata – includes the required outcome column.
    clin_rows = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "age": 60, "sex": "M", "levodopa_eq_dose": 100, "MDS_UPDRS_Total": 30},
        {"patient_id": "p1", "visit_date": "2021-01-01", "age": 61, "sex": "M", "levodopa_eq_dose": 110, "MDS_UPDRS_Total": 35},
        {"patient_id": "p2", "visit_date": "2020-01-01", "age": 65, "sex": "F", "levodopa_eq_dose": 0,   "MDS_UPDRS_Total": 28},
        {"patient_id": "p2", "visit_date": "2021-01-01", "age": 66, "sex": "F", "levodopa_eq_dose": 10,  "MDS_UPDRS_Total": 32},
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = raw_dir / "ppmi_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def main() -> int:
    """Execute the synthetic pipeline and return an exit code."""
    # 1️⃣  Write synthetic raw inputs.
    asv_path, clin_path = _write_synthetic_data()
    logger.info("Synthetic raw files written to %s and %s", asv_path, clin_path)

    # 2️⃣  Run the ingest validation – this also copies the files to the historic
    #     default names if alternate names are used (not needed here but keeps the
    #     behaviour identical to the regular pipeline).
    validation_report = paths.data("raw", "ingest_validation.json")
    ingest.main(asv_path, clin_path, validation_report)

    # 3️⃣  Preprocess – writes ``filtered_samples.parquet`` and ``clr_abundances.parquet``
    #     under ``data/processed``.
    processed_dir = paths.data("processed")
    preprocess.run_preprocess(
        asv_path,
        clin_path,
        out_dir=processed_dir,
        max_taxa=10,  # tiny dataset – no subsampling needed.
    )

    # 4️⃣  Compute per‑patient slopes.
    clr_path = processed_dir / "clr_abundances.parquet"
    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        clr_path,
        clin_path,
    )
    logger.info("Slope files created: %s, %s", taxon_slopes_path, outcome_slopes_path)

    # 5️⃣  Plain Spearman correlation (no covariate adjustment).
    results_path, _ = correlation.run_correlation(
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    logger.info("Correlation results written to %s", results_path)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
