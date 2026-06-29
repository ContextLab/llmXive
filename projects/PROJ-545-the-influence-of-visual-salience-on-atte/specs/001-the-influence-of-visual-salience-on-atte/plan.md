# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Branch**: `001-visual-salience-aDDM` | **Date**: 2026-06-25 | **Spec**: `specs/001-visual-salience-aDDM/spec.md`
**Input**: Feature specification from `specs/001-visual-salience-aDDM/spec.md`

## Summary

This feature implements a computational study testing whether visual salience modulates attentional drift patterns in the attentional drift diffusion model (aDDM) applied to moral dilemma choices. The technical approach involves ingesting the Moral Machine dataset, computing visual/textual salience scores, fitting a choice-only aDDM variant via grid search on CPU, and comparing against a baseline model using AIC/BIC with multiple-comparison correction.

**Critical Limitation**: The aDDM implementation is a choice-only variant without response time (RT) data, as the Moral Machine dataset contains choice outcomes only. This constrains parameter identifiability and is explicitly acknowledged as a methodological limitation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: numpy, scipy, pandas, opencv-python, scikit-learn, numba (for CPU vectorization)  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: pytest (contract tests against schemas)  
**Target Platform**: Linux (GitHub Actions Free Runner: 2 CPU, 7 GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Grid search convergence ≤ 30 mins on 2-core CPU; Salience computation ≤ 30 mins for subset.  
**Constraints**: No GPU/CUDA; No deep learning training; Memory ≤ 7 GB; Observational framing only.  
**Scale/Scope**: Up to 50,000 rows (subset to [deferred] for grid search optimization).
**Convergence Target**: ≥ 95% of 5-fold cross-validation splits must converge within 30 minutes (SC-002).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. Data checksummed. Dataset verification gap documented per Constitution Principle I. |
| **II. Verified Accuracy** | **PASS** | Citations validated via Reference-Validator Agent. Moral Machine dataset URL flagged as unverified in `research.md` per system constraints. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations in new files. PII scan required on commit. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/` rows and `code/` blocks. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`. `updated_at` timestamps updated on artifact change. |
| **VI. Construct Operationalization** | **PASS** | Salience (ITTI/GBVS + text heuristics) and aDDM params defined in `code/` before analysis. |
| **VII. Ethical Use** | **PASS** | No PII extracted. Aggregated metrics only. Compliance with dataset license. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-salience-aDDM/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-545-the-influence-of-visual-salience-on-atte/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py       # Ingest Moral Machine (FR-001)
│   │   ├── salience.py       # Compute ITTI/GBVS + Text (FR-002)
│   │   └── preprocess.py     # Subsetting & Cleaning
│   ├── models/
│   │   ├── addm.py           # aDDM Implementation (FR-003)
│   │   └── fit.py            # Grid Search (FR-004)
│   ├── analysis/
│   │   ├── compare.py        # Model Comparison (FR-005, FR-007)
│   │   └── diagnostics.py    # VIF & Collinearity (FR-008)
│   └── main.py
├── data/
│   ├── raw/                  # Raw downloads (checksummed)
│   └── processed/            # Derived CSV/Parquet
├── tests/
│   ├── contract/             # Schema validation
│   └── unit/                 # Logic tests
└── paper/                    # Drafts (SSO-T)
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize overhead for computational research. Matches Constitution Principle I (Reproducibility) by keeping all artifacts in one repo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Grid Search vs. Optimization** | Spec requires grid search (FR-004). | Gradient descent is unstable for aDDM likelihood surfaces; grid search ensures robustness within CPU limits. |
| **Subsampling for Fit** | 50k rows may exceed 30-min CPU limit for grid steps. | Full fit on 50k rows risks timeout; stratified sample guarantees US-002 convergence. |
| **Choice-Only aDDM** | RT data unavailable in dataset. | Full aDDM requires RT; choice-only variant is the only feasible option given data constraints. |
| **5-Fold CV Requirement** | SC-002 mandates ≥95% convergence rate. | Single split insufficient; 5-fold CV measures generalizability and convergence stability. |

