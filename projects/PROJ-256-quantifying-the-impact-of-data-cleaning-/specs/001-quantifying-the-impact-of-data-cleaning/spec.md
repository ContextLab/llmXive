# Feature Specification: Quantifying the Impact of Data Cleaning on Statistical Inference

**Feature Branch**: `001-quantify-cleaning-impact`
**Created**: 2024-01-15
**Status**: Draft
**Input**: User description: "How do different data cleaning strategies (outlier removal, missing value imputation, data type correction) quantitatively affect p-values, confidence intervals, and effect sizes in common statistical tests?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1)

Researcher downloads a small number of public datasets from UCI Machine Learning Repository and OpenML.

The research question is: How do different data cleaning strategies (outlier removal, missing value imputation, data type correction) quantitatively affect p-values, confidence intervals, and effect sizes in common statistical tests?

The method is: We will evaluate the impact of systematic data cleaning on statistical inference by applying outlier removal, missing value imputation, and data type correction to public datasets. Performance will be measured by comparing p-values, confidence intervals, and effect sizes before and after cleaning.

**Hypothesis**: We predict that outlier removal will result in a statistically significant reduction in p-values and an increase in effect sizes compared to the baseline, particularly in datasets with n < 50.

References: (as of 2024‑01‑26), then runs baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics.

**Why this priority**: Without a baseline comparison, no cleaning‑induced shifts can be measured. This is the foundation for all downstream analysis.

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p‑values, confidence intervals, and effect sizes for that dataset.

**Acceptance Scenarios**:

