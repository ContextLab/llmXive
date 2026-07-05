# Implementation Plan: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Branch**: `001-cognitive-fatigue-eeg-complexity` | **Date**: 2026-06-28 | **Spec**: [link]
**Input**: Feature specification from `specs/001-cognitive-fatigue-eeg-complexity/spec.md`

## Summary

This project implements a reproducible pipeline to investigate the association between resting-state EEG complexity (Lempel-Ziv complexity and Permutation Entropy) and subjective cognitive fatigue. The technical approach involves downloading public EEG and fatigue datasets, preprocessing signals using MNE-Python (1-40 Hz bandpass, artifact rejection), extracting non-linear complexity metrics, and performing correlation analyses with Benjamini-Hochberg correction. The pipeline is constrained to CPU-only execution with strict memory (≤7 GB) and runtime (≤6 h) limits.

Crucially, the analysis design is conditional: it first verifies if the dataset contains paired pre/post resting-state segments. If so, it uses an ANCOVA approach (Post ~ Pre + Fatigue) to avoid collinearity. If only single-timepoint data exists, it pivots to a cross-sectional analysis (Baseline Complexity vs. Baseline Fatigue).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `scikit-learn`, `numpy`, `pandas`, `lempel-ziv-complexity`, `scipy`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`), Parquet/CSV formats  
**Testing**: `pytest` (unit tests for signal processing, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: vCPU, 7 GB RAM, no GPU)  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline  
**Performance Goals**: Runtime ≤ 6 hours for N=30; Memory ≤ 7 GB  
**Constraints**: No GPU/CUDA; strict variable validation before analysis; all steps reproducible with pinned seeds.  
**Scale/Scope**: Single cohort analysis (N≈), resting-state segments (≥120s), Multiple EEG channels.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Plan / Justification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All code will use pinned random seeds (`np.random.seed`, `random.seed`). External data sources will be fetched via verified URLs. `requirements.txt` will pin all versions. The `lempel-ziv-complexity` library is designated as the SSoT for LZC calculation. |
| **II. Verified Accuracy** | **PASS** | The Reference-Validator Agent runs on every artifact write to verify citations against primary sources before they contribute to the plan. Dataset URLs are strictly limited to the "Verified datasets" block. |
| **III. Data Hygiene** | **PASS** | Raw data will be downloaded to `data/raw` and checksummed. Derived data (preprocessed, features) will be written to `data/processed` with new filenames. No in-place modification. PII scan will be run. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `data/processed` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be tracked with content hashes in the project state YAML. The `state/projects/PROJ-470...yaml` file will be updated with `updated_at` timestamps upon any artifact change, and the Advancement-Evaluator Agent will invalidate stale records. |
| **VI. EEG Signal Processing** | **PASS** | Pipeline will use MNE-Python. Bandpass filtering within the lower frequency range.. Artifact rejection at ±100 µV. Average re-referencing. Configuration parameters stored in a config file. |
| **VII. Statistical Transparency** | **PASS** | Correlation analysis will report Pearson/Spearman, p-values, CIs. Confounds will be controlled if available; otherwise, limitations will be explicitly stated. ANCOVA or cross-sectional models used to avoid collinearity. Benjamini-Hochberg correction applied. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cognitive-fatigue-eeg-complexity/
├── plan.md              # This file (Phase 0)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created after research complete)
```

### Source Code (repository root)

```text
projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
├── data/
│   ├── raw/             # Downloaded raw EEG and fatigue data (checksummed)
│   └── processed/       # Preprocessed signals, extracted features, analysis results
├── code/
│   ├── config.yaml      # Pipeline parameters (filter cutoffs, thresholds, seeds)
│   ├── requirements.txt # Pinned dependencies
│   ├── download.py      # Data retrieval script
│   ├── preprocess.py    # MNE-Python preprocessing (filtering, artifact rejection)
│   ├── features.py      # Complexity metric extraction (LZC, PE)
│   ├── analysis.py      # Correlation, correction, sensitivity analysis
│   └── report.py        # Report generation
├── tests/
│   ├── unit/            # Unit tests for signal processing logic
│   └── integration/     # End-to-end pipeline tests on sample data
└── docs/
    └── ...
```

**Structure Decision**: Single project structure chosen for simplicity and reproducibility. All processing steps are linear and script-based, avoiding complex microservices or web frontends. This aligns with the computational nature of the task and the CI constraints.

## Complexity Tracking

*No violations found. The plan adheres strictly to the spec and constitution.*