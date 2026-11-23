# Specification for Quantifying the Impact of Data Cleaning

## Overview
This document defines the functional requirements, success criteria, and research hypotheses for the project **Quantifying the Impact of Data Cleaning on Statistical Inference**.

## User Stories & Testing

### User Story US-001 – Assess Impact of Cleaning (Priority: P1)
**Why this priority**: Understanding how common cleaning operations affect statistical inference is the core scientific question and drives all downstream analyses.
**Independent Test**: Run the full pipeline on a single verified dataset and verify that all delta metrics, assumption checks, and robustness fall‑backs are produced as specified.
**Acceptance Scenarios**:
1. **Given** a dataset with a documented outcome variable, **When** the baseline analysis and each cleaned variant are executed, **Then** a `cleaned_metrics.json` entry containing numeric `effect_size_change` (3‑decimal), `direction` (“increase” or “decrease”), `ci_overlap` (0‑1), and `p_value_delta` (numeric) is written for that dataset.
2. **Given** the same dataset, **When** assumption checks detect violations, **Then** the pipeline automatically switches to robust tests and records the fallback in `cleaned_metrics.json` with a `robust_test_used` field.

### User Story US-002 – Sensitivity to Size & Missingness (Priority: P2)
**Why this priority**: The effect of cleaning may depend on dataset size and missingness; quantifying this sensitivity is required for generalizable conclusions.
**Independent Test**: For each size‑bin (n < 50, 50‑200, >200) and missingness level (no missingness, MCAR, MAR, MNAR), run the pipeline on at least one dataset and verify that stratified reports are produced.
**Acceptance Scenarios**:
1. **Given** a dataset in the “50‑200” size bin with MCAR missingness artificially introduced, **When** the sensitivity analysis runs, **Then** the results appear in `sensitivity_metrics.json` and include the bin identifier and missingness level.

### User Story US-003 – Reproducibility & Contract Compliance (Priority: P3)
**Why this priority**: Guarantees that all artefacts conform to agreed‑upon schemas, enabling downstream validation and reuse.
**Independent Test**: Execute the validation script; it must pass without errors for dataset, baseline, cleaned, delta, and bootstrap artefacts.
**Acceptance Scenarios**:
1. **Given** the downloaded raw datasets, **When** the schema validator runs, **Then** it confirms compliance with `contracts/dataset.schema.yaml`.
2. **Given** the generated `baseline_metrics.json`, **When** the result validator runs, **Then** it confirms compliance with `contracts/baseline_metrics.schema.yaml`.

## Functional Requirements

### FR-001 – Baseline Analysis (See US-001)
- Download **10–15** public datasets that have a clearly documented **binary or continuous** outcome variable (see dataset list below). The collection must include at least one dataset in each size bin (n < 50, 50‑200, >200). Multi‑class categorical outcomes are excluded unless transformed to a binary indicator.
- Run two‑sample t‑tests (or Welch’s t‑test when variances differ) and linear regressions on the raw (uncleaned) data.
- Store p‑values, 95 % confidence intervals, effect‑size metrics, and dataset‑level metadata in `data/processed/baseline_metrics.json`.
- Validate each raw dataset against `contracts/dataset.schema.yaml` before analysis.
- Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation.
- Generate `data/processed/dataset_metadata.json` containing the verified outcome column name, sample size, and missingness proportion for every dataset and validate it against `contracts/dataset.schema.yaml`.

**Verified Datasets (examples)**
- UCI Wine Quality – outcome: `quality` – https://archive.ics.uci.edu/ml/datasets/Wine+Quality
- UCI Breast Cancer Wisconsin Diagnostic – outcome: `diagnosis`
- UCI Heart Disease – outcome: `target` – https://archive.ics.uci.edu/ml/datasets/Heart+Disease
- UCI Parkinsons Telemonitoring – outcome: `total_UPDRS`
- UCI Diabetes – outcome: `progression`
- UCI Statlog (German Credit Data) – outcome: `credit_risk`
- UCI Adult Income – outcome: `income`
- UCI Student Performance – outcome: `G`
- UCI Car Evaluation – outcome: `class_value`
- UCI Ionosphere – outcome: `target`

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

### FR-006 – Sensitivity Analysis (See US-002)
- Stratify analyses by dataset size bins (**n < 50**, **50‑200**, **>200**) and missingness levels (**no missingness**, **MCAR**, **MAR**, **MNAR**).
- Ensure at least **one** dataset appears in each bin; if a bin is empty, acquire an additional public dataset that satisfies the missingness and size criteria.
- Store stratified results in `data/processed/sensitivity_metrics.json`.

### FR-007 – Dataset Schema Validation (See US-003)
- Validate each downloaded raw dataset against `contracts/dataset.schema.yaml`.
- Abort processing with a clear error if validation fails.

### FR-008 – Baseline Metrics Schema Validation (See US-003)
- Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation.

