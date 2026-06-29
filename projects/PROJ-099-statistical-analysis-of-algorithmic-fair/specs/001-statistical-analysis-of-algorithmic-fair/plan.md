# Implementation Plan: Fairness Metric Divergence Analysis

**Branch**: `001-fairness-metric-divergence-analysis` | **Date**: 2024-01-15 | **Spec**: `specs/001-fairness-metric-divergence-analysis/spec.md`
**Input**: Feature specification from `/specs/001-fairness-metric-divergence-analysis/spec.md`

## Summary

Analyze statistical patterns in algorithmic fairness metric discrepancies across datasets and predict divergence from dataset characteristics. The technical approach involves downloading multiple public datasets with binary protected attributes and outcomes, training multiple baseline models per dataset, computing multiple fairness metrics, performing correlation analysis with multiple-comparison correction, and fitting OLS regression models (with dataset and model as categorical covariates) to predict metric discrepancies from dataset characteristics.

> **Note on Terminology**: The spec.md User Story 3 uses "fixed-effects regression" terminology. Per research.md clarification, this implementation uses OLS regression with dataset characteristics as predictors. Including dataset/model as categorical covariates would consume 4+ degrees of freedom with n=5 datasets, leaving insufficient power for additional predictors. The spec terminology is acknowledged but implementation follows OLS approach.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: scikit-learn, statsmodels, pandas, numpy, scipy, requests, hashlib
**Storage**: Local filesystem (data/, logs/, data/analysis/)
**Testing**: pytest
**Target Platform**: Linux (GitHub Actions free-tier)
**Project Type**: computational research project
**Performance Goals**: Complete all phases within 6-hour GitHub Actions job window
**Constraints**: CPU-only execution, ≤7 GB RAM, ≤14 GB disk, no GPU/CUDA
**Scale/Scope**: multiple datasets, multiple models per dataset, multiple fairness metrics, Multiple bootstrap iterations (reducible as necessary)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Random seeds pinned in code/, external datasets fetched from canonical sources, checksums recorded in data/ |
| II. Verified Accuracy | PASS | All citations validated against primary sources before contributing review points |
| III. Data Hygiene | PASS | Datasets checksummed, no in-place modifications, PII scan required |
| IV. Single Source of Truth | PASS | All figures/statistics trace to data/ and code/, no hand-typed numbers |
| V. Versioning Discipline | PASS | Content hashes for all artifacts, updated_at timestamp on state file |
| VI. Fairness Metric Transparency | PASS | Dataset characteristics stored in data/, referenced in figures/tables |
| VII. Statistical Rigor in Fairness Evaluation | PASS | Correlation analysis with effect sizes and CIs, methodology documented in code/, power analysis documented in research.md |

## Project Structure

### Documentation (this feature)

```text
specs/001-fairness-metric-divergence-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-099-statistical-analysis-of-algorithmic-fair/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_data_acquisition.py
│   ├── 02_preprocessing.py
│   ├── 03_model_training.py
│   ├── 04_fairness_metrics.py
│   ├── 05_correlation_analysis.py
│   ├── 06_regression_analysis.py
│   ├── 07_bootstrap_analysis.py
│   ├── 08_metric_guidance.py
│   └── utils/
│       ├── metrics.py
│       ├── dataset_loaders.py
│       └── validators.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── analysis/
│       ├── metrics.csv
│       ├── correlations.csv
│       ├── regression_results.csv
│       ├── bootstrap_results.csv
│       └── guidance.csv
├── logs/
│   └── exclusion.log
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── state/
    └── projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml
```

**Structure Decision**: Single project structure under projects/PROJ-099 with modular code/ directory for computational pipeline. Data stored in data/ with raw/ for downloaded files, processed/ for preprocessed datasets, and analysis/ for computed results. Logs stored in logs/ for exclusion events. Tests organized by type (contract, integration, unit).

## Implementation Phases

### Phase 0: Dataset Acquisition (FR-001, FR-002)

**Objective**: Download and validate 5-8 public datasets with binary protected attributes and outcomes.

**Steps**:
1. Download datasets from verified sources (COMPAS, UCI Adult, Bank Marketing, German Credit, Law School)
2. Verify SHA-256 checksums for all downloaded files
3. Validate presence of required variables (protected_attribute, outcome, predictions)
4. Sample datasets >100k rows to ≤100k using stratified sampling
5. Log exclusions to logs/exclusion.log with dataset_id and missing_variable_name

**Output**: Validated datasets in data/processed/ with checksums recorded

**FR Coverage**: FR-001, FR-002

**SC Coverage**: SC-001 (measured against research design requirements)

### Phase 1: Model Training (FR-003)

**Objective**: Train multiple baseline models per dataset using scikit-learn.

**Steps**:
1. Split each dataset into train/test (stratified)
2. Train Logistic Regression, Random Forest, Gradient Boosting models
3. Pin random seeds for reproducibility
4. Save trained models to data/processed/models/

**Output**: Trained models with performance metrics

**FR Coverage**: FR-003

### Phase 2: Fairness Metric Computation (FR-004)

**Objective**: Compute ≥6 fairness metrics per model.

