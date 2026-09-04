# Implementation Plan: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Branch**: `001-temporal-prediction-errors` | **Date**: 2026-06-27 | **Spec**: `specs/001-neural-correlates-of-temporal-prediction/spec.md`
**Input**: Feature specification from `specs/001-neural-correlates-of-temporal-prediction/spec.md`

## Summary

This project implements a reproducible EEG analysis pipeline to investigate the neural correlates of temporal prediction errors (Mismatch Negativity, MMN) in auditory scene analysis. The system downloads a publicly available EEG dataset, preprocesses it (filtering, ICA, re-referencing), segments epochs, and computes MMN metrics (amplitude, latency) for both simple oddball and complex auditory scene conditions. Statistical comparisons (interaction effects via Linear Mixed Models or Two-Way ANOVA) and visualizations (ERP waveforms, topographies) are generated to test the hypothesis that prediction error signatures scale with scene complexity.

**Critical Constraint**: The pipeline strictly requires a dataset containing *independent* "simple" and "complex" experimental conditions. If the dataset lacks a valid "complex" condition (i.e., if "complex" is merely a heuristic mapping of "deviant" trials), the pipeline **MUST HALT** with a specific error. Synthetic data is permitted *only* for unit-testing code logic, never for scientific results.

**Note on Spec Conflict (Flagged for Kickback)**: The original specification (FR-007) mandates a heuristic fallback. However, methodological review confirms this creates circular logic (mapping 'deviant' to 'complex'). This plan overrides that requirement to ensure scientific validity: the pipeline **HALTS** if the 'complex' condition is not an independent experimental variable. The specification must be updated to reflect this correction.

**Note on Dataset Conflict (Flagged for Kickback)**: The original specification assumes OpenNeuro ds000246 contains both conditions. This plan identifies ds000246 as lacking the 'complex' condition. The pipeline **HALTS** if no alternative dataset with both conditions is found. The specification must be updated to reflect this data constraint.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne` (>=1.7.0), `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `requests`  
**Storage**: Local filesystem (`data/` for raw/processed files, `results/` for outputs)  
**Testing**: `pytest` (contract tests against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`, unit tests for preprocessing logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU cores, ~7 GB RAM)  
**Project Type**: Data Science / Computational Neuroscience Pipeline  
**Performance Goals**: Process dataset within 6 hours; memory usage < 7 GB via streaming/sampling if necessary.  
**Constraints**: CPU-only execution (no local GPU); strict adherence to OpenNeuro BIDS format; no modification of raw data in place.  
**Scale/Scope**: Single dataset processing; analysis of a cohort of subjects; A large array of electrodes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pinning, random seed setting, and CI re-runs. |
| **II. Verified Accuracy** | **PASS** | **Verified Accuracy Workflow** defined below: Agent fetches dataset URL, checks against `# Verified datasets` block, validates checksum, logs status. The Reference-Validator Agent runs at three points: (1) On every artifact write that introduces or modifies citations, (2) Inside the Advancement-Evaluator before awarding any review point, (3) As a blocking gate on the `research_review` → `research_accepted` transition. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivatives checksummed; PII scan mandated. |
| **IV. Single Source of Truth** | **PASS** | Pipeline outputs (CSV/JSON) will be the sole source for paper figures; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded explicitly in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` upon generation. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. |
| **VI. Neurophysiological Signal Integrity** | **PASS** | Preprocessing steps (low-frequency cutoff, ICA, mastoid re-reference) are hardcoded; epoch window (pre-stimulus to post-stimulus) fixed. |
| **VII. Statistical Rigor** | **PASS** | Interaction tests (ANOVA/LMM) and FDR correction (Benjamini-Hochberg) are mandatory. |

### Verified Accuracy Workflow
To satisfy Constitution Principle II, the following automated workflow is implemented:
1.  **Fetch**: The `download.py` script retrieves the dataset URL.
2.  **Validate**: The script checks the URL against the `# Verified datasets` block in `research.md`.
3.  **Checksum**: The script computes the SHA-256 hash and compares it against the known-good hash (if available) or logs the hash for `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` recording.
4.  **Log**: The status (Valid/Invalid) is recorded in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml`.
5.  **Gate**: The Reference-Validator Agent runs at three points (artifact write, advancement evaluation, stage transition) to ensure no unreachable or mismatched citations exist.

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-correlates-of-temporal-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-250-neural-correlates-of-temporal-prediction/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download.py           # Implements FR-001, Verified Accuracy Workflow
│   ├── preprocess.py         # Implements FR-002, FR-003
│   ├── analysis.py           # Implements FR-004, FR-005 (Interaction Tests)
│   ├── visualize.py          # Implements FR-006
│   └── main.py               # Orchestration script
├── data/
│   ├── raw/                  # Downloaded BIDS dataset (checksummed)
│   └── processed/            # Epochs, ICA components (checksummed)
├── results/
│   ├── metrics.csv           # MMN amplitude/latency table
│   ├── stats.json            # Interaction test results, p-values, effect sizes
│   └── figures/              # PNG/SVG outputs
└── specs/001-neural-correlates-of-temporal-prediction/
    └── ... (this feature spec)
```

**Structure Decision**: Single project structure with distinct `code/`, `data/`, and `results/` directories to enforce separation of concerns and data hygiene (Constitution Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The pipeline is linear and modular. | A single script would violate "Data Hygiene" by mixing download, processing, and analysis logic, making reproducibility harder to audit. |

## Critical Path & Assumptions

- **Assumption**: The selected dataset contains *independent* "simple" and "complex" experimental conditions.
- **Assumption**: If the dataset (e.g., ds000246) lacks the "complex" condition, the system **halts** (FR-008). It does *not* attempt to synthesize "complex" from "deviant" trials, as this creates a circular logic (stimulus type vs. condition complexity).
- **Assumption**: A canonical MMN topography template exists or can be derived from a verified source (not ds000246 for complex condition) for SC-004.
- **Assumption**: The heuristic fallback (FR-007) is scientifically invalid and is overridden by this plan's HALT condition. (Spec must be updated).
- **Assumption**: The dataset ds000246 is insufficient for the full hypothesis and must be replaced by a dataset with both conditions. (Spec must be updated).

## Data Availability & Compute Feasibility

- **Dataset Strategy**: Only use datasets with verified URLs that contain both "simple" and "complex" conditions. If none are found, the pipeline halts.
- **Compute**: CPU-first. MNE-Python and statsmodels are optimized for CPU. Data will be processed in chunks or streamed if the dataset > 7 GB. No GPU required for MMN analysis.
- **Feasibility**: The pipeline is designed to run within the 6-hour limit on a GitHub Actions free-tier runner (2 CPU, ~7 GB RAM).