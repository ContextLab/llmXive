# Implementation Plan: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

**Branch**: `001-glass-transition-prediction` | **Date**: 2025-01-15 | **Spec**: `specs/001-glass-transition-prediction/spec.md`
**Input**: Feature specification from `/specs/001-glass-transition-prediction/spec.md`

## Summary

This project implements a computational pipeline to predict the glass transition temperature ($T_g$) of chalcogenide glasses based on their elemental composition. The primary requirement is to quantify the **associational contribution** of mean coordination number (topological constraint) and chemical heterogeneity (electronegativity/atomic radius variance) to $T_g$. The technical approach involves downloading a supplementary dataset, engineering compositional descriptors using periodic property databases, training a CPU-tractable Gradient Boosting Regressor with 5-fold cross-validation, and applying SHAP analysis for interpretability. The entire pipeline is constrained to run on a GitHub Actions free-tier runner (limited CPU, constrained RAM, a bounded time limit) without GPU acceleration. All findings are explicitly framed as **associational, not causal**.

> **Note on Causal Language**: The phrase "jointly determine" in the user prompt is interpreted strictly as "jointly predict" in this observational study. The plan does not claim causal determination.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `mendeleev`, `requests`, `numpy`, `pytest`, `statsmodels`  
**Storage**: Local file system (`data/`, `artifacts/`, `state/`); no external database.  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data science / Computational materials science pipeline.  
**Performance Goals**: Complete full pipeline (load, feature, train, evaluate, explain) within 6 hours.  
**Constraints**: No GPU/CUDA; memory usage < 7 GB; dataset size handled via sampling if > 5000 samples for SHAP.  
**Scale/Scope**: Dataset size ~1000 samples (estimated); 3 derived features; 2 model types.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Dataset fetched from canonical source on every run. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **Current Status**: Dataset URL is unverified (Research.md). **Strategy**: If URL unreachable, halt with `DATA_MISSING: URL_UNREACHABLE`. No data fabrication. |
| **III. Data Hygiene** | Raw data checksummed upon download. Derived features, **residualized features**, and **SHAP subsets** written to new files with content hashes recorded in `state/manifest.json`. |
| **IV. Single Source of Truth** | All figures/stats trace to `data/` rows and `code/` blocks. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | Artifacts carry content hashes. `state/manifest.json` records hashes for raw, processed, and derived artifacts. |
| **VI. Interpretability & Physical Consistency** | SHAP analysis mandatory to verify $T_g$ aligns with mean coordination number and heterogeneity. **Cross-family transferability tests** validate mechanism consistency. |
| **VII. Composition-Based Generalization** | Stratified train/test split by chemical family implemented. If strata are small (<10 samples), fallback to **Leave-One-Family-Out (LOFO)** cross-validation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-glass-transition-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── chalcogenide_sample.schema.yaml
│   ├── model_performance.schema.yaml
│   ├── shap_importance.schema.yaml
│   └── shap_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # FR-001: Download and validate dataset
│   ├── preprocess.py        # FR-002: Feature engineering (coordination, heterogeneity, residualization)
│   └── split.py             # FR-003: Stratified split or LOFO
├── models/
│   ├── train.py             # FR-004: Train GB and Linear models with CV
│   ├── evaluate.py          # FR-005: Compute RMSE, R², Power Analysis
│   └── explain.py           # FR-006: SHAP analysis + Transferability Test
├── utils/
│   ├── constants.py         # Periodic property helpers
│   └── metrics.py           # VIF, bootstrapping, orthogonalization helpers
└── main.py                  # Orchestration script

tests/
├── unit/
│   ├── test_feature_engineering.py
│   └── test_split.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py

data/
├── raw/                     # Downloaded supplementary data (checksummed)
├── processed/               # Feature-engineered CSVs (checksummed)
├── residualized/            # Orthogonalized features (checksummed)
└── shap_subset/             # Derived SHAP sampling artifact (checksummed)

