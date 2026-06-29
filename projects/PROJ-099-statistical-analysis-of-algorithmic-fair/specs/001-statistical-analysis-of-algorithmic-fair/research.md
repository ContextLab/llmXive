# Research: Statistical Analysis of Algorithmic Fairness Metrics

## Dataset Strategy

The system MUST use ONLY the verified URLs listed below. If a dataset lacks required variables (binary protected attribute, binary outcome, ≥3 features), it MUST be skipped and logged (per Edge Case).

| Dataset Source | Verified URL | Expected Variables | Fit Status |
|:--- |:--- |:--- |:--- |
| **COMPAS Recidivism** | ` | Protected (Race), Outcome (Recidivism), Features | **High** (Known fairness dataset) |
| **COMPAS Priors** | ` | Protected (Race), Outcome (Recidivism), Features | **High** (Known fairness dataset) |
| **Synthetic Compassion** | ` | Protected, Outcome, Features | **Medium** (Verify binary attributes) |
| **UCI HAR** | ` | Activity, Sensors | **Low** (Likely lacks fairness attributes) |
| **UCI Shopper** | ` | Purchase Intent, Demographics | **Medium** (Verify protected attribute) |
| **UCI DROP** | ` | QA Pairs | **Low** (Likely lacks fairness attributes) |

**Dataset Variable Fit Note**: The spec requires ≥5 datasets with binary protected attributes and binary outcomes. The verified list contains COMPAS datasets (high fit) and UCI datasets (variable fit unknown). The plan will attempt to load all verified URLs. If UCI datasets lack protected attributes, they will be skipped (per Edge Case). If ≥5 suitable datasets are not found in the verified list, the plan will proceed with available suitable datasets and note the constraint in `research.md`.

## Statistical Methodology

### Correlation Analysis
- **Method**: Pearson/Spearman correlation between metric pairs within dataset.
- **Correction**: Bonferroni correction applied for family-wise error rate across ≥15 pairwise tests (FR-010, SC-002).
- **Uncertainty**: 95% Confidence Intervals via bootstrap resampling (n=1000) at dataset level (FR-007, SC-004).

### Regression Modeling
- **Model**: Linear Mixed-Effects Models (LMM).
- **Fixed Effects**: Base rate difference, feature dimensionality, class imbalance ratio.
- **Random Effects**: Random intercepts for dataset, random slopes for base rate/imbalance.
- **Collinearity**: Variance Inflation Factor (VIF) diagnosed for predictors. If base rate and class imbalance are definitionally related, effects reported descriptively (Assumption).
- **Causal Framing**: Observational design; claims framed as associational, not causal (Assumption).

### Power & Sample Size
- **Limitation**: With ≥5 datasets, power for regression is limited. Findings are exploratory.
- **Justification**: Datasets are constrained by verified public sources. Bootstrap mitigates uncertainty in correlation estimates.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (standard CPU, 7 GB RAM, 14 GB disk).
- **GPU**: None. No CUDA, no quantization.
- **Memory**: Data sampled to ≤100k rows (FR-009) to ensure ≤7 GB RAM usage.
- **Runtime**: Total pipeline ≤6 hours.
- **Libraries**: `scikit-learn`, `statsmodels`, `pandas` (CPU-tractable).

## Decision Rationale

1. **Why Mixed-Effects?**: Accounts for dataset-level variance (FR-006).
2. **Why Bootstrap?**: Robust CI estimation for small sample sizes (n=5 datasets) (FR-007).
3. **Why Sampling?**: Ensures compliance with 7 GB RAM constraint (FR-009, SC-006).
4. **Why Bonferroni?**: Controls family-wise error rate across multiple correlation tests (FR-010, SC-002).
