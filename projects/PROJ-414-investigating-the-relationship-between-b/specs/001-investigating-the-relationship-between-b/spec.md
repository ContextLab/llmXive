# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download publicly available fMRI datasets (e.g., OpenNeuro ds000246, ds001600) containing musicians performing improvisation tasks, preprocess them on a CPU‑only environment (motion correction, slice timing, normalization, bandpass filtering) using FSL (≥ 6.0) or AFNI pipelines, and generate clean time‑series data for specific Regions of Interest (ROIs).

**Why this priority**: Without clean, preprocessed neuroimaging data, no analysis can occur. This is the foundational data engineering step required for the entire study.

**Independent Test**: Can be fully tested by executing the pipeline on a single subject's data from OpenNeuro and verifying that the output contains normalized, filtered BOLD time‑series matrices for the defined ROIs without requiring GPU acceleration, using the specified FSL/AFNI tools.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID for a musician improvisation study, **When** the pipeline is executed on a CPU‑only runner using FSL, **Then** the system outputs preprocessed NIfTI files and ROI time‑series matrices for all subjects without requiring GPU acceleration.
2. **Given** a dataset with motion artifacts, **When** the motion correction step runs, **Then** the output time‑series shows reduced frame‑wise displacement metrics compared to the raw input, adhering to standard fMRI preprocessing thresholds (e.g., FD < 0.5 mm).
3. **Given** a standard parcellation atlas (e.g., Schaefer 100), **When** the ROI extraction runs, **Then** the system generates a time‑series matrix with dimensions (timepoints × ROIs) for each subject.

---

### User Story 2 - Network Metric Computation and Skill Correlation (Priority: P2)

The researcher needs to compute time‑varying functional connectivity metrics (global efficiency, modularity, participation coefficient) using sliding‑window correlations with robust statistical estimators, reduce dimensionality to avoid spurious findings, and statistically correlate these metrics with task conditions (Improvisation vs. Scripted) or expert blind‑rating scores of improvisation skill (primary) and years of training (secondary) while controlling for confounds (age, motion, instrument type, genre, practice intensity, education level).

**Why this priority**: This implements the core scientific hypothesis. It transforms raw data into the specific network dynamics and skill relationships the project aims to investigate, while addressing the statistical challenges of small‑N, high‑dimensional data.

**Independent Test**: Can be fully tested by running the correlation analysis on a synthetic dataset with known correlations between a “task” variable and a “network metric” variable, verifying that the system recovers the input correlation using the specified regularized estimator and permutation test.

**Acceptance Scenarios**:

1. **Given** preprocessed time‑series data and task labels for ≥20 subjects, **When** the sliding‑window correlation (using Ledoit‑Wolf estimator) and network metric calculation runs, **Then** the system outputs a table of metrics per subject per window.
2. **Given** the computed metrics and expert rating scores, **When** the regression analysis runs with PCA dimensionality reduction and controls for age, motion, instrument type, genre, practice intensity, and education level, **Then** the system outputs a correlation coefficient and permutation p‑value for the relationship between network flexibility and skill level.
3. **Given** multiple metrics are tested, **When** the significance testing runs, **Then** the system applies False Discovery Rate (FDR) correction to the permutation p‑values to control for multiplicity.

---

### User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

The researcher needs to perform a sensitivity analysis on the sliding‑window parameters (varying both window size and step size) to ensure results are robust, and generate visualizations of network topology differences between high‑skill and low‑skill groups using a specific, verifiable library stack.

**Why this priority**: This ensures the methodological soundness of the findings (threshold justification) and provides the necessary artifacts for the final report, though the core correlation can exist without the visualization.

