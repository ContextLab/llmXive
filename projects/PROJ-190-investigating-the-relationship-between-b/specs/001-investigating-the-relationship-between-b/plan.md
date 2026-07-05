# Implementation Plan: Brain Network Efficiency and Fluid Intelligence

**Branch**: `001-brain-network-efficiency-fluid-intelligence` | **Date**: 2024-01-15 | **Spec**: `specs/001-brain-network-efficiency-fluid-intelligence/spec.md`
**Input**: Feature specification from `specs/001-brain-network-efficiency-fluid-intelligence/spec.md`

## Summary

This project implements a computational pipeline to investigate the associational relationship between brain network efficiency (global and frontoparietal) and fluid intelligence using the Human Connectome Project (HCP) large-scale release. The technical approach involves downloading preprocessed fMRI data, applying specific nuisance regression and band-pass filtering, parcellating using the Schaefer atlas (and 400 ROIs), computing graph efficiency metrics on thresholded binary and weighted graphs, and performing statistical analysis (correlation and multiple regression) with rigorous family-wise error correction via permutation testing. All analysis is constrained to run on CPU-only CI (GitHub Actions free-tier) with a reasonable time limit and ~7GB RAM, requiring dataset sampling if necessary.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `requests`, `tqdm`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results/`) with checksums recorded in `state/*.yaml` as the Single Source of Truth (Constitution Principle III).  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete full pipeline (or sampled subset) within 6 hours; memory usage < 7GB. Adaptive sampling: Target N=500, fallback to N=200 if runtime > 4 hours. Permutation count: a sufficient number of permutations to ensure feasibility.  
**Constraints**: No GPU; no deep learning training; strict adherence to HCP preprocessing; CPU-tractable permutation testing (a feasible number of permutations); sampling to ≤200 subjects if time limit breached.  
**Scale/Scope**: Up to 1200 subjects (potentially sampled to 500 or 200); -ROI and -ROI parcellations; 2 primary hypothesis tests (Global/FP on A binary representation of a fixed number of ROIs.).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/` will pin seeds; `requirements.txt` pins versions; data fetched from canonical HCP source (or mock for CI). |
| **II. Verified Accuracy** | **PASS** | Citations (NIH Toolbox, Yeo-7, Schaefer) will be validated by the Reference-Validator Agent against primary sources, ensuring Title Token Overlap ≥ `CITATION_TITLE_OVERLAP_THRESHOLD`. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations written to new files; checksums recorded in `state/*.yaml`; PII scan passed. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; `state/*.yaml` `updated_at` timestamp updated on every artifact change as required by the Constitution. |
| **VI. Neuroimaging Data Integrity** | **PASS** | HCP 1200 release used; nuisance regression + band-pass (low-frequency cutoff to a low frequency) implemented as specified. |
| **VII. Graph-Theoretical Consistency** | **PASS** | Primary analysis: 200-ROI, [deferred] density, binary graphs. Robustness: 400-ROI, weighted graphs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-brain-network-efficiency-fluid-intelligence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-190-investigating-the-relationship-between-b/
├── data/
│   ├── raw/             # Downloaded HCP data (checksummed)
│   └── processed/       # Preprocessed time series, matrices
├── code/
│   ├── __init__.py
│   ├── download.py      # FR-001: HCP data acquisition
│   ├── preprocess.py    # FR-002: Nuisance regression, band-pass, FD calc
│   ├── graph_metrics.py # FR-003, FR-004, FR-012, FR-013: Parcellation, efficiency
│   ├── stats.py         # FR-005, FR-006, FR-007, FR-009: Correlation, regression, permutations, VIF
│   └── main.py          # Orchestrator
├── tests/
│   ├── unit/
│   └── integration/
├── results/
│   ├── figures/
│   └── reports/
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data processing and statistical analysis, facilitating reproducibility on CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Permutation Testing (1,000)** | FR-007 requires FWE correction. A large-scale sample size is infeasible on 2-CPU CI; 1,000 is the feasible maximum for N=500. | Parametric approximations (e.g., Bonferroni) are less powerful for dependent tests; A sufficient number of permutations is the best feasible approximation for FWE. |
| **Two Atlas Resolutions** | FR-012 requires robustness check with 400-ROI. | Single resolution risks parcellation-specific artifacts; robustness check ensures findings are not atlas-dependent. |
| **Adaptive Sampling** | FR-011 requires sampling if >6h runtime. | Fixed 1200-subject run risks CI timeout; adaptive sampling (N=500 -> N=200) ensures completion within constraints. |
| **Disconnected Components** | Negative edges only can cause disconnection. | Standard global efficiency fails on disconnected graphs; harmonic mean efficiency handles infinite path lengths. |
| **Edge Sign Robustness** | Discarding negative edges may bias results. | Absolute value graphs provide a sensitivity check for edge sign handling. |