state/
└── manifest.json            # Artifact hash registry
```

**Structure Decision**: Single project structure selected. Separation of concerns (data, models, utils) ensures modularity and testability. No external services required.

## Complexity Tracking

| Requirement | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Orthogonalization (Residualization)** | Required to disentangle MCN and Heterogeneity effects when VIF > 5. | Simple descriptive framing is insufficient for the research question; we must estimate *unique* variance. |
| **LOFO Cross-Validation** | Required when chemical families are small (<10 samples) to prevent high variance in generalization estimates. | Stratified split fails with small strata, leading to unreliable performance metrics. |
| **Power Analysis** | Required to quantify the study's ability to detect the heterogeneity effect size. | Without it, a null result could be due to low power rather than a true lack of effect. |
| **Cross-Family Transferability** | Required to validate if learned mechanisms are universal or family-specific. | Feature importance could be an artifact of the specific training families. |
| **SHAP Memory Optimization** | SHAP on large datasets can require substantial RAM. | Standard `KernelExplainer` is too slow/memory heavy. `TreeExplainer` is used with dataset sampling (≤5000) to balance feasibility and accuracy. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Task 0.1**: Download dataset from verified URL. If URL unreachable, halt with `DATA_MISSING: URL_UNREACHABLE`.
- **Task 0.2**: Validate columns (composition, Tg). If missing, log `DATA_MISSING: Required column [column_name] not found` (SC-008).
- **Task 0.3**: Compute checksums for raw data and record in `state/manifest.json`.
- **Task 0.4**: **Power Analysis**: Estimate Minimum Detectable Effect Size (MDES) for the heterogeneity term given estimated N and MCN variance. If power < 0.80, flag as "Power Limitation" in the final report.

### Phase 1: Feature Engineering & Splitting
- **Task 1.1**: Compute MCN, electronegativity variance, atomic radius variance.
- **Task 1.2**: **Stratified Split with LOFO Fallback**: Split by chemical family. If any family has < 10 samples in the test set, automatically switch to **Leave-One-Family-Out (LOFO)** cross-validation for that family.
- **Task 1.3**: **Generate SHAP subset artifact** (if needed), compute hash, record in `state/manifest.json` (Constitution Principle III).
- **Task 1.4**: Compute checksums for processed features and record in `state/manifest.json`.

### Phase 2: Model Training
- **Task 2.1**: Train Linear Regression baseline.
- **Task 2.2**: Train Gradient Boosting Regressor with k-fold cross-validation.
- **Task 2.3**: Compute RMSE, R².

### Phase 3: Analysis & Mitigation
- **Task 3.1**: Compute VIF. If VIF ≥ 5, apply **Residualization**: Regress heterogeneity descriptors against MCN and use residuals as the "unique heterogeneity" predictor.
- **Task 3.2**: Validate orthogonalized features for family-specific bias. If bias persists, restrict interpretation to global effects.
- **Task 3.3**: Compute **95% bootstrapped confidence intervals** for SHAP differences (SC-006). Record `ci_lower`, `ci_upper`, `is_significant` in `performance_metrics.json`.
- **Task 3.4**: Compute Permutation Importance to validate against deterministic bias.
- **Task 3.5**: **Cross-Family Transferability Test**: Train on N-1 families, test on held-out family. Compare feature importances. If CI excludes zero, flag as "Family-Specific Mechanism".

### Phase 4: Reporting
- **Task 4.1**: Generate `shap_report.md` with explicit **Causal Disclaimer** section (FR-008), **Power Limitation** note (if applicable), and `causal_disclaimer` field (per `shap_report.schema.yaml`).
- **Task 4.2**: Generate `performance_metrics.json` with all required fields (including CI for SC-006, MDES, and transferability metrics).
- **Task 4.3**: Record artifact hashes for all derived files (including SHAP subset, residualized features) in `state/manifest.json`.

## Constraints & Assumptions

- **Dataset Size**: Assumed ≤1000 samples. If >5000, sample for SHAP analysis.
- **Memory**: SHAP sampling to ≤5000 samples ensures <7 GB RAM usage.
- **Collinearity**: If VIF > 5, Residualization is applied (mitigation strategy for SC-007).
- **Causal Claims**: All findings are explicitly labeled as **ASSOCIATIONAL**.
- **Power**: If MDES is too large for the expected effect, the report will explicitly state "Insufficient Power to Detect Small Effects".
- **Spec Note**: The source `spec.md` User Story 2 contains a broken sentence regarding the research question. This plan adopts the corrected question: "How do mean coordination number and chemical heterogeneity jointly *predict* the glass transition temperature...".