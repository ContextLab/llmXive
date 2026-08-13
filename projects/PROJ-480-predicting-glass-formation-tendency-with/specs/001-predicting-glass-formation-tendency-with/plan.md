# Implementation Plan: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Branch**: `001-predict-glass-formation` | **Date**: 2026-07-12 | **Spec**: `specs/001-predicting-glass-formation-tendency-with/spec.md`

## Summary

This feature implements a reproducible machine learning pipeline to predict metallic glass formation tendency. The system ingests **experimental** critical casting thickness ($D_c$) data from a verified public source (Figshare), computes thermodynamic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) using `pymatgen` with precise mathematical definitions, and trains a CPU-constrained model (XGBoost or Ridge Regression if collinearity is high). The pipeline supports both regression and classification modes, with rigorous validation including **Adaptive Leave-One-Group-Out (LOGO)** Cross-Validation, a priori power analysis, and robust non-linear circularity checks. All findings are framed as associational.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `xgboost`, `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `pyyaml`
**Storage**: Local file system (`data/`, `state/`, `code/`) with checksummed artifacts
**Testing**: `pytest` (unit, integration, contract)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)
**Project Type**: Data Science Pipeline / CLI Tool
**Performance Goals**: Training completion < 6 hours (target < 30 mins); Memory < 7GB
**Constraints**: CPU-only execution; No external GPU required; Data must be open/downloadable without auth
**Scale/Scope**: Dataset size target ≥ 500 samples (min 30); Adaptive LOGO CV; Threshold sweep

> **Dataset Source Update**: The primary source is a verified dataset containing **raw experimental $D_c$ values** (Figshare). The previously cited Zenodo DOI (10.5281/zenodo.5778205) was identified as containing only calculated descriptors/predicted scores, not ground-truth $D_c$. The pipeline now targets the verified experimental source. **Manual Fallback**: If the API fails (auth/network), the pipeline expects `data/raw/glass_data.csv` to be pre-placed. This ensures reproducibility even if network access is blocked, provided the file is pre-placed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Note |
|:--- |:--- |:--- |
| **I. Reproducibility** | PASS | Random seed fixed to a deterministic value. Data source pinned to verified Figshare DOI. **Manual Fallback**: If API fails, pipeline expects `data/raw/glass_data.csv`. This ensures reproducibility even if network access is blocked. |
| **II. Verified Accuracy** | PASS | Citations validated against primary experimental source. No fabricated URLs. |
| **III. Data Hygiene** | PASS | SHA-256 checksums computed for processed data. Raw data preserved. |
| **IV. Single Source of Truth** | PASS | All metrics traced to `data/` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifacts hashed. State file updated on change. |
| **VI. Descriptor-Based FE** | PASS | All features derived strictly from `pymatgen` atomic descriptors with explicit mathematical definitions. |
| **VII. CPU-Constrained** | PASS | XGBoost/Ridge configured for CPU. Memory limits enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-glass-formation/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ ├── descriptor_set.schema.yaml # NEW: Contract for computed descriptors
│ └── model_artifact.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│ ├── download.py # Data ingestion (Verified Experimental Source)
│ ├── descriptors.py # pymatgen descriptor computation (with explicit formulas)
│ └── validation.py # Data hygiene, circularity, and collinearity checks (Validates against descriptor_set.schema.yaml)
├── models/
│ ├── train.py # Adaptive LOGO CV & Model Selection (XGB/Ridge)
│ ├── evaluate.py # Metrics, Power Analysis, MDES
│ └── interpret.py # Feature importance, VIF, Plots
├── reports/
│ ├── sensitivity.py # Threshold sweep analysis
│ └── generate.py # Final report generation
├── cli/
│ └── run_pipeline.py # Orchestration script
└── lib/
 ├── constants.py # Seeds, thresholds, file paths
 └── utils.py # Checksum, logging helpers

tests/
├── contract/ # Schema validation tests (includes descriptor_set)
├── integration/ # End-to-end pipeline tests
└── unit/ # Descriptor & metric unit tests
```

**Structure Decision**: Single-project structure selected to align with the CLI nature of the pipeline. Separation of concerns (data, models, reports) ensures modularity and testability. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Adaptive Leave-One-Group-Out (LOGO) CV** | Prevents data leakage from chemical families. **Fallback**: If chemical families are sparse (<5 samples), LOGO ensures every sample is tested against a model trained on distinct families, eliminating unstable fold metrics. | Random CV would overestimate performance. Fixed 5-fold stratification fails on sparse data (1-2 samples per fold). |
| **Dual-Mode (Reg/Class)** | Data may contain $D_c$ (continuous) or only binary labels. | Forcing one mode would discard valid data or require arbitrary label conversion. |
| **Robust Circularity Check** | Ensures target is not a mathematical function of descriptors. Uses **Permutation Test** on shuffled targets, comparing real vs. shuffled performance. | Simple linear R² fails to detect non-linear circularity or valid high-correlation physics. |
| **Collinearity Handling** | Thermodynamic descriptors are often collinear. **Strategy**: If VIF > 10, switch to **Ridge Regression**; if VIF > 30, use **PCA**. | Ignoring collinearity inflates feature importance. XGBoost alone may be unstable in small samples. |
| **A Priori Power Calculation** | Justifies sample size requirements. | Post-hoc analysis on small datasets is statistically invalid for power claims. |

