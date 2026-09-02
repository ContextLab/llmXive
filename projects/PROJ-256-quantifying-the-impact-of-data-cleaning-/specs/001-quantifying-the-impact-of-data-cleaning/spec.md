# Specification for Quantifying the Impact of Data Cleaning

## Overview
This document defines the functional requirements, success criteria, and research hypotheses for the project **Quantifying the Impact of Data Cleaning on Statistical Inference**.

## User Stories & Testing

### User Story US-001 – Assess Impact of Cleaning (Priority: P1)
**Why this priority**: Understanding how common cleaning operations affect statistical inference is the core scientific question and drives all downstream analyses.
**Independent Test**: Run the full pipeline on a single verified dataset and verify that all delta metrics, assumption checks, and multiple‑comparison corrections are produced as specified.
**Acceptance Scenarios**:
1. **Given** a dataset with a documented outcome variable, **When** the baseline analysis and each cleaned variant are executed, **Then** a `delta` entry containing numeric `p_value_delta` (3‑decimal) **and** a `direction` flag with string values “increase” or “decrease” is written for that dataset.
2. **Given** the same dataset, **When** assumption checks detect violations, **Then** the pipeline automatically switches to robust tests and records the fallback in `cleaned_metrics.json`.

### User Story US-002 – Sensitivity to Size & Missingness (Priority: P2)
**Why this priority**: The effect of cleaning may depend on dataset size and missingness; quantifying this sensitivity is required for generalizable conclusions.
**Independent Test**: For each size‑bin (n < 50, 50‑200, >200) and missingness level ([deferred], [deferred], [deferred], [deferred]), run the pipeline on at least one dataset and verify that stratified reports are produced.
**Acceptance Scenarios**:
1. **Given** a dataset in the “50‑200” size bin with [deferred] artificially introduced missingness, **When** the sensitivity analysis runs, **Then** the results appear in `sensitivity_metrics.json` and include the bin identifier.

### User Story US-003 – Reproducibility & Contract Compliance (Priority: P3)
**Why this priority**: Guarantees that all artefacts conform to agreed‑upon schemas, enabling downstream validation and reuse.
**Independent Test**: Execute the validation script; it must pass without errors for dataset, baseline, cleaned, and bootstrap artefacts.
**Acceptance Scenarios**:
1. **Given** the downloaded raw datasets, **When** the schema validator runs, **Then** it confirms compliance with `contracts/dataset.schema.yaml`.
2. **Given** the generated `baseline_metrics.json`, **When** the result validator runs, **Then** it confirms compliance with `contracts/baseline_metrics.schema.yaml`.

## Functional Requirements

### FR-001 – Baseline Analysis (See US-001)
- Download **10–15** public datasets that have a clearly documented **binary or continuous** outcome variable (see dataset list below). The collection must include at least one dataset in each size bin (n < 50, 50‑200, >200). Multi‑class categorical outcomes are excluded unless transformed to a binary indicator.
- Run two‑sample t‑tests (or Welch’s t‑test when variances differ) and linear regressions on the raw (uncleaned) data.
- Store p‑values, 95 % confidence intervals, effect‑size metrics, **p_value_delta**, **direction** (“increase”/“decrease”), **ci_overlap** (proportion of overlapping confidence intervals), and **effect_size_change** in `data/processed/baseline_metrics.json`.
- Validate each raw dataset against `contracts/dataset.schema.yaml` before analysis.
- Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation.
- Generate `data/processed/dataset_metadata.json` containing the verified outcome column name for every dataset and validate it against `contracts/dataset.schema.yaml`.

**Verified Datasets (examples)**
First, **UCI Wine Quality** – outcome: `quality` – https://archive.ics.uci.edu/ml/datasets/Wine+Quality
A dataset: **UCI Breast Cancer Wisconsin Diagnostic** – outcome: `diagnosis` – (Diagnostic)
**UCI Heart Disease** – outcome: `target` – https://archive.ics.uci.edu/ml/datasets/Heart+Disease
**UCI Parkinsons Telemonitoring** – outcome: `total_UPDRS` – https://archive.ics.uci.edu/ml/datasets/Parkinsons+Telemonitoring
Dataset entry: **UCI Diabetes** – outcome: `progression` – https://archive.ics.uci.edu/ml/datasets/Diabetes
**UCI Statlog (German Credit Data)** – outcome: `credit_risk` – (German+Credit+Data)
**UCI Adult Income** – outcome: `income` – https://archive.ics.uci.edu/ml/datasets/Adult
- **UCI Student Performance** – outcome: `G3` – https://archive.ics.uci.edu/ml/datasets/Student+Performance
**UCI Car Evaluation** – outcome: `class_value` – https://archive.ics.uci.edu/ml/datasets/Car+Evaluation
A representative dataset – **UCI Ionosphere** – outcome: `target` – https://archive.ics.uci.edu/ml/datasets/Ionosphere

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
- All encoded columns must be numeric and suitable for downstream t‑tests and regressions.

