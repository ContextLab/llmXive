# Implementation Plan: Statistical Analysis of Algorithmic Fairness Metrics

**Branch**: `001-fairness-metric-analysis` | **Date**: 2025-01-15 | **Spec**: `specs/001-statistical-analysis-of-algorithmic-fair/spec.md`
**Input**: Feature specification from `specs/001-statistical-analysis-of-algorithmic-fair/spec.md`

## Summary

This feature implements a statistical analysis pipeline to investigate how dataset properties (base rate differences, feature dimensionality, class imbalance) predict divergence among fairness metrics. The system downloads ≥5 public datasets, preprocesses them to extract binary protected attributes and outcomes, trains baseline models, computes ≥6 fairness metrics, and performs correlation and regression analysis with bootstrap confidence intervals. All analysis runs on CPU-only infrastructure within 6 hours and ≤7 GB RAM.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `requests`
**Storage**: Local CSV/Parquet files under `data/`
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Data Analysis Pipeline
**Performance Goals**: ≤6 hours total runtime, ≤Moderate RAM peak, ≤14 GB disk usage
**Constraints**: No GPU, no deep learning training, sampling to ≤100k rows if larger
**Scale/Scope**: multiple datasets, multiple models per dataset, 6+ metrics per model

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|:--- |:--- |:--- |
| **I. Reproducibility** | Pass | Random seeds pinned in `code/` via `random.seed()` and `np.random.seed()`. External datasets fetched from canonical verified URLs. `requirements.txt` pins exact versions (e.g., `pandas==2.1.0`, `scikit-learn==1.3.0`). |
| **II. Verified Accuracy** | Pass | Citations in `research.md` use ONLY URLs from the `# Verified datasets` block. Reference-Validator Agent will check titles against primary sources. |
| **III. Data Hygiene** | Pass | Raw data preserved in `data/raw/` with checksums. Derivations in `data/processed/` with new filenames. Checksums recorded in `state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml` artifact_hashes map. No PII committed. |
| **IV. Single Source of Truth** | Pass | Figures/stats in paper trace to exactly one row in `data/analysis/` and one script in `code/`. Derived numbers computed programmatically, not hand-typed. |
| **V. Versioning Discipline** | Pass | Artifacts carry content hashes via SHA-256. `state/` updated on artifact changes. `updated_at` timestamp in project state YAML. |
| **VI. Fairness Metric Transparency** | Pass | Dataset characteristics (base_rate_diff, feature_dim, imbalance_ratio) stored in `data/analysis/characteristics.csv` and referenced in all figures discussing metric behavior. |
| **VII. Statistical Rigor** | Pass | Correlation/regression tests include p-values, CIs, FDR correction (Benjamini-Hochberg), and VIF for collinearity. Effect sizes reported alongside significance. |

## Project Phases & Requirement Mapping

### Phase 0: Data Acquisition & Preprocessing
*Addresses: FR-001, FR-002, FR-009, SC-001, SC-007*

1. **Download**: Fetch datasets from verified URLs (COMPAS, UCI Adult, German Credit, Law School Admission). Validate file size ≤500MB. Record SHA-256 checksums per Constitution Principle III.
 - **How FR-001 addressed**: Download ≥5 datasets from verified sources; validate each file size ≤500MB; log checksums.
2. **Preprocess**: Extract binary protected attribute, binary outcome, and feature matrix (≥3 features). Document derivation path.
 - **How FR-002 addressed**: For each dataset, identify binary protected attribute (first alphabetically if multiple), binary outcome, and ≥3 numeric features. Write to `data/processed/{dataset_id}.parquet`.
3. **Sample**: If rows >100k, sample to ≤100k using stratified sampling on outcome variable. **Sampling occurs AFTER preprocessing** to ensure binary protected attribute extraction is complete.
 - **How FR-009 addressed**: Apply stratified sampling to ≤100k rows; log sample ratio; ensure outcome distribution preserved.
4. **Validate**: Log warning/skip if binary protected attribute missing (Edge Case). Verify each dataset contains required variables (base rate, feature dimensionality, class imbalance). Ensure ≥5 datasets processed or document constraint.
 - **How SC-001 addressed**: Count processed datasets; log to `data/processed/logs/dataset_count.log`; skip invalid datasets with warning.
 - **How SC-007 addressed**: Validate each preprocessed dataset contains base_rate, feature_dim, imbalance_ratio, and all 6 fairness metrics are computable.

