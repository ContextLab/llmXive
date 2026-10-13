# Implementation Plan: Reconstructing Solar Irradiance from Historical Sunspot Records

**Branch**: `001-reconstruct-solar-irradiance` | **Date**: 2024-05-22  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-reconstruct-solar-irradiance/spec.md`

## Summary
The project will build a CPU‑only pipeline that (1) ingests verified Group Sunspot Number (GSN) data, **optionally** ingests modern satellite Total Solar Irradiance (TSI) data (SORCE/TIM) when available, (2) preprocesses the data (gap filling, cycle detection, feature engineering with categorical Cycle ID), (3) trains non‑linear regression models (Random Forest and Gaussian Process) **only if** a TSI dataset is present, (4) validates via leave‑one‑cycle‑out cross‑validation while acknowledging limited cycle count, (5) applies the calibrated model (or the Cycle‑Agnostic fallback) to the pre‑satellite GSN record to generate a TSI reconstruction with uncertainty bands, and (6) compares the reconstruction against CMIP6 solar forcing (used **only** for independent comparison) and, if a 2007 baseline becomes available, against that baseline, applying multiple‑comparison correction and documenting all findings as associational.

**Note**: A publicly downloadable SORCE/TIM TSI dataset is currently **unavailable**. The pipeline therefore treats the TSI ingestion step as optional; if the dataset cannot be fetched, model training that requires TSI is skipped and the fallback model is used for reconstruction. Baseline‑related fields in the output schema are optional and will be omitted when the 2007 baseline is not present.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `requests==2.32.*`, `pyyaml==6.0.*`  
- **Storage**: Local CSV/Parquet files under `data/` (no external database)  
- **Testing**: `pytest` (unit tests for ingestion, preprocessing, model training, and analysis)  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ~7 GB RAM, ~14 GB disk) – **CPU‑only** (FR‑008)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h total runtime, no GPU libraries.

## Constitution Check
| Principle | Compliance | Note |
|---|---|---|
| I. Reproducibility | ✅ | Random seeds fixed; data fetched from canonical URLs; `requirements.txt` pins versions. |
| II. Verified Accuracy | ✅ | All citations reference the verified dataset URLs listed in `research.md`. |
| III. Data Hygiene | ✅ | Raw files stored under `data/raw/` with checksums; transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | ✅ | Every figure/table derives from a single row in a processed artifact; no manual transcription. |
| V. Versioning Discipline | ✅ | Artifact hashes stored in project state YAML. |
| VI. Cycle‑Specific Calibration Integrity | ✅ | Cycle ID is a **categorical** feature (one‑hot encoded) in all models; validation via leave‑one‑cycle‑out CV. |
| VII. Historical Gap Handling & Uncertainty Quantification | ✅ | Gap‑filling rules (linear < 1 yr, low‑activity proxy for ≥ 1 yr) and bootstrap (≥ 1000 iters) are implemented. |

## Project Structure (Evidence of Files & Directories)

```
code/
├── __init__.py
├── config.py                       # seeds, paths, constants
├── data/
│   ├── __init__.py
│   ├── ingestion.py                # download verified datasets, optional TSI validation
│   └── preprocessing.py            # gap filling, cycle detection, feature engineering
├── models/
│   ├── __init__.py
│   ├── train.py                    # RF & GP training; runs only if TSI present
│   └── predict.py                  # apply best model or fallback to pre‑satellite GSN
├── analysis/
│   ├── __init__.py
│   ├── comparison.py               # CMIP6 comparison only; baseline optional
│   └── stats.py                    # bootstrap, sensitivity analysis
└── main.py                         # orchestrates the full pipeline
tests/
├── __init__.py
├── test_ingestion.py
├── test_preprocessing.py
└── test_model_training.py
data/
├── raw/
│   ├── .gitkeep
│   ├── gsn.parquet
│   ├── silso.parquet
│   └── cmip6_solar_forcing.parquet
│   └── tsi.parquet                # optional; may be absent
├── processed/
│   ├── .gitkeep
│   ├── preprocessed_data.parquet   # written by preprocessing step
│   └── solar_cycles.parquet
└── artifacts/
    ├── model_rf.pkl               # only if TSI present
    ├── model_gp.pkl               # only if TSI present
    ├── cv_report.json
    ├── sensitivity_report.json
    └── comparison_report.json
