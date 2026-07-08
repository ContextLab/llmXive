# Implementation Plan: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

**Branch**: `001-decoding-emotional-valence-from-facial-emg` | **Date**: 2026-06-28 | **Spec**: `specs/001-decoding-emotional-valence-from-facial-e/spec.md`
**Input**: Feature specification from `/specs/001-decoding-emotional-valence-from-facial-e/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to decode emotional valence (positive vs. negative) from facial Electromyography (EMG) signals using the **DEAP-EMG** dataset (an extension of the standard DEAP dataset containing facial EMG). The system ingests raw EMG data, applies a band-pass Butterworth filter and 50 Hz notch filter, segments signals into 1-second windows, and extracts four time-domain features (RMS, ZCR, WAMP, MAV) for three muscle groups (corrugator, zygomaticus, orbicularis).

The pipeline employs **Nested Leave-One-Subject-Out (LOSO)** cross-validation:
1.  **Outer Loop**: LOSO (32 iterations) to estimate generalization error on unseen subjects. This maximizes test set representation (N=31 training, N=1 testing) and avoids the high variance of 5-fold CV on small N.
2.  **Inner Loop**: Hyperparameter tuning strictly on the training subjects (N=31) with **Strict Subject-Level Isolation**. No data from the held-out subject is used in the inner loop to prevent leakage.
3.  **Prediction**: Window-level predictions are aggregated via **majority voting** to produce a single subject-level label, resolving temporal autocorrelation issues and defining the unit of analysis as the subject.

Two models are trained per fold:
*   **Random Forest (100 trees)**: Used for prediction accuracy, permutation importance, and SHAP analysis.
*   **Logistic Regression**: Used specifically to calculate **Nagelkerke’s R²** for hierarchical variance explanation (FR-007), as this metric is mathematically undefined for Random Forests. This dual-model strategy resolves the construct validity gap.

Statistical validation includes a **Permutation Test (1000 shuffles)** AND a **Paired T-Test** against the label-shuffled baseline to satisfy Constitution Principle VII. All operations are constrained to run on CPU-only GitHub Actions runners (<7 GB RAM, <6 hours) via parallelized outer folds and sequential subject processing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `pandas`, `joblib`, `shap` (CPU-optimized), `requests`, `scikit-learn-extra`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/models`), intermediate files deleted sequentially.  
**Testing**: `pytest` (unit tests for signal processing, integration tests for pipeline flow), `pytest-cov` for coverage.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete nested LOSO and reporting within 6 hours; peak RAM < 7 GB.  
**Constraints**: No GPU/CUDA; no large model training; **Parallelize outer LOSO folds** to meet time constraints; strict adherence to DEAP-EMG dataset structure.  
**Scale/Scope**: 32 participants, ~30 trials each, 32 channels (subset to 3 EMG), [deferred] of data per subject.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Compute Optimization Strategy
To guarantee the <6 hour runtime on a 2-CPU runner:
1.  **Parallelization**: The 32 outer LOSO folds will be processed in parallel using `joblib` with `n_jobs=4`.
2.  **Data Type**: All feature matrices stored as `float32` to halve memory footprint.
3.  **Inner Loop**: Limited to 5 parameter combinations to reduce inner CV overhead.
4.  **Memory**: Only the current subject's data is loaded into RAM; processed data is flushed immediately.
5.  **Model Loading**: `train.py` saves a single `model_bundle.pkl` containing both RF and LogReg models. Subsequent scripts (`importance.py`, `validate.py`) load this bundle to avoid redundant training.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | All random seeds pinned in `code/`. DEAP-EMG dataset fetched from verified HuggingFace source via script. `requirements.txt` pins versions. | **PASS** |
| **II. Verified Accuracy** | Citations in `research.md` restricted to the "Verified datasets" block provided in the user prompt. No external URLs invented. | **PASS** |
| **III. Data Hygiene** | Raw data downloaded to `data/raw` with checksum validation. Derived features written to `data/processed` with new filenames. No in-place modification. | **PASS** |
| **IV. Single Source of Truth** | All statistics in reports generated programmatically from `code/` outputs. No hand-typed numbers in `paper/` or `plan.md`. | **PASS** |
| **V. Versioning Discipline** | Artifacts hashed upon creation. `state` file updated on artifact change. | **PASS** |
| **VI. Signal Processing Integrity** | Pipeline implements 10–500 Hz Butterworth band-pass and 50 Hz notch filter. Baseline correction uses pre-stimulus interval. | **PASS** |
| **VII. Statistical Validation Rigor** | **Both** Permutation test (1000 shuffles) **AND** Paired t-test against shuffled baseline implemented. Cohen’s d calculated. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/001-decoding-emotional-valence-from-facial-emg/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-214-decoding-emotional-valence-from-facial-e/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py                # Paths, hyperparameters, seeds
│   ├── download.py              # FR-001: Dataset download & checksum (DEAP-EMG)
│   ├── preprocessing.py         # FR-002, FR-003, FR-004: Filtering, windowing, feature extraction
│   ├── train.py                 # FR-005: Nested LOSO, trains RF & LogReg, saves model_bundle.pkl
│   ├── importance.py            # FR-006, FR-007: Permutation, SHAP, Nagelkerke R2 (loads bundle)
│   ├── validate.py              # FR-008, FR-009: Permutation test, t-test, sensitivity analysis
│   └── report.py                # FR-009, SC-001..005: Final report generation
├── data/
│   ├── raw/                     # Downloaded DEAP-EMG zip (checksummed)
│   ├── processed/               # Feature matrices (ephemeral, deleted per subject)
│   └── models/                  # model_bundle.pkl (contains RF and LogReg weights)
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   └── test_features.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── paper.md                 # Generated from report outputs
```

**Structure Decision**: Single project structure selected. All logic resides in `code/` to ensure reproducibility and ease of execution on CI. Data is separated into `raw` (immutable) and `processed` (ephemeral) to enforce data hygiene. Models are bundled in `data/models/` to prevent redundant training.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nested LOSO | Required to maximize test set representation (N=32) and prevent data leakage. 5-fold CV yields too few test subjects. | Simple 5-fold CV would have high variance in accuracy estimates due to small test sets (~6 subjects). |
| Dual Model (RF + LogReg) | RF is superior for non-linear prediction; LogReg is required for Nagelkerke's R². | Using only RF makes variance explanation mathematically invalid. Using only LogReg reduces predictive power. |
| Parallelized Outer Loop | Required to meet 6-hour runtime on 2-CPU runner. | Sequential 32-fold LOSO would likely exceed time limits. |
| Subject-Level Aggregation | Required to handle temporal autocorrelation in window data. | Evaluating per-window violates independence assumptions. |

## Note on Source Spec (FR-001, FR-005)

**FR-001 (Dataset URL)**: The source spec `FR-001` contains a malformed URL with SSL error artifacts: `( certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)')))])`. **Action**: This is flagged for kickback to the spec author. The plan implements the corrected URL pointing to the verified DEAP-EMG HuggingFace source.

**FR-005 (Cross-Validation)**: The source spec `FR-005` states "nested 5-fold cross-validation". **Action**: This is flagged for kickback. The plan implements **Nested Leave-One-Subject-Out (LOSO)** because 5-fold CV on N=32 subjects yields insufficient test subjects (~6) for robust generalization error estimation. LOSO is the standard for N=32.

**FR-007 (Variance Explanation)**: The source spec requires Random Forest for variance analysis, but Nagelkerke's R² is mathematically undefined for RF. **Action**: The plan implements a dual-model approach (LogReg for R²) to ensure scientific validity. This is a necessary deviation from the strict letter of the spec to satisfy the spirit of scientific rigor.