### Phase 1: Modeling & Metric Computation
*Addresses: FR-003, FR-004, SC-002*

1. **Train**: Fit multiple baseline models (Logistic Regression, Random Forest, Gradient Boosting) per dataset using scikit-learn with pinned random seeds (e.g., `random_state=42`).
 - **How FR-003 addressed**: Train multiple models per dataset; store model parameters (not weights) for reproducibility; use same train/test split per dataset.
2. **Metrics**: Calculate multiple fairness metrics (Demographic Parity Difference, Equalized Odds Difference, Predictive Parity, Calibration Within Groups, Disparate Impact Ratio, False Positive Rate Disparity).
 - **How FR-004 addressed**: Compute all relevant metrics per model; store in `data/analysis/metrics.csv` with failure_reason if calculation fails.
3. **Handle Errors**: Record NA with failure_reason (e.g., "zero_predictions_class_1") if metric calculation fails. Log reason to `data/processed/logs/metric_errors.log`. Continue without crashing.
 - **How SC-002 addressed**: Log failure_reason per Constitution Principle III data hygiene; enables debugging while maintaining data quality.
4. **Output**: Store metric values in `data/analysis/metrics.csv` with columns: metric_id, dataset_id, model_id, metric_name, value, failure_reason, timestamp.

### Phase 2: Correlation & Regression Analysis
*Addresses: FR-005, FR-006, FR-010, SC-003*

1. **Correlation**: Compute pairwise Pearson/Spearman correlations between metrics at **dataset-model aggregated level** (not treating all metric pairs as independent). Apply clustering-robust standard errors to avoid Type I error inflation from hierarchical nesting.
 - **How FR-005 addressed**: Aggregate metrics by dataset-model; compute ≥15 pairwise correlations; use robust SE for clustering.
 - **Circular Validation Avoidance**: Base-rate-dependent metrics (demographic parity, disparate impact) are NOT correlated with base_rate_diff as predictor; these relationships reported descriptively only.
2. **Correction**: Apply Benjamini-Hochberg False Discovery Rate (FDR) control for multiple comparisons across ≥15 pairwise tests. **FDR chosen over Bonferroni** because with 15 tests on 5 datasets, Bonferroni (α adjusted for multiple comparisons) is overly conservative and risks Type II errors.
 - **How FR-010 addressed**: Apply FDR correction; report both raw and adjusted p-values; note FDR method in documentation.
3. **Regression**: Fit **fixed-effects linear regression** (not LMM with random slopes) to predict metric discrepancies from dataset characteristics. With ≥5 datasets, random effects estimation is unreliable (minimum ~10-20 groups recommended). Fixed-effects model includes dataset as fixed factor.
 - **Collinearity Diagnosis**: VIF computed for predictors; if VIF >5, base_rate_diff and class_imbalance_ratio reported descriptively rather than as independent effects. **Base_rate_diff defined as**: |P(Y=1|A=1) - P(Y=1|A=0)|.
 - **How FR-006 addressed**: Fixed-effects regression outputs ≥3 coefficients with p-values and 95% CIs; VIF diagnostic included.
4. **Output**: Store regression coefficients, p-values, CIs, and VIF values in `data/analysis/regression.csv`.

### Phase 3: Validation & Visualization
*Addresses: FR-007, FR-008, SC-004, SC-005, SC-006*

1. **Bootstrap**: Perform **observation-level resampling** (n=1000 per dataset) to estimate Confidence Intervals for correlation coefficients. **Dataset-level bootstrap with 5 datasets is invalid**; observation-level provides meaningful uncertainty quantification.
 - **How FR-007 addressed**: Bootstrap within each dataset; compute 95% CI for each correlation; store in `data/analysis/bootstrap_ci.csv`.
 - **How SC-004 addressed**: CI width computed for each correlation; uncertainty quantified per dataset.
2. **Visualize**: Generate correlation heatmap and scatter plots with regression lines. Save to `data/analysis/figures/`.
 - **How FR-008 addressed**: ≥2 figures generated; correlation heatmap shows all metric pairs; scatter plots show regression relationships with CIs.
