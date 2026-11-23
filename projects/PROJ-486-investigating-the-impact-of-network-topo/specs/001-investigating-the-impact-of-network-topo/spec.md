# Feature Specification: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Feature Branch**: `001-network-topology-entrainment`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli"

## User Scenarios & Testing

### User Story 1 - Core Correlation Analysis (Priority: P1)

The system must compute resting-state network topology metrics (clustering coefficient, characteristic path length) from HCP fMRI data and correlate them with entrainment strength metrics (real data only) to determine if a statistical association exists.

**Power Analysis & Data Thresholds**:
- **Target Sample Size**: N=85 subjects to achieve [deferred] power to detect a moderate effect size (Spearman r=0.45) at alpha=0.05 (two-tailed).
- **Exploratory Floor**: N=30 subjects is the minimum floor for generating an *exploratory* report.
- **Hypothesis Test Halt**: If N < 30, the system MUST **Halt the Hypothesis Test** (skip statistical inference) and output a "Data Insufficient" status. The pipeline MUST NOT generate synthetic data to answer the hypothesis. However, the pipeline MUST continue to generate descriptive statistics and an exploratory report if requested, explicitly flagged as "Underpowered".

**Why this priority**: This is the primary scientific hypothesis. Without establishing the baseline correlation between structure and function using real data, no further analysis has value.

**Independent Test**: Can be fully tested by executing the correlation pipeline on a subset of subjects (N >= 30) and verifying that a scatter plot and correlation coefficient (r, p-value) are generated for the primary hypothesis. If N < 30, verify the system halts the hypothesis test but continues to generate the "Data Insufficient" report.

**Acceptance Scenarios**:

1. **Given** a valid set of HCP fMRI parcellation files and a matching CSV of entrainment metrics with N >= 85, **When** the analysis script runs, **Then** it outputs a CSV containing individual subject IDs, their calculated clustering coefficients, path lengths, and the corresponding correlation statistics (Spearman r, p-value against H0: r=0, adjusted p) with a "Definitive" status.
2. **Given** a valid set of HCP fMRI parcellation files and a matching CSV of entrainment metrics with 30 <= N < 85, **When** the analysis script runs, **Then** it outputs the correlation statistics but flags the report as "Exploratory (Underpowered)" and includes a warning that the study lacks power to detect small-to-moderate effects.
3. **Given** N < 30 or missing entrainment data, **When** the script runs, **Then** it **Halts the Hypothesis Test** (no p-values reported) and outputs a report flagging "Data Insufficient" with the exact string: "Data Insufficient: N < 30. Hypothesis test skipped." The pipeline continues to generate descriptive statistics if requested.

---

### User Story 2 - Multiple Comparisons & Power Correction (Priority: P2)

The system must apply Holm-Bonferroni correction to the p-values derived from the multivariate model and univariate tests. The **Family of Tests** for correction is explicitly defined as: (1) The set of all valid univariate tests (Clustering Coefficient, Path Length) AND (2) The set of predictors in the MLR model (if executed).

**Why this priority**: The study involves testing multiple metrics. Without correction, the risk of Type I error is inflated. This is a methodological necessity.

**Independent Test**: Can be fully tested by providing a dataset with known raw p-values (synthetic or real) to the *correction module only*, running the correction step, and verifying that the output p-values are correctly adjusted using the Holm-Bonferroni method and the significance threshold is correctly updated. This test validates the *logic* without invoking the hypothesis test on N<30 real data.

**Acceptance Scenarios**:

1. **Given** a set of raw p-values from the MLR analysis and univariate tests, **When** the correction step executes, **Then** the output includes a column for "adjusted_p_value" calculated via Holm-Bonferroni on the *combined family* of tests, and a boolean "is_significant" based on `adjusted_p < 0.05`.
2. **Given** a sample size N < 30, **When** the report is generated, **Then** it explicitly flags the power limitation in the summary report text with the exact string: "Power Warning: N < 30 (Exploratory)" and halts the hypothesis test (no inference reported).

