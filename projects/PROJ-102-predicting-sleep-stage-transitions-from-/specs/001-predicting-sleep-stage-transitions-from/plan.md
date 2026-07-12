# Implementation Plan: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

**Branch**: `001-predict-sleep-transitions` | **Date**: 2026-07-12 | **Spec**: `specs/001-predict-sleep-transitions/spec.md`
**Input**: Feature specification from `/specs/001-predict-sleep-transitions/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to predict sleep stage transitions using single-channel scalp EEG (Fpz-Cz) from the Sleep-EDF Expanded Database (SC subset). The approach involves: (1) automated downloading and integrity verification of PhysioNet data; (2) rigorous preprocessing (linear interpolation, 0.5–45 Hz bandpass, 50/60 Hz notch) and segmentation into stable epochs and transition windows; (3) extraction of time, frequency, and non-linear features followed by Cluster-Based Permutation Tests with FDR correction; and (4) training a lightweight 1D-CNN (≤100k parameters) to predict transition probability.

**Critical Methodological Update**: To avoid tautological validation (predicting the annotation boundary itself), the model predicts the *onset* of a transition **prior to** the annotated stage change. The input window ends a short duration prior to the transition label, ensuring the model learns pre-transition physiological precursors. The statistical testing and model training are decoupled; the model uses the full feature set regardless of univariate significance, with a fallback to raw signal input if feature extraction is underpowered.

The entire pipeline is constrained to run within 6 hours on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `mne`, `scikit-learn`, `pandas`, `torch` (CPU-only), `matplotlib`, `seaborn`, `mne-features`, `joblib`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`), Parquet/NPY for data, YAML for state. SQLite is used **only** for transient metadata during pipeline execution and is not the persistent data store.  
**Testing**: `pytest` with contract tests against schema definitions.  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Neuroscience / Data Science Pipeline  
**Performance Goals**: Pipeline completion ≤ 6 hours; Model training ≤ 4 hours; Peak RSS ≤ 7 GB  
**Constraints**: No GPU; No deep learning frameworks requiring CUDA; Parameter count ≤ 100k; No modification of raw data  
**Scale/Scope**: Sleep-EDF SC subset (a cohort of subjects); A large number of epochs total; A set of transition windows will be utilized.  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; `requirements.txt` pins versions; Data fetched from canonical PhysioNet source via `wget` with checksum verification. |
| **II. Verified Accuracy** | **PASS** | Citations to Sleep-EDF and methodology papers will be validated by Reference-Validator Agent. **Gating Mechanism**: A CI step (`ci.yml`) runs `reference_validator` before any merge or stage advancement. If any citation is `unreachable` or `mismatch`, the build fails and blocks progress. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw` with checksums recorded in `state/...yaml`; all transformations (filtering, segmentation) write to new files in `data/processed` with derivation hashes. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final report will be generated directly from `code/` outputs and stored in `data/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all artifacts (data, models, code) will be recorded. **Automated Trigger**: A CI script (`scripts/update-state-hash.sh`) runs on artifact changes to recalculate hashes and update the `state/...yaml` `updated_at` timestamp, invalidating stale review records as required. |
| **VI. EEG Signal Integrity** | **PASS** | Preprocessing pipeline (interpolation → bandpass → notch) implemented as immutable stages; raw signal never modified in place; transition windows mathematically traceable to original annotations. |
| **VII. Computational Constraints** | **PASS** | Model architecture (1D-CNN) strictly validated for ≤100k parameters. **Enforcement**: `tests/contract/test_constraints.py` is integrated into the GitHub Actions workflow (`ci.yml`) to fail the build if parameter count or memory usage predictions exceed limits. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-sleep-transitions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # PhysioNet download & checksum
│   ├── preprocess.py        # Interpolation, filtering, segmentation
│   └── loader.py            # Dataset loading utilities
├── features/
│   ├── extraction.py        # Time, freq, non-linear features
│   └── stats.py             # Cluster-based permutation tests
├── models/
│   ├── architecture.py      # Lightweight 1D-CNN definition
│   ├── train.py             # Training loop (CPU) with LOSO CV
│   └── validate.py          # Held-out subject validation
├── utils/
│   ├── config.py            # Paths, seeds, hyperparameters
│   └── logging.py           # Logging & metrics tracking
└── main.py                  # Pipeline orchestrator

tests/
├── contract/
│   ├── test_schemas.py      # Validate data against YAML schemas
│   └── test_constraints.py  # Verify param count & memory limits (Gated in CI)
├── integration/
│   └── test_pipeline.py     # End-to-end run on small subset
└── unit/
    ├── test_preprocess.py
    ├── test_features.py
    └── test_model.py

data/
├── raw/                     # Downloaded Sleep-EDF files (checksummed)
├── processed/               # Filtered, segmented, feature vectors (Parquet/NPY)
└── interim/                 # Temporary intermediate files
```

**Structure Decision**: Single project structure selected to minimize overhead and align with the computational nature of the pipeline. All modules are organized by function (data, features, models) to ensure modularity and testability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| None | The project adheres strictly to the "lightweight" constraint (≤100k params, CPU-only) and the single-source-of-truth principle. No unnecessary complexity is introduced. | N/A |

## Methodological Safeguards (Addressing Panel Concerns)

1.  **Temporal Separation**: To prevent tautological validation, the model input window **ends 30 seconds before** the annotated transition. The target is "Will a transition occur in the next 30s?", not "Is this a transition?".
2.  **Decoupled Analysis**: Statistical tests (Cluster-Based Permutation) are performed for exploratory insight but do **not** gate the model training. The model uses all features (or raw signal) to avoid underpowered filtering.
3.  **Robust Validation**: Model validation uses **Leave-One-Subject-Out (LOSO)** cross-validation to ensure generalizability to unseen subjects, with strict regularization (Dropout, L2) to prevent overfitting on the small N (~40 subjects).
4.  **Class Imbalance**: Statistical tests use stratified permutation to handle the rarity of transition windows compared to stable epochs.