3. **Monitor**: Track runtime (alert if >5 hours) and memory (alert if >6 GB). Total pipeline must complete within 6 hours and ≤7 GB RAM.
 - **How SC-005 addressed**: Runtime logged to `data/analysis/logs/runtime.log`; alert if approaching 6-hour limit.
 - **How SC-006 addressed**: Memory usage tracked via `tracemalloc`; logged to `data/analysis/logs/memory.log`.
4. **Finalize**: Commit analysis artifacts to `data/`. Update state/ with artifact hashes.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-algorithmic-fair/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ └── fairness-metrics-output.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── download/
│ └── download_datasets.py
├── preprocess/
│ └── preprocess_data.py
├── analysis/
│ ├── train_models.py
│ ├── compute_metrics.py
│ ├── regression_analysis.py
│ └── bootstrap_analysis.py
├── viz/
│ └── generate_plots.py
├── utils/
│ └── helpers.py
└── main.py

data/
├── raw/
├── processed/
└── analysis/

tests/
├── unit/
└── integration/
```

**Structure Decision**: Single project structure under `code/` to simplify dependency management and ensure reproducibility on CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Fixed-Effects Regression** | Required to model dataset-level variance with only ≥5 datasets (LMM with random slopes unstable). | LMM with random slopes requires ~10-20 groups for reliable variance estimation; would produce unstable coefficients. |
| **Observation-Level Bootstrap** | Required for meaningful uncertainty quantification with small dataset count. | Dataset-level bootstrap with 5 items provides no variance reduction; observation-level within datasets is statistically valid. |
| **FDR Correction** | Required to balance Type I/II error risk with 15 tests on 5 datasets. | Bonferroni correction (α≈0.0033) is overly conservative for exploratory analysis; increases Type II error risk. |
| **Sampling to 100k** | Required to fit 7 GB RAM constraint on GitHub Actions free-tier. | Full datasets may exceed memory; stratified sampling preserves outcome distribution. |


## projects/PROJ-099-statistical-analysis-of-algorithmic-fair/specs/001-statistical-analysis-of-algorithmic-fair/research.md

# Research: Statistical Analysis of Algorithmic Fairness Metrics

## Dataset Strategy

The system MUST use ONLY the verified URLs listed below. If a dataset lacks required variables (binary protected attribute, binary outcome, ≥3 features), it MUST be skipped and logged (per Edge Case).

| Dataset Source | Verified URL | Expected Variables | Fit Status |
|:--- |:--- |:--- |:--- |
| **COMPAS Recidivism** | ` | Protected (Race), Outcome (Recidivism), Features | **High** (Known fairness dataset) |
| **COMPAS Priors** | ` | Protected (Race), Outcome (Recidivism), Features | **High** (Known fairness dataset) |
| **Synthetic Compassion** | ` | Protected, Outcome, Features | **High** (Verify binary attributes) |
| **UCI Adult Income** | ` | Protected (Race/Gender), Outcome (Income >50K), Features | **High** (Standard fairness benchmark) |
| **German Credit** | ` | Protected (Age/Gender), Outcome (Credit Default), Features | **High** (Standard fairness benchmark) |
| **Law School Admission** | ` | Protected (Race), Outcome (Bar Passage), Features | **High** (Standard fairness benchmark) |

**Dataset Variable Fit Note**: The spec requires ≥5 datasets with binary protected attributes and binary outcomes. The verified list contains a number of datasets with high expected fit. (COMPAS variants, Synthetic Compassion, UCI Adult, German Credit, Law School Admission). If any dataset lacks required variables, it will be skipped and logged. If <5 suitable datasets are found, the plan will proceed with available datasets and document this constraint in the final report per Constitution Principle IV (Single Source of Truth).

**Fallback Strategy**: If <5 suitable datasets are found after processing all verified URLs:
1. Document constraint in `data/processed/logs/dataset_constraint.log`
2. Proceed with available datasets (minimum 3 for correlation analysis)
3. Frame findings as preliminary/exploratory in final report
4. Note limitation in paper methodology section

## Statistical Methodology

### Construct Validity

**Base Rate Difference Definition**: Base rate is the proportion of positive outcomes in each protected group. Base rate difference is defined as:
```
base_rate_diff = |P(Y=1|A=1) - P(Y=1|A=0)|
```
where A=1 is the protected group and A=0 is the unprotected group. This represents the absolute difference in outcome prevalence between groups.

### Correlation Analysis
- **Method**: Pearson/Spearman correlation between metric pairs at **dataset-model aggregated level**. Metrics are nested within models within datasets; clustering-robust standard errors used to avoid Type I error inflation from hierarchical nesting.
- **Circular Validation Avoidance**: Base-rate-dependent metrics (demographic parity, disparate impact) are NOT correlated with base_rate_diff as predictor in regression. These relationships reported descriptively only to avoid circular validation where outcome is partially determined by predictor.
- **Correction**: Benjamini-Hochberg False Discovery Rate (FDR) control applied for family-wise error rate across ≥15 pairwise tests. FDR chosen over Bonferroni because with 15 tests on 5 datasets, Bonferroni (α≈0.0033) is overly conservative and risks Type II errors.
- **Uncertainty**: 95% Confidence Intervals via **observation-level bootstrap resampling** (n=1000 per dataset). Dataset-level bootstrap with 5 datasets is invalid; observation-level provides meaningful uncertainty quantification.

### Regression Modeling
- **Model**: **Fixed-effects linear regression** (not LMM with random slopes). With ≥5 datasets, random effects estimation is statistically unreliable (a sufficient number of groups recommended for stable variance component estimates). Fixed-effects model includes dataset as fixed factor.
- **Fixed Effects**: Base rate difference (primary predictor), feature dimensionality, class imbalance ratio.
- **Random Effects**: None (fixed-effects model due to small N).
- **Collinearity**: Variance Inflation Factor (VIF) diagnosed for predictors. If base_rate_diff and class_imbalance_ratio VIF >5, effects reported descriptively rather than claiming independent predictive effects (per Assumption on predictor collinearity).
- **Causal Framing**: Observational design; claims framed as associational, not causal (per Assumption).
- **Power & Sample Size**: With ≥5 datasets, regression power is severely limited. Findings are exploratory and preliminary. Bootstrap mitigates uncertainty in correlation estimates. Final report will explicitly acknowledge power limitation.

### Multiple Comparison Control

| Method | Adjusted Alpha | Type I Error | Type II Error | Suitability |
|:--- |:--- |:--- |:--- |:--- |
| Bonferroni | 0.05/15 ≈ 0.0033 | Low | High | Poor (overly conservative for 5 datasets) |
| FDR (BH) | ~0.05 | Moderate | Moderate | **Good** (balanced for exploratory analysis) |

FDR selected for this project to balance Type I and Type II error risk in exploratory analysis with limited sample size.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (standard CPU, 7 GB RAM, 14 GB disk).
- **GPU**: None. No CUDA, no quantization.
- **Memory**: Data sampled to ≤100k rows to ensure ≤7 GB RAM usage.
- **Runtime**: Total pipeline ≤6 hours.
- **Libraries**: `scikit-learn`, `statsmodels`, `pandas` (CPU-tractable).

## Decision Rationale

1. **Why Fixed-Effects Regression?**: LMM with random slopes requires ~10-20 groups for reliable variance estimation; with ≥5 datasets, random effects are unstable. Fixed-effects is statistically valid for small-N.
2. **Why Observation-Level Bootstrap?**: Dataset-level bootstrap with 5 items provides no variance reduction; observation-level within datasets provides meaningful uncertainty quantification for correlation estimates.
3. **Why Sampling?**: Ensures compliance with 7 GB RAM constraint on GitHub Actions free-tier.
4. **Why FDR over Bonferroni?**: With multiple tests on several datasets, Bonferroni is overly conservative and increases Type II error risk. FDR provides better balance for exploratory analysis.
5. **Why Avoid Circular Validation?**: Base-rate-dependent metrics (demographic parity, disparate impact) are definitionally related to base_rate_diff; correlating them creates circular validation. These relationships reported descriptively only.

## Dataset Variable Fit Confirmation

Before analysis proceeds, each dataset will be validated to confirm it contains:
- Binary protected attribute (e.g., Race: White/Non-White, Gender: Male/Female)
- Binary outcome (e.g., Recidivism: Yes/No, Income: >50K/≤50K)
- ≥3 numeric features for model training

Datasets failing validation will be skipped and logged. If <5 datasets pass validation, the constraint will be documented and analysis will proceed with available datasets.
