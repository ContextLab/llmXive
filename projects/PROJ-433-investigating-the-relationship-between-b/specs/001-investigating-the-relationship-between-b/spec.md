# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to automatically download the Human Connectome Project (HCP) large-scale resting-state fMRI and behavioral datasets, and preprocess the fMRI data using a distributed fMRIPrep configuration so that I can obtain clean, normalized neuroimaging data ready for dynamic connectivity analysis.

**Why this priority**: Without preprocessed data, no analysis can occur. This is the foundational step that enables all subsequent metrics. It is independent because the pipeline can be tested and validated by verifying the existence and format of the output files without needing to run the correlation analysis.

**Independent Test**: The pipeline is tested by executing the download and preprocessing script on a 10-subject subset. The system must verify that the output contains valid NIfTI files in MNI space with motion correction applied, consuming ≤ 2 CPU cores and ≤ 7 GB RAM per node, AND verify that output NIfTI files pass fMRIPrep QC metrics (e.g., motion < 0.5mm, valid tissue segmentation).

**Acceptance Scenarios**:

1. **Given** a valid HCP access token and a distributed compute environment (or a single-node subset for testing), **When** the download and preprocessing script is executed, **Then** the system outputs preprocessed fMRI NIfTI files for at least 100 subjects (or 10 for local testing) in MNI space within 6 hours (distributed) or 10 hours (local subset).
2. **Given** a corrupted or incomplete download of the HCP dataset, **When** the download script runs, **Then** the system retries the download up to 3 times before failing with a clear error message, ensuring data integrity.

---

### User Story 2 - Network Reconfigurability Metric Computation (Priority: P2)

As a researcher, I need the system to compute sliding-window functional connectivity matrices and extract network reconfigurability metrics (community state transitions) for each subject so that I can quantify brain network dynamics.

**Why this priority**: This step transforms raw preprocessed data into the specific predictor variables required for the hypothesis test. It is independent because the metric computation can be validated by checking the statistical properties of the output matrices against the input data, separate from the behavioral correlation.

**Independent Test**: The module is tested by running it on a single preprocessed subject and verifying that the output JSON contains the network reconfigurability metric with valid numerical ranges (transitions >= 0), completing within 30 minutes on 2 CPU cores.

**Acceptance Scenarios**:

1. **Given** a preprocessed fMRI NIfTI file for a single subject, **When** the sliding-window analysis runs with a 30-second window duration and 5-second step size, **Then** the system generates a community state transition count stored in a structured JSON file.
2. **Given** a subject with excessive motion artifacts (framewise displacement > 0.5mm), **When** the quality control check runs, **Then** the system excludes the subject from the metric computation and logs the exclusion reason.
3. **Given** a subject where the Louvain algorithm fails to converge, **When** the metric computation runs, **Then** the system retries the algorithm with a different random seed up to 3 times; if it still fails, the subject is excluded and logged.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

As a researcher, I need the system to perform Spearman correlations between the network reconfigurability metrics and cognitive processing speed scores (Digit Symbol Substitution Test), apply Bonferroni correction, and generate scatter plots with confidence intervals so that I can evaluate the hypothesis.

**Why this priority**: This is the final analytical step that directly answers the research question. It depends on the outputs of US-01 and US-02 but can be tested independently by injecting mock data to verify the statistical logic and visualization rendering.

**Independent Test**: The analysis module is tested by running it against a synthetic dataset of subjects with known correlation properties, verifying that the reported p-values and effect sizes match the expected values within 1e-6 numerical tolerance, and that plots are generated without error.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 subjects with computed reconfigurability metrics and behavioral scores, **When** the correlation analysis runs, **Then** the system outputs a CSV containing the Spearman correlation coefficient, p-value, and Bonferroni-corrected p-value for each metric-behavior pair.
2. **Given** the correlation results, **When** the visualization script runs, **Then** the system generates a set of scatter plots (one for each metric-behavior pair) with 95% confidence intervals and effect size annotations, saving them as PNG files.

---

### User Story 4 - Permutation Testing Validation (Priority: P3)

As a researcher, I need the system to perform permutation testing (1000 shuffles) on the correlation results to confirm that the observed association is not spurious due to multiple comparisons or non-normal data distribution.

**Why this priority**: This validation step is critical for scientific soundness, ensuring the reported correlations are robust. It depends on US-3 outputs but is a distinct validation process.

**Independent Test**: The module is tested by running it on a dataset where the null hypothesis is known to be true (shuffled data), verifying that the p-value distribution is uniform and the observed p-value is not significant (p > 0.05).

**Acceptance Scenarios**:

1. **Given** the correlation results from US-3, **When** the permutation test runs with 1000 shuffles, **Then** the system outputs a p-value derived from the permutation distribution that indicates significance (or lack thereof) relative to the null hypothesis.

---

### Edge Cases

