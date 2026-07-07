# Implementation Plan: Molecular Topology and Reaction Selectivity

**Branch**: `001-molecular-topology-selectivity` | **Date**: 2026-07-04 | **Spec**: `specs/001-molecular-topology-selectivity/spec.md`
**Input**: Feature specification from `specs/001-molecular-topology-selectivity/spec.md` (Verified Accuracy Gate: PASSED)

## Summary

This project investigates the relationship between molecular topology (Wiener, Balaban, Zagreb indices) and reaction selectivity (Theoretical Regioisomer Count) using the USPTO dataset. The technical approach involves ingesting USPTO data, filtering for Electrophilic Aromatic Substitution (EAS) reactions, computing topological descriptors via `rdkit`, and modeling the relationship using Ordinal Logistic Regression and Random Forest. 

**Critical Scope Clarification & Spec Revision Required**: 
1.  **Target Definition**: The "Regioisomer Diversity Count" is **not** an observed outcome in the USPTO-50k dataset (which is single-product). It is a **deterministic theoretical value** derived from the *reactant's* symmetry (number of non-equivalent substitution sites). The analysis tests whether global topological indices can serve as sufficient proxies for local symmetry constraints.
2.  **Model Validity**: Poisson Regression is scientifically invalid for this deterministic target. The primary models are **Ordinal Logistic Regression** and **Random Forest**. The spec's requirement for Poisson Regression (FR-004) and Zero-Inflated Poisson fallback (FR-007) contradicts the research reality and must be updated to reflect the deterministic nature of the target.
3.  **Synthetic Test Validity**: The synthetic test in User Story 3 (spec.md) generates data via `target ~ Poisson(exp(Xβ))`. This validates a stochastic premise that contradicts the deterministic reality of the target. The spec must be updated to use a deterministic step function or symmetry logic for synthetic testing to avoid false positives.

All findings are framed as **associational** only.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit` (chemistry), `pandas`, `scikit-learn`, `statsmodels`, `pyyaml`  
**Storage**: Local file system (CSV, Parquet) within `data/` directory  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Data analysis pipeline / Research prototype  
**Performance Goals**: Descriptor calculation < 15 mins; Full pipeline < 6 hours.  
**Constraints**: No GPU, no large LLMs, strict memory limits (7GB).  
**Scale/Scope**: ~50k raw reactions, filtered to EAS subset (expected N > 100).

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt` and random seeds in all modeling steps.
- **II. Verified Accuracy**: The input `spec.md` and all dataset URLs in the "Verified datasets" block have **already been validated** by the Reference-Validator Agent prior to this plan generation. No deferral is permitted.
- **III. Data Hygiene**: Plan includes checksumming of raw data and derived descriptor tables.
- **IV. Single Source of Truth**: Data model defines strict schemas; code will write to `data/`. The future paper **MUST reference the specific content hashes** of these files as recorded in the state file `state/projects/PROJ-083-investigating-the-relationship-between-m.yaml` to ensure traceability from figure to raw data row.
- **V. Versioning Discipline**: Artifacts will be versioned via content hashes in the state file `state/projects/PROJ-083-investigating-the-relationship-between-m.yaml`, updated by the **Advancement-Evaluator Agent**.
- **VI. Computational Resource Compliance**: Pipeline explicitly uses CPU-only libraries and includes logic to abort if memory/time limits are exceeded.
- **VII. Topological Descriptor Transparency**: Descriptors will be logged with `rdkit` version and parameters; output stored in `data/` with checksums.

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-topology-selectivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── descriptors.schema.yaml
│   ├── model_results.schema.yaml
│   ├── output.schema.yaml
│   └── ...
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-083-investigating-the-relationship-between-m/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingestion.py           # FR-001, FR-006
│   ├── descriptors.py         # FR-002
│   ├── modeling.py            # FR-004, FR-005, FR-007 (Updated for Ordinal/RF)
│   └── main.py                # Orchestrator
├── data/
│   ├── raw/                   # Downloaded USPTO files
│   ├── processed/             # Filtered EAS, descriptors
│   └── models/                # Saved model artifacts
├── tests/
│   ├── test_ingestion.py
│   ├── test_descriptors.py
│   └── test_modeling.py
└── docs/
    └── reports/               # Generated figures and tables
```

**Structure Decision**: Single project structure selected to maintain simplicity for a research pipeline. All logic resides in `code/` with data separation in `data/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Deterministic Target Logic** | Target is a symmetry count, not a stochastic Poisson variable. | Poisson regression assumes stochasticity; using it on deterministic data yields meaningless p-values. |
| **Ordinal Regression** | Target is a deterministic integer count (1, 2, 3) derived from symmetry. | Linear regression is valid but Ordinal better respects the categorical nature of symmetry classes. |
| **Spec Revision Required (Synthetic Test)** | The spec's synthetic test (Poisson generation) contradicts the deterministic target reality. | A synthetic test based on a false premise (stochasticity) validates the code but not the science. The spec must be updated to use a deterministic symmetry-based generator. |
| **Tautology Check** | Predictors and target derive from the same graph. | Analysis explicitly tests if global indices are sufficient proxies for local symmetry, acknowledging the mathematical dependency. |
| **Power Limitation** | Target is a small integer within a limited range.; variance may be low. | If variance is low, regression is underpowered. The plan mandates reporting MDE and defaulting to descriptive statistics. |

## Statistical Rigor & Power

- **Multiplicity**: Bonferroni correction applied for 3 tests (alpha = 0.0167).
- **Collinearity**: Variance Inflation Factor (VIF) calculated. If VIF > 5, indices analyzed sequentially or jointly.
- **Causality**: Claims framed as **associational** only (observational data). Confounding variables (catalyst, solvent, temperature) are **acknowledged as unmeasured omitted variables** that may confound the relationship.
- **Power**: 
  - The target is a small integer. 
  - If the target variance is low (e.g., >90% of samples have count=1), the regression is deemed underpowered. 
  - The plan mandates reporting the **Minimum Detectable Effect (MDE)**. 
  - If the MDE is unachievable with the observed sample size, the primary output will be a **descriptive analysis** of the target distribution rather than a regression model.

## Spec Revision Required

The following elements in the source `spec.md` are scientifically invalid and must be updated before the project can proceed to implementation without contradiction:

1.  **FR-004 & FR-007**: The requirement for **Poisson Regression** and **Zero-Inflated Poisson** fallback is invalid for a deterministic target. These must be replaced with **Ordinal Logistic Regression** and **Binary Classification** (if variance=0) or **Descriptive Statistics**.
2.  **User Story 3 (Independent Test)**: The synthetic test `target ~ Poisson(exp(Xβ))` generates data based on a stochastic premise. This must be updated to a **deterministic symmetry-based generation** (e.g., `target = f(symmetry_class)`) to validate the pipeline against the actual scientific question.
3.  **Assumptions (Dataset Variable Fit)**: The assumption that "count defaults to 0" if metadata is insufficient is outdated. The target is **always** derived from reactant symmetry (e.g., benzene = 1). The "default to 0" logic implies a missing data fallback that no longer applies.