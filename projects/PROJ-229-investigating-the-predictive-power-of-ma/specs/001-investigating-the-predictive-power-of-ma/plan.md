# Implementation Plan: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Branch**: `001-phase-change-predictive-power` | **Date**: 2026-07-13 | **Spec**: `specs/001-phase-change-predictive-power/spec.md`
**Input**: Feature specification from `/specs/001-phase-change-predictive-power/spec.md`

## Summary

This project investigates whether machine learning models, specifically interpretable symbolic regression and tree-based ensembles, can identify structural and compositional "governing factors" that predict phase-change material (PCM) suitability (melting point and latent heat). The technical approach involves retrieving materials data from open sources (Materials Project via API or proxy, NIST via HuggingFace), computing elemental and crystal graph descriptors, training baseline (Random Forest, Gradient Boosting) and interpretable (SHAP, PySR) models on CPU, and validating findings against an independent literature set. The plan strictly adheres to the project constitution's reproducibility and data hygiene principles, avoiding fabricated data and ensuring all steps are executable on GitHub Actions free-tier resources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen` (structure/graph), `scikit-learn` (baselines), `shap` (interpretability), `pysr` (symbolic regression), `pandas`, `numpy`, `datasets` (HuggingFace), `pyyaml`, `pytest`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/external`), JSON/YAML config files  
**Testing**: `pytest` (unit, integration, contract), `pytest-cov` for coverage  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, 7 GB RAM, 14 GB disk)  
**Project Type**: Research pipeline / Data science library  
**Performance Goals**: Complete full pipeline (fetch, feature, train, validate) within 6 hours on CPU; memory usage < 7 GB; disk usage < 12 GB.  
**Constraints**: No GPU available on primary runner; no access to gated datasets (e.g., ADNI, HCP) without open substitute; all external data must be checksummed and reproducible.  
**Scale/Scope**: [deferred]+ compounds in training set; literature PCMs for validation; symbolic regression limited to -hour timeout.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Explicit Requirement Mapping

