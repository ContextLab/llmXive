# Implementation Plan: Reconstructing Solar Irradiance from Historical Sunspot Records

**Branch**: `001-reconstruct-solar-irradiance` | **Date**: 2024-05-22  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-reconstruct-solar-irradiance/spec.md`

## Summary

Build a CPU‑only pipeline that (1) ingests the verified Group Sunspot Number (GSN) and SILSO sunspot datasets plus the CMIP v3.2 solar‑forcing parquet, (2) preprocesses the GSN record (gap filling, SILSO‑method cycle detection, categorical Cycle‑ID feature engineering), (3) **conditionally** trains Random Forest and Gaussian Process regressors mapping sunspot numbers to Total Solar Irradiance (TSI) **only if a verified SORCE/TIM TSI dataset is available** — otherwise the training step is skipped and all downstream steps that depend on a trained model are omitted, (4) validates via leave‑one‑cycle‑out CV **and** a dedicated hold‑out split (2016‑present) when TSI data exist, (5) generates a pre‑satellite (1610–2002) TSI reconstruction with uncertainty bands **only if a model was trained**, and (6) compares the reconstruction against CMIP6 solar forcing (comparison only, never a training target) applying Bonferroni correction and associational framing throughout.

**Scope gap (flagged, not silently worked around)**: FR‑014 (verified SORCE/TIM TSI) and FR‑013 (2007 baseline) have no open, verified source. The pipeline therefore logs their absence (`tsi_available = false`, `baseline_available = false`) and skips any step that requires them. A spec revision is required to make these inputs optional or to provide an open source.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.1`, `scipy==1.13.1`, `pyarrow==16.1.0`, `requests==2.32.3`, `python-dotenv==1.0.1`, `pyyaml==6.0.1`, `matplotlib==3.9.0`
- **Storage**: Parquet/CSV files under `data/` (no database)
- **Testing**: `pytest==8.2.2` (unit + contract tests)
- **Target Platform**: GitHub Actions Linux runner, 2 vCPU, ~7 GB RAM, **CPU‑only** (FR‑008)
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h total runtime excluding downloads; no CUDA/bitsandbytes.
- **Project Type**: Data‑analysis pipeline (scripts + library modules)
- **Performance Goals**: Full pipeline ≤ 6 h on 2 cores; bootstrap (1000 iters) ≤ 2 h
- **Scale/Scope**: ~several thousand monthly GSN rows (1610–present); CMIP6 parquet shard; ≤ 10 k training rows if TSI present

## Constitution Check

| Principle | Compliance | Note |
|---|---|---|
| I. Reproducibility | ✅ | Seeds pinned in `code/config.py`; canonical URLs in `code/data/ingestion.py`; `requirements.txt` pins all versions. |
| II. Verified Accuracy | ✅ | Only the three verified URLs (GSN, SILSO, CMIP6) are cited; unrelated URLs are rejected. |
| III. Data Hygiene | ✅ | Raw files under `data/raw/` with SHA‑256 checksums recorded; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | ✅ | All figures/statistics trace to `data/processed/` and `data/artifacts/` files; no hand‑typed numbers. |
| V. Versioning Discipline | ✅ | Artifact hashes recorded in the project state YAML; `updated_at` bumped on change. |
| VI. Cycle‑Specific Calibration Integrity | ✅ | Cycle ID is a one‑hot categorical feature in RF and GP models; **when TSI is present** validation uses leave‑one‑cycle‑out CV **and** a 2016‑present hold‑out split as required by the constitution. If TSI is unavailable, this requirement is deferred (noted in the final report). |
| VII. Historical Gap Handling & Uncertainty | ✅ | Linear interpolation < 1 yr; low‑activity proxy = fixed TSI value 1360.8 W/m² for gaps ≥ 1 yr; uncertainty bands from GPR prediction intervals; bootstrap ≥ 1000 iterations. Cycle detection follows SILSO‑method and aligns to SILSO maxima within ±6 months. |

## Project Structure

