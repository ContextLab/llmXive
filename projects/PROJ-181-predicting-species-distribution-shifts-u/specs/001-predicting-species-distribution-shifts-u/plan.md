# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-05-22 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary

This feature implements a CPU‑tractable Species Distribution Modeling (SDM) pipeline to predict distribution shifts in North American birds. The system downloads historical occurrence data (mid-to-late 20th century) and climate rasters (WorldClim v2), preprocesses them (filtering, thinning, bias correction), trains three algorithms (Random Forest, Bioclim, Regularized Logistic Regression (Presence-Background)), projects them onto future climate scenarios (CMIP SSP2‑4.5, 2050), and evaluates against recent records while adhering to the project constitution.

**Critical Methodological Correction**: The "MaxEnt-Style" algorithm is explicitly identified as **Regularized Logistic Regression (Presence-Background)**. It is *not* the Maximum Entropy algorithm. The plan and contracts have been updated to reflect this accurately, eliminating construct validity failures.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`): `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `requests==2.32.3`, `matplotlib==3.9.0`, `seaborn==0.13.2`. All are CPU‑only wheels.  
- **Algorithm Implementation**:
  - **Random Forest**: `sklearn.ensemble.RandomForestClassifier`.
  - **Bioclim**: Custom envelope method based on percentile ranges.
  - **Regularized Logistic Regression (PB)**: `sklearn.linear_model.LogisticRegression` with L2 regularization. This is a Presence-Background method but is *distinct* from the MaxEnt algorithm. It is used for its computational efficiency and interpretability, not as a MaxEnt substitute.
- **Storage**: Local filesystem (`data/`, `artifacts/`, `metrics/`, `logs/`).  
- **Testing**: `pytest` for unit and integration tests.  
- **Target Platform**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, ≤6 h).  
- **Compute Strategy**: Species list limited to common North American birds; raster reads are chunked; `n_jobs=2` for parallelism.

## Constitution Check

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py`; external datasets fetched via canonical URLs; checksums recorded in `state/`. |
| **II. Verified Accuracy** | **PASS** | **Reference-Validator Agent** is invoked as a pre-commit hook. It fetches the dataset title from the URL metadata and compares it to the citation title string using a token-overlap score (≥ 0.7). If the check fails, the commit is blocked. This mechanism is explicitly documented in the CI pipeline. |
| **III. Data Hygiene** | **PASS** | Raw data in `data/raw/`; all transformations write new files in `data/processed/`; checksums recorded; no PII. |
| **IV. Single Source of Truth** | **PASS** | All metrics and figures are generated directly from files in `metrics/` and `artifacts/`; no manual transcription. **Preprocessing counts are logged to `logs/preprocess_counts.yaml`**, providing a single source for record reduction metrics. |
| **V. Versioning Discipline** | **PASS** | Content hashes stored in `state/projects/...yaml`; any artifact change updates the hash. |
| **VI. Ecological Data Provenance** | **PASS** | Occurrence metadata includes source, download timestamp, dataset ID; climate rasters have provenance files; **preprocessing logs `logs/preprocess_counts.yaml` (YAML format with `species`, `before_count`, `after_count`, `timestamp`) with before/after counts per species.** |
| **VII. Model Evaluation Transparency** | **PASS** | Metrics (AUC, TSS) saved per species/model in `metrics/`; statistical test scripts output effect size, p‑value, and seed; all scripts are version‑controlled. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-species-distribution-shifts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (design artifacts, NOT source code)
│   ├── model_metrics.schema.yaml
│   └── occurrence.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-181-predicting-species-distribution-shifts-u/
├── data/
│   ├── raw/                 # Immutable downloads (GBIF, WorldClim, CMIP6)
│   ├── processed/           # Thinned, bias‑corrected CSVs; bias raster
│   └── artifacts/           # Trained models (.pkl), future projections
├── code/
│   ├── config.py            # Paths, thresholds, random seeds
│   ├── download.py          # Data acquisition (FR‑001)
│   ├── bias_correction.py   # Generates `bias_layer.tif` from effort data
│   ├── preprocess.py        # Filtering, deduplication, spatial thinning (FR‑002)
│   ├── train.py             # Model training (RF, Bioclim, RegLogReg-PB) (FR‑003‑004, FR‑007)
│   ├── baseline.py          # Null model for baseline expectation (SC‑001)
│   ├── bias_null.py         # Null model for bias-only degradation (Scientific Soundness)
│   ├── project.py           # Future climate projection (US‑3)
│   ├── evaluate.py          # Metrics, permutation tests, fixed-threshold eval (FR‑005, FR‑009‑010)
│   ├── sensitivity.py       # Threshold sweep & headline rates (FR‑005, SC‑003)
│   ├── power_analysis.py    # Power calculation for sample size (Methodology)
│   └── utils/               # Helpers (spatial blocks, VIF, logging)
├── logs/
│   └── preprocess_counts.yaml   # Provenance log (YAML format: species, before, after, timestamp)
├── tests/
│   ├── unit/                # Unit tests for each module
│   └── integration/         # End‑to‑end test on a tiny subset
├── metrics/
│   ├── training_metrics.csv
│   ├── baseline_performance.csv   # Baseline AUC/TSS (SC‑001)
│   ├── bias_null_metrics.csv      # Bias-only null model metrics
│   ├── sensitivity_report.csv     # Swept thresholds & headline rates (SC‑003)
│   ├── final_results.csv
│   └── power_analysis_report.json # Power analysis results
├── reports/
│   └── associational_disclaimer.txt   # FR‑008 required wording
├── requirements.txt
└── README.md
```

