# Specification for Quantifying the Impact of Data Cleaning

## Overview
This document defines the functional requirements, success criteria, and research hypotheses for the project **Quantifying the Impact of Data Cleaning on Statistical Inference**.

## User Stories & Testing

### User Story US-001 – Assess Impact of Cleaning (Priority: P1)
**Why this priority**: Understanding how common cleaning operations affect statistical inference is the core scientific question and drives all downstream analyses.
**Independent Test**: Run the full pipeline on a single verified dataset and verify that all delta metrics, assumption checks, and robustness fall‑backs are produced as specified.
**Acceptance Scenarios**:
1. **Given** a dataset with a documented outcome variable, **When** the baseline analysis and each cleaned variant are executed, **Then** a `delta_metrics.json` entry containing numeric `p_value_delta` (3‑decimal) **and** a `direction` flag with values “increase” or “decrease” is written for that dataset.
2. **Given** the same dataset, **When** assumption checks detect violations for a continuous outcome, **Then** the pipeline automatically switches to robust tests and records the fallback in `cleaned_metrics.json` with `assumptions_met: false`.

### User Story US-002 – Sensitivity to Size & Missingness (Priority: P2)
**Why this priority**: The effect of cleaning may depend on dataset size and missingness; quantifying this sensitivity is required for generalizable conclusions.
**Independent Test**: For each size‑bin (n < 64, 64‑200, >200) and missingness level ([deferred], [deferred], [deferred], [deferred]), run the pipeline on at least one dataset and verify that stratified reports are produced.
**Acceptance Scenarios**:
1. **Given** a dataset in the “64‑200” size bin with [deferred] artificially introduced missingness, **When** the sensitivity analysis runs, **Then** the results appear in `sensitivity_metrics.json` and include the bin identifier.

### User Story US-003 – Reproducibility & Contract Compliance (Priority: P3)
**Why this priority**: Guarantees that all artefacts conform to agreed‑upon schemas, enabling downstream validation and reuse.
**Independent Test**: Execute the validation script; it must pass without errors for dataset, baseline, cleaned, delta, and bootstrap artefacts.
**Acceptance Scenarios**:
1. **Given** the downloaded raw datasets, **When** the schema validator runs, **Then** it confirms compliance with `contracts/dataset.schema.yaml`.
2. **Given** the generated `baseline_metrics.json`, **When** the result validator runs, **Then** it confirms compliance with `contracts/baseline_metrics.schema.yaml`.

## Functional Requirements

### FR-001 – Baseline Analysis (See US-001)
- Download **at least 10 distinct** public datasets that have a clearly documented **binary or continuous** outcome variable (see dataset list below). The collection must include at least one dataset in each size bin (n < 64, 64‑200, >200). Multi‑class categorical outcomes are excluded unless transformed to a binary indicator.
- **Statistical testing conditional on outcome type**:
 *For binary outcomes*: perform chi‑square (or Fisher’s exact when cell counts < 5) and logistic regression.
 *For continuous outcomes*: perform two‑sample t‑test (Welch’s t‑test when variances differ) and ordinary linear regression.
- Store raw test results (p‑values, 95 % confidence intervals, effect‑size metrics) **without delta fields** in `data/processed/baseline_metrics.json`.
- Validate each raw dataset against `contracts/dataset.schema.yaml` before analysis.
- Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation.
- Generate `data/processed/dataset_metadata.json` containing the verified outcome column name, sample size, and missingness proportion for every dataset and validate it against `contracts/dataset.schema.yaml`.

