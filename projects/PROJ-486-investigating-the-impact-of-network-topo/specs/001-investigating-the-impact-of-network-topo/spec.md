# Feature Specification: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Feature Branch**: `001-network-topology-entrainment`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli"

## User Scenarios & Testing

### User Story 1 - Core Correlation Analysis (Priority: P1)

The system must compute resting-state network topology metrics (clustering coefficient, characteristic path length) from HCP fMRI data and correlate them with external entrainment strength metrics to determine if a statistical association exists.

**Why this priority**: This is the primary scientific hypothesis. Without establishing the baseline correlation between structure and function, no further analysis or sensitivity testing has value.

**Independent Test**: Can be fully tested by executing the correlation pipeline on a subset of subjects and verifying that a scatter plot and correlation coefficient (r, p-value) are generated for the primary hypothesis.

**Acceptance Scenarios**:

1. **Given** a valid set of HCP fMRI parcellation files and a matching CSV of entrainment metrics, **When** the analysis script runs, **Then** it outputs a CSV containing individual subject IDs, their calculated clustering coefficients, path lengths, and the corresponding correlation statistics (r, p) against entrainment strength.
2. **Given** the output CSV, **When** the visualization module runs, **Then** it generates a scatter plot with 95% confidence intervals showing the relationship between the primary topology metric and entrainment strength.

---

### User Story 2 - Multiple Comparisons & Power Correction (Priority: P2)

The system must apply Bonferroni correction to the p-values derived from testing multiple topology metrics and report the adjusted significance status, acknowledging the sample size limitations.

**Why this priority**: The study involves testing at least two hypotheses (clustering and path length). Without correction, the risk of Type I error is inflated, rendering the findings scientifically invalid. This is a methodological necessity.

**Independent Test**: Can be fully tested by providing a synthetic dataset with known raw p-values, running the correction module, and verifying that the output p-values are scaled by the number of tests (N=2) and the significance threshold is correctly updated.

**Acceptance Scenarios**:

1. **Given** a set of raw p-values from the correlation analysis, **When** the correction step executes, **Then** the output includes a column for "adjusted_p_value" calculated as `min(raw_p * 2, 1.0)` and a boolean "is_significant" based on `adjusted_p < 0.05`.
2. **Given** a sample size N < 30, **When** the report is generated, **Then** it explicitly flags the power limitation in the summary text with the exact string: "Power Warning: N < 30 (Exploratory)".

---

### User Story 3 - Robustness Sensitivity Analysis (Priority: P3)

The system must re-run the core correlation analysis using alternative parcellation schemes (AAL, Power) to verify that the observed relationship is not an artifact of a single atlas choice.

**Why this priority**: While the primary hypothesis uses the Schaefer atlas, confirming that results hold across different spatial definitions is crucial for establishing the robustness of the finding. This is secondary to the primary result.

**Independent Test**: Can be fully tested by swapping the input atlas file to "AAL" and verifying that the pipeline completes without error and produces a comparative result table.

**Acceptance Scenarios**:

1. **Given** the configuration parameter `atlas_type` set to "AAL", **When** the pipeline executes, **Then** it generates a secondary correlation result table and a comparative **bar chart** showing the **absolute difference** in effect sizes between the Schaefer and AAL results.
2. **Given** a significant result in the primary analysis, **When** the sensitivity analysis completes, **Then** the report indicates whether the direction of the correlation (positive/negative) remains consistent across the alternative parcellations.

---

### Edge Cases