**Independent Test**: Can be fully tested by running the analysis with three distinct window sizes (30 s, 45 s, 60 s) and two step sizes (5 s, 10 s), verifying that the system outputs a comparison report showing how the correlation strength varies across these thresholds.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the sensitivity analysis is triggered, **Then** the system re‑runs the metric calculation and correlation for window sizes ∈ {30, 45, 60} seconds and step sizes ∈ {5, 10} seconds, reporting the variance in correlation coefficients.
2. **Given** subjects grouped by task condition (Improvisation vs. Scripted), **When** the visualization module runs using NetworkX and Matplotlib, **Then** the system generates a network topology graph showing the difference in edge weights between groups.
3. **Given** the full analysis is complete, **When** the final report is generated, **Then** it includes the primary correlation results, the sensitivity analysis table, and the visualizations.

### Edge Cases

- What happens when a subject has excessive motion (FD > 0.5 mm for >20 % of volumes)? The system must flag and exclude the subject from the correlation analysis, logging the exclusion reason.
- How does the system handle datasets where the “improvisation” vs. “scripted” task distinction is ambiguous or missing? The system must detect missing task labels and halt with a clear error message requesting clarification or manual intervention, or fall back to using expert rating scores if available.
- How does the system handle cases where the correlation is non‑significant (p > 0.05)? The system must still output the result and explicitly flag it as “null result” rather than failing, as null results are scientifically valid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse OpenNeuro datasets ds000246 and ds001600 for fMRI data containing musical improvisation tasks, ensuring data fits within ~7 GB RAM constraints by processing subjects sequentially or in small batches. (See User Story 1)
- **FR-002**: System MUST preprocess fMRI data using **FSL (version ≥ 6.0)** (or optionally AFNI) including motion correction, slice timing, normalization to MNI space, and bandpass filtering targeting low‑frequency components (up to ≈ 0.1 Hz). (See User Story 1)
- **FR-003**: System MUST compute time‑varying functional connectivity matrices using sliding‑window correlations with **default window size = 45 s**, step size = 10 s, **using Pearson correlation with a rectangular window function and a Ledoit‑Wolf regularized estimator** to ensure stability with short windows (minimum 30 timepoints), and derive network metrics (global efficiency, modularity, participation coefficient) for each window. (See User Story 2)
- **FR-004**: System MUST perform a correlation/regression analysis between the computed network metrics and **expert blind‑rating scores of improvisation skill** (primary proxy) or, if ratings are unavailable, **task condition (Improvisation vs. Scripted)** or **years of training** (secondary proxies), controlling for age, head motion (FD), instrument type, musical genre, practice intensity, and education level as covariates. (See User Story 2)
- **FR-005**: System MUST apply **permutation testing (A substantial number of permutations.)** to generate p‑values, and THEN apply **False Discovery Rate (FDR) correction** to these p‑values to control for family‑wise error rates. (See User Story 2)
- **FR-006**: System MUST perform a sensitivity analysis sweeping the sliding‑window size over {30 s, 45 s, 60 s} **AND step size over {5 s, 10 s}** and report the variation in correlation coefficients to justify threshold robustness. (See User Story 3)
- **FR-007**: System MUST generate network topology visualizations comparing task conditions using **NetworkX for graph construction and Matplotlib for rendering**. (See User Story 3)
- **FR-008**: System MUST perform **Principal Component Analysis (PCA)** on the set of network metrics to reduce dimensionality before correlation analysis to mitigate the curse of dimensionality. (See User Story 2)
- **FR-009**: System MUST incorporate **expert blind‑rating scores** of improvisation skill (e.g., melodic novelty, rhythmic complexity) when such ratings are available for a subject, storing them in the Subject entity. (See User Story 2)
- **FR-010**: System MUST conduct an a priori **power analysis** targeting [deferred] power to detect a medium effect size (Cohen’s d = 0.5) at α = 0.05, and report the required sample size; the pipeline must abort if the available subject count is below this threshold. (See User Story 2)
- **FR-011**: System MUST include additional covariates **instrument type, musical genre, practice intensity, and education level** in the regression model when such metadata are present. (See User Story 2)
- **FR-012**: System MUST produce a **master CSV manifest** (e.g., `results/manifest.csv`) that records for every subject all derived metrics, covariates, expert ratings, and statistical outcomes; this manifest serves as the Single Source of Truth per Constitution Principle I. (See User Story 2)

