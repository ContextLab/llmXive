# Implementation Plan: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Branch**: `001-visual-search-emotional-faces` | **Date**: 2025-01-15 | **Spec**: `specs/001-visual-search-emotional-faces/spec.md`
**Input**: Feature specification from `specs/001-visual-search-emotional-faces/spec.md`

## Summary

This project implements a reproducible, CPU-tractable pipeline to investigate the **association** between visual search strategies (global vs. local) and attentional capture by emotional faces using eye-tracking data. The technical approach involves: (1) acquiring and validating public eye-tracking datasets; (2) extracting fixation metrics (duration, saccade amplitude) relative to predefined ROIs (eyes, mouth) or a generic face grid; (3) classifying participants into processing strategies via k-means clustering with robustness checks (silhouette scores, sensitivity analysis), while prioritizing a continuous fixation ratio for primary modeling to avoid circularity; (4) fitting linear mixed-effects models (LMM) to test associational effects on detection time; and (5) performing a priori and post-hoc power analysis and multiple-comparison corrections. All components are constrained to run on GitHub Actions free-tier runners (CPU-only, limited RAM).

**Key Methodological Correction**: To address concerns about circularity and triviality, the primary statistical predictor will be the **continuous ratio of eye-to-mouth fixation time**, not a binary cluster label. The cluster label will be used for descriptive purposes and visualization only. The analysis will include a permutation test to ensure the association is non-trivial.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `datasets` (HuggingFace), `joblib`, `scipy`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`)  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete analysis within 6 hours; memory usage < 7GB; no GPU dependencies.  
**Constraints**: No CUDA, no quantization, no deep learning training. All models must be CPU-compatible. Data sampling may be applied if dataset size exceeds memory limits.  
**Scale/Scope**: Targeting [deferred] participants (see `research.md` for dataset selection criteria); analysis limited to available emotion categories in source datasets.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | All code pinned in `requirements.txt`; random seeds set in `code/`; datasets fetched from canonical HuggingFace sources. |
| **II. Verified Accuracy** | PASS | `Reference-Validator Agent` integrated as a CI gate; title overlap threshold ≥0.7 enforced before analysis proceeds. |
| **III. Data Hygiene** | PASS | Raw data checksummed in `state/`; transformations produce new files; PII scan integrated into CI. |
| **IV. Single Source of Truth** | PASS | All statistics trace to `data/processed/`; figures generated from code, not hand-typed. |
| **V. Versioning Discipline** | PASS | `hash_artifacts.py` script runs in CI to generate SHA-256 hashes for all `data/` and `code/` artifacts, updating `state/` with `updated_at` timestamp. |
| **VI. Measurement Synchronization** | PASS | Fixation patterns and response times recorded in same session log; millisecond precision enforced in data model. |
| **VII. Operational Strategy Definition** | PASS | 'Holistic' and 'feature-based' strategies implemented as distinct code paths: `code/analysis/strategy_classifier.py::classify_holistic()` and `classify_feature_based()`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-search-emotional-faces/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── sensitivity_report.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-290-the-impact-of-visual-search-strategies-o/
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── download.py
│   │   └── validate.py
│   ├── features/
│   │   ├── extraction.py
│   │   └── classification.py
│   ├── analysis/
│   │   ├── strategy_classifier.py   # Contains classify_holistic() and classify_feature_based()
│   │   ├── lmm.py
│   │   └── power.py
│   ├── utils/
│   │   ├── logging.py
│   │   ├── diagnostics.py
│   │   └── hash_artifacts.py        # Implements Constitution Principle V
│   └── validation/
│       └── reference_validator.py   # Implements Constitution Principle II
├── data/
│   ├── raw/
│   └── processed/
├── results/
│   ├── figures/
│   ├── reports/
│   └── sensitivity_report.yaml      # Output of SC-006
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure selected to maintain modularity while ensuring reproducibility. All data processing, feature extraction, and modeling are encapsulated in dedicated modules under `code/`. This aligns with the "Reproducibility" principle by isolating dependencies and ensuring isolated virtualenv execution.

## Implementation Tasks

### Phase 1: Data Acquisition and Validation

**Task 1.1: Dataset Search and Download**
- Search HuggingFace for datasets with 'eye-tracking', 'face', and 'emotion' keywords.
- Download the first dataset that contains `gaze_coordinates`, `response_times`, `emotion_labels`.
- If `roi_annotations` are missing, apply a **Generic ROI Fallback**: split the face image into a 3x3 grid and define 'eye' as the top-center and 'mouth' as the bottom-center regions.
- Implement retry logic with exponential backoff (1s, 2s, 4s) for network failures (FR-002).

**Task 1.2: Data Validation**
- Validate the presence of critical variables (`gaze_coordinates`, `response_times`, `emotion_labels`, `roi_annotations` or generic fallback).
- **HALT** execution and log a specific error if any critical variable is missing (FR-009).
- Exclude participants with >20% missing gaze data; document exclusion rate.

### Phase 2: Feature Extraction and Strategy Classification

**Task 2.1: Fixation Metric Extraction**
- Compute fixation duration on eye and mouth regions (or generic ROI), saccade amplitude, and dispersion for each trial (FR-003).
- Output features in `data/processed/features.csv`.

**Task 2.2: Continuous Predictor Calculation**
- Calculate the **continuous ratio** of eye-to-mouth fixation time for each participant. This will be the primary predictor for the LMM to avoid circularity.

**Task 2.3: Strategy Classification (Exploratory)**
- Attempt k-means clustering (k=2) on fixation distribution features (FR-004).
- Calculate silhouette scores; if < 0.25, log a warning and proceed with descriptive statistics only.
- **Bootstrap Stability Check**: Repeat clustering on multiple bootstrap samples to assess label stability (replaces invalid k-fold CV for unsupervised clustering).

**Task 2.4: Sensitivity Analysis**
- Sweep k over a small set of integer values greater than 1. and report how cluster composition and **model coefficients** (from a secondary model using cluster labels) vary (FR-010, SC-006).
- Output `results/sensitivity_report.yaml`.

### Phase 3: Statistical Analysis

**Task 3.1: Linear Mixed-Effects Modeling**
- Fit an LMM with detection time as outcome and **continuous fixation ratio** as the fixed effect, participant as random intercept (FR-006).
- Include a **Permutation Test**: permute detection times relative to fixation patterns repeatedly to establish a null distribution and ensure non-triviality (Scientific Soundness).
- If the model fails to converge, fallback to a simpler linear model.

**Task 3.2: Multiple Comparison Correction**
- Apply Bonferroni or Benjamini-Hochberg correction at α=0.05 if >1 hypothesis test is performed (FR-007).

**Task 3.3: Power Analysis**
- Perform **a priori** power analysis based on literature effect sizes (d=0.5) to estimate required sample size.
- Perform post-hoc power analysis for the actual sample size; document if <0.80 (FR-008).

### Phase 4: Reporting and Validation

**Task 4.1: Verified Accuracy Gate**
- Run `Reference-Validator Agent` to validate all citations in the report against primary sources.
- Enforce title overlap threshold ≥0.7. If validation fails, halt and report.

**Task 4.2: Versioning and Hashing**
- Run `hash_artifacts.py` to generate SHA-256 hashes for all `data/` and `code/` artifacts.
- Update `state/` file with `updated_at` timestamp and artifact hashes (Constitution Principle V).

**Task 4.3: Final Report Generation**
- Generate final report with all statistics, figures, and limitations (including observational nature and dataset constraints).

## Complexity Tracking

> No violations detected in Constitution Check; complexity is minimal and justified by the research requirements.

## Risk Mitigation

- **Circularity**: Addressed by using continuous fixation ratio as primary predictor and permutation testing for non-triviality.
- **Dataset Unavailability**: Addressed by Generic ROI Fallback and explicit HALT on missing critical variables.
- **Clustering Instability**: Addressed by Bootstrap Stability Check and sensitivity analysis.
- **Underpowered Study**: Addressed by a priori power analysis and explicit documentation of limitations.
- **Causal Claims**: Addressed by reframing all results as associational.