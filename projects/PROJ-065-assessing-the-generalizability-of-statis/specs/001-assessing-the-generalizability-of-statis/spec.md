# Feature Specification: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

**Feature Branch**: `001-assessing-the-generalizability-of-statis`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Assessing the Generalizability of Statistical Significance in Pre-Registered Studies"

## User Scenarios & Testing

### User Story 1 - Retrieve and Parse Pre-Registered Study Data (Priority: P1)

**Description**: As a researcher, I need to programmatically download raw datasets and extract original statistical models (test statistics, p-values, sample sizes) from pre-registered studies hosted on the Open Science Framework (OSF) so that I can establish a baseline for reproducibility analysis.

**Why this priority**: Without access to the raw data and original analytical specifications, no robustness or fragility analysis can be performed. This is the foundational data ingestion step.

**Independent Test**: The system can successfully fetch multiple distinct pre-registered study data bundles from OSF, parse their metadata to identify the primary statistical test, and extract the reported p-value into a structured CSV file.

**Acceptance Scenarios**:

1. **Given** a list of valid OSF project IDs from the OSF API, **When** the ingestion script runs, **Then** the script downloads the associated data bundles and extracts the reported p-value and sample size into a `baseline_metrics.csv` file.
2. **Given** an OSF project ID with missing or corrupted data files, **When** the ingestion script runs, **Then** the script logs a specific error for that ID and continues processing the remaining valid projects without crashing.
3. **Given** a pre-registration document where the statistical model is described in text but lacks a numeric p-value, **When** the parser runs, **Then** the system flags the entry as "missing_p_value" and excludes it from the primary fragility calculation.

### User Story 2 - Execute Bootstrap Resampling and Sensitivity Analysis (Priority: P2)

**Description**: As a researcher, I need the system to run 1,000 bootstrap iterations with stratified sampling for a baseline model and 5 alternative model specifications for each study to determine how often the original statistical significance (p < 0.05) holds under variation. The system MUST calculate separate stability rates for sampling variability (baseline model only) and model specification uncertainty (aggregated across 5 models) to distinguish the sources of fragility.

**Why this priority**: This is the core analytical engine. It directly addresses the research question regarding the fragility of findings. Distinguishing between sampling noise and model choice is essential for valid interpretation. If this fails, the study cannot generate the "fragility index" or separate stability metrics.

**Independent Test**: For a single study with N=200 data points, the system completes 1,000 bootstrap iterations for the baseline model and [deferred] iterations for each of 5 alternative specifications within 10 minutes on a 2-core CPU, outputting two distinct distributions of p-values and two calculated "stability rates".

**Acceptance Scenarios**:

1. **Given** a dataset of N=200 with a reported p-value of 0.04, **When** the resampling engine runs 1,000 stratified bootstrap iterations on the baseline model, **Then** the output file contains a histogram of p-values and a calculated "Sampling Stability Rate" (percentage of baseline iterations where p < 0.05).
2. **Given** a dataset requiring covariate adjustment, **When** the system runs the 5 alternative specifications (varying covariate inclusion, data transformation, and outlier handling), **Then** the system calculates a "Specification Stability Rate" (percentage of all [deferred] alternative iterations where p < 0.05) and compares it to the Sampling Stability Rate to identify the source of instability.
3. **Given** a study where the bootstrap iterations exceed 60 minutes of CPU time, **When** the job runs, **Then** the system terminates the specific study iteration, logs a "timeout" warning, and proceeds to the next study to ensure overall job completion.

### User Story 3 - Aggregate Fragility Indices and Generate Visualizations (Priority: P3)

**Description**: As a researcher, I need the system to aggregate the stability rates across all analyzed studies, calculate the proportion of findings that lose significance, and generate forest plots and histograms to visualize the results, including heterogeneity metrics.

**Why this priority**: This synthesizes the individual study results into the final research output (the "generalizability" metric) and provides the visual evidence required for the paper.

**Independent Test**: The system processes a folder of 10 completed study result files and generates a `summary_report.pdf` containing a forest plot of stability rates, a histogram of p-value stability rates, and an I² heterogeneity statistic.

**Acceptance Scenarios**:

1. **Given** a directory containing 20 CSV files of study results, **When** the aggregation script runs, **Then** it calculates the mean and median "Sampling Stability Rate" and "Specification Stability Rate" across all studies and outputs a summary statistics table.
2. **Given** the aggregated results, **When** the visualization module runs, **Then** it generates a forest plot where each study is represented by a point estimate and a 95% confidence interval of its stability rate, alongside an I² statistic indicating heterogeneity.
3. **Given** a dataset where >50% of studies show a stability rate < 80%, **When** the summary report is generated, **Then** the report highlights this finding in the "Key Results" section with a specific count of fragile findings.

### Edge Cases