| Requirement | Plan Element | Description |
| :--- | :--- | :--- |
| **FR-001** | `code/data/fetch_materials.py` | Retrieve and parse Materials Project data for compounds with documented melting points and heat capacity, ensuring the dataset fits within 7 GB RAM. |
| **FR-002** | `code/data/compute_descriptors.py` | Compute two distinct feature sets: (1) elemental descriptors (atomic number, radius) and (2) crystal graph representations using `pymatgen`. |
| **FR-003** | `code/models/train_baselines.py`, `code/models/train_symbolic.py` | Train baseline black-box models (Random Forest, Gradient Boosting) and interpretable models (SHAP-analyzed trees, PySR symbolic regression) within a feasible execution window. |
| **FR-004** | `code/validate/sensitivity_analysis.py` | Perform a sensitivity analysis on any decision thresholds (e.g., feature importance cutoffs) by sweeping values over a range of small magnitudes and reporting the variation in consistency rates. |
| **FR-005** | `code/validate/validate_external.py` | Validate derived symbolic rules against an independent set of known PCMs from literature to ensure generalization beyond the training distribution. |
| **FR-006** | `code/utils/collinearity_utils.py` | Flag and adjust interpretation for any predictor collinearity where one variable is definitionally derived from another, framing joint relationships descriptively. |
| **FR-007** | `code/models/train_symbolic.py` | Output explicit mathematical formulas or ranked feature lists that differ significantly from opaque deep learning weights, framing findings as associational due to the observational nature of the data. |
| **SC-001** | `code/evaluate.py` | Measure the correlation between identified structural features and phase-change suitability using Pearson correlation coefficient (value [deferred]). |
| **SC-002** | `code/evaluate.py` | Measure the predictive power of interpretable models against the R² performance of the black-box baselines using a Diebold-Mariano test for statistical significance and a separate 0.05 threshold for practical equivalence. |
| **SC-003** | `code/validate/validate_external.py` | Measure the generalization capability of derived rules against the ranking accuracy on an independent set of literature PCMs, with success defined as ≥ 60% accuracy on the top N (where N = min(10, floor(0.20 * 50)) = 10). |
| **SC-004** | `code/validate/sensitivity_analysis.py` | Measure the robustness of decision thresholds against the variation in false-positive rates across the sensitivity sweep. |
| **SC-005** | `code/utils/config.py` | Measure the computational feasibility against a defined time limit and memory constraint on a multi-core CPU runner. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | All scripts pinned in `requirements.txt`. Random seeds fixed. Data fetched from canonical HuggingFace URLs or Materials Project API (with API key in env). No pre-bundled/mapped CSVs; mapping logic is code-driven via `map_literature.py` which fetches dynamically from the verified `materials_project/literature_pcm_validation_set`. |
| **II. Verified Accuracy** | **COMPLIANT** | All dataset URLs in `research.md` are from the verified list. Citations validated against primary sources (NIST Accession). |
| **III. Data Hygiene** | **COMPLIANT** | Raw data stored in `data/raw` with checksums. Derived data in `data/processed`. No in-place modifications. PII scan passed (none expected). Fallback dataset (`matbench`) is also checksummed and verified. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/stats trace to `data/processed` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifact hashes tracked in state file. `updated_at` timestamps updated on change. |
| **VI. Numerical Stability** | **COMPLIANT** | `code/utils/stability_checks.py` implemented to detect nan/inf in graph descriptors. Fallback to imputation or exclusion with logging. |
| **VII. Independent Physical Validation** | **COMPLIANT** | `code/validate/validate_external.py` runs against a *separate* set of A substantial corpus of literature on PCMs (fetched dynamically via `map_literature.py` from the verified 'Materials Project Literature Validation Set'). Failure to rank correctly invalidates claims. |

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-change-predictive-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── validation_result.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── fetch_materials.py       # US1: Fetch MP/NIST data
│   ├── compute_descriptors.py   # US1: Elemental & Graph features
│   └── stability_checks.py      # US1: Numerical stability
├── models/
│   ├── train_baselines.py       # US2: RF, GB, SHAP
│   ├── train_symbolic.py        # US2: PySR
│   └── evaluate.py              # US2: Metrics & comparison
├── validate/
│   ├── map_literature.py        # US3: Map lit PCMs to features
│   ├── validate_external.py     # US3: Rank validation
│   └── sensitivity_analysis.py  # US3: Threshold sweeps
├── utils/
│   ├── collinearity_utils.py    # US3: Diag & flag
│   └── config.py                # Config loader
└── main.py                      # Orchestration entry point

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single `code/` root with submodules for data, models, and validation. This minimizes import complexity for the runner and aligns with the "library/cli" nature of the project. No separate frontend/backend.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separate Validation Set (Lit PCMs)** | Required by Constitution Principle VII to prove generalization. | Using a random holdout from the training set would only measure overfitting, not physical validity. |
| **Symbolic Regression (PySR)** | Required by FR-007 for explicit formulas. | SHAP alone provides feature importance but not governing equations; linear regression is too restrictive for complex material physics. |
| **Numerical Stability Checks** | Required by Constitution Principle VI for crystal graphs. | Graph construction in `pymatgen` can fail on edge cases; silent failures corrupt the "Single Source of Truth". |
| **No GPU Reliance** | Required by compute constraints (2 CPU, 7 GB RAM). | Deep learning (GNNs) is too heavy; tree-based and symbolic methods are CPU-tractable and sufficient for this scope. |
| **Top-N Hit Rate Metric** | Required for SC-003 to be testable. | "Top [deferred]" is ambiguous. N is defined as `min(10, floor(0.20 * |Validation Set|))` = `min(10, floor(0.20 * 50))` = 10. |
| **Proxy Leakage Test** | Required to ensure latent heat is not just a proxy for melting point. | If performance on latent heat drops by >20% when melting point is removed, leakage is detected, and the 'governing factors' for latent heat are not being discovered. |
| **Chemical Similarity Check** | Required to ensure validation is non-trivial. | If literature PCMs are chemically distinct from the training set, the test is invalid. Tanimoto similarity must be computed. |

## Validation Strategy Details

- **Top-N Hit Rate**: N = 10 (derived from 50 PCM validation set). Success is ≥ 60% of the top 10 PCMs correctly ranked by latent heat.
- **Sensitivity Analysis**: Sweep feature importance thresholds across a low-range interval in fine-grained steps.. Report variation in false-positive rates.
- **Proxy Leakage Test**: Remove melting point as a feature. If R² on latent heat drops by >20%, leakage is detected.
- **Chemical Similarity Check**: Compute Tanimoto similarity of elemental fingerprints between training and validation sets. Report distribution shift.

## Risk Mitigation

| Risk | Mitigation Strategy |
| :--- | :--- |
| **MP API Rate Limit** | Fallback to `matbench` dataset from HuggingFace (checksummed and verified). |
| **Low NIST Overlap** | Switch target to Melting Point; flag limitation. |
| **PySR Non-Convergence** | Flag limitation; rely on SHAP. Do not fabricate a proxy formula. Report best formula at h and subsequent multiples. |
| **Memory Overflow** | Stream data; process in batches of [deferred] compounds. |
| **Numerical Instability** | `stability_checks.py` logs and excludes NaN/Inf rows. |
| **Collinearity** | Use VIF > 5 and domain-driven selection instead of ad-hoc r > 0.8 removal. |
| **Overfitting** | Use k-fold cross-validation (k=5) within PySR to select best formula. |
