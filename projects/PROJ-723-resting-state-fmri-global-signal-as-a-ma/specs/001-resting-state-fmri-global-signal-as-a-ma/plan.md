# Implementation Plan: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

**Branch**: `001-gene-regulation` | **Date**: 2026-06-17 | **Spec**: `specs/001-resting-state-fmri-global-signal-as-a-ma/spec.md`
**Input**: Feature specification from `/specs/001-resting-state-fmri-global-signal-as-a-ma/spec.md`

## Summary

This project investigates whether the amplitude (standard deviation) of the resting-state fMRI global signal predicts individual differences in self-reported mind-wandering frequency (MWQ). The approach involves ingesting minimally preprocessed HCP resting-state fMRI data and MWQ scores, computing the global signal standard deviation, and performing a ridge regression analysis adjusted for motion and demographic covariates. The plan emphasizes strict adherence to the project constitution (reproducibility, data hygiene) and computational feasibility on free-tier CPU-only CI (2 cores, ~7GB RAM).

**Critical Data Note**: The plan assumes the verified HCP parquet files contain either raw 4D time-series or pre-computed global signal columns. If these are absent, the pipeline will halt with a `FATAL: Dataset Mismatch` error to prevent invalid analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `nibabel`, `requests`, `pyyaml`, `statsmodels`, `scipy`  
**Storage**: Local file system (HCP data cached in `data/raw/`, processed metrics in `data/processed/`)  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research / Data analysis pipeline  
**Performance Goals**: Complete full pipeline (ingestion + modeling + robustness) in <6 hours on 2 CPU cores.  
**Constraints**: No GPU; RAM usage <7GB; Disk usage <14GB; No PII in repo.  
**Scale/Scope**: Target a subset of HCP subjects; multiple runs per subject.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin all versions. Random seeds (numpy, sklearn) will be set globally. Data fetching scripts will use canonical URLs. |
| **II. Verified Accuracy** | **PENDING DATA VERIFICATION** | All dataset URLs in `research.md` are sourced from the "Verified datasets" block. Verification of data content (raw time-series vs. summary) is a runtime check; if missing, the pipeline halts. |
| **III. Data Hygiene** | **PASS** | Raw data will be downloaded to `data/raw/` with checksums recorded in `state/...yaml`. Derived metrics (CSV) will be written to `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Final statistics will be generated programmatically from `data/processed/` and written to `results/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data artifacts will be tracked. The plan documents the hash update procedure. |
| **VI. Neuroimaging Data Integrity** | **PENDING DATA VERIFICATION** | BIDS-compatible directory structure (`sub-<label>/func/`) will be enforced for raw data. JSON sidecars with acquisition parameters (TR, pipeline version) will be generated. This is contingent on data availability. |
| **VII. Behavioral Assessment Standardization** | **PASS** | MWQ scoring logic will be implemented in `code/mwq_scoring.py`, documenting the version and reverse-scoring rules. Scores stored in de-identified CSVs with metadata. |

## Project Structure

### Documentation (this feature)

```text
specs/001-resting-state-fmri-global-signal-as-a-ma/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── mwq_scoring.py       # Principle VII: MWQ version, reverse-scoring logic
├── ingestion.py         # FR-001, FR-002, FR-008, FR-009: Data download, metric computation, validation
├── diagnostics.py       # VIF, GSA-Motion correlation checks
├── modeling.py          # FR-004, FR-005: Ridge regression, permutation tests (Full vs Reduced)
├── robustness.py        # FR-006, FR-007: Sensitivity analysis & variance check
├── utils.py             # Logging, file I/O helpers
└── main.py              # Pipeline orchestrator

data/
├── raw/                 # Downloaded HCP data (cached)
│   └── sub-<label>/
│       └── func/        # BIDS structure with JSON sidecars
├── processed/           # Cleaned CSVs, computed metrics
└── results/             # Final JSON reports, plots

tests/
├── test_ingestion.py
├── test_modeling.py
└── test_robustness.py

requirements.txt
```