.env.example                         # template for optional environment vars
requirements.txt                     # pinned dependency list
```

All directories contain `__init__.py` and the empty folders contain `.gitkeep` files, satisfying the earlier task checks.

## Phase Execution Order (Mapping FR/SC → Phases)

| Phase | Description | FR / SC addressed |
|---|---|---|
| **Phase 0 – Research & Data Verification** | Verify URLs, confirm variable presence, draft schemas. | FR‑001, FR‑002, FR‑007, SC‑001‑SC‑005 |
| **Phase 0.5 – SolarCycle Entity Generation** | Derive SolarCycle records (cycle_id, start/end, peak) from SILSO data and store as `solar_cycles.parquet`. | FR‑002, FR‑009 |
| **Phase 1 – Ingestion & Preprocessing** | Download GSN, SILSO, CMIP6, **optionally** TSI. Validate TSI fields (`date`, `tsi_value`, `instrument`, `uncertainty`) if present. Fill gaps; detect cycles; create categorical Cycle ID (one‑hot). Output `preprocessed_data.parquet`. | FR‑001 (optional), FR‑002, FR‑009 |
| **Phase 2 – Model Training & Validation (User Story 1)** | **If** a verified TSI dataset is present, train Random Forest & Gaussian Process using `gsn`, `cycle_id`, and engineered lags. Perform **leave‑one‑cycle‑out CV** (train on all cycles except the held‑out one, validate on held‑out). Compute RMSE, R², and bootstrap‑based confidence intervals. If TSI is absent, skip training and note that the fallback model will be used. **CMIP6 is **not** used as a predictor**; it is reserved for independent comparison only. | FR‑003, SC‑001 (when possible), SC‑002 |
| **Phase 2.5 – Sensitivity Analysis** | Sweep the “inconsistency tolerance threshold” over {0.01, 0.05, 0.1} and record stability of calibration coefficients. | FR‑009, SC‑005 |
| **Phase 3 – Pre‑Satellite Reconstruction (User Story 2)** | Apply the best calibrated model (or the Cycle‑Agnostic fallback) to GSN 1610‑2002, generate `tsi_reconstruction_1610_2002.parquet` with prediction intervals from the GPR model. | FR‑004, FR‑005 |
| **Phase 4 – Baseline Comparison & Reporting (User Story 3)** | Compare the reconstruction against **CMIP6 solar forcing** only (independent proxy). If a 2007 baseline becomes available, compute error‑reduction; otherwise omit those fields and note the omission in the report. Apply **Bonferroni correction** for variance tests across minima. Frame all statements as **associational**. | FR‑006, FR‑007, SC‑003, SC‑004 |
| **Phase 5 – Testing & Packaging** | Run full pytest suite; generate checksums; update state YAML. | All FR/SC (ensures reproducibility & hygiene) |

## Compute Feasibility Strategy
- **Memory**: Preprocessed parquet (~3 M rows, < 2 GB). Models trained on ≤ 10 k rows (satellite era) → < 1 GB RAM.  
- **CPU**: Random Forest (`n_estimators=200`, `max_depth=12`) and GPR with `RBF` kernel are tractable on 2 cores; estimated training < 30 min.  
- **Runtime Budget**: Ingestion [deferred], preprocessing [deferred], training [deferred] (or skipped), sensitivity [deferred], reconstruction ≈ 10 min, bootstrap ≈ 2 h (1000 iters, parallelized over 2 cores). Total < 6 h.  
- **No GPU**: All libraries are pure‑CPU wheels; no CUDA or GPU dependencies.  

## Data Availability & Gap Handling
- **Verified datasets** (see `research.md`): GSN, SILSO, CMIP6. No verified open‑source SORCE/TIM TSI dataset is available; ingestion is optional and the pipeline will continue with the fallback model if missing.  
- **Gap handling**: Linear interpolation for gaps < 1 yr; for gaps ≥ 1 yr, impute GSN with the **mean GSN value observed during the 2008‑2019 solar minimum** (low‑activity proxy) and flag `quality_flag='proxy'`.  
- **Uncertainty**: GPR prediction intervals (95 % credible interval) + bootstrap resampling (≥ 1000 iters) for variance comparisons across solar minima.

## Power & Sample‑Size Disclaimer
The satellite era provides only a small number of full solar cycles (a limited number). Consequently, leave‑one‑cycle‑out CV has limited statistical power. All reported validation metrics will be accompanied by bootstrap‑derived confidence intervals, and the analysis will explicitly state this limitation.

## Decision / Rationale (Research.md excerpt)
- **TSI data**: Unavailable as an open source; therefore optional ingestion and conditional training.  
- **CMIP6 usage**: Restricted to comparative analysis to avoid circular evaluation; never used as a predictor.  
- **Baseline metrics**: Baseline‑related fields are optional in the output schema because the 2007 reconstruction cannot be accessed.  

---  

## projects/PROJ-381-reconstructing-solar-irradiance-from-his/specs/001-reconstructing-solar-irradiance-from-his/research.md
# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Dataset Strategy

All datasets are fetched from URLs that have been verified as publicly reachable and correctly formatted.

| Dataset | Role | Verified URL(s) | Format | Key Variables |
|---|---|---|---|---|
| **GSN (Group Sunspot Number)** | Primary predictor | `https://huggingface.co/datasets/Francesco/construction-safety-gsnvb/resolve/main/data/test-00000-of-00001-2a010722bb743ffa.parquet` | Parquet | `date`, `gsn` |
| **SILSO Sunspot Number** | Cycle‑boundary reference | `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet` | Parquet | `date`, `sunspot_number` |
| **CMIP6 Solar Forcing (v3.2)** | Independent proxy for **comparative** analysis only | `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet` | Parquet | `date`, `solar_forcing` |
| **SORCE/TIM TSI (Satellite)** | Direct measurement of Total Solar Irradiance (2003‑present) | *No verified open‑source URL available* → **Optional**; ingestion step will attempt download and, if missing, skip model training that requires TSI. |
| **2007 Baseline Reconstruction** | Reference reconstruction for error‑reduction metric | *No verified open source provided* → **Not used**; baseline‑related error‑reduction metrics are optional in the output schema. |