```text
code/
├── __init__.py
├── config.py                       # seeds, paths, constants; loads .env
├── data/
│   ├── __init__.py
│   ├── ingestion.py                # download verified datasets, checksums, schema validation
│   └── preprocessing.py            # gap filling, cycle detection, feature engineering; writes preprocessed_data.parquet
├── models/
│   ├── __init__.py
│   ├── train.py                    # RF & GP + leave‑one‑cycle‑out CV (runs only if TSI present)
│   └── predict.py                  # reconstruction 1610‑2002 with uncertainty bands (runs only if model exists)
├── analysis/
│   ├── __init__.py
│   ├── sensitivity.py              # tolerance‑threshold sweep {0.01,0.05,0.1} (runs only if model exists)
│   └── comparison.py               # CMIP6 comparison, bootstrap variance tests, final report
└── main.py                         # orchestrates the full pipeline
tests/
├── __init__.py
├── test_ingestion.py
├── test_preprocessing.py
├── test_model_training.py
└── test_contracts.py               # validates outputs against contracts/*.schema.yaml
data/
├── raw/
│   ├── .gitkeep
│   ├── gsn.parquet
│   ├── silso.parquet
│   ├── cmip6_solar_forcing.parquet
│   └── checksums.json
├── processed/
│   ├── .gitkeep
│   ├── solar_cycles.parquet
│   ├── preprocessed_data.parquet
│   └── tsi_reconstruction_1610_2002.parquet   # created only if a model is trained
└── artifacts/
    ├── cv_report.json
    ├── sensitivity_report.json
    ├── comparison_report.json
    └── figures/
        └── reconstruction.png               # created only if a model is trained
.env.example
requirements.txt
```

**Structure Decision**: Single‑project layout (Option 1): a small analysis library under `code/` with `main.py` as entry point, `tests/` mirroring modules, and `data/` split into raw/processed/artifacts. Every `code/` subpackage and `tests/` contains `__init__.py`; empty data directories contain `.gitkeep` (addresses T001a–T001c).

## Phase Execution Order (FR/SC coverage — all requirements mapped)

| Phase | Description | FR / SC addressed |
|---|---|---|
| **Phase 0 – Scaffolding** | Create directory tree, `__init__.py` files, `.gitkeep` files, `.env.example`, `requirements.txt`, `code/config.py` (seeds, paths, dotenv loading). | FR‑008, SC‑004 (enabling) |
| **Phase 1 – Ingestion** | Download GSN, SILSO, CMIP6 from the three verified URLs; record SHA‑256 checksums; validate each file against `contracts/dataset.schema.yaml`. Attempt optional TSI fetch (no verified URL exists → logged limitation). If TSI were present, apply documented drift‑correction. | FR‑001 (GSN/SILSO part), FR‑010, FR‑013 (schema conformance; flagged unavailable), FR‑014 (attempted; flagged unavailable) |
| **Phase 2 – SolarCycle & preprocessing** | Derive `solar_cycles.parquet` from SILSO records (external definitions, no leakage); fill GSN gaps (linear < 1 yr; low‑activity proxy = **1360.8 W/m²** for gaps ≥ 1 yr, flagged `proxy`); detect cycle boundaries via SILSO‑method 13‑month smoothed peak detection, verified within ±6 months of SILSO maxima; one‑hot Cycle ID; compute `gsn_lag1`; add a fixed facular baseline offset (internal constant, not persisted). Write `preprocessed_data.parquet`. | FR‑002, FR‑012, FR‑003 (features) |
| **Phase 3 – Model training & CV** (conditional) | **If verified TSI is present**: train Random Forest and Gaussian Process with `gsn`, one‑hot `cycle_id`, `gsn_lag1`; perform leave‑one‑cycle‑out CV **and** a dedicated hold‑out validation on 2016‑present data (satisfying Constitution Principle VI); compute RMSE/R² per held‑out cycle + bootstrap CIs; also train a Cycle‑Agnostic fallback (GSN‑only) for unseen cycles. **If TSI is absent**: skip training, log `tsi_available = false`, and set all model‑dependent metrics to `null`. | FR‑003, FR‑004 (model side), SC‑001 (conditional), SC‑002 (conditional) |
| **Phase 4 – Sensitivity analysis** (conditional) | **If models were trained**: sweep inconsistency‑tolerance threshold over {0.01, 0.05, 0.1}; record stability of cycle‑specific calibration coefficients. **If no training**, skip this phase and note the omission in the report. | FR‑009, SC‑005 (conditional) |
| **Phase 5 – Reconstruction** (conditional) | **If a model exists**: apply calibrated model (or Cycle‑Agnostic fallback for unseen cycle IDs) to GSN 1610‑2002; output `tsi_reconstruction_1610_2002.parquet` with [deferred] prediction‑interval bands and generate time‑series figure. **If no model**, reconstruction step is omitted and flagged. | FR‑004, FR‑012 (conditional) |
| **Phase 6 – Comparison & statistics** (conditional) | Perform bootstrap variance comparison across Maunder, Dalton, Modern minima (1000 iterations, Bonferroni‑corrected); compute RMSE/bias vs CMIP6 solar forcing; generate final report with associational framing, multiple‑comparison note, and explicit flags `tsi_available` / `baseline_available`. If TSI or baseline are unavailable, related metrics are set to `null` with explanatory notes. | FR‑005, FR‑006, FR‑007, FR‑011, SC‑001 (CMIP6 part, conditional), SC‑003 (cautionary note) |
| **Phase 7 – Tests & packaging** | Full pytest suite incl. contract tests against the unified schemas; checksum manifest; state‑YAML update. | SC‑004, all FRs (regression) |

