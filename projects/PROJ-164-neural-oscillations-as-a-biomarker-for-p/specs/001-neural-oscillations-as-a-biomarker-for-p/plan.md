# Implementation Plan: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Branch**: `001-neural-oscillations-tDCS-biomarker` | **Date**: 2026-06-24 | **Spec**: `specs/001-neural-oscillations-tDCS-biomarker/spec.md`
**Input**: Feature specification from `/specs/001-neural-oscillations-tDCS-biomarker/spec.md`

## Summary

This feature implements a computational pipeline to test whether resting-state and task-related EEG oscillatory features can predict individual motor performance improvement after tDCS. Due to the **confirmed absence of paired EEG/tDCS data** in all verified public repositories, the system implements a **Fallback-First Architecture**. The "Primary Mode" (real data analysis) is scientifically unexecutable with current verified sources; therefore, the pipeline defaults to **Fallback Mode** for structural validation and positive control testing. The pipeline adheres to strict CPU-only constraints (≤7 GB RAM, no GPU) and implements rigorous statistical controls (FDR, permutation testing, sensitivity analysis, power analysis).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `requests`, `seaborn`, `statsmodels`  
**Storage**: Local file system (`data/`, `code/`); no external database.  
**Testing**: `pytest` (unit/contract tests), `mne` built-in validation.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM, No GPU).  
**Project Type**: Data Science / Computational Neuroscience Pipeline  
**Performance Goals**: Runtime ≤ 6 hours (assumed from NFR-001 and GitHub Actions limits); Memory ≤ 7 GB peak; CPU-bound operations only.  
**Constraints**: No GPU/CUDA; no large-LLM inference; strict memory management via epoch subsampling; synthetic data generation includes both decoupled noise and positive control signal; dimensionality reduction applied to mitigate overfitting.  
**Scale/Scope**: Single cohort analysis; processing of subjects at the PhysioNet scale with subsampling if memory limits are approached.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`; `requirements.txt` with exact versions; data fetched from canonical HuggingFace URLs; pipeline runnable end-to-end on fresh runner. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs cited are from the "Verified datasets" block. No external citations added without validation. Invalid datasets (e.g., structural fMRI for behavioral scores) are explicitly excluded. |
| **III. Data Hygiene** | **Pass** | Raw data preserved in `data/` with checksums; derived files (epochs, features) written to new filenames; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All stats in reports generated directly from `code/` output; no hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | `main.py` generates SHA-256 hashes for all output artifacts and programmatically updates `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml` `artifact_hashes` and `updated_at` fields on every run. |
| **VI. Neurophysiological Data Integrity** | **Pass** | Pipeline enforces 1–45 Hz band-pass (assuming 1 Hz lower bound per spec typo FR-003), common average re-reference, and automated bad-channel rejection (z-score) via `mne`. Data state detection prevents double-processing. |
| **VII. Biomarker Validation** | **Pass** | Pipeline designed to accept independent datasets (e.g., Kaggle EEG Motor Imagery) via configuration. If no verified secondary dataset exists, a simulation of generalization testing is logged. Permutation tests and cross-validation implemented to assess generalizability. |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-oscillations-tDCS-biomarker/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── feature.schema.yaml
    ├── model_output.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, hyperparameters, mode flags
├── data/
│   ├── __init__.py
│   ├── ingest.py        # Download, verify checksums, detect data state
│   ├── preprocess.py    # MNE pipeline: filter, re-ref, epoch (skipped if pre-processed)
│   └── synthetic.py     # Fallback Mode generator (Decoupled & Positive Control)
├── features/
│   ├── __init__.py
│   ├── extract.py       # Spectral power, PLV, wPLI
│   └── select.py        # Dimensionality reduction (PCA/Variance) to mitigate overfitting
├── models/
│   ├── __init__.py
│   ├── train.py         # Ridge regression, CV, tuning (reduced permutations for speed)
│   └── validate.py      # Permutation, FDR, sensitivity, Power Analysis
├── reports/
│   ├── __init__.py
│   └── generate.py      # Sensitivity tables, plots, versioning updates
└── main.py              # Orchestrator (Mode selection, Versioning)

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_output_schema.py
├── integration/
│   └── test_pipeline_mode_switch.py
└── unit/
    ├── test_preprocess.py
    └── test_synthetic.py
```