**Verified Datasets (examples)**
- UCI Wine Quality – outcome: `quality` – https://archive.ics.uci.edu/ml/datasets/Wine+Quality
- UCI Breast Cancer Wisconsin Diagnostic – outcome: `diagnosis` – (Diagnostic)
- UCI Heart Disease – outcome: `target` – https://archive.ics.uci.edu/ml/datasets/Heart+Disease
- UCI Parkinsons Telemonitoring – outcome: `total_UPDRS` – https://archive.ics.uci.edu/ml/datasets/Parkinsons+Telemonitoring
- UCI Diabetes – outcome: `progression` – https://archive.ics.uci.edu/ml/datasets/Diabetes
- UCI Statlog (German Credit Data) – outcome: `credit_risk` – (German+Credit+Data)
- UCI Adult Income – outcome: `income` – https://archive.ics.uci.edu/ml/datasets/Adult
- UCI Student Performance – outcome: `G3` – https://archive.ics.uci.edu/ml/datasets/Student+Performance
- UCI Car Evaluation – outcome: `class_value` – https://archive.ics.uci.edu/ml/datasets/Car+Evaluation
- UCI Ionosphere – outcome: `target` – https://archive.ics.uci.edu/ml/datasets/Ionosphere

*All listed datasets provide clear documentation of the dependent variable and are freely downloadable.*

### FR-002 – Outlier Removal (See US-001)
- Implement IQR‑based outlier detection with configurable threshold *k* (default **k = 1.5**).
- Log the number of rows removed and warn if **≥ 50 %** of rows are removed.

### FR-003 – Imputation (See US-001)
- Provide mean, median, and K‑nearest‑neighbour imputation strategies.
- Ensure no missing values remain after imputation and warn if variance reduction **≥ 20 %**.

### FR-004 – Categorical Recoding (See US-001)
- Encode **nominal** variables with ≤ 10 distinct categories using **one‑hot encoding**.
- Encode **ordinal** variables or nominal variables with > 10 categories using **integer label encoding** that preserves order where applicable.
- All encoded columns must be numeric and suitable for downstream tests.

### FR-005 – Outcome Variable Definition (See US-001)
- For each dataset, verify that a column is explicitly designated as the dependent variable in the dataset’s documentation.
- Record the name of this column in `data/processed/dataset_metadata.json`.
- **Do not** infer the outcome column by variance; it must be documented.

### FR-006 – Outlier Threshold Sweep (See US-001)
- Perform outlier removal using the IQR method with threshold multipliers **k = 1.5** and **k = 2.0**.
- For each threshold, generate a cleaned version of every dataset and re‑run the baseline statistical analyses.
- Record per‑threshold metrics (p‑values, confidence intervals, effect sizes) in `cleaned_metrics.json`.

### FR-007 – Multiple‑Comparison Adjustment (See US-001)
- **No multiple‑comparison correction will be applied** across cleaning‑variant p‑values. This decision is documented for traceability; all p‑values are reported unadjusted.

### FR-008 – Sensitivity Analysis (See US-002)
- Stratify analyses by dataset size bins (**n < 64**, **64‑200**, **>200**) and missingness levels ([deferred], [deferred], [deferred], [deferred]).
- Ensure at least **one** dataset appears in each bin; if a bin is empty, acquire an additional public dataset that satisfies the missingness and size criteria.
- Store stratified results in `data/processed/sensitivity_metrics.json`.

### FR-009 – Dataset Schema Validation (See US-003)
- Validate each downloaded raw dataset against `contracts/dataset.schema.yaml`.
- Abort processing with a clear error if validation fails.

### FR-010 – Baseline Metrics Schema Validation (See US-003)
- Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation.

### FR-011 – Cleaned Metrics Schema Validation (See US-003)
- Validate `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml` after generation.

### FR-012 – Cleaning Metadata Capture (See US-001)
- Each cleaning function returns a metadata dict containing `rows_removed`, `missing_before`, `missing_after`, and `variance_reduction`.
- These fields are written to `cleaned_metrics.json` for every variant.

### FR-013 – Cleaning Metadata Schema Validation (See US-003)
- Validate the cleaning‑metadata fields in `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml`.

### FR-014 – Bootstrap Variance Estimation (See US-002)
- Perform a sufficient number of bootstrap iterations for each cleaned variant; store bootstrap confidence intervals in `bootstrap_metrics.json`.
- The iteration count is **configurable via `BOOTSTRAP_ITERATIONS` (default = 1000)** and must be passed explicitly; no fallback to fewer iterations is permitted.