- What happens when the HCP behavioral dataset lacks cognitive scores (DSST) for a specific subject included in the fMRI set? (System excludes the subject from the correlation analysis and logs the missing data count).
- How does the system handle subjects where the Louvain algorithm fails to converge on a community structure? (The system retries the algorithm with a different random seed up to 3 times; if it still fails, the subject is excluded and logged).
- What happens if the computed p-values are exactly 0 or 1? (The system applies a floor/ceiling of a small positive constant to prevent division-by-zero or log errors in effect size calculations).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the HCP large-scale resting-state fMRI and behavioral datasets from the public release and store them locally, ensuring data integrity via checksum verification (See US-1).
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep in distributed/single-CPU mode as available, performing motion correction, slice-timing correction, normalization to MNI space, and nuisance regression, ensuring output files are valid NIfTI format (See US-1).
- **FR-003**: System MUST compute sliding-window functional connectivity matrices using a fixed-duration window and a stepped step size for 200 cortical parcels defined by the Schaefer atlas (See US-2).
- **FR-004**: System MUST extract the network reconfigurability metric: number of community state transitions using the Louvain algorithm. If the algorithm fails to converge after a predefined number of retries, the system MUST exclude the subject and log the reason. (See US-2).
- **FR-005**: System MUST perform Spearman rank correlations between the extracted reconfigurability metrics and behavioral cognitive scores (Digit Symbol Substitution Test) ONLY for subjects where both metrics and behavioral scores are present; otherwise, exclude and log (See US-3).
- **FR-006**: System MUST apply Bonferroni correction for multiple comparisons across connectivity metrics and behavioral measures, reporting adjusted p-values (See US-3).
- **FR-007**: System MUST generate scatter plots with 95% confidence intervals and report effect sizes (Cohen's r) for all significant correlations (See US-3).
- **FR-008**: System MUST perform permutation testing with a sufficient number of shuffles to validate the significance of the observed correlations against a null distribution (See US-4).

### Non-Functional Requirements

- **NFR-001**: The pipeline MUST be designed to support distributed execution (e.g., via SLURM, Kubernetes, or Dask) to process the full subject cohort within a 6-hour window on a cluster. Local testing on a single node is limited to a small subset of subjects.
- **NFR-002**: All random number generators used in the Louvain algorithm and permutation testing MUST be seeded for reproducibility.

### Key Entities

- **Subject**: Represents an individual participant in the HCP study, identified by a unique subject ID, containing attributes for fMRI file path, behavioral scores, and QC metrics.
- **ConnectivityMatrix**: Represents a time-varying functional connectivity matrix for a specific subject and time window, containing pairwise correlation values between 200 cortical parcels.
- **ReconfigurabilityMetric**: Represents the computed dynamic network properties for a subject, containing the count of community state transitions.
- **CorrelationResult**: Represents the output of the statistical analysis, containing the correlation coefficient, p-value, adjusted p-value, and effect size for a specific metric-behavior pair.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of subjects successfully processed through the fMRIPrep pipeline is measured against the total number of downloaded subjects (See US-1).
- **SC-002**: Re-running the metric computation on a fixed random seed yields identical results (difference < 1e-9), ensuring reproducibility of the network reconfigurability metrics (See US-2).
- **SC-003**: The system successfully outputs a CSV file containing p-values for all metric-behavior pairs without error, demonstrating correct execution of the statistical pipeline (See US-3).
- **SC-004**: The effect sizes (Cohen's r) for the observed correlations are measured against standard benchmarks for small, medium, and large effects to interpret the practical significance of the findings (See US-3).
- **SC-005**: The system successfully generates all required scatter plots and permutation test reports for the analyzed cohort (See US-3, US-4).

## Assumptions

- **Assumption about data availability**: The HCP public release contains the Digit Symbol Substitution Test (DSST) scores for the subjects included in the resting-state fMRI subset., serving as a validated proxy for cognitive processing speed and time perception accuracy.
- **Assumption about computational resources**: The fMRIPrep pipeline and sliding-window analysis are designed for distributed execution. Local testing on a single node is limited to a 10-subject subset due to hardware constraints; full processing of 100 subjects requires a cluster environment.
- **Assumption about methodological validity**: The Schaefer 200-parcel atlas provides sufficient spatial resolution to capture the dynamic network reconfigurability relevant to time perception. The 30-second window length is appropriate for capturing the relevant timescales of brain network dynamics, as slow hemodynamic fluctuations (in the low-frequency range) are theorized to reflect the accumulation mechanism of the internal clock model linked to time perception.
- **Assumption about statistical power**: A sample size of approximately 100 subjects (after QC exclusions) provides sufficient power to detect a moderate correlation (r ≈ 0.3) with 80% power at α = 0.05, acknowledging that the Bonferroni correction and permutation testing will increase the required threshold for significance.
- **Assumption about threshold justification**: The 30-second window size and 5-second step size are standard defaults in the dynamic connectivity literature; a sensitivity analysis sweeping the window size over a range of short durations will be conducted to ensure the results are robust to this choice.
- **Assumption about inference framing**: The study design is observational (using existing HCP data without random assignment), so all reported findings will be framed as associational relationships between network reconfigurability and cognitive processing speed, not causal effects.