# Feature Specification: Predicting Molecular Complexity Using Information Theory

**Feature Branch**: `001-predict-molecular-complexity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does information-theoretic molecular complexity (measured as minimal description length of molecular graphs) correlate with established chemical properties such as synthetic accessibility and drug-likeness?"

## User Scenarios & Testing

### User Story 1 - Core Correlation Analysis (Priority: P1)

**User Journey**: A researcher needs to determine if information-theoretic complexity (Shannon entropy of vertex degrees and Lempel-Ziv compression of canonical SMILES) correlates with established chemical properties (Synthetic Accessibility Score and QED) for a dataset of molecules.

**Why this priority**: This is the primary research question. Without establishing the correlation, the utility of the information-theoretic metric cannot be validated. It forms the foundation of the entire study.

**Independent Test**: The system must successfully download [deferred] molecules, compute all four metrics (Entropy, LZ, SA, QED), and output a statistical report containing Pearson correlation coefficients and p-values for both metric pairs.

**Acceptance Scenarios**:

1. **Given** a valid PubChem CID range (1-5000) and a clean Python environment with RDKit installed, **When** the analysis script is executed, **Then** the system downloads [deferred] SMILES strings, computes the four metrics, and outputs a JSON report with correlation coefficients (r) and p-values for (Entropy vs. SA) and (LZ vs. SA).
2. **Given** the analysis script, **When** the dataset contains molecules with missing structural data (e.g., invalid SMILES), **Then** the system skips invalid entries, logs the count of skipped entries, and proceeds with the remaining valid molecules without crashing.
3. **Given** the computed metrics, **When** the correlation is calculated, **Then** the system explicitly labels the results as "associational" and does not claim causal relationships in the output report.

---

### User Story 2 - Statistical Robustness & Sensitivity (Priority: P2)

**User Journey**: A researcher needs to verify that the observed correlations are not artifacts of the specific dataset sample or arbitrary threshold choices, requiring bootstrap resampling and sensitivity analysis.

**Why this priority**: Raw correlation can be spurious. Bootstrap resampling validates stability, and sensitivity analysis ensures that any derived thresholds (if used in future extensions) are robust. This addresses the "Methodological Soundness" requirement for multiplicity and threshold justification.

**Independent Test**: The system must perform a sufficient number of bootstrap iterations to generate confidence intervals for the correlation coefficients and report the stability of the findings.

**Acceptance Scenarios**:

1. **Given** the initial correlation results, **When** the bootstrap resampling module runs 1,000 iterations, **Then** the system outputs 95% confidence intervals for the correlation coefficients and reports the standard deviation of the bootstrapped correlations.
2. **Given** the analysis logic, **When** multiple hypothesis tests are performed (e.g., testing both Entropy and LZ against both SA and QED), **Then** the system applies a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) and reports the adjusted p-values.

---

### User Story 3 - Visualization & Reporting (Priority: P3)

**User Journey**: A researcher needs to visualize the relationship between information-theoretic measures and chemical properties to interpret the magnitude and direction of the correlation.

**Why this priority**: While statistical numbers are essential, visual confirmation is required for human interpretation and publication. This is a supporting feature to the core analysis.

**Independent Test**: The system must generate scatter plots with regression lines, 95% confidence intervals, and annotated p-values for all four metric pairs.

**Acceptance Scenarios**:

1. **Given** the computed metrics, **When** the visualization module is triggered, **Then** the system generates four distinct scatter plots (Entropy-SA, Entropy-QED, LZ-SA, LZ-QED) with linear regression lines and 95% confidence intervals.
2. **Given** the plots, **When** they are rendered, **Then** each plot includes the Pearson correlation coefficient (r), the p-value, and the sample size (n) in the title or caption.
3. **Given** the final analysis, **When** the report is generated, **Then** the system outputs a single PDF or HTML report containing the statistical tables and all generated plots.

---

### Edge Cases

- **What happens when** the PubChem API rate limits the request? The system must implement a retry mechanism with exponential backoff (a limited number of retries, wait 2-10 seconds) before failing the job.
- **How does the system handle** molecules with extremely large molecular weights or complex structures that might cause RDKit to hang or consume excessive memory? The system must set a timeout of 60 seconds per molecule; if exceeded, the molecule is skipped and logged as "timeout".
- **What happens when** the dataset size exceeds the 4 GB RAM limit of the CI runner? The system must process the dataset in chunks (e.g., a defined batch size) and aggregate results incrementally to stay within memory bounds.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download [deferred] molecules from PubChem (CID 1-5000) in SMILES format, handling rate limits with a retry mechanism of at most 3 attempts per molecule. (See US-1)
- **FR-002**: System MUST compute Shannon entropy based on the distribution of vertex degrees in the molecular graph and Lempel-Ziv compressed byte counts of the canonical SMILES string (using RDKit v2023.09 or later) for every valid SMILES string. (See US-1)
- **FR-003**: System MUST calculate Synthetic Accessibility (SA) and Quantitative Estimate of Drug-likeness (QED) scores using RDKit's standard implementations for every valid molecule. (See US-1)
- **FR-004**: System MUST perform Pearson correlation analysis between (Shannon Entropy, SA), (Shannon Entropy, QED), (LZ, SA), and (LZ, QED), explicitly framing results as associational. (See US-1)
- **FR-005**: System MUST execute exactly 1,000 bootstrap resampling iterations to generate 95% confidence intervals for all correlation coefficients. (See US-2)
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to all p-values generated from the four correlation tests. (See US-2)
- **FR-007**: System MUST generate scatter plots with linear regression lines, 95% confidence intervals, and annotated statistical metrics (r, p, n) for all metric pairs. (See US-3)
- **FR-008**: System MUST process the dataset in chunks such that peak memory usage remains ≤ 4 GB. (See US-1)

### Key Entities

- **Molecule**: Represents a chemical compound identified by a CID, containing attributes: `smiles`, `shannon_entropy`, `lz_length`, `sa_score`, `qed_score`.
- **CorrelationResult**: Represents the statistical relationship between two metrics, containing attributes: `metric_pair`, `pearson_r`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`.
- **BootstrapSample**: Represents a single iteration of resampling, containing attributes: `iteration_id`, `resampled_correlation`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Pearson correlation coefficient (r) between information-theoretic complexity (Shannon Entropy of vertex degrees) and Synthetic Accessibility Score is measured against the expected moderate-to-strong positive correlation (r > 0.5) as hypothesized in the research question. (See US-1)
- **SC-002**: The Pearson correlation coefficient (r) between Lempel-Ziv complexity (of canonical SMILES) and Synthetic Accessibility Score is measured against the expected moderate-to-strong positive correlation (r > 0.5). (See US-1)
- **SC-003**: The stability of the correlation coefficients is measured against the 95% confidence intervals derived from bootstrap iterations, ensuring the intervals do not include zero for significant findings. (See US-2)
- **SC-004**: The false-positive rate is measured against the significance threshold (α = 0.05) after applying multiple-comparison correction, ensuring the family-wise error rate is controlled. (See US-2)
- **SC-005**: The computational execution time is measured against a duration limit of ≤ 45 minutes, ensuring the full analysis (download, compute, bootstrap, plot) completes within this window. (See US-1)
- **SC-006**: The memory footprint is measured against a peak usage threshold of ≤ 4 GB, ensuring peak usage never exceeds this threshold during the chunked processing of the dataset. (See US-1)

