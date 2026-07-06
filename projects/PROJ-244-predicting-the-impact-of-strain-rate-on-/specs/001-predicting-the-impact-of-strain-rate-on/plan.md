# Implementation Plan: Predicting the Impact of Strain Rate on the Yield Strength of Metals

**Branch**: `001-predict-strain-rate-yield` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-strain-rate-yield/spec.md`

## Summary

This project implements a computational pipeline to predict the yield strength of metals as a function of strain rate, alloy composition, and grain size. **Due to the absence of verified real-world materials science datasets (NIST, OpenML) in the current verified block, the pipeline is currently RESTRICTED to a Physics-Consistent Simulated Data generator.** Real-world ingestion from NIST/OpenML is DISABLED for this run. The pipeline standardizes units, imputes missing values using k-Nearest Neighbors (KNN), and trains machine learning models (Random Forest, Gradient Boosting) to compete against empirical constitutive models (Johnson-Cook, Zerilli-Armstrong). The plan emphasizes strict data hygiene, CPU-only feasibility, and rigorous statistical validation of feature importance and model performance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `shap`, `matplotlib`, `numpy`, `pyyaml`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed), checksums tracked in `state/`  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: End-to-end runtime < 6 hours on CPU; memory footprint < 6GB during peak processing  
**Constraints**: No GPU usage; no deep learning; strict adherence to unit standardization (MPa, s⁻¹, µm); missing strain rate/yield strength records must be dropped.  
**Scale/Scope**: Target dataset size ≤ 100,000 records (CPU feasibility); analysis of ≥ 3 alloy families.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS (Simulated Only)** | All scripts will use pinned random seeds (`numpy`, `sklearn`). External datasets (simulated) will be fetched from canonical local generators defined in `research.md`. |
| **II. Verified Accuracy** | **AT RISK** | Real-world data is unavailable. Accuracy is verified against the simulated generator's known physics. Real-world validation is deferred. **HALT GATE**: If no real data is found in Phase 0, the project halts. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Transformations produce new files in `data/processed/`. Checksums recorded in `state/`. No PII expected (materials data). |
| **IV. Single Source of Truth** | **PASS** | All figures and stats trace to `data/processed/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. `updated_at` timestamps updated on artifact changes. |
| **VI. Unit Standardization** | **PASS (Simulated Only)** | Pipeline enforces MPa, s⁻¹, µm conversion. Records missing critical predictors (strain rate) are dropped per FR-003. |
| **VII. Physics-Based Benchmarking** | **PASS** | Johnson-Cook and Zerilli-Armstrong models are mandatory baselines. Failure regimes will be documented via partial dependence plots. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-strain-rate-yield/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── literature_expectations.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── config.py            # Paths, seeds, dataset URLs
├── data/
│   ├── raw/             # Unmodified downloads (or generated)
│   └── processed/       # Cleaned, standardized, imputed data
├── ingestion/
│   ├── fetchers.py      # Downloaders for NIST/OpenML (disabled) / Generator
│   └── parsers.py       # CSV/JSON/XML parsing logic
├── preprocessing/
│   ├── standardize.py   # Unit conversion (MPa, s⁻¹)
│   ├── impute.py        # KNN composition & grain size logic
│   └── validate.py      # Correlation checks, drop/flag logic
├── modeling/
│   ├── empirical.py     # Johnson-Cook, Zerilli-Armstrong fitting
│   ├── ml_models.py     # RF, GB, Ridge, Linear
│   ├── train.py         # Hyperparameter tuning, cross-validation
│   └── evaluation.py    # Metrics, SHAP, Wilcoxon tests, Sensitivity Analysis
├── visualization/
│   └── plots.py         # Partial dependence, feature importance
└── tests/
    ├── unit/
    ├── integration/
    └── contract/        # Schema validation tests

data/
├── raw/
└── processed/

state/
└── projects/PROJ-244-.../
    ├── artifact_hashes.yaml
    └── state.yaml
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`ingestion`, `preprocessing`, `modeling`, `visualization`) to ensure clear data flow dependencies and testability. This structure supports the strict ordering required by the unresolved concerns (Data Discovery -> Preprocessing -> Modeling -> Evaluation).

## Complexity Tracking

No additional complexity layers are introduced beyond the spec requirements. The separation of `empirical.py` and `ml_models.py` ensures fair benchmarking (Constitution VII) without adding unnecessary abstraction layers.

## Phase 0: Data Discovery & Feasibility

### 0.1 Data Availability Check
- **Task T008**: Create `research.md` verifying dataset availability.
  - **Action**: Attempt to fetch real data from NIST/OpenML. If unavailable, activate `Physics-Consistent Simulated Data` generator.
  - **Gate**: **HALT** if no data source (real or simulated) is available.
  - **Output**: `research.md` with updated 'Verified Datasets' table.

### 0.5 Power & Feasibility Analysis
- **Task T009**: Estimate N and Power Analysis.
  - **Action**: Calculate required sample size (N) to detect effect size of strain rate sensitivity (deferred value) given the simulated data variance. Check CPU feasibility (N ≤ 100k).
  - **Gate**: Block Phase 1 if N < 1000 or CPU time > 6h.
  - **Output**: `state/feasibility_report.yaml`.
- **Task T010**: Validate CPU Feasibility.
  - **Action**: Run a small-scale prototype to measure memory usage and runtime.
  - **Gate**: Block Phase 1 if memory > 6GB or runtime > 1h for 1000 rows.
  - **Output**: `state/feasibility_report.yaml`.

## Phase 1: Design & Contracts