Ordering guarantees: data downloaded (Phase 1) before preprocessing (Phase 2) before training (Phase 3) before reconstruction (Phase 5); figures generated (Phase 5) before the report that includes them (Phase 6).

## Compute Feasibility Strategy

- **CPU‑first, no GPU**: all libraries are pure‑CPU wheels; no CUDA/bitsandbytes anywhere (FR‑008). No GPU escape hatch needed.
- **Memory**: monthly GSN (~5 k rows) and one CMIP6 parquet shard fit in < 1 GB; RF (`n_estimators=200`, `max_depth=12`) and GP (RBF kernel, ≤ 10 k rows) < 1 GB.
- **Runtime**: ingestion [deferred], preprocessing [deferred], training (if TSI) ≤ 30 min, sensitivity ≤ 20 min, reconstruction ≤ 5 min, bootstrap 1000 iters ≤ 2 h on 2 cores. Total ≤ 6 h (SC‑004).

## Data Availability & Gap Handling

- **Verified and used**: GSN parquet, SILSO parquet, CMIP6 parquet (URLs in research.md — the only three verified sources whose content matches the project's needs).
- **Rejected verified‑datasets URLs**: the URLs listed under “TSI/SORCE/TIM” in the verified‑datasets block are unrelated datasets (Ethereum transactions, chat logs, Amazon reviews) and are rejected as dataset‑variable‑fit failures. Using them would be a fatal flaw; they are not used.
- **Unavailable (flagged)**: SORCE/TIM TSI (FR‑014) and Wang et al. 2007 baseline (FR‑013/SC‑001). TSI ingestion is attempted and skipped with a logged limitation; baseline metrics are optional and omitted. The spec should be revised if a verified source becomes available.
- **Gap handling**: linear interpolation for gaps < 1 yr; for gaps ≥ 1 yr, **fixed low‑activity proxy = 1360.8 W/m²** (average TSI during the 2008‑2019 minimum), flagged `proxy`; Maunder‑Minimum gaps are flagged but not interpolated.

## Power & Statistical‑Rigor Disclaimers

- **Power**: only a few full satellite cycles exist; leave‑one‑cycle‑out CV and the 2016‑present hold‑out have limited power. All metrics carry bootstrap CIs and the limitation is noted in every report.
- **Causal framing**: purely observational data → all findings framed associational (FR‑006).
- **Multiplicity**: Bonferroni correction for the three pairwise variance tests (FR‑007).
- **Collinearity**: Cycle ID and GSN are jointly predictive; no independent‑effect claims beyond modulation (per spec assumption).

## Complexity Tracking

No constitution violations requiring justification. The TSI/baseline unavailability is a spec‑scope gap (flagged above), not a plan‑level complexity addition.