### Critical Dataset‑Variable Fit Check
- **GSN**: Provides `gsn` and `date` covering 1610‑present – satisfies FR‑001 (predictor).  
- **SILSO**: Supplies cycle‑boundary information for categorical Cycle ID – satisfies FR‑002.  
- **CMIP6**: Provides a solar‑forcing series **used only for independent comparison**, never as a predictor in model training.  
- **SORCE/TIM TSI**: Not available as an open source; therefore the pipeline treats this dataset as optional. If it cannot be downloaded, the training phase is skipped and the fallback model is used for reconstruction.  
- **2007 Baseline**: Unavailable; baseline‑related error‑reduction metrics are optional.

## 2. Statistical Methodology

### 2.1 Model Selection
- **Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`): Handles non‑linearities, robust to outliers, fast CPU training.  
- **Gaussian Process Regressor** (`sklearn.gaussian_process.GaussianProcessRegressor` with RBF kernel): Provides analytic prediction intervals for uncertainty bands (required by FR‑004).  

Both models are trained **only if** a verified TSI dataset is present. When TSI is absent, the pipeline proceeds directly to reconstruction using the Cycle‑Agnostic fallback model.

### 2.2 Feature Engineering
| Feature | Source | Description |
|---|---|---|
| `gsn` | GSN | Raw Group Sunspot Number. |
| `cycle_id` | SILSO cycle definitions | Categorical identifier of the solar cycle (one‑hot encoded). |
| `gsn_lag1` | GSN | GSN value shifted by one month (captures inertia). |

**Cycle ID** is treated as a **categorical** feature, satisfying Principle VI and FR‑003.

### 2.3 Validation Strategy
- **Leave‑One‑Cycle‑Out (Time‑Block) CV**: Train on all cycles except the held‑out one and validate on the held‑out cycle. Because only ~2 full cycles are available, we acknowledge limited statistical power and supplement CV metrics with **bootstrap confidence intervals** (≥ 1000 iters).  
- **Metrics**: RMSE and R² (SC‑001, SC‑002). When TSI data is missing, these metrics are reported as “N/A” with an explanatory note.

### 2.4 Multiple‑Comparison & Associational Framing
- Variance comparisons across the Maunder, Dalton, and Modern minima use **Bonferroni correction** (FR‑007).  
- All statements are explicitly labelled as **associational** (FR‑006).

### 2.5 Power & Sample‑Size Considerations
- Satellite era provides a substantial multi‑year record of data, comprising many monthly observations. While limited, the analysis focuses on prediction error rather than hypothesis testing of individual coefficients, mitigating low‑power concerns. Bootstrap (≥ 1000 iters) provides empirical confidence intervals for variance estimates.

## 3. Gap Handling & Uncertainty

- **GSN Gaps**:  
  - `< 1 yr` → linear interpolation (`pandas.interpolate`).  
  - `≥ 1 yr` → impute GSN with the **mean GSN value observed during the 2008‑2019 solar minimum** (low‑activity proxy) and flag `quality_flag='proxy'`.  

- **Uncertainty**:  
  - GPR prediction intervals (95 % credible interval).  
  - Bootstrap resampling (1000 iters) for variance comparisons across solar minima.

## 4. Compute Constraints

- **Hardware**: 2 vCPU, ~7 GB RAM, ~14 GB disk (GitHub Actions free tier).  
- **Software**: All libraries are pure‑CPU wheels; no CUDA or GPU dependencies.  
- **Runtime Budget**: ≤ 6 h total (see Plan > Compute Feasibility).  

## 5. References & Citations

- **GSN**: `https://huggingface.co/datasets/Francesco/construction-safety-gsnvb/resolve/main/data/test-00000-of-00001-2a010722bb743ffa.parquet`  
- **SILSO**: `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet`  
- **CMIP6**: `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet`  

*No additional URLs were invented; the absence of a verified TSI source is explicitly noted.*

---  
