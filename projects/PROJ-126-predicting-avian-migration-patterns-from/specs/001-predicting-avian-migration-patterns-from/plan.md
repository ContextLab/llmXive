# Implementation Plan: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-09-08 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-avian-migration/spec.md`

## Summary

This project implements a spatiotemporal data pipeline to predict the "first arrival" date of the American Redstart (*Setophaga ruticilla*) within the **Lake Powell region** (North America) using eBird Basic Dataset (EBD) records and MODIS remote sensing data. The system aggregates observations into discrete grid cells., derives arrival metrics via cumulative count thresholds, and trains a Gradient Boosting Regressor (XGBoost) with lagged environmental predictors (temperature, NDVI). The plan strictly adheres to a CPU-first execution model on GitHub Actions free-tier runners (limited CPU resources, constrained RAM), utilizing streaming for large datasets and scaled-down sampling where necessary to fit within the runtime limit. Statistical rigor is enforced via Diebold-Mariano tests on temporal error aggregates, VIF filtering for collinearity, and explicit performance/stability measurement tasks.

**Scope Note**: The verified MODIS dataset is limited to the Lake Powell region. Consequently, the study scope is explicitly reduced from "continental" to "regional (Lake Powell)" to ensure construct validity. All maps and predictions are confined to this region. **Critical Constraint**: The project relies on a verified EBD subset. If this subset lacks *Setophaga ruticilla* or the 2015-2023 temporal range, the pipeline will fail explicitly (fail-fast) rather than proceeding with incomplete data. No alternative verified source for the full EBD is available in the prompt's verified block; the study is contingent on the subset's adequacy.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `xgboost`, `shap`, `scikit-learn`, `datasets` (HuggingFace), `modis-tools` (or `rasterio` + `requests`), `matplotlib`, `seaborn`, `statsmodels` (for Diebold-Mariano), `pyyaml`.
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/outputs`) with checksums; no external database.
**Testing**: `pytest` (unit tests for data filters, integration tests for pipeline phases).
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).
**Project Type**: Data Science Pipeline / Research Prototype.
**Performance Goals**: Complete pipeline (download → preprocess → train → evaluate) ≤ 6 hours; Peak RAM ≤ 7 GB.
**Constraints**: No GPU on primary runner; must handle data gaps (clouds, missing checklists) without hallucination; strict temporal split (earlier period train, later period val, most recent period test); **Regional Scope (Lake Powell)**; **Fail-fast validation** on dataset content.
**Scale/Scope**: Regional (Lake Powell), 9 years (2015-2023), 0.5° grid resolution.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `config.py`; `requirements.txt` pins versions; data fetches from canonical HuggingFace URLs; pipeline is fully scriptable. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs in `research.md` are restricted to the verified block provided in the prompt. **Scope Reduction**: The plan explicitly limits the study to the Lake Powell region to match the verified MODIS data. **Fail-Fast**: Explicit validation ensures the EBD subset contains the target species and years; if not, the pipeline aborts. |
| **III. Data Hygiene** | **Pass** | Raw data stored in `data/raw` with checksums; derived data in `data/processed` with new filenames; no in-place modifications; PII scan passed (eBird data is aggregated). |
| **IV. Single Source of Truth** | **Pass** | All metrics (RMSE, p-values) written to `data/outputs/metrics.json` and referenced directly in the report generation; no manual entry. |
| **V. Versioning Discipline** | **Pass** | Artifacts tracked via content hashes in `state.yaml`; `plan.md` versioned as 1.0.0. |
| **VI. Citizen Science Data Bias** | **Pass** | Pipeline strictly filters for "complete checklists" (duration ≥ 1 min, observers ≥ 1, distance ≤ 10 km) as per spec; aggregation fixed at a moderate spatial resolution. Effort correction (rarefaction) is noted as a limitation/optional step. |
| **VII. Temporal Integrity** | **Pass** | Feature engineering enforces lagged predictors (several weeks prior); model split strictly temporal (train, val, test); evaluation uses temporal residuals. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-avian-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (YAML schemas used for validation)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-126-predicting-avian-migration-patterns-from/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Paths, seeds, hyperparameters, Lake Powell bbox
│   ├── data_loader.py            # EBD/MODIS download & streaming
│   ├── preprocessing.py          # Grid aggregation, first-arrival derivation, VIF filtering
│   ├── model_training.py         # XGBoost, SHAP, Diebold-Mariano, Permutation
│   └── visualization.py          # Regional maps and plots
├── data/
│   ├── raw/                      # Downloaded CSVs/Parquets (checksummed)
│   ├── processed/                # Aggregated grids, derived features
│   └── outputs/                  # Metrics, SHAP plots, feasibility logs, stability reports
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── run_pipeline.sh
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and maximize compatibility with the GitHub Actions free-tier runner. This aligns with the CPU-first constraint where complex microservices are unnecessary for a batch data pipeline.

**Contract Utilization**: The YAML schemas in `contracts/` are loaded at runtime by `data_loader.py` and `model_training.py` to validate input/output data structures (e.g., `GridCellObservation`, `ModelPerformanceMetric`) before processing or saving, ensuring type safety and schema compliance.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Data Loading** | EBD/MODIS full datasets may exceed 7 GB RAM if loaded entirely. | Loading full CSVs into Pandas DataFrames would cause OOM errors on the GitHub Actions runner. Streaming is required for feasibility. |
| **Temporal Split** | Required to avoid look-ahead bias in phenology prediction. | Random K-Fold splits would leak future migration patterns into the training set, invalidating the scientific hypothesis. |
| **Permutation Importance + SHAP + VIF** | Temperature and NDVI are highly collinear. | Relying solely on XGBoost `feature_importance` (gain) is insufficient as it can be biased by correlated features. VIF filtering removes redundant features before training; SHAP/Permutation provides robust ranking. |
| **Regional Scope (Lake Powell)** | Verified MODIS dataset is limited to Lake Powell. | Attempting a continental analysis with regional data would result in hallucinated predictions for uncovered areas. Scope is reduced to ensure data validity. |
| **Fail-Fast Validation** | Verified EBD subset may lack target species or years. | Proceeding with incomplete data would produce invalid results. The pipeline must abort if the subset is insufficient. |

## FR/SC Coverage Map

| Requirement | Plan Phase | Implementation Detail |
| :--- | :--- | :--- |
| **FR-001** (EBD Download) | Phase 0 | `data_loader.py` streams EBD, filters for complete checklists, validates species/year. **Fails if missing**. |
| **FR-002** (MODIS Resample) | Phase 0 | `data_loader.py` resamples MODIS to 0.5°/weekly, handles cloud gaps via interpolation. |
| **FR-003** (First Arrival) | Phase 1 | `preprocessing.py` calculates arrival for thresholds {3, 5, 10}, excludes low-count cells. |
| **FR-004** (XGBoost Training) | Phase 2 | `model_training.py` trains with temporal split (2015-2020/21/22), lagged features. |
| **FR-005** (SHAP/Permutation) | Phase 2 | `model_training.py` computes SHAP values and Permutation Importance after VIF filtering. |
| **FR-006** (Diebold-Mariano) | Phase 2 | `model_training.py` runs DM test on **temporal aggregates** of errors (not spatial cells). |
| **FR-007** (Maps) | Phase 3 | `visualization.py` generates **regional maps** (Lake Powell) of predicted dates and gradients. |
| **SC-001** (RMSE/Correlation) | Phase 2 | Metrics calculated on temporal residuals, saved to `metrics.json`. |
| **SC-002** (DM Significance) | Phase 2 | DM test p-values recorded in `metrics.json`. |
| **SC-003** (Stability) | Phase 3 | **Stability Analysis Task**: Calculate variation across thresholds, flag if >7 days, save to `stability_report.json`. |
| **SC-004** (Feasibility) | Phase 4 | **Performance Verification Task**: Run `time` and `free -m`, log to `feasibility.log`, assert limits. |
| **SC-005** (Robustness) | Phase 2 | Permutation importance used to verify rankings are not collinearity artifacts. |

## Implementation Phases

### Phase 0: Data Ingestion & Validation
1.  **Download**: Stream EBD and MODIS data from verified HuggingFace URLs.
2.  **Validation**: Verify presence of *Setophaga ruticilla* and years 2015-2023 in EBD. **If missing, fail with explicit error message** (e.g., "CRITICAL: Verified EBD subset lacks target species or required years. Aborting.").
3.  **Filtering**: Apply complete checklist filters (FR-001).
4.  **Resampling**: Align MODIS to 0.5° grid and weekly frequency (FR-002).
5.  **Output**: `data/raw/ebd_subset.csv`, `data/raw/modis_resampled.csv` (checksummed).

### Phase 1: Feature Engineering & Target Derivation
1.  **Aggregation**: Bin observations into 0.5° grid cells and weekly intervals.
2.  **Target Calculation**: Derive "first arrival" for thresholds {3, 5, 10} (FR-003).
3.  **Feature Creation**: Create lagged features (1-4 weeks) for LST and NDVI.
4.  **Multicollinearity Check**: Compute VIF for predictors; drop features with VIF > 5.
5.  **Output**: `data/processed/grid_cell_data.parquet`, `data/processed/first_arrival_sweep.csv`.

### Phase 2: Modeling & Statistical Testing
1.  **Split**: Temporal split (Train: 2015-2020, Val: 2021, Test:).
2.  **Training**: Train XGBoost models (Temp-only, NDVI-only, Combined) (FR-004).
3.  **Evaluation**: Calculate RMSE and Pearson R on **temporal residuals** (SC-001).
4.  **Interpretability**: Compute SHAP values and Permutation Importance (FR-005, SC-005).
5.  **Statistical Test**: Run Diebold-Mariano test on **aggregated temporal errors** (FR-006, SC-002).
6.  **Output**: `data/outputs/metrics.json`, `data/outputs/feature_importance.csv`.

### Phase 3: Visualization & Stability Analysis
1.  **Stability Analysis**: Compare first-arrival dates across thresholds {3, 5, 10}. Calculate median variation. Flag if >7 days (SC-003).
2.  **Visualization**: Generate regional maps of predicted arrival dates and predictor gradients (FR-007).
3.  **Output**: `data/outputs/stability_report.json`, `data/outputs/regional_maps.png`.

### Phase 4: Performance Verification
1.  **Measurement**: Execute `time ./run_pipeline.sh` and capture `free -m` logs.
2.  **Validation**: Assert peak RAM ≤ 7 GB and elapsed time ≤ 6 hours (SC-004).
3.  **Output**: `data/outputs/feasibility.log`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Verified MODIS dataset is too small (Lake Powell only)** | Cannot model continental migration. | **Mitigation**: Scope reduced to Lake Powell region. All outputs explicitly labeled "Regional". |
| **Missing eBird data in remote areas** | Sparse grid cells, unreliable arrival dates. | **Mitigation**: Exclude cells with < 10 annual observations (FR-003). |
| **Cloud cover in MODIS** | Gaps in LST/NDVI time series. | **Mitigation**: Temporal interpolation; exclude weeks with > 50% cloud cover. |
| **Compute Time > 6 hours** | CI job fails. | **Mitigation**: Use smaller grid resolution (if needed), limit `n_estimators`, stream data. Phase 4 verifies this. |
| **Observer Effort Bias** | High-effort areas show earlier arrival. | **Mitigation**: Filter for complete checklists; acknowledge limitation; optional rarefaction step. |
| **Collinearity (Temp vs NDVI)** | Unstable coefficients. | **Mitigation**: VIF filtering before training; Permutation Importance for ranking. |
| **DM Test Assumption Violation** | Spatial autocorrelation invalidates p-values. | **Mitigation**: DM test performed on time-series of aggregated errors, not spatial cells. |
| **Verified EBD Subset Insufficient** | Pipeline fails to find target species/years. | **Mitigation**: **Fail-fast validation** in Phase 0. If the subset lacks *Setophaga ruticilla* or 2015-2023, the pipeline aborts with a clear error. No alternative verified source exists; the study is contingent on the subset's adequacy. |
