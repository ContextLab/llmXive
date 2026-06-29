# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Branch**: `001-visual-salience-aDDM` | **Date**: 2026-06-25 | **Spec**: `specs/001-visual-salience-aDDM/spec.md`
**Input**: Feature specification from `/specs/001-visual-salience-aDDM/spec.md`

## Summary

This project implements a computational analysis to test whether text-based salience systematically modulates attentional drift patterns in moral decision-making using the text-only Moral Machine dataset. The approach ingests the dataset, computes text-salience scores (as visual salience is not applicable), fits an attentional Drift Diffusion Model (aDDM) using nested numerical optimization and grid search on CPU, and compares the salience-augmented model against a baseline via permutation testing. All findings are framed as associational correlations, avoiding causal claims, and robustness is ensured via sensitivity analysis on the salience weight parameter and collinearity diagnostics.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-learn` (for VIF and residualization), `requests`, `tqdm`  
**Storage**: Local filesystem (`data/` for raw/processed CSVs, `code/` for scripts)  
**Testing**: `pytest` (unit tests for salience calculation, integration tests for model convergence)  
**Target Platform**: GitHub Actions Free Runner (2 CPU, 7 GB RAM, 14 GB Disk, No GPU)  
**Project Type**: Computational Research / Data Analysis  
**Performance Goals**: Salience computation ≤ 30 minutes (subset); Model convergence ≥ 95% of splits within 30 minutes; Total runtime ≤ 6 hours.  
**Constraints**: No GPU/CUDA; No deep learning training; Dataset subset ≤ 5,000 rows (reduced from 50k for feasibility); Memory usage < 7 GB; Strict adherence to spec-defined thresholds ({0.01, 0.05, 0.10}) for salience weight sensitivity analysis.  
**Scale/Scope**: [deferred] moral dilemma scenarios; Grid search over multiple salience weights; -fold cross-validation.

> Dataset subset size reduced to [deferred] rows to ensure aDDM fitting completes within 30 minutes on a 2-CPU runner. This reduces statistical power but ensures feasibility.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in all scripts (`np.random.seed(42)`). Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | All dataset citations in `research.md` restricted to the "Verified datasets" block (Awad et al. 2018). No external URLs invented. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations (salience scores) written to new files with checksums recorded in state. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in paper trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes updated on every data/code change; `updated_at` timestamps managed by state agent. |
| **VI. Construct Operationalization** | **PASS** | Salience metrics (text-heuristic only) and aDDM parameters defined in `research.md` before analysis. No unapproved constructs (e.g., "System 1/2") used. |
| **VII. Ethical Use of Human Decision Data** | **PASS** | Dataset used per license; no PII extracted; only aggregated metrics used. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-salience-aDDM/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
projects/PROJ-545-the-influence-of-visual-salience-on-atte/
├── data/
│   ├── raw/                  # Original Moral Machine dump (or subset)
│   └── processed/            # salience_enriched.csv, model_outputs.csv
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── ingest.py         # FR-001: Download & subset
│   │   ├── salience.py       # FR-002: Compute text-salience heuristics (image branch removed)
│   │   └── preprocess.py     # FR-008: Proxy variable selection, residualization
│   ├── models/
│   │   ├── aDDM.py           # FR-003: aDDM simulation (NumPy/SciPy)
│   │   └── fit.py            # FR-004: Nested grid search & convergence, 5-fold CV loop
│   ├── analysis/
│   │   ├── compare.py        # FR-003, FR-007: Model comparison (permutation test), Bonferroni logic
│   │   └── sensitivity.py    # FR-005: Salience weight sweep {0.01, 0.05, 0.10}
│   └── utils/
│       ├── diagnostics.py    # VIF calculation (threshold for multicollinearity detection), collinearity check
│       └── logging.py        # Error handling, retry caps (max 3)
└── tests/
    ├── unit/
    │   └── test_salience.py
    └── integration/
        └── test_convergence.py
```

**Structure Decision**: Single project structure chosen to minimize overhead and ensure all data flows directly from ingestion to analysis within the constrained CI environment. The separation of `data/`, `models/`, and `analysis/` ensures modularity while maintaining a linear execution path required for reproducibility.

## Specific Task Mappings

| Spec Requirement | Task Description | Script/Module |
| :--- | :--- | :--- |
| **FR-001** | Download and subset to [deferred] rows. | `code/data/ingest.py` |
| **FR-002** | Compute text-salience heuristics (word frequency/position). Image branch skipped. | `code/data/salience.py` |
| **FR-003** | Implement aDDM in NumPy/SciPy (float64). | `code/models/aDDM.py` |
| **FR-004** | Grid search over salience weights across a range of negative values with fine-grained steps with nested L-BFGS-B optimization for other parameters. | `code/models/fit.py` |
| **FR-005** | Sensitivity analysis: Sweep salience weight over {0.01, 0.05, 0.10}. | `code/analysis/sensitivity.py` |
| **FR-006** | Frame all findings as associational. | `code/analysis/compare.py` (reporting) |
| **FR-007** | Apply Bonferroni correction if number of tests > 3. | `code/analysis/compare.py` |
| **FR-008** | Detect absence of 'culpability' labels; use proxy attributes (species, age, lives). | `code/data/preprocess.py` |
| **SC-002** | 5-fold CV: Generate 5 folds, fit per fold, calculate `cv_convergence_rate`. | `code/models/fit.py` (main loop) |
| **SC-003** | Report sensitivity variation for {0.01, 0.05, 0.10}. | `code/analysis/sensitivity.py` |
| **SC-004** | VIF threshold 5.0; residualize if VIF > 5.0. | `code/utils/diagnostics.py` |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. The plan strictly adheres to spec constraints and avoids unapproved scope (e.g., no "Voluntary/Involuntary" tagging, no "System 1/2" proxies). | N/A |