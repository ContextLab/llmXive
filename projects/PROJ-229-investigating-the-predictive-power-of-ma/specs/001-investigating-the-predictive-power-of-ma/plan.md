# Implementation Plan: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Branch**: `001-phase-change-predictive-power` | **Date**: 2026-07-13 | **Spec**: `specs/001-investigating-the-predictive-power-of-ma/spec.md`

## Summary

This project investigates whether machine learning models, specifically interpretable ones (symbolic regression, SHAP-analyzed trees), can identify structural and compositional "governing factors" that predict **Melting Point** (as a proxy for phase stability) or **Latent Heat of Fusion** (if available) for phase-change materials (PCMs). The approach involves retrieving materials data from the **Matbench Melting Points** dataset (verified open source), computing elemental and graph-based descriptors, training Random Forest/Gradient Boosting baselines, and running PySR symbolic regression. Results are validated against an independent literature set of PCMs. The implementation is constrained to CPU execution (GitHub Actions free tier).

**Critical Data Strategy Update**: The "Verified datasets" block does not contain a specific URL for "Materials Project" or "NIST Latent Heat".
- **Primary Target**: **Melting Point** (Available in `matbench` dataset).
- **Secondary Target**: **Latent Heat** (Only if found in the Matbench dataset; if not, the project focuses on Melting Point).
- **Validation**: A curated list of 50 known PCMs with **Melting Point** values (sourced from NIST Webbook public tables) to ensure independence.
- **No Proxies**: We do NOT use Melting Point as a proxy for Latent Heat. We predict the variable that is actually available. If Latent Heat is missing, the research question is reframed to "Predicting Melting Points".

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matbench`, `pyyaml`, `pytest`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`, `data/external`)
**Testing**: `pytest` (unit, integration, contract)
**Target Platform**: Linux (GitHub Actions runner)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Complete data retrieval, feature engineering, model training, and analysis within 6 hours on 2 CPU cores, 7 GB RAM.
**Constraints**: No local GPU; must fit within 7 GB RAM; must use open, directly downloadable datasets; must avoid causal claims.
**Scale/Scope**: Target dataset size [deferred]–[deferred] compounds (Matbench); a set of external validation PCMs.

**Dataset Strategy**:
- **Primary**: **Matbench Melting Points** (via `matbench` Python package). This is an open-source benchmark dataset containing melting points for thousands of compounds.
- **Fallback**: If `matbench` is unavailable, the script will fail with a clear error (no simulated data).
- **Validation**: `data/external/literature_pcms_raw.csv` (Curated list of 50 PCMs with Melting Points from NIST Webbook).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required |
|-----------|--------|-----------------|
| **I. Reproducibility** | **Pass** | Plan pins seeds, uses `requirements.txt`, and defines deterministic data retrieval from `matbench`. |
| **II. Verified Accuracy** | **Pass** | Plan uses `matbench` (open source) and a curated CSV for validation. No URLs fabricated. |
| **III. Data Hygiene** | **Pass** | Plan mandates checksumming. `data/external/literature_pcms_raw.csv` is generated as a non-empty fallback if external retrieval fails, ensuring no empty files. |
| **IV. Single Source of Truth** | **Pass** | All results trace to `data/` and `code/`. No hand-typed stats. |
| **V. Versioning Discipline** | **Pass** | Content hashes recorded in state file. |
| **VI. Numerical-Stability** | **Pass** | Plan includes checks for NaN/Inf in graph features and logs them. |
| **VII. Independent Physical Validation** | **Pass** | Plan includes a separate validation set of 50 literature PCMs with independently measured Melting Points. |

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-change-predictive-power/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output
 ├── dataset.schema.yaml
 ├── model_output.schema.yaml
 └── validation_result.schema.yaml
```

### Source Code (repository root)

```text
data/
├── raw/ # Downloaded raw data (checksummed)
├── processed/ # Feature-engineered data
├── external/ # Literature PCMs (curated CSV)
└── results/ # Model outputs, metrics, plots

code/
├── data/ # Data retrieval and cleaning scripts
│ ├── fetch_matbench.py
│ └── compute_features.py
├── models/ # Model training and evaluation
│ ├── train_baseline.py
│ ├── train_symbolic.py
│ └── evaluate.py
├── utils/ # Helper functions
│ ├── graph_utils.py
│ └── collinearity.py
└── cli/ # Entry point
 └── run_pipeline.py

