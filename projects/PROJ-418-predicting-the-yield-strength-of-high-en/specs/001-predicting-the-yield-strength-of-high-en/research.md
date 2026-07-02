# Research: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Overview

This research document outlines the data strategy, model selection rationale, and statistical methodology for predicting HEA yield strength. It addresses the "Verified datasets" constraint by strictly utilizing only the provided URLs.

## Dataset Strategy

The project requires a dataset containing:
1. **Composition**: Elemental fractions (atomic percent).
2. **Target**: Yield Strength (MPa).
3. **Metadata**: Phase structure (single-phase) and Testing Temperature (Room Temp).
4. **Elemental Properties**: Atomic radii, electronegativity, valence electrons (for descriptor calculation).

### Verified Sources Analysis

The following verified datasets are available in the "Verified datasets" block:
- **NIST (jsonl)**: ` (and related parquet files).
 - *Content*: Medical conversations (doctor-patient).
 - *Fit*: **NO**. Contains no HEA composition or yield strength data.
- **HEA (jsonl)**: ` (and related).
 - *Content*: Mental health counseling conversations.
 - *Fit*: **NO**. Despite the label "HEA" in the list, the content is medical text, not materials science data.
- **CPU-only (parquet)**: `.
 - *Content*: LLM training data overlap scores.
 - *Fit*: **NO**.
- **MPa (parquet)**: `.
 - *Content*: XSum text summarization data.
 - *Fit*: **NO**.
- **WebElements (parquet)**: ` (and train).
 - *Content*: Elemental properties (atomic radii, electronegativity, etc.).
 - *Fit*: **PARTIAL**. This dataset provides the **elemental property tables** required for calculating descriptors (δ, Δχ, VEC). It does **not** contain the HEA compositions or yield strength targets.

### Dataset Gap & Mitigation Strategy

**Critical Finding**: The provided "Verified datasets" block **does not contain** a dataset with HEA compositions and yield strength measurements. The only relevant dataset is `WebElements`, which provides the reference tables for descriptor engineering.

**Action Plan**:
1. **Descriptor Engine**: Use `WebElements` (verified URL) to load elemental properties (atomic radius, electronegativity, valence electrons) into `data/raw/webelements.parquet`.
2. **HEA Composition Data**: Since no verified HEA composition dataset exists in the provided list, the `data/download.py` module **MUST** terminate execution with a specific error: `DATA_SOURCE_MISSING: No verified HEA composition dataset found in the Verified datasets block.`
 - The pipeline **will not** fall back to local files or user-provided URLs. This strict behavior ensures adherence to Constitution Principle I (Reproducibility) and FR-001 (Automatic download from open repository).
 - The implementation will document this as a "Blocking Gap" in the final report.
 - *Note*: The spec assumes "HEA datasets from Materials Project, NIST, or Zenodo contain ≥500...". Since no verified URL for these specific datasets is in the provided block, the implementation must handle the case where the data is missing by failing gracefully and reproducibly.

**Decision**: The research phase acknowledges that the **target variable (Yield Strength) and composition data are missing from the verified source list**. The implementation will:
- Load `WebElements` for reference properties.
- Check for a valid HEA composition URL in the verified list.
- **If no URL is found**: Terminate with `DATA_SOURCE_MISSING` error.
- **If a URL is found**: Proceed with data acquisition and analysis.

## Model Selection Rationale

### Baseline: Linear Regression
- **Rationale**: Provides a simple, interpretable baseline. HEA yield strength is often modeled as a linear combination of descriptors in literature.
- **Constraints**: CPU-efficient, fast training.
- **Collinearity Diagnostics (VIF)**: VIF will be calculated **ONLY** for this baseline model to assess its interpretability. It is **NOT** a validation metric for the tree-based models (RF/GB), which are robust to collinearity.

### Tree-Based Models: Random Forest (RF) & Gradient Boosting (GB)
- **Rationale**:
 - Capture non-linear interactions between descriptors (e.g., VEC and δ might interact).
 - Robust to outliers in experimental data.
 - Provide permutation importance for feature selection.
- **Constraints**:
 - **Hyperparameters**: `n_estimators` ≤ 50, `max_depth` ≤ 10 (per FR-004) to ensure CPU feasibility.
 - **Validation**: 5-fold cross-validation to maximize data usage given potential small N (<500).
 - **Feasibility**: These parameters are well within the 7 GB RAM / 2 CPU core limits of GitHub Actions.

### Data Split Strategy (FR-005)
- **Method**: 80/20 random hold-out split.
- **Seed**: Fixed seed `42` for reproducibility.
- **Mechanism**: The split is performed **after** filtering and descriptor calculation, ensuring the test set is truly held out during training.

## Statistical Validation Plan

### Permutation Testing (Conditional)
- **Method**: To address the collinearity of descriptors (δ, Δχ, VEC, etc.), we will use **Conditional Permutation** (residualization). Each descriptor is permuted while preserving its correlation with other descriptors.
- **Fallback**: If conditional permutation is computationally infeasible on CPU, the method defaults to simple permutation but explicitly reports p-values as **"Predictive Utility"** rather than "Independent Effect," acknowledging the limitation.
- **Purpose**: Assess feature relevance without relying on model-specific importance scores.
- **Correction**: Apply Benjamini-Hochberg (FDR) or Bonferroni for ≥5 tests (FR-007).

### Bootstrap Resampling
- **Method**: Resample rows with replacement (1000 iterations).
- **Purpose**: Generate 95% confidence intervals for R², MAE, RMSE (FR-011).
- **Stability**: If CI width is large, the model is unstable.
- **Power Constraint**: If N < 50, bootstrap resampling is skipped and a "Insufficient Power" flag is raised.

### Collinearity Diagnostics (VIF)
- **Metric**: Variance Inflation Factor (VIF).
- **Scope**: Calculated **ONLY** for the Linear Regression baseline.
- **Threshold**: VIF > 10 flags collinearity in the baseline model.
- **Action**: If VIF > 10, the report states "Baseline model exhibits collinearity; independent effects cannot be claimed for linear interpretation." This is **NOT** used to validate the RF/GB models.

### Sensitivity Analysis
- **Sweep**: α ∈ {0.01, 0.05, 0.1}.
- **Output**: Table showing count of significant descriptors and R² at each threshold (FR-008).

## Assumptions & Limitations

1. **Data Availability**: The primary limitation is the absence of a verified HEA composition dataset in the provided list. The pipeline **will not proceed** without a verified URL, ensuring reproducibility.
2. **Observational Nature**: All findings are associational. No causal claims (FR-010).
3. **Unit Standardization**: All yield strength values must be converted to MPa.
4. **Missing Elements**: Compositions with elements missing from `WebElements` will be excluded.
5. **Statistical Power**: If the verified dataset yields N < 50, advanced statistical tests (permutation, bootstrap) are skipped to avoid unreliable results.