## Methodology Details

### 1. Power Analysis & Sample Size
- **A Priori Calculation**: Based on linear regression with $k=5$ predictors, $\alpha=0.05$, Power=0.80, and expected effect size $f^2=0.15$ (medium).
 - **Formula**: $N \approx \frac{(L + k)}{f^2} + k + 1$ (where $L$ is the non-centrality parameter).
 - **Calculated Result**: **N = 77** is required for [deferred] power to detect a medium effect size.
 - **Action**:
 - If $N < 30$: Halt with `DataValidationError` (Insufficient data for any statistical inference).
 - If $30 \le N < 77$: Proceed with a `PowerWarning`. The study is **underpowered**; report the Minimum Detectable Effect Size (MDES) explicitly. Do not claim "no effect" if power is low.
 - If $N \ge 77$: Proceed normally with full power justification.

### 2. Feature Engineering (Precise Definitions)
Using `pymatgen`, compute:
1. **Atomic Size Mismatch ($\delta$)**: $\delta = \sqrt{\sum c_i (1 - \frac{r_i}{\bar{r}})^2}$ where $r_i$ is atomic radius, $c_i$ is atomic fraction. (Standard deviation based).
2. **Mixing Enthalpy ($\Delta H_{mix}$)**: $\Delta H_{mix} = \sum_{i \neq j} 4 c_i c_j \Delta H_{ij}^{mix}$.
3. **Electronegativity Difference ($\Delta \chi$)**: Variance of electronegativity weighted by atomic fraction.
*Note*: All descriptors must be non-null. If an element is unknown to `pymatgen`, the sample is flagged and excluded.

### 3. Adaptive Leave-One-Group-Out (LOGO) Cross-Validation
- **Family Derivation**: Algorithmically determine `chemical_family` from the composition string:
 1. Parse elements and atomic percentages.
 2. Identify the element with the highest atomic percentage.
 3. Assign family = "Element-based" (e.g., "Zr-based"). If multiple elements are within 1%, assign "Multi-Component".
 4. **Physical Rationale**: Glass formation in these systems is often dominated by the primary matrix element's packing efficiency; thus, the majority element serves as a physically meaningful proxy for the "family".
- **Stratification**:
 - **Standard**: **Leave-One-Group-Out (LOGO)**. Train on all groups except one, test on the left-out group. Repeat for all groups.
 - **Fallback**: If a group has only 1 sample, LOGO is still valid (train on all others, test on that one). This ensures stable variance estimates even with sparse data.

### 4. Circularity & Collinearity Diagnostics
- **Circularity Check (Non-Linear, Relative)**:
 1. Train the model on **shuffled** target values (permutation test, 100 iterations).
 2. Calculate the mean performance (R²/AUC) of the shuffled models ($P_{shuffled}$).
 3. Calculate the mean performance of the real model ($P_{real}$).
 4. **Threshold**: If $P_{shuffled} \ge 0.95 \times P_{real}$, flag as `CircularDataError`.
 5. **Physical Correlation Note**: High $P_{real}$ is valid and expected. The check only flags if the model learns the **shuffled** data almost as well as the real data (indicating data leakage or mathematical identity).
- **Collinearity Handling**:
 1. Calculate VIF for all predictors.
 2. **If VIF > 10**: Switch model from XGBoost to **Ridge Regression** (L2 regularization) to stabilize coefficients.
 3. **If VIF > 30**: Perform PCA on descriptors before modeling.
 4. Report VIF scores and the chosen model type in `ModelArtifact`.

### 5. Selection Bias Measurement
- **Method**: Compare the distribution of descriptors in the dataset against a **physically constrained random distribution** of 10,000 synthetic compositions.
 - **Reference Distribution**: Compositions generated within physical bounds that **satisfy Inoue's Rules** (multi-component, large atomic size difference, negative mixing enthalpy).
- **Metric**: Calculate Kolmogorov-Smirnov (K-S) statistic.
- **Threshold**: If K-S > 0.2, report "Significant Selection Bias" in the final report.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Experimental Data Unavailable** | High (No ground truth) | Fallback to manual file upload. If no experimental data exists, the pipeline halts with a clear message. |
| **Insufficient Samples (<30)** | High (No model) | Halt execution with `DataValidationError`. |
| **Power < 0.80 (30 <= N < 77)** | Medium (False negatives) | Proceed with warning and report MDES. Do not claim "no effect" if power is low. |
| **Circular Target** | High (Invalid model) | Robust permutation test with relative threshold. Halt if detected. |
| **High Collinearity** | Medium (Unstable importance) | Automatic switch to Ridge Regression or PCA. |
| **Missing Cooling Rate** | Medium (Confounder) | Document as a limitation in the final report. |