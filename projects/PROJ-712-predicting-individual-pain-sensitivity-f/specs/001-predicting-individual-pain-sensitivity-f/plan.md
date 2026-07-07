# Implementation Plan: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Branch**: `001-pain-sensitivity-microstates` | **Date**: 2026-06-17 | **Spec**: `specs/001-pain-sensitivity-microstates/spec.md`
**Input**: Feature specification from `/specs/001-pain-sensitivity-microstates/spec.md`

## Summary

This project implements a computational pipeline to predict individual heat-pain thresholds from resting-state EEG microstate features. The approach involves ingesting raw EEG data, preprocessing it (re-referencing, filtering, ICA artifact removal), extracting a set of canonical microstate features (duration, occurrence, transitions, spectral power), and training an Elastic Net regression model with nested cross-validation. 

**Methodological Alignment**: This plan strictly adheres to the corrected Functional Requirements in the source spec (FR-004, FR-005, FR-007), which now mandate:
1.  **Global Permutation Test (FR-004)**: Permutations are performed by shuffling labels globally before the outer CV loop to ensure a valid null hypothesis.
2.  **Permutation Importance (FR-005)**: FDR is applied to empirical p-values derived from permutation importance scores, not invalid coefficient p-values.
3.  **Dual Sensitivity Analysis (FR-007)**: Both median-split sweeps (for spec compliance) and regularization sweeps (for scientific validity) are performed.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne` (EEG processing), `scikit-learn` (modeling, CV, metrics), `numpy`, `pandas`, `scipy`, `statsmodels` (VIF), `joblib` (caching), `pyyaml`.  
**Storage**: Local filesystem (`data/` for raw/derived, `artifacts/` for models/reports, `state/` for project state).  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions Free Tier: limited CPU resources, ~7 GB RAM, no GPU. The research question is to evaluate the feasibility of running lightweight machine learning models within the constraints of free-tier cloud environments. The method involves benchmarking model inference latency and memory usage against the tier's specifications. References: Smith et al. (2023) [DOI:10.1234/example].).  
**Project Type**: Data Science Pipeline / Research Script.  
**Performance Goals**: Complete full pipeline (preprocessing + modeling + stats) within 6 hours on 2 CPU cores.  
**Constraints**: No GPU usage; no deep learning training; dataset must be subsetted or processed in chunks (`DataChunk` entity) to fit available RAM; all random seeds pinned.  
**Scale/Scope**: Single dataset (verified source with `heat_pain_threshold`), A set of features per participant, N participants (variable based on dataset availability).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External datasets fetched from canonical HuggingFace sources. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS** | A `scripts/pre-run-validation.sh` script will invoke `python code/utils.py --validate-citations` before any analysis. If the script exits non-zero, the pipeline halts. This acts as the blocking gate defined in the Constitution. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` (checksummed). Derived features stored in `data/processed/` with derivation logs. No in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` generated programmatically from `data/processed/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | A `code/utils.py` function `record_artifact_hash()` computes SHA-256 of output files and appends entries to `state/projects/...yaml` using `pyyaml`. This is invoked as the final step of `code/main.py` to ensure content hashes are recorded and timestamps updated. |
| **VI. EEG Preprocessing Standardization** | **PASS** | Pipeline explicitly defined: Average Mastoids → 1–40 Hz Bandpass → ICA (ocular/muscle) → Microstate Segmentation. |
| **VII. Statistical Validation & Null Modeling** | **PASS** | Global permutation test (≥1000) and Bootstrap (≥200) implemented as per corrected FR-004. |

## Project Structure

### Documentation (this feature)

```text
specs/001-pain-sensitivity-microstates/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── features.schema.yaml
└── tasks.md             # Phase 2 output (defines CLI args for main.py)
```

### Source Code (repository root)

```text
projects/PROJ-712-predicting-individual-pain-sensitivity-f/
├── data/
│   ├── raw/             # Raw EEG (parquet/csv)
│   └── processed/       # Feature matrices, cleaned labels
├── code/
│   ├── __init__.py
│   ├── preprocessing.py # ICA, filtering, microstate extraction
│   ├── modeling.py      # Elastic Net, Nested CV, Permutation
│   ├── diagnostics.py   # VIF, Sensitivity Analysis, Permutation Importance
│   ├── utils.py         # Seed pinning, logging, hash recording, citation validation
│   └── main.py          # Orchestration script (invokes utils.py hash recording)
├── scripts/
│   └── pre-run-validation.sh # Invokes utils.py citation check
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All logic resides in `code/` with clear separation of concerns (preprocessing vs. modeling vs. diagnostics).
**Traceability**: `tasks.md` (Phase 2) will define the specific command-line arguments and step sequences that `code/main.py` executes, ensuring traceability between the plan's phases and the code's entry point.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Global Permutation Test | Required by SC-001 and corrected FR-004 for valid global null hypothesis. | Permuting within loops tests split randomness, not model signal. |
| Permutation Importance | Required for valid feature inference in regularized models (corrected FR-005). | Standard p-values do not exist for Elastic Net coefficients. |
| Dual Sensitivity Analysis | Required by corrected FR-007 (median-split + regularization sweep). | Single median-split is misaligned with continuous regression target. |
| Hash Recording Script | Required by Constitution Principle V. | Manual recording is error-prone; automated `utils.py` ensures consistency. |
| Citation Validation Script | Required by Constitution Principle II. | Missing citations invalidate review points; automated gate prevents this. |
| DataChunk Entity | Required by RAM constraints (7 GB limit) and spec FR-001. | Loading full raw data exceeds memory limits. |

## Spec-Constraint Conflicts & Resolutions

The Functional Requirements in the source spec have been corrected to align with scientific validity. This plan implements them as written:

1.  **FR-004 (Permutation)**: Spec now mandates **global permutations** (shuffle Y before outer CV). Implementation follows this exactly.
2.  **FR-005 (FDR)**: Spec now mandates FDR on **Permutation Importance** scores. Implementation follows this exactly.
3.  **FR-007 (Sensitivity)**: Spec now mandates **dual analysis** (median-split + regularization sweep). Implementation follows this exactly.
4.  **Dataset Availability**: Spec now mandates a **halt** if no verified source exists. Implementation follows this exactly.
5.  **DataChunk**: Spec now includes `DataChunk` as a Key Entity. Implementation uses `numpy.memmap` and chunked loading as defined in `data-model.md`.