### Key Entities

- **Subject**: Represents an individual musician participant with attributes: ID, Age, Years of Training, Head Motion (FD), Task Condition (Improvisation/Scripted), Instrument Type, Musical Genre, Practice Intensity, Education Level, Expert Rating (optional), and associated fMRI data.
- **Network Metric**: Represents a calculated graph property (e.g., Global Efficiency, Modularity) with attributes: Metric Name, Window ID, Value, and associated Subject ID.
- **Task Condition**: Represents the experimental condition (Improvisation vs. Scripted) associated with specific fMRI time‑series segments.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation between network flexibility (principal component scores) and expert rating scores is measured against the null hypothesis using **permutation testing (1000 permutations) followed by FDR correction**, and the result is considered successful if the **FDR‑corrected p‑value is < 0.05**. (See User Story 2)
- **SC-002**: The robustness of the correlation finding is measured against variations in sliding‑window parameters (window sizes ∈ {30 s, 45 s, 60 s} and step sizes ∈ {5 s, 10 s}); the analysis is successful if the **standard deviation of correlation coefficients across all window/step combinations is ≤ 0.05**. (See User Story 3)
- **SC-003**: The statistical validity of the findings is measured against the FDR‑corrected p‑value threshold (α < 0.05) to ensure control over multiplicity across tested metrics. (See User Story 2)
- **SC-004**: The feasibility of the analysis is measured against the hardware constraint of a standard GitHub Actions free‑tier runner (A modest number of CPU cores., ~7 GB RAM, ≤6 hours runtime) by verifying that the **analysis pipeline completes successfully without error and produces valid statistical output within the time limit**. (See User Story 1)
- **SC-005**: The power analysis requirement is satisfied when the a priori calculation (FR‑010) yields a required sample size ≤ the number of subjects actually available; otherwise the pipeline aborts with a clear insufficient‑power message. (See User Story 2)
- **SC-006**: The master manifest CSV (FR‑012) is verified to contain entries for every processed subject and to be syntactically valid (consistent columns, no missing mandatory fields). (See User Story 2)

## Assumptions

- **Assumption about data availability**: The OpenNeuro datasets ds000246 and ds001600 are expected to contain fMRI data with “improvisation” and “scripted” task labels, as well as metadata fields for age, instrument type, genre, practice intensity, and education level. Expert blind‑rating scores will be sourced from a parallel behavioral study or provided by collaborating musicologists; if unavailable, the analysis will fall back to task condition and years of training as secondary proxies.
- **Assumption about computational resources**: The fMRI preprocessing and network analysis can be completed within the 6‑hour time limit and ~7 GB RAM constraint of the free‑tier CI runner by processing subjects sequentially and using optimized CPU‑only libraries (FSL, AFNI, Nilearn for ancillary steps) without GPU acceleration.
- **Assumption about measurement validity**: **Expert blind‑rating scores are the primary validated measure of musical improvisation skill**; task condition and years of training are secondary proxies used only when ratings are absent. This addresses construct‑validity concerns.
- **Assumption about methodological framing**: Since the study uses observational data from existing datasets without random assignment, the findings will be framed strictly as associational (correlational) rather than causal, and the analysis will not claim to prove causation.
- **Assumption about collinearity**: The chosen network metrics (global efficiency, modularity, participation coefficient) may be correlated; the analysis will use PCA to handle this, treating the principal components as descriptors rather than claiming fully independent predictive effects.
- **Assumption about threshold justification**: The default sliding‑window size of 45 s follows community standards for fMRI dynamic connectivity; the sensitivity analysis (FR‑006) confirms robustness across the {30, 45, 60} s range and step sizes {5, 10} s.
- **Assumption about power analysis**: An a priori power analysis (FR‑010) targeting [deferred] power for a medium effect size is feasible given the expected subject pool; if the required N exceeds the available subjects, the study will be reported as under‑powered.