**Structure Decision**: Single-project structure selected to minimize I/O overhead and simplify dependency management on constrained runners. Modules are separated by function (ingest, preprocess, features, models) to allow parallel testing and clear separation of concerns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Fallback-First Architecture** | Required by FR-001/US-1. Verified datasets lack paired EEG/tDCS data. Primary Mode is scientifically impossible with current sources. | A single-mode pipeline would fail to run or produce invalid scientific claims. Fallback Mode allows structural validation of the code and statistical power testing without making false claims. |
| **Dual Synthetic Data Generation** | Required to satisfy SC-002-FB (Decoupled, R²≈0) and Methodology Panel concerns (Positive Control, R²>0). | A single synthetic mode cannot simultaneously validate code execution (decoupled) and statistical power (signal-injected). |
| **Dimensionality Reduction** | Required to address the "curse of dimensionality" (N=109 vs. high-dim EEG features). | Direct modeling without feature reduction risks severe overfitting and unstable variance estimates in nested CV. |
| **Runtime Optimization** | Nested CV + 1000 permutations on 2 CPU cores may exceed 6 hours. | Full nested CV with 1000 permutations is computationally infeasible. Reduced permutations (100) in inner loop and feature subsampling are necessary to meet the 6-hour constraint. |
| **Versioning Automation** | Required by Constitution Principle V. | Manual hash generation is error-prone. Automated updates in `main.py` ensure compliance. |

## Methodological Rigor & Spec Coverage

### Statistical Approach
1.  **Feature Extraction**:
    -   **Spectral Power**: Welch's method for Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Gamma (30-45Hz).
    -   **Connectivity**: Phase Locking Value (PLV) and weighted Phase Lag Index (wPLI).
    -   **Preprocessing**: Band-pass 1–45 Hz (assuming 1 Hz lower bound per FR-003 typo), Common Average Reference (CAR), bad channel rejection via z-score (>3 SD).
    -   **Data State Detection**: If input data is pre-processed, skip filtering/re-referencing to avoid double-processing.

2.  **Modeling**:
    -   **Algorithm**: Ridge Regression (L2 regularization).
    -   **Dimensionality Reduction**: PCA or Variance Thresholding applied before modeling to reduce predictors to < N/10.
    -   **Validation**: 5-fold Cross-Validation.
        -   *Outer Loop*: Evaluation (1000 permutations).
        -   *Inner Loop*: Hyperparameter tuning (100 permutations to ensure <6h runtime).
    -   **Significance**: Permutation testing (1,000 permutations) to establish a null distribution for R².

3.  **Multiple Comparison Correction**:
    -   **FDR**: Benjamini-Hochberg procedure applied to p-values of model coefficients.

4.  **Sensitivity Analysis (FR-007)**:
    -   Sweep significance thresholds (p: low, 0.05, 0.1) and R² thresholds (0.2, 0.3, 0.4).
    -   **Justified Stability Rule**: The primary finding is "Justified" only if significance holds in **at least 2 out of 3** tested p-thresholds.
    -   **Reporting**: Explicitly report the threshold range where significance is lost.

5.  **Power Analysis**:
    -   Calculate Minimum Detectable Effect Size (MDES) for N=109.
    -   Report if power < 0.80 for expected effect sizes, qualifying any non-significant results.

### Success Criteria Mapping
-   **SC-001**: Data integrity via checksums.
-   **SC-002**: Primary Mode R² and p-value (if data exists; otherwise N/A).
-   **SC-002-FB**: Fallback Mode Decoupled R² ≈ 0.0 (±0.05).
-   **SC-003**: Runtime ≤ 6 hours (assumed from NFR-001 typo).
-   **SC-004**: Stability variance ≤ 0.05.

### Spec Typo Handling
-   **FR-003**: Spec says "low-frequency". Plan assumes **1 Hz** based on standard EEG practice and context.
-   **SC-003**: Spec says "-hour". Plan assumes **6 hours** based on GitHub Actions free tier limits.
-   **Action**: These assumptions are documented. A kickback to the spec author is recommended to fix the typos.

## Assumptions & Risks

-   **Assumption**: No verified dataset contains paired EEG and tDCS motor scores. The system defaults to Fallback Mode.
-   **Assumption**: The PhysioNet parquet file is pre-processed. The pipeline detects this and skips redundant steps.
-   **Risk**: The OpenNeuro dataset cited is structural/fMRI and lacks behavioral scores.
    -   **Mitigation**: Explicitly excluded from Primary Mode. System defaults to Fallback Mode.
-   **Risk**: Overfitting due to high dimensionality.
    -   **Mitigation**: Dimensionality reduction (PCA) applied before modeling.
-   **Risk**: Runtime > 6 hours.
    -   **Mitigation**: Reduced permutations in inner CV loop; feature subsampling.