1. **Given** a public dataset URL from UCI or OpenML, **When** the acquisition script runs, **Then** the dataset downloads successfully and baseline t‑test/linear regression metrics (p‑value, CI, Cohen's d/R²) are recorded for at least 1 dataset
2. **Given** 10‑15 datasets selected, **When** baseline analysis completes, **Then** a baseline metrics table is generated with ≥10 datasets containing valid p‑values (0 < p < 1) and finite confidence intervals

### User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

Researcher applies three cleaning strategies systematically: (a) IQR‑based outlier removal, (b) mean/median/KNN imputation for missing values, (c) categorical recoding, then re‑runs identical statistical tests on each cleaned variant.

**Why this priority**: This is the core intervention being studied. Without systematic cleaning application, the research question cannot be answered.

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p‑values, which delivers the primary research outcome for that strategy.

**Acceptance Scenarios**:

1. **Given** a dataset with ≥5% missing values, **When** mean imputation is applied, **Then** the cleaned dataset has zero missing values in the imputed columns and the same number of rows as the original
2. **Given** a dataset with outliers defined by IQR (k=1.5), **When** outlier removal is applied, **Then** at least 1 outlier is removed and the cleaned dataset has ≤original row count
3. **Given** a dataset with mixed data types, **When** categorical recoding is applied, **Then** all categorical columns are properly encoded as factors for statistical testing

### User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

Researcher computes absolute and relative differences between baseline and cleaned results, performs sensitivity analysis across dataset sizes (n<50, 50‑200, >200) and missingness rate bins (0‑[deferred], 5‑[deferred], 10‑[deferred], >20%), and generates summary visualizations.

**Why this priority**: This delivers the quantitative conclusions about cleaning‑induced bias magnitude and conditions. Lower priority because it depends on US‑1 and US‑2 completing first.

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p‑value shifts, CI width changes, and effect size variations with valid numeric values.

**Acceptance Scenarios**:

1. **Given** baseline and cleaned metrics for the same dataset, **When** the comparison script runs, **Then** absolute p‑value difference is calculated with ≥3 decimal precision (e.g., 0.047)
2. **Given** all three cleaning strategies applied, **When** sensitivity analysis runs, **Then** results are stratified by dataset size bins (n<50, 50‑200, >200) with ≥1 dataset per bin and by missingness bins (0‑[deferred], 5‑[deferred], 10‑[deferred], >20%)
3. **Given** multiple hypothesis tests across datasets, **When** the analysis completes, **Then** a multiple‑comparison correction (Benjamini‑Hochberg) is applied to control family‑wise error rate at α≤0.05

### Edge Cases

- **Missing outcome >80%**: If a dataset has >80% missing values in the outcome variable, the script logs a warning and skips the dataset, recording it as excluded.
- **No outliers**: If no values lie outside the IQR bounds, the script reports “0 outliers removed” and proceeds with analysis.
- **Variance reduction ≥20% after imputation**: The script flags a warning when post‑imputation standard deviation decreases by ≥20% relative to pre‑imputation.
- **Row removal ≥50%**: When cleaning removes ≥50% of rows, results are reported both *with* the dataset (noting the high‑impact removal) and *without* it, and a bias note is added to the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a representative subset of datasets by sample size from the OpenML Small Datasets collection.

The research question is: Can large language models effectively generate data quality reports for diverse datasets?

The method is: We will evaluate the performance of a large language model in generating data quality reports for a collection of datasets, comparing the generated reports to established data quality metrics.

References: (DOI/arXiv/author-year) (as of 2024‑01‑26) that have n ≥ 20 and at least one numeric outcome variable (See US‑1)
- **FR-002**: System MUST apply IQR‑based outlier removal with k=1.5 threshold (standard community default per Tukey) and record the number of rows removed per dataset (See US‑2)
- **FR-003**: System MUST implement 3 missing‑value imputation strategies (mean, median, KNN with k=5) and allow selection of which to apply per dataset; after imputation, targeted columns must contain zero missing values (See US‑2)
- **FR-004**: System MUST execute t‑tests and linear regressions using scipy/statsmodels on both raw and cleaned data, recording p‑values (rounded to ≥3 decimal places), % confidence intervals, and effect sizes (Cohen's d for t‑tests, R² for regression) (See US‑2)
- **FR-005**: System MUST compute absolute p‑value difference (|p_cleaned − p_baseline|, rounded to decimal places), relative CI width change ((CI_width_cleaned − CI_width_baseline)/CI_width_baseline × 100, rounded to 2 decimal places), and effect‑size delta for each cleaning strategy (See US‑3)
- **FR-006**: System MUST sweep multiple outlier threshold values (k ∈ {1.5, 2.0}) and, for each, report (a) false‑positive rate estimated via A substantial number of permutation null datasets will be generated.

The research question is: Can we identify robust biomarkers for predicting treatment response in patients with glioblastoma using multi-omics data integration? ()

The method will involve integrating genomic, transcriptomic, and proteomic data, followed by feature selection using a permutation-based approach to assess biomarker stability and predictive power. (Lee et al., recent) per original dataset (outcome variable permuted within the dataset) and (b) inconsistency rate defined as the proportion of datasets where significance status (p ≤ 0.05 vs. p > 0.05) changes between baseline and cleaned analysis (See US‑3)
- **FR-007**: System MUST apply multiple‑comparison correction (Benjamini‑Hochberg) when >1 hypothesis test is run across datasets, controlling family‑wise error rate at α ≤ 0.05 (See US‑3)
- **FR-008**: System MUST stratify results by dataset size bins (n<50, 50‑200, >200) and missingness rate bins (0‑[deferred], 5‑[deferred], 10‑[deferred], >20%) with ≥1 dataset per bin (See US‑3)
- **FR-009**: System MUST compute bootstrap variance estimates for each metric shift using a minimum of 1000 resamples per dataset and report a 95 % confidence interval for the shift (See US‑3, Constitution Principle VI)
- **FR-010**: System MUST generate summary visualizations (forest plot of p‑value shifts, heatmap of CI‑width changes across strategies and dataset bins) and save them as PNG files (See US‑3)
- **FR-011**: System MUST estimate false‑positive rates for each outlier threshold by generating multiple permutation null datasets per original dataset (shuffling the outcome variable while keeping predictors fixed), applying the same outlier removal, and calculating the proportion of tests with p ≤ 0.05 (See FR‑006)

### Key Entities *(include if feature involves data)*

- **Dataset**: Represents a public dataset from UCI/OpenML with attributes: source_url, sample_size, missingness_rate, predictor_variables, outcome_variable
- **CleaningStrategy**: Represents a cleaning intervention with attributes: strategy_type (outlier_removal, imputation, recoding), parameters (e.g., k=1.5 for IQR), rows_affected
- **AnalysisResult**: Represents statistical output with attributes: dataset_id, strategy_id, p_value, ci_lower, ci_upper, effect_size, sample_size
- **ComparisonReport**: Represents cleaned‑vs‑baseline difference with attributes: baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Median absolute p‑value shift across datasets per cleaning strategy is reported with its inter‑quartile range (IQR); shift is defined as |p_cleaned − p_baseline| (See US‑)
- **SC-002**: Median percentage change in confidence‑interval width from baseline per cleaning strategy is reported with IQR (See US‑3)
- **SC-003**: Median effect‑size change (Cohen's d or ΔR²) per cleaning strategy and dataset‑size bin is reported with IQR (See US‑3)
- **SC-004**: Family‑wise error rate is controlled at α ≤ 0.05 using Benjamini‑Hochberg correction across all hypothesis tests (See US‑3)
- **SC-005**: Sensitivity analysis across the three outlier thresholds (k ∈ {1.0, 1.5, 2.0}) reports the false‑positive rate variation (median across datasets) (See US‑3)
- **SC-006**: Baseline metrics (p‑value, 95 % CI, effect size) are recorded for the available datasets (current n=2) with valid numeric values (≥3 decimal places for p‑values). If n≥10 datasets become available in future expansion, report median and IQR; otherwise, report per-dataset deltas with a limitation note (See US‑1)
- **SC-007**: Cleaning application is validated: outlier removal logs rows removed; each imputation strategy results in zero missing values in the imputed columns; categorical recoding yields factor‑encoded columns (See US‑2)
- **SC-008**: Bootstrap variance estimates (≥1000 iterations) are provided for each metric shift with a 95 % confidence interval (See US‑3, Constitution Principle VI)
- **SC-009**: Summary visualizations (forest plot of p‑value shifts, heatmap of CI‑width changes) are generated and saved as PNG files (See US‑3)

## Assumptions

- Datasets from UCI Machine Learning Repository and OpenML are publicly accessible without authentication and fit within standard RAM and disk constraints. (sample if needed)
- Analysis runs on GitHub Actions free‑tier runner (Multiple CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job)
- Python environment with scipy, statsmodels, scikit‑learn, pandas, numpy is available via standard package installation
- IQR‑based outlier removal uses k=1.5 threshold as community standard (Tukey, 1977); sensitivity analysis sweeps k ∈ {1.0, 1.5, 2.0}
- Multiple‑comparison correction uses Benjamini‑Hochberg method as appropriate for the number of tests
- Findings are framed as ASSOCIATIONAL (not causal) because this is an observational study without random assignment to cleaning strategies
- Sample size/power considerations are recorded as [deferred] with acknowledgment that small‑sample datasets (n<50) may have limited power to detect cleaning‑induced shifts
- Validated statistical instruments are not required (this study uses existing public datasets, not new questionnaires)
- Predictor collinearity diagnostics (VIF) are required when multiple predictors are included in regression models; if predictors are definitionally related, independent effects are NOT claimed
- No GPU/CUDA/accelerators are used; all methods are CPU‑tractable (classical statistics, scikit‑learn on modest data, exact/closed‑form computation)
- Total compute time must not exceed a reasonable limit on free‑tier runner; if exceeded, dataset sampling or method simplification is applied
- Bootstrap resampling (with a sufficient number of iterations) is CPU‑tractable for the dataset sizes studied; if not, iteration count is reduced to a predefined threshold or method is replaced with closed‑form approximation