**Structure Decision**: Single `code/` directory for scripts. This minimizes overhead and ensures all logic is accessible for the CPU-only CI runner. `data/` is split into `raw` (immutable, BIDS) and `processed` (derived).

## Implementation Phases

### Phase 0: Data Verification & Ingestion Setup
**Goal**: Verify data availability, establish BIDS structure, and prepare the ingestion environment.

*   **Step 1: Environment Setup**
    *   Install dependencies from `requirements.txt`.
    *   Set random seeds (numpy, sklearn, random).
*   **Step 2: Dataset Fetch & Schema Check (FR-001)**
    *   Download verified datasets (`HCP-flat`, `MWQ`).
    *   **Critical Check**: Inspect `HCP-flat` for `global_signal` (array) or `global_signal_sd` (float).
    *   **Halt Condition**: If raw time-series or pre-computed GSA is missing, log `FATAL: Dataset Mismatch - Required columns not found in verified URL` and exit. Do not proceed.
    *   Verify MWQ scores exist and are joinable via `subject_id`.
*   **Step 3: BIDS Structure & Sidecars (Principle VI)**
    *   Organize raw data into `data/raw/sub-<label>/func/`.
    *   Generate JSON sidecars for each run containing TR, voxel size, and preprocessing pipeline version.
*   **Step 4: MWQ Scoring Script (Principle VII)**
    *   Implement `code/mwq_scoring.py` to document the specific MWQ version, reverse-scoring rules, and total score calculation.

### Phase 1: Data Processing & Validation
**Goal**: Clean data, compute metrics, validate subjects, and perform diagnostics.

*   **Step 1: Metric Computation (FR-002)**
    *   If raw time-series provided: Compute voxel-wise mean (global signal) and its standard deviation per run.
    *   If pre-computed: Validate against definition.
    *   Average across runs per subject.
*   **Step 2: Power Analysis (Methodology)**
    *   Calculate Minimum Detectable Effect Size (MDES) for N=200, alpha=0.05, power=0.80 using `statsmodels`.
    *   Log MDES; if expected effect < MDES, flag low power risk.
*   **Step 3: Collinearity Diagnostics (Methodology)**
    *   Calculate Variance Inflation Factors (VIF) for predictors (GSA, FD, DVARS, Age, Sex).
    *   Calculate correlation between GSA and FD/DVARS.
    *   If VIF > 5 or GSA-FD correlation > 0.7, flag "High Collinearity" and proceed with caution (interpret as predictive, not causal).
*   **Step 4: Subject Validation & Exclusion (FR-008, FR-009)**
    *   **Pair Validation (FR-009)**: Join fMRI and MWQ data on `subject_id`. Exclude unmatched pairs. Log count.
    *   **Motion Exclusion (FR-008)**: Calculate mean FD per subject. Exclude subjects where `mean_fd > 0.5mm`. Log count and IDs.
    *   **Zero Variance Check**: Exclude subjects with `global_signal_sd == 0`. Log count.
    *   **Output**: Write `data/processed/cleaned_data.csv` with `exclusion_reason` column if applicable.

### Phase 2: Modeling & Robustness
**Goal**: Run statistical models, validate findings, and isolate GSA effect.

*   **Step 1: Primary Model (FR-004)**
    *   Fit Ridge Regression (Y ~ GSA + FD + DVARS + Age + Sex).
    *   Nested 5-fold CV: Outer loop for performance, Inner loop for alpha tuning across a range of orders of magnitude.
    *   Record Out-of-Fold MAE, Pearson r, R².
*   **Step 2: Global Signal Specificity Check (Methodology)**
    *   Compute partial correlation of GSA with MWQ controlling for FD/DVARS (using OLS on residuals if VIF allows, otherwise report predictive gain).
    *   Log if GSA effect is indistinguishable from motion artifacts.