## Assumptions

- **Dataset-variable fit**: We assume the PubChem dataset (CID 1-5000) contains valid SMILES strings for all requested CIDs and that these structures are sufficient to compute adjacency matrices and compression lengths. If a CID returns no data or invalid SMILES, it is skipped, and the sample size is adjusted accordingly.
- **Inference framing**: Since this is an observational study using existing molecular data without random assignment, all findings regarding the relationship between complexity and chemical properties are strictly framed as **associational**, not causal.
- **Compute feasibility**: The analysis assumes the use of CPU-only methods (Shannon entropy calculation, Lempel-Ziv compression, linear regression) that do not require GPU acceleration or heavy deep learning training, fitting within a constrained multi-core, limited RAM, and time-bound environment.
- **Threshold justification**: No arbitrary decision thresholds (e.g., "high complexity" cutoffs) are introduced in this phase; the analysis focuses on continuous correlation. If thresholds are defined in future work, a sensitivity analysis will be required.
- **Measurement validity**: We assume RDKit's implementations of SA Score and QED are the standard, validated benchmarks for synthetic accessibility and drug-likeness, respectively, as cited in the literature.
- **Predictor collinearity**: We assume that while Shannon Entropy (vertex degrees) and Lempel-Ziv length (canonical SMILES) both measure complexity, they capture different structural aspects (graph topology vs. string redundancy), but collinearity diagnostics will be reported if both are used as predictors in a joint model.
- **Data sampling**: The dataset is limited to the first [deferred] CIDs to ensure the analysis remains computationally tractable on free-tier CI runners; this sample is assumed to be representative of general chemical space for the purpose of this exploratory study.
- **API reliability**: The PubChem REST API is assumed to be available and stable; transient failures are handled via the retry mechanism described in FR-001.
- **SA Complexity Component**: We explicitly acknowledge that the Synthetic Accessibility Score (SA) includes a topological complexity component (Bertz CT). The study tests whether information-theoretic measures provide *incremental* predictive power over standard size/complexity metrics, rather than merely re-confirming the internal structure of the SA score.
- **Canonicalization Bias**: We acknowledge that Lempel-Ziv compression on SMILES is dependent on the canonicalization algorithm. The results are interpreted as "complexity of the canonical SMILES representation" rather than "absolute graph complexity," and the specific RDKit version used for canonicalization is recorded in the output.