- **Missing Data**: How does the system handle subjects present in the fMRI dataset but missing from the entrainment dataset? (System must exclude these subjects and log the count).
- **Zero Variance**: What happens if a topology metric has zero variance across the sample (e.g., all subjects have identical path length)? (System must detect this, halt the correlation for that metric, and flag it as "Non-informative" rather than returning NaN).
- **Data Mismatch**: How does the system handle a mismatch in subject IDs between the two input sources? (System must perform an inner join and warn if the resulting N drops below the minimum power threshold of 30, outputting the flag "Power Warning: N < 30 (Exploratory)" but continuing execution).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess resting-state fMRI data from the Human Connectome Project (HCP) S release, parcellating into the Schaefer atlas with a standard high-resolution parcellation. (See US-1)
- **FR-002**: System MUST compute the Clustering Coefficient and Characteristic Path Length for each subject using a weighted correlation matrix derived from the fMRI data. (See US-1)
- **FR-003**: System MUST ingest external entrainment strength metrics (phase-locking values) from a provided CSV and align them by subject ID with the topology metrics. (See US-1)
- **FR-004**: System MUST calculate Spearman correlation coefficients between each topology metric and the entrainment strength, applying Bonferroni correction for the two tested metrics. The system MUST also calculate the Variance Inflation Factor (VIF) between the two metrics and flag the result as "Collinearity Warning: VIF > 5" if the VIF exceeds 5. (See US-1, US-2)
- **FR-005**: System MUST generate visualizations (scatter plots with 95% CIs) and a summary report containing correlation statistics (r, p, adjusted p) and effect sizes. (See US-1)
- **FR-006**: System MUST allow the user to specify an alternative parcellation atlas (e.g., AAL, Power 264) to perform a sensitivity analysis on the correlation results. (See US-3)
- **FR-007**: System MUST validate that the dataset contains the required variables (subject ID, topology metric, entrainment metric) before execution and halt with a clear error if any are missing. (See US-1)
- **FR-008**: System MUST validate the input entrainment CSV for the presence of required columns (subject_id, entrainment_metric) and data types (numeric) before processing, and halt with error "Invalid Entrainment Data" if validation fails. (See US-1)

### Key Entities

- **Subject**: Represents an individual participant, identified by a unique ID, containing attributes for fMRI connectivity data and behavioral/entrainment metrics.
- **TopologyMetric**: Represents a calculated network property (Clustering Coefficient or Path Length) associated with a specific subject and atlas configuration.
- **EntrainmentStrength**: Represents the quantified neural response (e.g., Phase-Locking Value) for a subject to a rhythmic stimulus.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The statistical association between network topology and entrainment strength is measured against the null hypothesis (r=0) using Spearman correlation and Bonferroni-corrected p-values (alpha=0.05). (See FR-004, US-1)
- **SC-002**: The robustness of the findings is measured against alternative parcellation schemes (AAL, Power 264) by generating a comparative **bar chart** showing the **absolute difference** in effect sizes between the primary and alternative results. (See FR-006, US-3)
- **SC-003**: The validity of the multiple comparison handling is measured by verifying that the system correctly applies Bonferroni correction for N=2 tests and correctly calculates and reports the Variance Inflation Factor (VIF), flagging the result if VIF > 5. (See FR-004, US-2)
- **SC-004**: The computational feasibility is measured by ensuring the entire pipeline (preprocessing, calculation, plotting) completes within 6 hours on a **GitHub Actions ubuntu-latest runner (2 cores, 7GB RAM)**. (See FR-001, US-1)
- **SC-005**: The input data validity is measured by verifying that the system halts with the error "Invalid Entrainment Data" if the input CSV lacks required columns or contains non-numeric entrainment values. (See FR-008)

## Assumptions

- **Dataset Availability**: It is assumed that the HCP release data is accessible via the provided open-access credentials and that the specific subset of subjects with matching external entrainment data can be identified and downloaded within the 14GB disk limit.
- **Methodological Framing**: The analysis assumes an observational design; therefore, all findings will be framed as associational (correlation) rather than causal, as no random assignment of network topology exists.
- **Measurement Validity**: It is assumed that the external entrainment metrics provided in the input dataset were derived using validated EEG/MEG protocols and that the phase-locking values are directly comparable across subjects.
- **Compute Constraints**: The analysis assumes that the NetworkX computation on a 200x200 matrix and the subsequent statistical tests are computationally trivial and will not exceed the 2-core/7GB RAM limits of the free-tier runner.
- **Threshold Justification**: The significance threshold is fixed at `p < 0.05` (Bonferroni corrected) based on standard community norms for exploratory neuroscience; no sensitivity sweep of the **alpha level** is required as the threshold is a standard convention. (Note: This refers strictly to alpha sensitivity, not the atlas choice sensitivity covered in US-3).
- **Collinearity**: It is assumed that Clustering Coefficient and Characteristic Path Length, while related, provide distinct topological information; however, if the correlation between these two predictors exceeds 0.8 (VIF > 5), the joint analysis will be flagged as potentially collinear and interpreted descriptively.