---

### User Story 3 - Robustness Sensitivity Analysis (Priority: P3)

The system must re-run the core correlation analysis using alternative parcellation schemes (AAL, Power) to verify that the observed relationship is not an artifact of a single atlas choice. The sensitivity analysis MUST use the same statistical metric (**Spearman correlation**) as the primary hypothesis.

**Why this priority**: While the primary hypothesis uses the Schaefer atlas, confirming that results hold across different spatial definitions is crucial for establishing the robustness of the finding. This is secondary to the primary result.

**Independent Test**: Can be tested by swapping the input atlas file to "AAL" and verifying that the pipeline completes without error and produces a comparative result table and a combined bar chart.

**Acceptance Scenarios**:

1. **Given** the configuration parameter `atlas_type` set to "AAL" or "Power", **When** the pipeline executes, **Then** it generates a secondary correlation result table and a **single comparative bar chart** (PNG format) containing **one bar for each requested alternative atlas** labeled "[Atlas Name] Diff" showing the **absolute difference in Spearman correlation coefficients** (|r_Schaefer - r_Alternative|) between the Schaefer baseline and each alternative atlas.
2. **Given** a significant result in the primary analysis, **When** the sensitivity analysis completes, **Then** the report indicates whether the direction of the correlation (positive/negative) remains consistent across the alternative parcellations.

---

### User Story 4 - Pipeline Validation Mode (Priority: P4)

The system must generate synthetic data to verify that the analysis pipeline correctly recovers a known correlation parameter. This mode is strictly for code validation and MUST NOT be used to answer the primary research hypothesis. **This mode explicitly bypasses the N>=30 real-data check.**

**Why this priority**: Ensures the code logic is correct before applying it to real data. This is a methodological safeguard, not a scientific result.

**Independent Test**: Can be fully tested by running the pipeline with `validation_mode=true`, verifying that the system generates data with a known target correlation, analyzes it, and reports that the recovered correlation matches the target within a tolerance of ±0.01.

**Acceptance Scenarios**:

1. **Given** `validation_mode=true` and a target correlation `r_target=0.5`, **When** the pipeline runs, **Then** it generates synthetic data, computes the correlation, and asserts that `|r_observed - r_target| < 0.01` before proceeding.
2. **Given** the validation passes, **When** the report is generated, **Then** it explicitly labels the results as "Pipeline Validation Only" and excludes them from the primary hypothesis summary.

---

### Edge Cases