### FR-009 – Cleaned Metrics Schema Validation (See US-003)
- Validate `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml` after generation.
- The schema must require the fields: `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, `ci_overlap`, `effect_size_change`, `p_value_delta`, `direction`, **and** `robust_test_used` (when applicable).

### FR-010 – Cleaning Metadata Capture (See US-001)
- Each cleaning function returns a metadata dict containing `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, **and** `robust_test_used` when applicable.
- These fields are written to `cleaned_metrics.json` for every variant.

### FR-011 – Cleaning Metadata Schema Validation (See US-003)
- Validate the cleaning‑metadata fields in `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml`.

### FR-012 – Bootstrap Variance Estimation (See US-002)
- Perform a sufficient number of bootstrap iterations for each cleaned variant; store bootstrap confidence intervals in `bootstrap_metrics.json`.
- The iteration count is **mandatory** and taken from `config.BOOTSTRAP_ITERATIONS` (default **1000**). No fallback to fewer iterations is permitted.

### FR-013 – Bin‑Coverage Dataset Acquisition (See US-002)
- If any size‑bin or missingness‑level bin lacks a dataset, automatically trigger a download of a public dataset that satisfies the missingness and size requirements, updating the dataset list accordingly.

### FR-014 – Dataset Metadata Generation & Validation (See US-001)
- Create `data/processed/dataset_metadata.json` containing, for each dataset, the outcome column name, sample size, and missingness proportion.
- Validate this file against `contracts/dataset.schema.yaml`.

### FR-015 – Comparison Report Generation (See US-003)
- Produce a final `comparison_report.json` conforming to `contracts/comparison_report.schema.yaml` that aggregates all delta metrics, CI overlap, effect‑size changes, and (where applicable) assumption‑check flags across datasets.

### FR-016 – Principle II Verification Step (See US-003)
- Run the citation‑validation script defined in the project constitution to verify that all external claims (e.g., dataset provenance, statistical method citations) are accurately referenced. Log the verification outcome.

### FR-017 – Hypothesis‑Testing on Δ Metrics (See US-001)
- Compute paired statistical tests **(Wilcoxon signed‑rank)** on the vector of `effect_size_change` across all datasets for each cleaning operation. Record the test statistic and p‑value in `hypothesis_test_results.json`. Report results alongside `p_value_delta` to aid interpretation.

### FR-018 – Assumption Checks & Robust Fallback (See US-001)
- For **continuous** outcomes, assess before each test:
 * Normality via **Shapiro‑Wilk** (α = 0.05).
 * Homoscedasticity via **Levene’s test** (α = 0.05).
 * Linearity via residual‑scatter inspection (automated R‑squared check ≥ 0.7).
- If any violation is detected, automatically switch to robust alternatives (Welch’s t‑test for means, rank‑based regression for linear models) and flag the change in `cleaned_metrics.json` with `assumptions_met: false` **and** record the specific robust test used in a new field `robust_test_used`.

### FR-019 – Interaction Modeling for Sensitivity (See US-002)
- Fit a two‑way ANOVA (or mixed‑effects model) on the `effect_size_change` (and optionally `p_value_delta`) with factors *size bin* and *missingness level* to test for interaction effects. Record interaction F‑statistics and p‑values in `sensitivity_metrics.json`.

### FR-020 – Factorial Cleaning Design (See US-001)
- Implement a factorial experimental design that isolates each preprocessing component (outlier removal, imputation, recoding). Run pipelines for each factor individually and for all combinations, enabling attribution of observed metric changes to specific steps.

### FR-021 – Separate Effect‑Size Metrics per Test Type (See US-001)
- For two‑sample t‑tests report **Cohen’s d** as the primary effect‑size metric.
- For linear regressions report **R²** as the primary effect‑size metric.
- Both metrics must be stored (to three‑decimal precision) in `cleaned_metrics.json` with explicit field names (`cohens_d` or `r_squared`) alongside `effect_size_change` for consistency.

### FR-022 – Effect‑Size Stability Metric (See US-001)
- Compute the coefficient of variation (CV) of the primary effect‑size metric across all cleaning variants for each dataset. Store this `effect_size_cv` in `cleaned_metrics.json` as an independent validation of stability, separate from hypothesis testing.

### FR-023 – Sample Size Justification (See US-001)
- Provide a concise justification (≤ 150 words) for the chosen 10–15 dataset range based on prior meta‑analyses that indicate this quantity is sufficient to observe systematic cleaning effects in comparable studies. Document the rationale in `sample_size_justification.md`.

### FR-024 – Bootstrap Configuration Enforcement (See US-002)
- The pipeline must read `BOOTSTRAP_ITERATIONS` from `config.py` and pass it explicitly to all bootstrap functions. No automatic reduction of iterations is allowed; if the variable is missing, the pipeline aborts with an error.

