# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Branch**: `518-brain-dynamics-creativity` | **Date**: 2026-06-25 | **Spec**: `specs/518-brain-dynamics-creativity/spec.md`
**Input**: Feature specification from `/specs/518-brain-dynamics-creativity/spec.md`

## Summary

This project implements a computational pipeline to investigate the relationship between dynamic reconfiguration of functional brain networks (specifically "flexibility") during rest and individual differences in **creative achievement** (measured by the Creative Achievement Questionnaire, CAQ). 

**Note on Construct Validity**: The original hypothesis mentioned "divergent thinking performance." However, the available data (CAQ) measures lifetime creative *achievements* (a trait), not real-time divergent *thinking* (a state). This plan explicitly tests the association between brain dynamics and creative *achievement*. The analysis will acknowledge this distinction as a limitation, as CAQ is a validated proxy but not a direct measure of the cognitive process.

The technical approach involves preprocessing resting-state fMRI data from the Human Connectome Project (HCP) via OpenNeuro, computing sliding-window functional connectivity, applying the Louvain community detection algorithm (with consensus clustering) to derive a flexibility metric, and testing its association with CAQ scores using a null-model-based statistical framework. The implementation is strictly constrained to run on CPU-only CI environments (GitHub Actions free tier).

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: `nilearn` (fMRI preprocessing/connectivity), `networkx` (graph analysis/Louvain), `scikit-learn` (regression/metrics), `numpy`, `pandas`, `matplotlib`, `scipy`, `brainconn` (for consensus clustering).
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/interim/`); no external database.
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions runner: CPU cores, ~7 GB RAM, no GPU).
**Project Type**: Computational Neuroscience Pipeline / CLI Tool.
**Performance Goals**: Complete full pipeline (preprocessing + analysis + visualization) within 6 hours on 2 cores; memory usage < 7 GB; plot file size < 5 MB.
**Constraints**: No GPU/CUDA; no large model training; strict adherence to HCP data availability (CAQ proxy); robust error handling for missing data/motion artifacts.
**Scale/Scope**: Subset of HCP participants (target ~, dynamically sampled to fit RAM); A set of ROIs (HCP-MMP atlas); sliding window lengths.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical OpenNeuro/HCP URLs; pipeline runs end-to-end in isolated venv. |
| **II. Verified Accuracy** | **Pass** | All citations (e.g., Louvain, CAQ validity) will be validated against primary sources before inclusion in `research.md`. |
| **III. Data Hygiene** | **Pass** | Raw data in `data/raw/` is immutable; checksums recorded in `data/checksums.json`; derived data in `data/processed/` with provenance logs. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` will be generated programmatically from `data/` artifacts; no hand-typed values. |
| **V. Versioning Discipline** | **Pass** | `code/utils/versioning.py` computes SHA-256 hashes for all artifacts and updates `state/projects/PROJ-518-investigating-the-relationship-between-b.yaml` automatically upon successful pipeline completion. |
| **VI. Neuroimaging Data Standardization** | **Pass** | Pipeline implements exact HCP-MMP atlas, -0.1 Hz band-pass, motion correction; versions and args logged in provenance files; data sourced from OpenNeuro. |
| **VII. Statistical Validation** | **Pass** | Regression includes covariates; significance assessed via a large number of permutations of the *outcome vector* (not full pipeline); effect sizes + CIs reported; deterministic seeds used. |

## Project Structure

### Documentation (this feature)

```text
specs/518-brain-dynamics-creativity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (schemas)
└── tasks.md             # Phase 2 output (generated later)
```
*Note: `tasks.md` remains in `specs/` as a planning artifact, distinct from the root-level `code/` and `data/` directories.*

### Source Code (repository root)

```text
projects/PROJ-518-investigating-the-relationship-between-b/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point (CLI)
│   ├── config.py               # Hyperparameters (window sizes, seeds)
│   ├── data/
│   │   ├── loader.py           # HCP data fetching & validation (FR-011)
│   │   └── preprocess.py       # fMRI preprocessing (FR-001)
│   ├── analysis/
│   │   ├── connectivity.py     # Sliding window & static strength (FR-002, FR-012)
│   │   ├── dynamics.py         # Louvain & Flexibility metric (FR-003, FR-004)
│   │   └── statistics.py       # Regression, Permutation, Sensitivity (FR-005, FR-006, FR-007, FR-010)
│   ├── viz/
│   │   └── plots.py            # Diagnostic & result visualizations (FR-008)
│   └── utils/
│       ├── logging.py          # Exclusion logging (FR-009)
│       └── versioning.py       # Hashing & State update (Principle V)
├── data/
│   ├── raw/                    # HCP raw files (immutable)
│   ├── processed/              # Preprocessed fMRI, matrices
│   ├── interim/                # Intermediate metrics
│   └── checksums.json          # Checksum registry for raw data (Principle III)
├── tests/
│   ├── unit/                   # Test metric calculations
│   ├── integration/            # Test pipeline flow
│   └── contract/               # Schema validation tests
├── docs/
│   └── outputs/                # Generated plots (PNGs)
└── requirements.txt            # Pinned dependencies
```

**Structure Decision**: Single project structure chosen to minimize overhead for a data-analysis pipeline. Separation of concerns (data, analysis, viz) ensures modularity and testability.

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  **CPU Constraints**: Using `nilearn` and `networkx` (CPU-optimized) instead of deep learning frameworks.
2.  **Memory Constraints**: Processing participants in batches and using memory-mapped arrays for fMRI data.
3.  **Data Validation**: Early exit (FR-011) prevents wasted compute on missing CAQ data.
4.  **Statistical Efficiency**: Permutation testing is performed on the outcome vector only, avoiding re-computation of fMRI metrics.