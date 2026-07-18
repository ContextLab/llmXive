# Implementation Plan: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Branch**: `001-predicting-phase-transitions` | **Date**: 2026-07-15 | **Spec**: `specs/001-predicting-phase-transitions/spec.md`
**Input**: Feature specification from `/specs/001-predicting-phase-transitions/spec.md`

## Summary
This project implements a CPU-first machine learning pipeline to predict glass transition temperatures ($T_g$) and crystallization propensity in amorphous solids. The approach generates short-range structural descriptors (RDF, bond angles, coordination) from molecular dynamics (MD) simulations and correlates them with experimental thermal properties sourced from a **hard-coded literature subset** to ensure reproducibility. The plan strictly adheres to compute constraints (limited CPU, constrained RAM, 6h limit) and constitutional requirements for data independence and trajectory integrity.

**Critical Scope Resolution**: While the spec targets 500 compositions, the 6-hour compute budget and 30-minute MD cap per composition limit the feasible sample to **24 compositions** (Pilot Study T001). This is calculated as: 24 compositions * 30 min/composition / 2 concurrent jobs = 360 min = 6 hours. This reduction is explicitly documented as a power limitation (SC-005) and mandates statistical validation (Null/Permutation tests) to ensure results are not noise.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `numpy`, `pandas`, `scikit-learn`, `shap`, `mdtraj`, `lammps` (via `pylammps` or CLI wrapper), `datasets` (Hugging Face)  
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for models)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7GB RAM)  
**Project Type**: Computational Science / Data Pipeline  
**Performance Goals**: End-to-end pipeline ≤ 6 hours; RMSE ≤ 15 K (vs. Null Model); ROC-AUC > 0.7  
**Constraints**: No GPU; MD simulations capped at 30 mins/composition; strict trajectory truncation (final 500 steps); **No synthetic data for labels**; Hard-coded literature subset for ground truth.  
**Scale/Scope**: **Pilot Sample: 24 compositions** (Stratified: Oxides, Sulfides, Organics). Target 500 is a long-term goal (FR-001 unmet in this phase).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned; **Hard-coded literature subset** (`data/raw/literature_subset.csv`) ensures automated fetch; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` and `data-model.md` validated against primary sources; no title-token-overlap < 0.7. |
| **III. Data Hygiene** | PASS | Checksums recorded for all files in `data/`; raw data immutable; transformations produce new files. |
| **IV. Single Source of Truth** | PASS | All figures/stats in `paper/` trace to specific rows in `data/processed/` and `code/` blocks. |
| **V. Versioning Discipline** | PASS | Content hashes updated in `state/` on every artifact change. |
| **VI. Simulation-to-Experiment Independence** | PASS (Conditional) | Labels derived *only* from experimental $T_x$/$T_g$ in the **hard-coded literature subset**; MD descriptors are strictly predictive features. No simulation thermodynamics used for labeling. Independence maintained by design, not by programmatic fetch. |
| **VII. Computational Feasibility & Trajectory Integrity** | PASS | MD runs capped at 30 mins; explicit truncation rule: **"keep final 500 steps"** if timeout; pipeline designed for 2-CPU/7GB RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-phase-transitions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── sensitivity.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-203-predicting-phase-transitions-in-amorphou/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Paths, seeds, hyperparameters, KIM ID
│   ├── data/
│   │   ├── validate_literature_subset.py  # Validates presence of hard-coded data (formerly fetch_experimental.py)
│   │   ├── run_md_sim.py          # LAMMPS wrapper with 30m cap & 500-step trunc
│   │   └── extract_descriptors.py # RDF, bond angles, coordination
│   ├── models/
│   │   ├── train_rf.py            # RF Regressor/Classifier with 6h hard timeout
│   │   ├── evaluate.py            # Metrics, CV, Sensitivity Analysis, Null/Permutation tests
│   │   └── interpret.py           # SHAP values, PDPs, Collinearity Report
│   └── utils/
│       ├── logger.py              # Timing logger for SC-005
│       └── validators.py          # VIF, NaN checks
├── data/
│   ├── raw/                       # Hard-coded literature_subset.csv, MD trajectories
│   ├── processed/                 # Merged feature-label dataset
│   └── logs/                      # Simulation truncation logs
├── artifacts/
│   ├── models/                    # Trained .pkl files
│   ├── figures/                   # SHAP plots, PDPs
│   └── reports/                   # Sensitivity, Collinearity, Null Model reports
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: Single project structure chosen to simplify dependency management and data flow between simulation, feature extraction, and modeling. The `code/` directory is isolated for `requirements.txt` pinning to satisfy Reproducibility.

## Complexity Tracking

> **No violations found.** The plan adheres to all constitutional principles and spec constraints.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Phases & Tasks

### Phase 0: Data Strategy & Sample Definition
- **T001 [US1]**: **Define Stratified Sample Strategy**. Resolve FR-001 (500 target) vs. compute constraints (6h). Define **Pilot Sample** of 24 compositions (stratified by family). Document power limitation.

### Phase 1: Data Pipeline & Descriptor Generation
- **T010 [US1]**: **Fetch/Validate Experimental Data**. Implement `validate_literature_subset.py` to check for `data/raw/literature_subset.csv`. **FAIL LOUDLY**: If missing, raise `FileNotFoundError` with message "FATAL: literature_subset.csv missing" and exit with code 1. No synthetic fallback.
- **T011 [US1]**: **Implement MD Simulations**. Enforce 30-minute CPU cap per composition. **Truncation Rule**: If timeout, keep **final 500 steps** only. Verify OpenKIM potentials (ID from `config.yaml`) are available.
- **T013 [US1]**: **Record and Flag Cooling Rate**. Record MD cooling rate. Do NOT attempt physical alignment. Set `SRO_Invariance_Assumed` flag in metadata.
- **T013.1 [US1]**: **Implement Timescale Matching Protocol (Record & Flag)**. Explicitly implement the protocol to record the cooling rate and flag results as "Conditional on SRO Invariance Assumption" to satisfy FR-008.
- **T014 [US1]**: **Extract Structural Descriptors**. Generate RDF, bond angles, coordination numbers. Log NaNs and mark as "failed".
- **T014.1 [US1]**: **Implement Crystallization Labeling Logic**. **Distinct Step**: Apply binary logic (1 if |Tx - Tg| <= 50K) to the merged dataset. Justify 50K threshold as a community-standard approximation. Output pre-labeled dataset.

### Phase 2: Model Training & Validation
- **T020 [US2]**: **Enforce 6-Hour Wall-Clock Limit**. Implement global context manager in `main.py` that wraps the entire pipeline. If time > 6h, trigger graceful shutdown and save partial results.
- **T020.1 [US2]**: **Implement Timing Logger**. Add a timing logger to `main.py` to monitor and enforce the 6-hour constraint as a hard requirement, mapping to FR-003.
- **T021 [US2]**: **Train Random Forest Models**. Regression (Tg) and Classification (Crystallization). k-fold CV.
- **T022 [US2]**: **Evaluate Performance**. Compute RMSE, ROC-AUC. Compare against **Null Model** (mean predictor).

### Phase 3: Interpretability & Rigor
- **T030 [US3]**: **Generate Stratified SHAP & PDPs**. Compute SHAP values and Partial Dependence Plots **stratified by chemical family** (Oxide, Sulfide, Organic). Save separate files per family.
- **T030.1 [US3]**: **Implement SHAP Value Computation**. Explicitly generate SHAP values and PDPs stratified by chemical family, mapping to FR-004.
- **T031 [US3]**: **Implement Multiple-Comparison Correction**. Apply Bonferroni/FDR to feature importance comparisons across families. Output `corrected_p_values` (Permutation tests on SHAP values).
- **T031.1 [US3]**: **Implement Multiple-Comparison Correction Logic**. Explicitly implement Bonferroni/FDR correction for feature importance comparisons across families, mapping to FR-005.
- **T032 [US3]**: **Generate Collinearity Report**. Calculate VIF for all predictors. If VIF > 5, flag feature. Output `collinearity_report.json`.
- **T032.1 [US3]**: **Implement Collinearity Diagnostics**. Explicitly calculate and report VIF values for correlated predictors, mapping to FR-007.
- **T033 [US3]**: **Implement Sensitivity Analysis**. Vary threshold across a range of magnitudes. Report FPR and class balance for each. If FPR varies >10%, flag threshold as unstable. Output `sensitivity_report.json`.
- **T033.1 [US3]**: **Implement Sensitivity Analysis Logic**. Explicitly perform sensitivity analysis on the crystallization threshold using a defined range of representative temperature increments., mapping to FR-006.
- **T034 [US3]**: **Implement Null Model & Permutation Test**. Train mean predictor. Run permutation test (1000 shuffles, p<0.05). Output `permutation_p_value`.
- **T034.1 [US3]**: **Implement Null Model & Permutation Test Logic**. Explicitly implement a Null Model and Permutation Test, mapping to the scientific soundness requirement for small sample size.

## Success Criteria Mapping

- **SC-001**: RMSE measured against experimental Tg. **Must be better than Null Model RMSE**.
- **SC-002**: ROC-AUC > 0.7.
- **SC-003**: Stability of top 3 descriptors across families (SHAP).
- **SC-004**: Sensitivity of classification to threshold (low to high).
- **SC-005**: Pipeline ≤ 6 hours. **Explicitly report N=24 power limitation**.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing Literature Data** | Fatal | `validate_literature_subset.py` aborts with clear error. No synthetic fallback. |
| **MD Simulation Timeout** | High | Truncate to final 500 steps (Constitution VII). Log truncation event. |
| **Compute Budget Exceeded** | High | Hard timeout (6h) in `main.py`. Report partial results if interrupted. |
| **Small Sample Size (N=24)** | High | **Mandatory Null Model & Permutation Test** (T034) to validate significance. Report power limitation. |
| **Cooling Rate Artifact** | Medium | Record rate; include as covariate or flag results as "conditional". |
| **Threshold Arbitrariness** | Medium | Sensitivity analysis (T033) across 25-100K. |