### FR-025 – Cleaned Metrics Schema Definition (See US-001)
- Provide `contracts/cleaned_metrics.schema.yaml` defining the required fields: `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, `ci_overlap`, `effect_size_change`, `p_value_delta`, `direction`, `robust_test_used` (optional), `cohens_d` (optional), `r_squared` (optional), `effect_size_cv` (optional). Validation of `cleaned_metrics.json` against this schema is performed in FR‑009 and FR‑011.

### FR-026 – Bootstrap Metrics Schema Validation (See US-002)
- Validate `bootstrap_metrics.json` against `contracts/bootstrap_metrics.schema.yaml` after generation.

### FR-027 – Sensitivity Metrics Schema Validation (See US-002)
- Validate `sensitivity_metrics.json` against `contracts/sensitivity_metrics.schema.yaml` after generation.

### FR-028 – Hypothesis Test Results Generation & Validation (See US-001)
- Generate `hypothesis_test_results.json` containing Wilcoxon test statistics and Bonferroni‑adjusted p‑values. Validate this artifact against `contracts/hypothesis_test_results.schema.yaml`.

## Success Criteria

- **SC-001** – Per‑dataset delta reporting (See US-001)  
  Each dataset’s output must include a JSON object in `cleaned_metrics.json` with fields `p_value_delta` (numeric, three‑decimal precision), `effect_size_change` (numeric, three‑decimal precision), `direction` (string “increase” or “decrease”), `ci_overlap` (numeric 0‑1), and `robust_test_used` (when applicable). Validation script asserts presence, type, and precision.

- **SC-002** – Metric precision (See US-001)  
  All numeric metrics (p‑values, confidence intervals, effect sizes, ci_overlap, effect_size_change) are stored with ≥ 3‑decimal precision.

- **SC-003** – Visualizations (See US-001)  
  Forest plot saved as `output/figures/forest_plot.png` (PNG, 300 dpi) and heatmap saved as `output/figures/heatmap.svg` (SVG). Both files must be referenced in the final report.

- **SC-004** – Bootstrap variance estimation (See US-002)  
  Perform **≥ 1000** bootstrap iterations for each cleaned variant; store bootstrap confidence intervals in `bootstrap_metrics.json`.

- **SC-005** – Outcome variable verification (See US-001)  
  `dataset_metadata.json` contains the verified outcome column name for every dataset; validation ensures the column exists, is numeric, and matches documentation.

- **SC-006** – Assumption checks and robust fallback (See US-001)  
  For each test, a boolean flag `assumptions_met` is recorded; if false, the robust alternative’s results are stored, the specific robust test is recorded in `robust_test_used`, and the permutation‑based FPR requirement has been removed per scope.

- **SC-007** – Reporting without multiple‑testing correction (See US-001)  
  Raw p‑values are reported for each cleaning variant; no family‑wise error correction is applied, and the rationale for this choice is documented in the methods section.

- **SC-008** – Stratified analysis coverage (See US-002)  
  Each size‑bin (n < 50, 50‑200, >200) and each missingness level (no missingness, MCAR, MAR, MNAR) contains **≥ 1** dataset; the report includes a table summarizing bin counts.

- **SC-009** – Reproducibility & contract compliance (See US-003)  
  All schema validation steps (FR‑007, FR‑008, FR‑009, FR‑011, FR‑014, FR‑026, FR‑027, FR‑028) must pass without errors for every artifact.

- **SC-010** – Sample size justification (See US-001)  
  The `sample_size_justification.md` artifact demonstrates that the selected dataset collection is justified based on prior literature.

- **SC-011** – Hypothesis‑testing of cleaning impact (See US-001)  
  The paired Wilcoxon test on `effect_size_change` (FR‑017) must be performed and its test statistic and Bonferroni‑adjusted p‑value reported in `hypothesis_test_results.json`. No significance threshold is imposed; results are interpreted in context.

- **SC-012** – Effect‑size stability metric (See US-001)  
  The `effect_size_cv` reported in `cleaned_metrics.json` must be ≤ 0.2 for a variant to be considered stable; this threshold is justified in the methods.

- **SC-013** – Principle II verification (See US-003)  
  The citation‑validation script must run without errors and produce a log confirming that all external claims are properly referenced.

- **SC-014** – Robust test identification (See US-001)  
  Every entry in `cleaned_metrics.json` includes a `robust_test_used` field when robust alternatives are invoked; validation ensures the field is present and non‑empty in such cases.

## Research Hypotheses
- **H1 (Associative)**: Data cleaning operations are *associated* with systematic changes in **effect‑size** estimates (direction and magnitude), as detected by the paired Wilcoxon test on `effect_size_change` (SC‑011).  
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with increased stability of effect‑size estimates, reflected by higher `ci_overlap` and lower `effect_size_cv` (SC‑012).

## Assumptions
- Public datasets listed are freely downloadable and contain a clearly documented binary or continuous outcome variable.
- All statistical tests assume independent observations; if this is violated, robust methods are applied as per FR‑018.
- The computational environment provides Python 3.11 with `scipy`, `statsmodels`, and `pandas`.
- Bootstrap iterations are set to **1 000** by default; this number provides stable variance estimates for the sample sizes considered.
- Normality, homoscedasticity, and linearity checks use significance level **α = 0.05**.
- Missingness levels for sensitivity analysis are: no missingness (baseline), MCAR, MAR, MNAR.
- Sample size justification is based on prior meta‑analyses rather than a formal a‑priori power calculation.