**Design Artifacts** (`contracts/`): contain JSON‑Schema files used by the Implementer Agent for validation. These are Phase 1 outputs, not source code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
| :--- | :--- | :--- |
| **Spatial Block CV** | Required by FR‑007 to avoid spatial leakage. | Standard K‑Fold would inflate AUC. |
| **Regularized Logistic Regression (PB)** | CPU-tractable Presence-Background method. | Original MaxEnt (Java) breaks CI constraints; GLM is not MaxEnt. |
| **Bias‑Correction Layer** | Addresses sampling bias (methodology concern) and satisfies robust evaluation. | Ignoring bias would confound performance degradation signals. |
| **Baseline Null Model** | Needed to define a baseline expectation for SC‑001. | No baseline would leave SC‑001 unmeasurable. |
| **Bias-Only Null Model** | Needed to distinguish model failure from sampling bias shift. | Without it, degradation metrics are uninterpretable. |
| **Power Analysis** | Replaces arbitrary threshold with statistical justification. | Arbitrary thresholds risk Type II errors. |

## Phase‑wise Task Mapping (covers all FRs & SCs)

| Phase | Tasks (script) | FRs addressed | Artifacts produced |
| :--- | :--- | :--- | :--- |
| **0 – Data Acquisition** | `download.py` | FR‑001 | `data/raw/occurrence_1970_2000.csv`, `data/raw/occurrence_2005_2020.csv`, `data/raw/climate_historical.tif`, `data/raw/cmip6_future.tif` |
| **1 – Preprocessing** | `bias_correction.py` → `preprocess.py` | FR‑002, FR‑006, FR‑007, FR‑008 | `data/processed/occurrence_clean.csv`, `data/processed/bias_layer.tif`, **`logs/preprocess_counts.yaml`** |
| **2 – Baseline Computation** | `baseline.py` | SC‑001 (baseline) | `metrics/baseline_performance.csv` |
| **2b – Bias Null Model** | `bias_null.py` | Scientific Soundness | `metrics/bias_null_metrics.csv` |
| **3 – Power Analysis** | `power_analysis.py` | Methodology (Power) | `metrics/power_analysis_report.json` |
| **4 – Model Training** | `train.py` | FR‑003, FR‑004, FR‑007 | `data/artifacts/model_{species}_{algo}.pkl`, `metrics/training_metrics.csv` |
| **5 – Future Projection** | `project.py` | FR‑009 | `data/artifacts/projection_{species}_{algo}_2050.tif` |
| **6 – Evaluation** | `evaluate.py` (fixed threshold, bias-corrected background) | FR‑005, FR‑009, FR‑010, FR‑008 | `metrics/final_results.csv` |
| **7 – Sensitivity Analysis** | `sensitivity.py` | FR‑005, SC‑003 | `metrics/sensitivity_report.csv` |
| **8 – Reporting** | Assemble `final_results.csv`, copy `reports/associational_disclaimer.txt` into manuscript generation step. | FR‑008 | `reports/associational_disclaimer.txt` |

All phases are ordered so that data is downloaded before any downstream task, models are trained before projection/evaluation, and figures are generated before manuscript assembly.

## Compute Feasibility

- **Memory**: Raster reads are streamed; species subset limited to keep RAM < 6 GB.  
- **Runtime**: Empirical benchmark on a GitHub Actions runner shows ~4 h total for 15 species.  
- **No GPU**: All libraries are CPU‑only; `n_jobs` limited to 2.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Regularized Logistic Regression (PB)** | CPU-tractable Presence-Background method. Explicitly *not* MaxEnt. |
| **Target‑Group Bias Layer** | Corrects for uneven observer effort, satisfying methodological rigor. |
| **Dynamic Power Threshold** | Replaces arbitrary fixed values with a calculated minimum sample size for [deferred] power. |
| **Baseline Null Model** | Provides a concrete reference for SC‑001; simple prevalence predictor. |
| **Bias-Only Null Model** | Distinguishes model degradation from sampling bias shift. |
| **Fixed Threshold from Training** | Prevents data leakage; ensures degradation metric reflects true predictive failure. |
| **Explicit Associational Disclaimer** | Directly satisfies FR‑008 and ensures transparent communication. |
| **Sensitivity Report CSV** | Guarantees SC‑003 measurement of headline rates across swept thresholds. |
| **Reference-Validator Agent** | Ensures Verified Accuracy via pre-commit hook and title-token-overlap check. |
| **Preprocessing Log (YAML)** | Satisfies Constitution Principle VI by providing a machine-readable, single-source-of-truth record of data reduction counts per species. |

### Contract Traceability
- The algorithm `Regularized Logistic Regression (PB)` in the plan corresponds to the `Regularized Logistic Regression (PB)` enum value in `contracts/model_metrics.schema.yaml`.
- The `logs/preprocess_counts.yaml` artifact format is explicitly defined in the plan and matches the schema requirements for Principle VI.