*   **Step 3: Null Distribution Generation & Isolation (FR-005)**
    *   **Procedure**:
        1.  Run the full nested CV pipeline on the **Full Model** (GSA + Covariates).
        2.  Shuffle `MWQ` scores multiple times to assess the stability of the results..
        3.  For each shuffle, run the full nested CV pipeline.
        4.  Collect a set of null MAE (and R²) values.
        5.  Calculate empirical p-value: $p = \frac{\text{count}(\text{Null MAE} \le \text{Observed MAE}) + }{1000 + 1}$.
    *   **Reduced Model Comparison (Isolation Step)**:
        1.  Fit a **Reduced Model** (Y ~ FD + DVARS + Age + Sex) without GSA.
        2.  Run a sufficient number of permutations on the Reduced Model.
        3.  Compare the distribution of $\Delta R^2$ (Full - Reduced) against 0.
        4.  This isolates the specific contribution of GSA, addressing the concern that the full model test does not isolate GSA.
*   **Step 4: Sensitivity Analysis (FR-006)**
    *   Sweep alpha over a range of values without nested CV (using optimal alpha from Step 1 as baseline).
    *   Report MAE variation across values.
*   **Step 5: Metric Variation Analysis (FR-007)**
    *   Repeat primary analysis using `global_signal_variance` instead of SD.
    *   Report Pearson r and compare to primary SD result (target: within ±0.05).

### Phase 3: Reporting
**Goal**: Generate final artifacts.

*   **Step 1: Aggregate Results**
    *   Combine primary, null, and robustness results into `data/results/final_report.json`.
*   **Step 2: Visualization**
    *   Generate plots: Null distribution histogram, Alpha sweep plot, Correlation matrix.
*   **Step 3: Final Review**
    *   Verify all success criteria (SC-001 to SC-005) are met.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Nested Cross-Validation** | Required by FR-004 to tune $\alpha$ without data leakage. | Simple CV would overfit the hyperparameter, inflating performance estimates. |
| **1,000 Permutations** | Required for robust p-value resolution (min 0.001) and tail stability. | A set of permutations yields coarse p-values (min 0.01), insufficient for distinguishing p=0.04 vs 0.06. |
| **Reduced Model Comparison** | Required to isolate GSA effect from covariates (Methodology concern). | Permuting the full model only tests the *whole* model, not the specific contribution of GSA. |
| **VIF Diagnostics** | Required to validate GSA interpretability against motion (Methodology concern). | Ridge shrinks coefficients but does not resolve collinearity ambiguity; diagnostics are needed to assess validity. |
| **Motion Confound Regression** | Required by FR-003 and FR-008 to control for motion artifacts which correlate with global signal. | Ignoring motion would introduce a severe confound, invalidating the association. |
| **BIDS Structure** | Required by Constitution Principle VI. | Flat structure violates neuroimaging standards and provenance tracking. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | Fatal: Cannot compute GSA from summary tables. | Explicit check in Phase 0. Halt with `FATAL: Dataset Mismatch - Required columns not found in verified URL` error if required columns missing. |
| **ID Mismatch** | High: Low N after join. | Implement fuzzy matching or ID normalization. Log exclusion counts (FR-009). |
| **Memory Overflow** | High: Crash on CI. | Process subjects in batches. Use `dtype` optimization. |
| **High Collinearity** | Medium: GSA effect indistinguishable from motion. | VIF diagnostics. If VIF > 5, report as "Predictive Gain" rather than "Independent Effect". |
| **Low Power** | Medium: Type II error. | Formal MDES calculation. Explicitly report power limits in final report. |
| **Interpretational Ambiguity** | Medium: GSA may be a motion proxy. | Explicitly state in reports that GSA is "predictive" not "causal" or "independent" if VIF is high or Reduced Model comparison shows no significant Delta R². |