### FR-005 – Outcome Variable Definition (See US-001)
- For each dataset, verify that a column is explicitly designated as the dependent variable in the dataset’s documentation.
- Record the name of this column in `data/processed/dataset_metadata.json`.
- **Do not** infer the outcome column by variance; it must be documented.

### FR-006 – Outlier Threshold Sweep, Assumption Checks & Permutation‑Based FPR Estimation (See US-001)

**Outlier Threshold Sweep**
- Perform outlier removal using the IQR method with threshold multipliers **k = 1.5** and **k = 2.0**.
- For each threshold, generate a cleaned version of every dataset and re‑run the baseline statistical analyses.
- Record per‑threshold metrics (p‑values, confidence intervals, effect sizes).

**Assumption Checks**
- Before each test, assess:
 * Normality via **Shapiro‑Wilk** (α = 0.05).
 * Homoscedasticity via **Levene’s test** (α = 0.05).
 * Linearity via residual‑scatter inspection (automated R‑squared check ≥ 0.7).
- If any violation is detected, automatically switch to robust alternatives (Welch’s t‑test, rank‑based regression) and flag the change in `cleaned_metrics.json` with `assumptions_met: false`.

**Permutation‑Based False‑Positive‑Rate (FPR) Estimation**
- For each cleaning variant, **first** permute the outcome variable **before** any cleaning step, preserving covariate structure. Perform a substantial number of permutations under both MCAR and MAR missingness mechanisms..
- Run the full cleaning pipeline on each permuted dataset and compute the proportion of permutations that yield a significant result (p < 0.05) after Holm‑Bonferroni correction. This proportion is the estimated FPR.
- Record the FPR in `cleaned_metrics.json` and require **FPR ≤ 0.05** for a variant to be considered trustworthy.

### FR-007 – Multiple‑Comparison Correction Across Variants (See US-001)
- Apply **Holm‑Bonferroni** correction across **all** cleaning‑variant p‑values **within each dataset** to control the family‑wise error rate at **α = 0.05**.
- Record adjusted p‑values in `cleaned_metrics.json`.

### FR-008 – Sensitivity Analysis (See US-002)
- Stratify analyses by dataset size bins (**n < 50**, **50‑200**, **>200**) and missingness levels (**[deferred]**, **[deferred]**, **[deferred]**, **[deferred]**).
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
- Perform a sufficient number of bootstrap iterations for each cleaned variant.; store bootstrap confidence intervals in `bootstrap_metrics.json`.
- The iteration count is configurable via `BOOTSTRAP_ITERATIONS` (default **1000**). No fallback to fewer iterations is permitted.

### FR-015 – Bin‑Coverage Dataset Acquisition (See US-002)
- If any size‑bin or missingness‑level bin lacks a dataset, automatically trigger a download of a public dataset that satisfies the missingness and size requirements, updating the dataset list accordingly.

### FR-016 – A Priori Power Analysis (See US-001)
- Conduct a power analysis assuming a medium effect size (Cohen’s d = 0.5), α = 0.05, desired power ≥ 0.8. Determine the minimum total number of rows and datasets required; the analysis must justify that the selected 10–15 datasets meet or exceed this requirement.

### FR-017 – Dataset Metadata Generation & Validation (See US-001)
- Create `data/processed/dataset_metadata.json` containing, for each dataset, the outcome column name, sample size, and missingness proportion. Validate this file against `contracts/dataset.schema.yaml`.

### FR-018 – Comparison Report Generation (See US-003)
- Produce a final `comparison_report.json` conforming to `contracts/comparison_report.schema.yaml` that aggregates all delta metrics, CI overlap, effect‑size changes, and FPR values across datasets.

### FR-019 – Principle II Verification Step (See US-003)
- Run the citation‑validation script defined in the project constitution to verify that all external claims (e.g., dataset provenance, statistical method citations) are accurately referenced. Log the verification outcome.

### FR-020 – External Benchmark Simulation (See US-001)
- Generate synthetic datasets with known null effect (true effect size = 0) and known non‑null effect (Cohen’s d = 0.5). Run the full cleaning pipeline on these benchmarks to provide an independent assessment of bias introduced by cleaning operations.