- **Missing Data**: How does the system handle subjects present in the fMRI dataset but missing from the entrainment dataset? (System must exclude these subjects, count the remaining N, and if N < 30, **Halt the Hypothesis Test** with status "Data Insufficient" and output the flag "Power Warning: N < 30 (Exploratory)" but NOT switch to simulation for the hypothesis test. The pipeline continues to generate descriptive statistics if requested.)
- **Zero Variance**: What happens if a topology metric has zero variance across the sample? (System must detect this, halt the correlation for that metric, set the 'status' column in the output CSV to 'Non-informative', and **dynamically adjust the Holm-Bonferroni correction family size** to exclude this metric from the p-value correction set.)
- **Data Mismatch**: How does the system handle a mismatch in subject IDs between the two input sources? (System must perform an inner join, count N, and if N < 30, **Halt the Hypothesis Test** with status "Data Insufficient" and output the flag "Power Warning: N < 30 (Exploratory)" but continuing execution for *other modes* is permitted.)
- **Validation Mode Override**: If `validation_mode=true`, the N>=30 check is **bypassed entirely**. The system proceeds with synthetic data generation regardless of real data availability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess resting-state fMRI data from the Human Connectome Project (HCP) S1200 release, parcellating into the Schaefer atlas with a standard high-resolution parcellation. (See US-1)
- **FR-002**: System MUST compute the Clustering Coefficient and Characteristic Path Length for each subject using a weighted correlation matrix derived from the fMRI data. (See US-1)
- **FR-003**: System MUST ingest external entrainment strength metrics (phase-locking values) from a provided CSV. If the CSV is missing or the inner join with fMRI data yields N < 30, the system MUST **Halt the Hypothesis Test** (skip statistical inference) and output a warning "Data Insufficient: N < 30". The pipeline MUST NOT generate synthetic data for the hypothesis test. However, the pipeline MUST continue to generate descriptive statistics and an exploratory report if requested. (See US-1)
- **FR-004**: System MUST perform a two-stage analysis: (1) Univariate Spearman correlations for each topology metric individually; (2) **Unconditionally proceed** to a **Multiple Linear Regression (MLR)** model with entrainment strength as the dependent variable and Clustering Coefficient and Characteristic Path Length as independent predictors (unless VIF > 5), regardless of univariate significance. The system MUST calculate the Variance Inflation Factor (VIF) for each predictor within this MLR model. If VIF > 5 for any predictor, the system MUST flag `collinearity_warning` as true, suppress the MLR coefficients, and report only the univariate results. If VIF ≤ 5, the system MUST report standardized coefficients, p-values, and apply **Holm-Bonferroni** correction for the **combined family of tests** (all valid univariate metrics + MLR predictors). **If a metric has zero variance, it is excluded from the correction family size.** (See US-1, US-2)
- **FR-005**: System MUST generate visualizations (scatter plots with 95% CIs) and a summary report containing correlation statistics (r, p-value) and, if applicable, MLR statistics (R-squared, coefficients, adjusted p-values) and effect sizes. (See US-1)
- **FR-006**: System MUST allow the user to specify an alternative parcellation atlas (e.g., AAL, Power 264) to perform a sensitivity analysis on the correlation results. If the inner join for the alternative atlas yields N < 30, the system MUST **Halt the Hypothesis Test** for that atlas but continue descriptive reporting. (See US-3)
- **FR-007**: System MUST validate that the dataset contains the required variables (subject ID, topology metric, entrainment metric) before execution and halt with a clear error if any are missing. (See US-1)
- **FR-008**: System MUST validate the input entrainment CSV for the presence of required columns (subject_id, entrainment_metric) and data types (numeric) before processing, and halt with error "Invalid Entrainment Data" if validation fails. (See US-1)
- **FR-009**: System MUST generate synthetic entrainment metrics correlated with topology metrics ONLY in **Validation Mode** (See US-4). The system MUST generate data with a specified target correlation (e.g., r=0.5) and noise, compute the correlation of the generated sample, and assert `|r_observed - r_target| < 0.01` before proceeding. The system MUST label the data source as "Simulated (Validation Only)" in all outputs and reports. **This mode bypasses the N>=30 real-data check.** (See US-4)
- **FR-010**: System MUST generate a **single comparative bar chart** (PNG) showing the **absolute difference in Spearman correlation coefficients** (|r_Schaefer - r_Alternative|) for **each requested** alternative atlas. If both AAL and Power 264 are requested, the chart must contain two bars labeled "AAL Diff" and "Power Diff". If only one is requested, the chart must contain exactly one bar. Numeric values must be in the title. (See US-3)

### Key Entities

