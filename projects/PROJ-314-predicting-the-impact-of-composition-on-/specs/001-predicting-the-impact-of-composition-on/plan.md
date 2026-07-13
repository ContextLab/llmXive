# Implementation Plan: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

**Branch**: `001-predict-weibull-modulus` | **Date**: 2026-07-13 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-composition-on-/spec.md`

## Summary

This project implements a computational pipeline to predict the Weibull modulus of ceramics based on their chemical composition and processing parameters. The approach involves ingesting raw data from open repositories (with a curated literature fallback), engineering elemental descriptors (e.g., cation size variance, electronegativity spread), training CPU-optimized Random Forest and Gradient Boosting models with strict cross-validation, and interpreting results via SHAP values while enforcing rigorous collinearity diagnostics and causal disclaimers.

**Critical Note on Data**: The project acknowledges that standard repositories (Materials Project, NIST) may not contain the specific target variable (Weibull modulus). The pipeline includes a robust "Data Gap Protocol" to handle cases where N < 30, generating a "Data Availability Report" instead of a model.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `numpy`, `chemparse`, `requests`, `pyyaml`, `scipy`
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)
**Testing**: `pytest` (unit tests for descriptor calculation, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM)
**Project Type**: Computational Research Pipeline / CLI
**Performance Goals**: Full pipeline execution < 6 hours; Memory usage < 7GB
**Constraints**: No GPU/CUDA; No deep learning; No external API calls during inference (only download); Strict adherence to a sufficiently large sample size for Weibull data; No causal claims.
**Scale/Scope**: Dataset size < 5,000 samples (assumed); Feature count < 100.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt`, fixed random seeds in all ML steps, and checksumming of all data artifacts. External datasets are fetched from canonical URLs only. A `hash_artifacts.py` script updates the project state file with content hashes.
- **II. Verified Accuracy**: All citations in `research.md` will be validated against the primary source. The "Curated Literature Dataset" fallback will be validated against its DOI/URL before ingestion.
- **III. Data Hygiene**: Raw data is immutable. All transformations produce new files with derivation logs. PII scanning is enforced.
- **IV. Single Source of Truth**: All figures and stats in the final report will trace to specific rows in `data/processed/` and code blocks in `code/`.
- **V. Versioning Discipline**: Content hashes for artifacts will be updated in the project state file (`state/...yaml`) upon any change via `hash_artifacts.py`.
- **VI. Computational Stability**: The plan explicitly limits hyperparameter search space (A manageable number of combinations) and mandates stratified k-fold CV (or hold-out/LOO for small N) to prevent overfitting.
- **VII. Explicit Separation**: The target variable is strictly `weibull_modulus`. Processing parameters are engineered as interaction terms, not conflated with mean strength.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-weibull-modulus/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── ceramic_entry.schema.yaml
    └── model_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-314-predicting-the-impact-of-composition-on-/
├── data/
│   ├── raw/             # Downloaded raw files (checksummed)
│   ├── processed/       # Cleaned, feature-engineered datasets
│   └── artifacts/       # Checksums and logs
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # Data fetching and cleaning (FR-001, FR-003)
│   ├── descriptors.py   # Feature engineering (FR-002) - Uses chemparse
│   ├── modeling.py      # Training, CV (FR-004, FR-005)
│   ├── diagnostics.py   # Collinearity, Descriptor Sufficiency (FR-005.5, FR-007)
│   ├── report.py        # Final report generation (FR-008, FR-009)
│   └── hash_artifacts.py # Versioning & Hashing (Principle V)
├── tests/
│   ├── test_descriptors.py
│   ├── test_ingestion.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular single-project structure is selected to facilitate the linear flow of data from ingestion to reporting. This minimizes overhead and aligns with the "Research Project" nature of the feature.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Strict Collinearity Diagnostics (VIF) | Compositional descriptors (mean vs. std) are definitionally related. | Simple correlation is insufficient to detect multicollinearity that inflates variance in regression coefficients. |
| Stratified Splitting | Material classes are likely imbalanced; simple random split could bias validation. | Random split risks a fold with zero representation of a specific ceramic class, invalidating the model's generalization claim. |
| Range Handling (Midpoint + Flag + Uncertainty) | Literature often reports Weibull modulus as a range. | Discarding range data reduces sample size; ignoring uncertainty biases the model. |
| Descriptor Sufficiency Check | 'Primary_anion_cation_group' is a proxy for composition. | Removing it tests if the *descriptors* capture the physics, not if there is leakage. |

