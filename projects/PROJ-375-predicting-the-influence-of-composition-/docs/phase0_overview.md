# Phase 0 Overview: Data Ingestion, Metadata Capture & Power / Coverage Analysis

This document outlines the Phase 0 workflow that prepares the dataset for downstream modeling. The steps are executed in order before any feature engineering or model training and are referenced in the pipeline execution order (see `tasks.md`).

## 1. Data Ingestion

- **Load curated CSV**: Read `data/raw/curated_metallic_glass.csv` which must contain at least `material_id`, `composition`, and `cte`.
- **Materials Project query**: Using `pymatgen.ext.matproj.MPRester` (API key from `MP_API_KEY`), retrieve entries whose `description` contains the word *glass*. Extract `material_id` and `composition`.
- **AFLOWlib query**: Query the public AFLOWlib REST endpoint for additional entries with “glass” in the description. If the endpoint is unreachable, log a warning and continue (no synthetic fallback).
- **De‑duplication**: Merge CSV and API results, de‑duplicate on `material_id`.
- **Amorphous filtering**: Keep rows flagged as amorphous (CSV flag or MP/AFLOW description contains “glass”) and with a non‑missing `cte`.

## 2. Metadata Capture

- **Source method**: Record whether each CTE value originates from *Experimental* measurements or *DFT* calculations.
- **Thermal‑history flag**: Add a boolean `thermal_history_flag` indicating if the original CSV supplies thermal‑history metadata.
- **Row checksum**: Compute a SHA‑256 checksum of the raw JSON record for each row and store it in a new column `checksum`.

## 3. Descriptor Calculation

For each retained entry:

1. Parse `composition` with `pymatgen.Composition`.
2. Using the `mendeleev` package, obtain elemental atomic radius, Pauling electronegativity, and valence‑electron count.
3. Compute the four required compositional descriptors:
 - **Weighted mean atomic radius**
 - **Electronegativity variance (weighted)**
 - **Valence electron concentration (VEC)**
 - **Atomic size coefficient of variation** (σ/μ)

The enriched table is written to `data/processed/clean_alloy_data.parquet`.

## 4. Coverage & Power Analysis

- **Coverage calculation**:
 `coverage = retrieved_entries / csv_entries`
 Write `results/ingestion_coverage.json` containing `{ "coverage": <value>, "total_entries": <value>, "status": "ok" }`.
- **Enforcement**: If `coverage < 0.95` **or** `total_entries < 500`, the script exits with status 1, causing the pipeline to fail (FR‑001).
- **Statistical power**: Using `statsmodels.stats.power.FTestPower`, compute achieved power for detecting an effect size `f² = 0.15` at α = 0.05 with the final sample size. Write a human‑readable report to `results/power_analysis.txt`. If power < 0.8, note the limitation.

## 5. Logging

- All progress, warnings, and errors are logged to `logs/ingestion.log` via the project logger (`get_logger(__name__)`).

## 6. Verification Checks

- **Schema validation**: `data/processed/clean_alloy_data.parquet` must validate against `specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml`.
- **Unit test**: `tests/unit/test_ingestion.py` checks that descriptor columns exist, contain no NaNs, and that the `checksum` matches a recomputed hash.
- **CI checks**: Presence of this markdown file and its headings are verified as part of the CI pipeline. [UNRESOLVED-CLAIM: c_45fa6136 — status=not_enough_info]

---

*This overview is referenced as the first step in the execution order (see `tasks.md`).*