- **Subject**: Represents an individual participant, identified by a unique `subject_id` (primary key), containing attributes for fMRI connectivity data and behavioral/entrainment metrics.
- **TopologyMetric**: Represents a calculated network property (Clustering Coefficient or Path Length) associated with a specific `subject_id` and atlas configuration.
- **EntrainmentStrength**: Represents the quantified neural response (e.g., Phase-Locking Value) for a `subject_id` to a rhythmic stimulus (or simulated value in validation mode).
- **Join Key**: The `subject_id` field is the explicit primary key used to join `Subject`, `TopologyMetric`, and `EntrainmentStrength` entities.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The statistical association between network topology and entrainment strength is measured against the null hypothesis (r=0) using the univariate Spearman correlation and, if applicable, the MLR model with Holm-Bonferroni-corrected p-values (alpha=0.05). For **Validation Mode**, success is defined as recovering the injected correlation parameter (r_target) within a tolerance of ±0.01. For **Empirical Mode**, success is defined as reporting the observed correlation and p-value **OR** correctly halting the hypothesis test and outputting a "Data Insufficient" report if N < 30. (See FR-004, US-1)
- **SC-002**: The robustness of the findings is measured against alternative parcellation schemes (AAL, Power 264) by generating a **single comparative bar chart** (PNG) showing the **absolute difference in Spearman correlation coefficients** (|r_Schaefer - r_Alternative|) between the primary and alternative results for **each requested** atlas. (See FR-010, US-3)
- **SC-003**: The validity of the multiple comparison handling is measured by verifying that the system correctly applies Holm-Bonferroni correction for the **combined family of tests** (univariate + MLR) and correctly calculates and reports the Variance Inflation Factor (VIF), flagging the result if VIF > 5. (See FR-004, US-2)
- **SC-004**: The computational feasibility is measured by ensuring the entire pipeline (preprocessing, calculation, plotting) completes within 6 hours on a **GitHub Actions ubuntu-latest runner (2 cores, 7GB RAM)** using a load profile of **N=50 subjects** with **200x200 matrices** derived from **HCP S1200 minimally preprocessed data (ICA-FIX)**. **This performance test applies to the pipeline logic in Validation Mode or synthetic stress tests, not the empirical hypothesis test.** (See FR-001, US-4)
- **SC-005**: The input data validity is measured by verifying that the system halts with the error "Invalid Entrainment Data" if the input CSV lacks required columns or contains non-numeric entrainment values. (See FR-008)

## Assumptions

- **Dataset Availability**: It is assumed that real-world HCP fMRI connectivity and rhythmic entrainment metrics for the same subjects may not exist in public repositories. Therefore, the primary execution path is **Empirical Analysis** requiring real data. If real data is unavailable or N < 30, the project **Halts the Hypothesis Test** with "Data Insufficient" and does NOT proceed to simulation for hypothesis testing. Simulation is strictly for **Pipeline Validation** (US-4) to verify code logic. **If the paired dataset does not exist, the scientifically valid outcome is the "Data Insufficient" report, not a fallback simulation.**
- **Methodological Framing**: The analysis assumes an observational design; therefore, all findings will be framed as associational (correlation) rather than causal, as no random assignment of network topology exists.
- **Measurement Validity**: It is assumed that simulated entrainment metrics (used ONLY in Validation Mode) are generated with a known correlation structure (target r=0.5) to validate the pipeline's ability to detect effects. **This does not constitute empirical evidence for the research question.**
- **Compute Constraints**: The analysis assumes that the NetworkX computation on a 200x200 matrix and the subsequent statistical tests are computationally trivial and will not exceed the 2-core/7GB RAM limits of the free-tier runner.
- **Threshold Justification**: The significance threshold is fixed at `p < 0.05` (Holm-Bonferroni corrected) based on standard community norms for exploratory neuroscience; no sensitivity sweep of the **alpha level** is required as the threshold is a standard convention. **The choice of Holm-Bonferroni over standard Bonferroni is an intentional methodological upgrade to control family-wise error rate more powerfully while maintaining rigor.**
- **Collinearity**: It is assumed that Clustering Coefficient and Characteristic Path Length, while related, provide distinct topological information; however, if the correlation between these two predictors exceeds the threshold (VIF > 5) in the MLR model, the joint analysis will be flagged as potentially collinear and interpreted descriptively (univariate results only).
- **Power Analysis**: The study is designed with a target N=85 for [deferred] power to detect r=0.45. N=30 is the minimum floor for exploratory reporting. Results with N < 30 are not interpretable for hypothesis testing.