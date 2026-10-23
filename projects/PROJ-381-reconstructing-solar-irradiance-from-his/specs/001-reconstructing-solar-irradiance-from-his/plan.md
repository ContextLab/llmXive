# Implementation Plan: Reconstructing Solar Irradiance from Historical Sunspot Records

**Branch**: `001-reconstruct-solar-irradiance` | **Date**: 2024-05-22  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-reconstruct-solar-irradiance/spec.md`

## Summary
Build a reproducible, CPU‑only pipeline that (1) downloads verified SILSO cycle definitions and the CMIP6 solar‑forcing dataset; (2) preprocesses the SILSO sunspot series (gap handling, cycle detection, Cycle‑ID feature engineering); (3) **conditionally** trains Random Forest and Gaussian Process regressors mapping sunspot numbers to Total Solar Irradiance (TSI) **only if a verified satellite‑era TSI dataset and a Group Sunspot Number (GSN) predictor are available**; (4) validates models with leave‑one‑cycle‑out cross‑validation **and** a dedicated 2016‑present hold‑out split (when possible); (5) reconstructs pre‑satellite TSI (1610‑2002) with uncertainty bands using the calibrated model or a Cycle‑Agnostic fallback; (6) **conditionally** compares the new reconstruction against CMIP6 solar forcing (illustrative benchmark) and, when available, the 2007 baseline, applying Bonferroni correction and explicit associational framing.

**Data Availability Note**: No verified open Group Sunspot Number (GSN) parquet exists, and no open SORCE/TIM TSI dataset is available. The pipeline will therefore log `gsn_available = false` and `tsi_available = false`. All downstream model‑dependent steps are skipped, and related metrics are recorded as `null` with explanatory notes. The final report clearly documents these limitations.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.1`, `scipy==1.13.1`, `pyarrow==16.1.0`, `requests==2.32.3`, `python-dotenv==1.0.1`, `pyyaml==6.0.1`, `matplotlib==3.9.0`  
- **Storage**: Parquet/CSV files under `data/` (no DB)  
- **Testing**: `pytest==8.2.2` (unit + contract tests)  
- **Target Platform**: GitHub Actions Linux runner, 2 vCPU, ~7 GB RAM, **CPU‑only** (no GPU needed)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h total runtime (excluding downloads)  
- **Project Type**: Data‑analysis pipeline (scripts + small library)  

## Constitution Check
| Principle | Compliance | Note |
|---|---|---|
| I. Reproducibility | ✅ | Seeds pinned in `code/config.py`; deterministic data URLs; `requirements.txt` pins versions. |
| II. Verified Accuracy | ❌ | No open‑source GSN dataset can be verified; the pipeline logs its unavailability. |
| III. Data Hygiene | ✅ | Raw files stored under `data/raw/` with SHA‑256 checksums; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | ✅ | All figures/tables trace back to rows in `data/processed/` or `data/artifacts/`; no hand‑typed numbers. |
| V. Versioning Discipline | ✅ | Artifact hashes recorded in project‑state YAML; `updated_at` updated on change. |
| VI. Cycle‑Specific Calibration Integrity | ✅ | Cycle ID is a one‑hot categorical feature; validation uses leave‑one‑cycle‑out CV **and** a 2016‑present hold‑out split when TSI is present. |
| VII. Historical Gap Handling & Uncertainty | ✅ | Linear interpolation for gaps < 1 yr; fixed low‑activity proxy for gaps ≥ 1 yr; uncertainty bands from GP prediction intervals; bootstrap (≥ 1000) for minima variance; SILSO‑method cycle detection aligned within ±6 months. |

## Project Structure
```text
code/
├── __init__.py                # ← created
├── config.py                  # seeds, paths, constants; loads .env
├── data/
│   ├── __init__.py            # ← created
│   ├── ingestion.py           # download, checksum, schema validation
│   └── preprocessing.py       # gap filling, cycle detection, feature engineering
├── models/
│   ├── __init__.py            # ← created
│   ├── train.py               # RF & GP + LOCO CV + hold‑out split (conditional)
│   └── predict.py             # reconstruction 1610‑2002 with uncertainty bands (conditional)
├── analysis/
│   ├── __init__.py            # ← created
│   ├── sensitivity.py         # tolerance‑threshold sweep (conditional)
│   └── comparison.py          # CMIP6 comparison, bootstrap variance tests, final report (conditional)
└── main.py                    # orchestrates the full pipeline
tests/
├── __init__.py                # ← created
├── test_ingestion.py
├── test_preprocessing.py
├── test_model_training.py
└── test_contracts.py          # validates outputs against contracts/*.schema.yaml
data/
├── raw/
│   ├── .gitkeep               # ← created
│   ├── silso.parquet
│   ├── cmip6_solar_forcing.parquet
│   └── checksums.json
├── processed/
│   ├── .gitkeep               # ← created
│   ├── solar_cycles.parquet
│   ├── preprocessed_data.parquet
│   └── tsi_reconstruction_1610_2002.parquet   # only if a model was trained
└── artifacts/
    ├── cv_report.json
    ├── sensitivity_report.json
    ├── comparison_report.json
    └── figures/
        └── reconstruction.png               # only if a model was trained
.env.example
requirements.txt
```
**Structure Decision**: Single‑project layout (Option 1). All code lives under `code/`; tests mirror the package structure; data is split into raw/processed/artifacts.

## Phase Execution Order (FR/SC coverage)