**Steps**:
1. Generate predictions on test set for each model
2. Compute: demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity
3. Document formulas per Appendix A
4. Store metrics in data/analysis/metrics.csv with model_id, dataset_id, protected_attribute

**Output**: Fairness metrics matrix

**FR Coverage**: FR-004

**SC Coverage**: SC-002 (measured against documented formulas)

### Phase 3: Correlation Analysis (FR-005)

**Objective**: Compute pairwise correlations between all metric pairs with multiple-comparison correction.

**Steps**:
1. Compute Pearson and Spearman correlations for all metric pairs (≥15 pairs for 6 metrics)
2. Apply Benjamini-Hochberg FDR correction (α=0.05)
3. Document mathematical dependencies: exclude DP-difference vs DI-ratio pairs due to theoretical relationship
4. Store correlations in data/analysis/correlations.csv with p-values and q-values

**Output**: Correlation matrix with corrected q-values

**FR Coverage**: FR-005

**SC Coverage**: SC-003, SC-004 (measured against total metric pairs and FDR correction)

### Phase 4: Regression Analysis (FR-006)

**Objective**: Fit OLS regression models to predict metric discrepancies from dataset characteristics.

**Steps**:
1. Compute dataset characteristics: feature dimensionality, class imbalance ratio (exclude base rate difference for DP models due to theoretical circularity per research.md)
2. Fit OLS regression with dataset and model as categorical covariates
3. Apply VIF diagnostics; exclude predictors with VIF > 5
4. Document effect size bounds and acknowledge n=5 dataset limitation
5. Store results in data/analysis/regression_results.csv

**Output**: Regression coefficients with VIF diagnostics

**FR Coverage**: FR-006

**SC Coverage**: SC-005 (measured against power analysis documentation in research.md)

**Note**: With n=15 observations (5 datasets × 3 models) and 3 predictors, minimum detectable R² of practical significance at α=0.05, power=0.80. This limitation is documented in all findings.

### Phase 5: Bootstrap Analysis (FR-007)

**Objective**: Estimate 95% confidence intervals for correlation coefficients via bootstrap resampling.

**Steps**:
1. Perform bootstrap resampling (n=1000 iterations, reducible to n=500 if time-constrained)
2. Compute 95% CIs for all correlation coefficients
3. Log iteration count and any reductions to logs/exclusion.log
4. Store results in data/analysis/bootstrap_results.csv

**Output**: Bootstrap confidence intervals

**FR Coverage**: FR-007

### Phase 6: Associational Framing (FR-008)

**Objective**: Ensure all outputs frame findings as associational only.

**Steps**:
1. Add disclaimer "Findings are associational only; no causal claims are made." to all reports and console output
2. Review all documentation for prescriptive language
3. Cross-reference FR-008 in FR-009 guidance output

**Output**: All documentation with associational disclaimer

**FR Coverage**: FR-008

### Phase 7: Metric Selection Guidance (FR-009)

**Objective**: Generate associational guidance mapping dataset characteristics to metric associations.

**Steps**:
1. Analyze correlation results to identify strongest metric associations with dataset characteristics
2. Generate guidance output in data/analysis/guidance.csv
3. Use associational language: "associations between dataset characteristics and metric values" (NOT "recommended metrics")
4. Include explicit FR-008 disclaimer in guidance output

**Output**: data/analysis/guidance.csv with associational mappings

**FR Coverage**: FR-009

**Note**: Guidance uses associational framing per FR-008; no causal or prescriptive claims made.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple dataset loaders | Different datasets have different formats and access patterns | Single loader cannot handle CSV, parquet, and varying column schemas |
| Separate metric computation module | 6+ metrics with distinct formulas require isolation | Inline computation would be error-prone and hard to validate |
| Bootstrap resampling module | 1000 iterations require dedicated computation | Single-pass approach would not provide confidence intervals |
| Separate guidance module | FR-009 requires explicit guidance output artifact | Inline generation would lack traceability and schema validation |

## FR/SC Coverage Matrix

| FR/SC | Phase | Output Artifact |
|-------|-------|-----------------|
| FR-001 | Phase 0 | data/raw/* with checksums |
| FR-002 | Phase 0 | data/processed/*, logs/exclusion.log |
| FR-003 | Phase 1 | data/processed/models/* |
| FR-004 | Phase 2 | data/analysis/metrics.csv |
| FR-005 | Phase 3 | data/analysis/correlations.csv |
| FR-006 | Phase 4 | data/analysis/regression_results.csv |
| FR-007 | Phase 5 | data/analysis/bootstrap_results.csv |
| FR-008 | Phase 6 | All documentation with disclaimer |
| FR-009 | Phase 7 | data/analysis/guidance.csv |
| SC-001 | Phase 0 | Dataset availability ≥5 with binary attributes |
| SC-002 | Phase 2 | Metrics computed per Appendix A formulas |
| SC-003 | Phase 3 | ≥15 correlation pairs with p-values and CIs |
| SC-004 | Phase 3 | Benjamini-Hochberg FDR correction applied |
| SC-005 | Phase 4 | Power analysis documented in research.md |