### 1.1 Data Model Definition
- **Task T006**: Create base data models/entities.
  - **Action**: Define `TensileTestRecord`, `AlloyFamily`, `ConstitutiveModelParameters`.
  - **Output**: `data-model.md`, `contracts/dataset.schema.yaml`.

### 1.2 Literature Expectations
- **Task T030**: Define Literature Expectations Contract.
  - **Action**: Create `contracts/literature_expectations.yaml` defining expected feature importance rankings (strain rate, composition, grain size) and noise-robustness checks.
  - **Output**: `contracts/literature_expectations.yaml`.

## Phase 2: Foundational Code

### 2.1 Configuration & Entry Point
- **Task T004**: Create `config.py`.
  - **Action**: Define paths, seeds, and dataset URLs (simulated generator).
  - **Output**: `code/config.py`.

- **Task T005**: Create `main.py`.
  - **Action**: Orchestrate pipeline steps.
  - **Output**: `code/main.py`.

## Phase 3: Ingestion & Preprocessing

### 3.1 Data Ingestion
- **Task T012**: Fetch data from source.
  - **Action**: Run simulated generator (or real fetcher if available). Output `data/raw/standardized.csv`.
  - **Output**: `data/raw/standardized.csv`.
  - **Note**: Specific endpoints defined in `code/config.py`.

### 3.2 Standardization
- **Task T013**: Unit conversion.
  - **Action**: Convert to MPa, s⁻¹, µm. Drop records with missing yield/strain rate.
  - **Output**: `data/raw/standardized.csv`.

### 3.3 Raw State Preservation
- **Task T011**: Preserve Raw State for Sensitivity Analysis.
  - **Action**: Copy `data/raw/standardized.csv` to `data/processed/raw_for_sensitivity.csv` BEFORE imputation.
  - **Output**: `data/processed/raw_for_sensitivity.csv`.

### 3.4 Imputation
- **Task T014**: Composition imputation.
  - **Action**: Impute missing composition using alloy family average.
  - **Output**: `data/processed/composition_imputed.csv`.

- **Task T015**: KNN grain size imputation.
  - **Action**: Impute missing grain size using KNN (k=5) on **composition and strain rate** (NOT yield strength). Validate correlation (r ≥ 0.3).
  - **Gate**: If r < 0.3, flag record as `is_low_confidence=True` and **exclude from sensitivity analysis** (but retain in main dataset per FR-003). Generate `data/processed/low_confidence_report.csv`.
  - **Output**: `data/processed/imputed.csv`, `data/processed/low_confidence_report.csv`.

### 3.5 Splitting
- **Task T017**: Stratified split.
  - **Action**: Split by alloy family using a standard train-test partition. Exclude low-sample families (< 20).
  - **Output**: `data/processed/train.csv`, `data/processed/test.csv`.

## Phase 4: Modeling & Evaluation

### 4.1 Baseline Validation
- **Task T020**: Baseline Validity Check.
  - **Action**: Fit Johnson-Cook on training data. Check if R² indicates saturation.
  - **Gate**: If saturated, flag in report and adjust comparison metric to 'Generalization to Noise'.
  - **Output**: `results/baseline_saturation_report.json`.

### 4.2 ML & Empirical Training
- **Task T016**: Train ML models (RF, GB, Ridge).
  - **Action**: Grid search, cross-validation.
  - **Output**: `results/models/ml_models.pkl`.

- **Task T017**: Fit Empirical models (JC, ZA).
  - **Action**: Optimize parameters on training data.
  - **Output**: `results/models/empirical_models.pkl`.

### 4.3 Evaluation
- **Task T018**: Sensitivity Analysis (FR-008).
  - **Action**: Train models on `data/processed/raw_for_sensitivity.csv` (pre-imputation) and `data/processed/imputed.csv`. Compare R².
  - **Output**: `results/sensitivity_analysis.json`.

- **Task T019**: Feature Importance & Validation (SC-002).
  - **Action**: Calculate SHAP values. Compare the top-ranked features against `contracts/literature_expectations.yaml`.
  - **Gate**: Fail if strain rate, composition, grain size not in the top tier of performance. (unless noise explains deviation).
  - **Output**: `results/feature_importance.json`.

- **Task T021**: Statistical Tests (SC-003).
  - **Action**: Wilcoxon signed-rank test on error distributions.
  - **Output**: `results/statistical_tests.json`.

- **Task T022**: Visualization.
  - **Action**: Generate partial dependence plots.
  - **Output**: `results/plots/`.

### 4.4 Literature Validation
- **Task T029**: Verify Feature Importance Against Literature.
  - **Action**: Run assertion in `tests/contract/test_feature_importance.py` to verify that `strain_rate_s_inv`, `composition_vector`, and `grain_size_um` are in the top 3 SHAP rankings.
  - **Output**: `tests/contract/test_feature_importance.py` (Pass/Fail).

## Phase 5: Reporting

- **Task T023**: Generate Final Report.
  - **Action**: Compile metrics, plots, and limitations (simulated data).
  - **Output**: `paper/001-report.md`.

## Risk Management

- **Data Risk**: If simulated data does not reflect real physics, results are invalid. **Mitigation**: Document limitations explicitly.
- **Feasibility Risk**: If N < 1000, power is insufficient. **Mitigation**: T009 blocks execution if N is too low.
- **Baseline Risk**: If Johnson-Cook is saturated, comparison is meaningless. **Mitigation**: T020 detects saturation and adjusts metrics.
- **Imputation Bias**: If KNN imputation introduces bias, sensitivity analysis (T018) will quantify it.