### FR-015 – Bin‑Coverage Dataset Acquisition (See US-002)
- If any size‑bin or missingness‑level bin lacks a dataset, automatically trigger a download of a public dataset that satisfies the missingness and size requirements, updating the dataset list accordingly.

### FR-016 – A Priori Power Analysis (See US-001)
- Conduct a power analysis appropriate to the outcome type:
 *Binary outcomes*: use `statsmodels.stats.proportion.proportions_ztest` effect size (difference in proportions) with medium effect (Δ = 0.2).
 *Continuous outcomes*: use two‑sample t‑test effect size (Cohen’s d = 0.5).
- Target α = 0.05, power ≥ 0.8. Determine the minimum total number of rows **(≥ 130 per size bin)** and the minimum number of datasets required.
- Record the analysis results, required totals, and justification in **`power_analysis.txt`**.

### FR-017 – Dataset Metadata Generation & Validation (See US-001)
- Create `data/processed/dataset_metadata.json` containing, for each dataset, the outcome column name, sample size, and missingness proportion.
- Validate this file against `contracts/dataset.schema.yaml`.

### FR-018 – Comparison Report Generation (See US-003)
- Produce a final `comparison_report.json` conforming to `contracts/comparison_report.schema.yaml` that aggregates all delta metrics, CI overlap, effect‑size changes, and (where applicable) assumption‑check flags across datasets.

### FR-019 – Principle II Verification Step (See US-003)
- Run the citation‑validation script defined in the project constitution to verify that all external claims (e.g., dataset provenance, statistical method citations) are accurately referenced. Log the verification outcome.

### FR-020 – Hypothesis‑Testing on Δ Metrics (See US-001)
- **Removed** – formal paired Wilcoxon test on `p_value_delta` is out of scope.

### FR-021 – Confidence‑Interval Overlap & Effect‑Size Change Metrics (See US-001)
- For each dataset and cleaning variant, calculate the proportion of overlap between baseline and cleaned 95 % confidence intervals (`ci_overlap`) and the absolute change in effect size (`effect_size_change`). Store these in both `baseline_metrics.json` and `cleaned_metrics.json`.
- **Delta metrics** (`p_value_delta`, `direction`) are stored exclusively in `delta_metrics.json`.

### FR-022 – Assumption Checks & Robust Fallback (See US-001)
- For **continuous** outcomes, assess before each test:
 * Normality via **Shapiro‑Wilk** (α = 0.05).
 * Homoscedasticity via **Levene’s test** (α = 0.05).
 * Linearity via residual‑scatter inspection (automated R‑squared check ≥ 0.7).
- If any violation is detected, automatically switch to robust alternatives (Welch’s t‑test, rank‑based regression) and flag the change in `cleaned_metrics.json` with `assumptions_met: false`.
- Record the resulting `p_value_delta` and `direction` for each variant in `delta_metrics.json`.

### FR-023 – Power Analysis Output Validation (See US-001)
- Verify that `power_analysis.txt` exists, is parseable, and that the required total sample size and dataset count meet or exceed the thresholds computed in FR‑016. Fail the pipeline if the justification is insufficient.

### FR-024 – Bin Power Adequacy (See US-002)
- Ensure each size bin (**n < 64**, **64‑200**, **>200**) contains a **cumulative sample size of at least 130 rows**, satisfying the medium‑effect power requirement from FR‑016. If a bin fails, acquire additional datasets until the requirement is satisfied.