- **What happens when** the OSF API returns a 429 (Too Many Requests) error? The system must implement an exponential backoff strategy (e.g., wait 2s, 4s, 8s) and retry up to 3 times before failing the specific download task.
- **How does the system handle** datasets with zero variance in a key predictor variable during bootstrap? The system must detect this condition, skip the specific iteration, and log a warning rather than crashing with a division-by-zero error.
- **What happens when** a pre-registration document contains ambiguous model specifications (e.g., "adjust for confounders" without listing them)? The system must flag the study as "ambiguous_model" and exclude it from the quantitative analysis, recording it in a "manual review" list.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download raw datasets from OSF using the OSF API for at least 50 pre-registered studies across 3 distinct disciplines (psychology, economics, biology) (See US-1).
- **FR-002**: The system MUST implement a stratified bootstrap resampling procedure with [deferred] iterations for the baseline model and [deferred] iterations for each of multiple alternative model specifications (See US-2).
- **FR-003**: The system MUST execute multiple alternative model specifications per study, varying covariate inclusion, data transformation, and outlier handling methods. (See US-2).
- **FR-004**: The system MUST calculate and record two distinct metrics for every study: (1) "Sampling Stability Rate" (percentage of [deferred] baseline iterations where p < 0.05) and (2) "Specification Stability Rate" (percentage of [deferred] alternative iterations where p < 0.05) (See US-2).
- **FR-005**: The system MUST generate a forest plot visualizing the stability rates of all analyzed studies with 95% confidence intervals and calculate the I² statistic for heterogeneity (See US-3).
- **FR-006**: The system MUST prepare data for a meta-analysis using a random-effects model by calculating the mean stability rate and standard error across studies, and report the I² statistic to quantify heterogeneity (See US-3).
- **FR-007**: The system MUST perform a sensitivity analysis on the significance threshold (p < 0.05) by sweeping the cutoff across {0.01, 0.05, 0.10} and reporting the variation in both Sampling and Specification Stability rates (See US-2).

### Key Entities

- **Study**: Represents a single pre-registered project; attributes include `osf_id`, `discipline`, `original_p_value`, `sample_size`, `sampling_stability_rate`, `specification_stability_rate`, `fragility_index`.
- **Iteration**: Represents a single resampling run; attributes include `study_id`, `iteration_number`, `resampled_p_value`, `model_specification_id`, `is_baseline` (boolean).
- **SensitivityResult**: Represents the outcome of a threshold sweep; attributes include `study_id`, `threshold_value`, `sampling_stability_rate_at_threshold`, `specification_stability_rate_at_threshold`.

## Success Criteria

- **SC-001**: The proportion of studies where the Sampling Stability Rate is < 95% is measured against the hypothesis that 30-50% of findings will lose significance to quantify fragility prevalence (See US-2).
- **SC-002**: The total runtime for processing a representative set of studies on a 2-CPU runner is measured against the 6-hour limit to ensure compute feasibility (See US-2).
- **SC-003**: The memory usage peak during the bootstrap process is measured against the RAM limit of the free-tier runner. (See US-2).
- **SC-004**: The number of studies excluded due to "ambiguous model" or "missing data" is measured against the target of ≤ 10% of the total studies attempted to ensure dataset viability (See US-1).
- **SC-005**: The variation in both Sampling and Specification Stability rates across the sensitivity sweep (thresholds 0.01, 0.05, 0.10) is measured to confirm the robustness of the primary findings and distinguish model sensitivity from threshold sensitivity (See US-2).

## Assumptions

- The Open Science Framework (OSF) API will remain accessible and provide raw data bundles for the selected 50-100 studies without requiring complex authentication beyond public access.
- The pre-registered studies selected contain sufficient sample sizes (N ≥ 50) to support 1,000 bootstrap iterations without numerical instability.
- The "3-5 alternative specifications" mentioned in the methodology sketch are technically implementable within the Python/R environment using standard statistical libraries (e.g., `statsmodels`, `scikit-learn`, `lme4`) without requiring custom, heavy-weight model training.
- The dataset variables required for the analysis (predictors, outcomes, covariates) are explicitly named and available in the raw data files provided by OSF; if a study lacks a required variable, it will be excluded from the analysis rather than imputed.
- The "Stability Rate" is the primary metric for this study; the traditional "Fragility Index" (minimum outcome events to flip significance) is acknowledged as a distinct metric that is not calculated due to computational constraints, and no equivalence is claimed between the two.
- All statistical tests performed are observational; therefore, findings will be framed as associational stability rather than causal generalizability.
- The sensitivity analysis on the significance threshold (FR-007) is essential to distinguish whether fragility arises from the arbitrary 0.05 cutoff or from genuine model instability, justifying its inclusion despite not being explicitly named in the original Idea's "Expected results".