| Phase | Description | FR / SC addressed |
|---|---|---|
| **Phase 0 – Scaffolding** | Create directory tree, add `__init__.py` in every package, place `.gitkeep` in empty data folders, provide `.env.example`, `requirements.txt`, and `code/config.py` (seeds, paths). | SC‑004 |
| **Phase 1 – Ingestion** | Programmatically download SILSO cycle definitions and CMIP6 from the two verified URLs; record SHA‑256 checksums; validate against `contracts/dataset.schema.yaml`. **No GSN download** – the pipeline logs `gsn_available = false`. Attempt to download SORCE/TIM TSI – flagged unavailable (`tsi_available = false`). | FR‑001, FR‑010, FR‑013 (optional), FR‑014 (optional) |
| **Phase 2 – Preprocessing & SolarCycle derivation** | Derive `solar_cycles.parquet` from SILSO definitions; fill SILSO gaps (linear < 1 yr, proxy for ≥ 1 yr); detect cycle boundaries via SILSO‑method (±6 months); create one‑hot `cycle_id`; compute `gsn_lag1` when GSN is present; add low‑sunspot offset constant (FR‑012). Write `preprocessed_data.parquet`. | FR‑002, FR‑003 (feature creation), FR‑012 |
| **Phase 3 – Model training & CV** (conditional) | **If a verified TSI target and GSN predictor exist**: train Random Forest (`n_estimators=200`, `max_depth=12`, seed pinned) and Gaussian Process (RBF kernel) using `gsn`, `gsn_lag1`, and one‑hot `cycle_id`. Perform leave‑one‑cycle‑out CV **and** a 2016‑present hold‑out split (satisfying Principle VI). Compute RMSE/R² per held‑out cycle, bootstrap CIs (covers SC‑001, **SC‑002**). Also train a Cycle‑Agnostic fallback (GSN‑only) when possible. If either dataset is absent, skip training, set model‑dependent metrics to `null` and log the missing data. | FR‑003, FR‑004 (model side), SC‑001, **SC‑002** (conditional) |
| **Phase 4 – Sensitivity analysis** (conditional) | Sweep inconsistency‑tolerance thresholds {0.01, 0.05, 0.1}; record stability of RMSE and model coefficients. Skip if no model. | SC‑005 (conditional) |
| **Phase 5 – Reconstruction** (conditional) | Apply the Cycle‑Specific model to GSN 1610‑2002; for cycles unseen in training use the Cycle‑Agnostic fallback. Output `tsi_reconstruction_1610_2002.parquet` with GP‑derived prediction intervals; generate a time‑series figure. Skip if no model. | FR‑004, FR‑012 (conditional) |
| **Phase 6 – Comparison & Statistics** (conditional) | Bootstrap variance comparison across Maunder, Dalton, Modern minima (1000 iterations, Bonferroni‑corrected). Compute RMSE & bias vs CMIP6 solar forcing (FR‑010, FR‑011). When baseline is present compute % RMSE reduction vs 2007 reconstruction (SC‑001). **Scientific‑soundness note**: CMIP6 solar forcing is model‑derived and shares sunspot‑based assumptions; it is used only as an illustrative benchmark, not as an independent validation. Produce final JSON report with associational framing (FR‑006) and multiple‑comparison note (FR‑007). Missing data → metrics set to `null` with explanatory notes. | FR‑005, FR‑006, FR‑007, FR‑011, SC‑001, SC‑003 |
| **Phase 7 – Tests & Packaging** | Run full pytest suite, including contract validation against `contracts/*.schema.yaml`. Update checksum manifest and project‑state YAML. | SC‑004, all FRs (regression) |

The ordering guarantees that data is downloaded before any consumption, models are trained before inference, and figures are produced before they are referenced in the final report.

## Compute Feasibility Strategy
- **CPU‑first**: All libraries have pure‑CPU wheels; no CUDA or bitsandbytes dependencies.  
- **Memory**: Raw SILSO and CMIP6 are a few thousand rows (< 1 GB). RF & GP models on ≤ 10 k rows stay well under 1 GB.  
- **Runtime**: Ingestion [deferred], preprocessing [deferred], training (if TSI & GSN) ≤ 30 min, sensitivity ≤ 20 min, reconstruction ≤ 5 min, bootstrap ≤ 2 h on 2 cores. Total ≤ 6 h (SC‑004).
- **No GPU‑only methods are used; therefore no GPU escape hatch is required.**

## Data Availability & Gap Handling
- **Verified open datasets**: SILSO sunspot numbers, CMIP6 solar forcing.  
- **Unavailable**: GSN parquet, SORCE/TIM TSI, Wang et al. 2007 baseline. Their absence is logged and all dependent steps are conditionally skipped.  
- **Gap policy**: Linear interpolation for gaps < 1 yr; for gaps ≥ 1 yr a fixed low‑activity proxy TSI = 1360.8 W/m² (average of the 2008‑2019 minimum) is inserted and flagged `proxy`. Maunder‑Minimum gaps are flagged but not interpolated.

## Statistical‑Rigor Disclaimers
- **Power**: Only a few full satellite cycles exist; all metrics include bootstrap confidence intervals and the limitation is noted.  
- **Associational framing**: All statements are explicitly labeled associational (FR‑006).  
- **Multiplicity**: Bonferroni correction applied to the three pairwise variance tests (FR‑007).  
- **Collinearity**: Cycle ID and GSN are jointly predictive; no claim of independent effects is made (Principle VI).

## Complexity Tracking
No constitution violations require justification beyond the flagged data‑source gaps (FR‑014, FR‑013). Those are recorded as scope gaps, not plan‑level complexity additions.

---