### FR-025 – Cleaned Metrics Schema Definition (See US-001)
- Provide `contracts/cleaned_metrics.schema.yaml` defining the required fields: `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, `ci_overlap`, `effect_size_change`, `p_value_delta`, `direction`.
- Validation of `cleaned_metrics.json` against this schema is performed in FR‑011 and FR‑013.

### FR-026 – Bootstrap Configuration Enforcement (See US-002)
- The pipeline must read `BOOTSTRAP_ITERATIONS` from `config.py` and pass it explicitly to all bootstrap functions. No automatic reduction of iterations is allowed; if the variable is missing, the pipeline aborts with an error.

## Success Criteria

- **SC-001** – Per‑dataset delta reporting (See US-001)
 Each dataset’s output must include a JSON object in `delta_metrics.json` with fields `p_value_delta` (numeric, three‑decimal precision), `direction` (string “increase” or “decrease”), `ci_overlap` (numeric 0‑1), and `effect_size_change` (numeric). Validation script asserts presence, type, and precision.

- **SC-002** – Metric precision (See US-001)
 All numeric metrics (p‑values, confidence intervals, effect sizes, ci_overlap) are stored with ≥ 3‑decimal precision.

- **SC-003** – Visualizations (See US-001)
 Forest plot and heatmap are saved under `output/figures/` and referenced in the final report.

- **SC-004** – Bootstrap variance estimation (See US-002)
 Perform a sufficient number of bootstrap iterations for each cleaned variant; store bootstrap confidence intervals in `bootstrap_metrics.json`.

- **SC-005** – Outcome variable verification (See US-001)
 `dataset_metadata.json` contains the verified outcome column name for every dataset; validation ensures the column exists and is numeric (for continuous) or binary (for binary).

- **SC-006** – Assumption checks and robust fallback (See FR-022)
 For continuous outcomes, a boolean flag `assumptions_met` is recorded; if false, the robust alternative’s results are stored and flagged. No permutation‑based FPR requirement remains.

- **SC-007** – Stratified analysis coverage (See US-002)
 Each size‑bin (n < 64, 64‑200, >200) and each missingness level ([deferred], [deferred], [deferred], [deferred]) contains **≥ 1** dataset; the report includes a table summarizing bin counts.

- **SC-008** – Reproducibility & contract compliance (See US-003)
 All schema validation steps (FR‑009, FR‑010, FR‑011, FR‑013, FR‑017, FR‑018) must pass without errors for every artifact.

- **SC-009** – Power analysis justification (See FR-016)
 The documented power analysis in `power_analysis.txt` must demonstrate that the selected dataset collection meets the power ≥ 0.8 target for the appropriate effect size and that **each size bin contains ≥ 130 rows**. The file must be present, parseable, and contain the computed minimum sample sizes.

- **SC-010** – Bin power adequacy (See FR-024)
 Each size bin satisfies the minimum sample‑size requirement (≥ 130 rows); otherwise the pipeline aborts with a clear message.

- **SC-011** – Principle II verification (See FR-019)
 The citation‑validation script runs successfully and logs that all external claims are properly referenced.

## Research Hypotheses
- **H1 (Associative)**: Outlier removal is *associated* with systematic changes in p‑values, direction, and confidence‑interval overlap; this association will be observed in the descriptive delta metrics across datasets.
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with increased stability of effect‑size estimates, reflected by higher `ci_overlap` and smaller variance in `effect_size_change`.

## Assumptions
- Public datasets listed are freely downloadable and contain a clearly documented binary or continuous outcome variable.
- All statistical tests assume independent observations; if this is violated, robust methods are applied as per FR‑022.
- The computational environment provides Python 3.11 with `scipy`, `statsmodels`, and `pandas`.
- Bootstrap iterations are set to **1 000** by default; this number provides stable variance estimates for the sample sizes considered.
- Normality, homoscedasticity, and linearity checks use significance level **α = 0.05** and are only applied to continuous outcomes.
- Missingness levels for sensitivity analysis are **[deferred]**, **[deferred]**, **[deferred]**, and **[deferred]**.
- Power analysis assumes a medium effect size (Cohen’s d = 0.5 for continuous outcomes; proportion difference Δ = 0.2 for binary outcomes) and targets power ≥ 0.8 at α = 0.05.
- The `delta_metrics.json` file is the sole repository for delta‑specific fields (`p_value_delta`, `direction`).