### FR-021 – Hypothesis‑Testing on Δ Metrics (See US-001)
- Compute paired statistical tests (Wilcoxon signed‑rank) on the vector of `p_value_delta` across all datasets for each cleaning operation. Record the test statistic and p‑value in `hypothesis_test_results.json`.

### FR-022 – Confidence‑Interval Overlap & Effect‑Size Change Metrics (See US-001)
- For each dataset and cleaning variant, calculate the proportion of overlap between baseline and cleaned 95 % confidence intervals (`ci_overlap`) and the absolute change in effect size (`effect_size_change`). Store these in `baseline_metrics.json` and `cleaned_metrics.json`.

## Success Criteria

- **SC-001** – Per‑dataset delta reporting (See US-001)  
  Each dataset’s output must include a JSON object with fields `p_value_delta` (numeric, three‑decimal precision), `direction` (string “increase” or “decrease”), `ci_overlap` (numeric 0‑1), and `effect_size_change` (numeric). Validation script asserts presence, type, and precision.

- **SC-002** – Metric precision (See US-001)  
  All numeric metrics (p‑values, confidence intervals, effect sizes, ci_overlap) are stored with ≥ 3‑decimal precision.

- **SC-003** – Visualizations (See US-001)  
  Forest plot and heatmap are saved under `output/figures/` and referenced in the final report.

- **SC-004** – Bootstrap variance estimation (See US-002)  
  Perform at least **1 000** bootstrap iterations for each cleaned variant; store bootstrap confidence intervals in `bootstrap_metrics.json`.

- **SC-005** – Outcome variable verification (See US-001)  
  `dataset_metadata.json` contains the verified outcome column name for every dataset; validation ensures the column exists and is numeric.

- **SC-006** – Assumption checks and robust fallback (See US-001)  
  For each test, a boolean flag `assumptions_met` is recorded; if false, the robust alternative’s results are stored and flagged. Additionally, the permutation‑based FPR for each variant must satisfy **FPR ≤ 0.05**.

- **SC-007** – Family‑wise error rate control (See US-001)  
  Adjusted p‑values after Holm‑Bonferroni must satisfy **FWER ≤ 0.05**; the script asserts this bound.

- **SC-008** – Stratified analysis coverage (See US-002)  
 Each size‑bin (n < 50, 50‑200, >200) and each missingness level ([deferred], [deferred], [deferred], [deferred]) contains **≥ 1** dataset; the report includes a table summarizing bin counts.

- **SC-009** – Reproducibility & contract compliance (See US-003)  
  All schema validation steps (FR‑009, FR‑010, FR‑011, FR‑013, FR‑017, FR‑018) must pass without errors for every artifact.

- **SC-010** – Power analysis justification (See US-001)  
  The documented power analysis (FR‑016) must demonstrate that the selected dataset collection meets the required power ≥ 0.8 for detecting a medium effect size.

- **SC-011** – Hypothesis‑testing of cleaning impact (See US-001)  
  The paired Wilcoxon test on `p_value_delta` (FR‑021) must yield a statistically significant result (p < 0.05) for at least one cleaning operation, confirming an association.

- **SC-012** – External benchmark validation (See US-001)  
  Results on synthetic benchmark datasets (FR‑020) must show that the estimated FPR on null‑effect data does not exceed 0.05 and that the effect‑size recovery on non‑null data meets a tolerance of ±0.1.

## Research Hypotheses
- **H1 (Associative)**: Outlier removal is *associated* with systematic changes in p‑values, direction, and confidence‑interval overlap; this association will be detected by the paired Wilcoxon test on `p_value_delta` (SC‑011).
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with increased stability of effect‑size estimates, reflected by reduced variance and higher `ci_overlap` (SC‑012).

## Assumptions
- Public datasets listed are freely downloadable and contain a clearly documented binary or continuous outcome variable.
- All statistical tests assume independent observations; if this is violated, robust methods are applied as per FR‑006.
- The computational environment provides Python 3.11 with `scipy`, `statsmodels`, and `pandas`.
- Bootstrap iterations are set to **1 000** by default; this number provides stable variance estimates for the sample sizes considered.
- Normality, homoscedasticity, and linearity checks use significance level **α = 0.05**.
- Missingness levels for sensitivity analysis are **no missingness (baseline)**, **[deferred]**, **[deferred]**, and **[deferred]**..
- Power analysis assumes a medium effect size (Cohen’s d = 0.5) and targets power ≥ 0.8 at α = 0.05.