## Implementation Phases

### Phase 0: Data Gap Analysis & Ingestion
- **Task 0.1**: Attempt to fetch data from verified sources (Materials Project, NIST).
- **Task 0.2**: If fetch fails or N < 30, attempt to load the "Curated Literature Dataset" (CSV fallback).
- **Task 0.3**: Validate source URL/DOI against primary source (Constitution Principle II).
- **Task 0.4**: If total valid entries (N) < 30, halt and generate "Data Availability Report" (Data Gap Protocol).

### Phase 1: Feature Engineering
- **Task 1.1**: Parse composition strings using `chemparse` (FR-002).
- **Task 1.2**: Compute descriptors: Mean Atomic Radius, Electronegativity Std, VEC, Cation Size Variance.
- **Task 1.3**: Handle missing `sintering_temp`: Impute with group median, add `is_imputed` flag. If group size < 5, use global median.
- **Task 1.4**: Handle range values: Extract midpoint, set `is_range_flag`, compute `range_uncertainty` (width).
- **Task 1.5**: Generate contract schemas (`ceramic_entry.schema.yaml`, `model_result.schema.yaml`).

### Phase 2: Modeling & Validation
- **Task 2.1**: Split data. If N >= 50, use Stratified 5-fold CV. If 30 <= N < 50, use Stratified 80/20 Hold-out. If any class has < 5 samples, exclude from stratification (Rare Class Handling).
- **Task 2.2**: Train Random Forest and Gradient Boosting (a limited set of hyperparameter combinations).
- **Task 2.3**: Baseline: Global mean predictor.
- **Task 2.4**: **SC-001 Check**: Calculate MAE improvement. Perform Permutation Test (sufficient iterations to ensure statistical robustness) to determine statistical significance (p < 0.05). If not significant, flag as "Not Statistically Significant".
- **Task 2.5**: **Descriptor Sufficiency Check**: Re-run best model without `primary_anion_cation_group`. If performance drops significantly, descriptors are insufficient. If not, descriptors are sufficient. (Corrected logic).

### Phase 3: Interpretability & SHAP Analysis
- **Task 3.1**: Generate SHAP values for the best model.
- **Task 3.2**: **FR-009**: Calculate Coefficient of Variation (CV) of top 5 feature importance scores across folds.
- **Task 3.3**: **Collinearity Handling**: Group correlated features (VIF > 5) into clusters. Report aggregate importance for clusters, not individual ranks.
- **Task 3.4**: Generate SHAP summary plots and feature ranking tables.

### Phase 4: Reporting & Compliance
- **Task 4.1**: **FR-008**: Run `sanitize_conclusion(text)` to append disclaimer and remove "cause" from the conclusion field.
- **Task 4.2**: Generate final report with all metrics, CI, and disclaimers.
- **Task 4.3**: Run `hash_artifacts.py` to update project state with content hashes.

## Success Criteria Logic

- **SC-001 (MAE Improvement)**: Model MAE must be < 90% of Baseline MAE **AND** Permutation Test p-value < 0.05. If either fails, report "Not Significant".
- **SC-002 (Stability)**: CV of top 5 features <= 0.2. If > 0.2, flag "Unstable Importance".
- **SC-003 (Collinearity)**: VIF < 5 for all features. If > 5, report as "Correlated Cluster".
- **SC-004 (Sample Size)**: If N < 30, trigger Data Gap Protocol.
- **SC-005 (Runtime)**: Total pipeline < 6 hours.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No valid dataset found** | Project cannot proceed (N < 30). | Implementation halts with "Data Availability Report". |
| **High Collinearity** | Feature importance rankings unstable. | Group features into clusters; report aggregate importance. |
| **Range Data Dominance** | High variance in target. | Include `range_uncertainty` as a feature; perform sensitivity analysis. |
| **Overfitting** | Poor generalization. | Strict hyperparameter limits; stratified CV; bootstrapping for CI. |
| **Power Limitation** | N < 100 makes effect sizes unreliable. | Report results as "Exploratory"; use bootstrapping for wide CIs. |