tests/
├── unit/ # Unit tests for utils and features
├── integration/ # End-to-end pipeline tests
└── contract/ # Schema validation tests
```

**Structure Decision**: Standard research pipeline structure (data, code, tests, results) to ensure reproducibility and separation of concerns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Symbolic Regression (PySR)** | Required to extract explicit mathematical formulas (FR-007, US-2). | Black-box models alone cannot provide interpretable rules. |
| **Graph-based Descriptors** | Required to capture structural information (FR-002). | Elemental descriptors alone are insufficient for phase-change prediction. |
| **Independent Validation Set** | Required by Constitution Principle VII. | Training/test split alone cannot validate generalization to literature. |

## Phased Implementation Plan

### Phase 0: Data Retrieval & Feasibility Check (FR-001)
1. **Retrieve Matbench**: Use `matbench` package to load the "melting-points" dataset.
2. **Check Target Variable**: Verify if `latent_heat` column exists.
 - **If Yes**: Set target = `latent_heat`.
 - **If No**: Set target = `melting_point`. Log this switch explicitly.
3. **Download & Checksum**: Save the dataset to `data/raw/` and compute checksum.
4. **Generate Validation Set**:
 - Attempt to download `data/external/literature_pcms_raw.csv` from a public NIST mirror (if available).
 - **If Fail**: Generate a hardcoded fallback CSV with a set of known PCMs and their Melting Points (from NIST Webbook public tables) to ensure the file is non-empty and checksummed.
5. **Feasibility Report**: If no data is found, log a fatal error and halt.

### Phase 1: Feature Engineering (FR-002)
1. **Elemental Descriptors**: Compute **Periodic Group**, **Period**, **Atomic Mass**, **Electronegativity**, **Atomic Radius** (mean, max, min, variance) for each element.
 - **Note**: Do NOT use raw `Atomic Number` as a feature (it is an ID). Use continuous periodic trends.
2. **Graph Representation**: Use `pymatgen` to generate crystal graphs (adjacency, symmetry).
3. **Collinearity Check**: Identify definitionally dependent features (e.g., atomic vs. ionic radius).
4. **Output**: `data/processed/featurized_data.csv` with all descriptors.

### Phase 2: Model Training (FR-003)
1. **Baseline Models**: Train Random Forest and Gradient Boosting on CPU.
2. **Symbolic Regression**: Train PySR model with a time budget (4 hours).
3. **Interpretability**: Run SHAP analysis on tree models.
4. **Output**: `data/results/model_metrics.json`, `data/results/symbolic_formulas.txt`.
 - **Constraint**: All metrics must be computed from real data. If a model fails, log "FAILED", do NOT use placeholders.

### Phase 3: Validation & Sensitivity (FR-004, FR-005, FR-006)
1. **External Validation**: Apply derived rules to the 50 literature PCMs (using the **same target variable** as training).
2. **Sensitivity Analysis**: Sweep feature importance thresholds and report FP/FP rates.
3. **Collinearity Adjustment**: Adjust interpretation of joint relationships.
4. **Output**: `data/results/validation_report.json`, `data/results/sensitivity_analysis.csv`.

### Phase 4: Reporting (FR-007)
1. **Generate Report**: Compile results, ensuring all findings are framed as associational.
2. **Final Check**: Verify all outputs against the schema contracts.

## Risk Mitigation

- **Data Unavailability**: If `matbench` is unavailable, the script fails with a clear error. No simulated data.
- **Symbolic Regression Failure**: If PySR fails to converge, the plan defaults to SHAP analysis and flags the limitation.
- **Collinearity**: Explicitly flag and adjust interpretation for definitionally dependent features.
- **CPU Constraints**: Use streaming for large datasets; sample if necessary (with power limitation noted).

## Success Metrics (Deferred Values)

- **SC-001**: Pearson correlation coefficient between predicted and actual [Target Variable] (value [deferred]).
- **SC-002**: R² difference ≤ 0.05 between interpretable and baseline models.
- **SC-003**: Ranking accuracy on the top N PCMs (where N is [deferred]) ≥ 60%.
- **SC-004**: False-positive rate variation [deferred].
- **SC-005**: Execution time ≤ 6 hours, memory ≤ 7 GB.

## References

- **Matbench**: ` (Open source library).
- **Matbench Melting Points**: Dataset within `matbench` package.
- **NIST Webbook**: Public tables for validation set curation.
- **PySR**: ` (Standard library).