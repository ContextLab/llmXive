# Feature Specification: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Structural and Dynamic Graph Metrics (Priority: P1)

A researcher needs to derive quantitative topological metrics (global efficiency, average clustering coefficient, modularity) from structural connectivity (dMRI) and dynamic functional states (fMRI) for a cohort of subjects to establish the primary dataset for analysis.

**Why this priority**: This is the foundational data generation step. Without valid, matched metrics for both modalities, no correlation analysis can occur. It represents the minimum viable dataset required to answer the core research question.

**Independent Test**: Can be fully tested by running the data processing pipeline on a single subject's preprocessed HCP data and verifying that the output JSON contains non-null values for global efficiency, clustering coefficient, modularity, and mean dwell time.

**Acceptance Scenarios**:

1. **Given** preprocessed dMRI and fMRI data for a single subject, **When** the pipeline executes the Schaefer 200-region parcellation and sliding-window state extraction via k-means, **Then** the output file contains valid numerical values for structural global efficiency, average clustering, modularity, and dynamic state dwell times.
2. **Given** a subject with missing fMRI frames, **When** the pipeline processes the time series, **Then** the system skips the subject or imputes missing values according to the defined protocol without crashing, and logs the exclusion/imputation event.
3. **Given** the full cohort of ~50 subjects, **When** the batch processing completes, **Then** the system produces a single aggregated CSV containing metrics for all subjects, and logs every subject exclusion with a specific reason (e.g., "convergence failure", "sparsity >90%").

---

### User Story 2 - Perform Structure-Function Correlation Analysis (Priority: P2)

A researcher needs to statistically correlate the derived structural topological metrics with dynamic functional metrics to determine if structural architecture predicts dynamic stability.

**Why this priority**: This directly addresses the research question. It transforms the raw metrics into scientific findings (correlation coefficients) and applies necessary statistical corrections (FDR) to ensure validity.

**Independent Test**: Can be fully tested by running the correlation script on the aggregated CSV and verifying that the output includes a correlation matrix with correlation coefficients (r) and corresponding p-values for every structural-dynamic metric pair.

**Acceptance Scenarios**:

1. **Given** the aggregated metrics CSV, **When** the correlation analysis runs, **Then** the output includes correlation coefficients (r) and p-values for the relationship between structural global efficiency and the number of visited states.
2. **Given** a set of multiple hypothesis tests (e.g., 3 structural metrics × 3 dynamic metrics), **When** the analysis completes, **Then** the system applies Benjamini-Hochberg FDR correction (q=0.05) and flags which correlations survive correction.
3. **Given** the correlation results, **When** the researcher requests a sensitivity check, **Then** the system re-runs the analysis with a sliding window of 20 TRs and reports the change in correlation coefficients compared to the baseline (30 TRs).

---

### User Story 3 - Generate Robustness and Methodological Reports (Priority: P3)

A researcher needs to verify that the findings are robust to parameter choices (window length, threshold density) and that the methodology adheres to observational study constraints (associational, not causal).

**Why this priority**: This ensures the scientific defensibility of the results, addressing the "methodological soundness" requirements regarding threshold justification and inference framing. It prevents the publication of artifacts driven by arbitrary parameter choices.

**Independent Test**: Can be fully tested by comparing the primary analysis report against the robustness report and verifying that the system explicitly labels findings as "associational" and documents the sensitivity of results to window length and threshold changes.

**Acceptance Scenarios**:

1. **Given** the primary correlation results, **When** the robustness report is generated, **Then** the report explicitly states that findings are "associational" and not causal, citing the observational nature of the HCP data.
2. **Given** the analysis with 30 TR windows, **When** the system runs the 20 TR window sensitivity analysis, **Then** the report includes a table showing the absolute difference in correlation coefficients for all metric pairs between the two window lengths.
3. **Given** the final results, **When** the researcher reviews the report, **Then** the report includes a section confirming CPU-only execution and a resource usage report (peak RAM, total runtime) demonstrating compliance with the 7GB RAM / 6-hour CPU constraints.

---

### Edge Cases

- **What happens when** the k-means clustering fails to converge for a specific subject due to noisy fMRI data?
  - *Handling*: The system must detect non-convergence (e.g., via iteration limit warnings) and exclude that subject from the dynamic metrics calculation, logging the exclusion reason.
- **How does system handle** a subject where the structural connectivity matrix is sparse (mostly zeros) due to poor dMRI quality?
  - *Handling*: The system must calculate a sparsity metric; if sparsity exceeds a high threshold, the subject is flagged and excluded from the structural metric calculation to prevent skewed correlation results.
- **What happens when** the FDR correction results in zero significant findings?
  - *Handling*: The system must still generate a report explicitly stating that no associations survived FDR correction, rather than silently omitting results or forcing significance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute structural graph metrics (global efficiency, average clustering coefficient, modularity) from preprocessed dMRI connectivity matrices using NetworkX. (See US-1)
- **FR-002**: System MUST extract dynamic functional states from resting-state fMRI time series by computing sliding-window correlation matrices (30 TR window, 1 TR step), concatenating these windowed matrices across all subjects, and applying k-means clustering (k=5) to define a common set of recurrent states. (See US-1)
- **FR-003**: System MUST calculate per-subject dynamic metrics including number of visited states and mean dwell time for each state based on the common state space defined in FR-002. (See US-1)
- **FR-004**: System MUST test for normality (Shapiro-Wilk, α=0.05) on structural and dynamic metrics; if normality is violated, use Spearman's rank correlation, otherwise use Pearson's correlation, between each structural metric and each dynamic metric across the subject cohort. (See US-2)
- **FR-005**: System MUST apply Benjamini-Hochberg FDR correction (q=0.05) to all correlation p-values to control for multiple comparisons. (See US-2)
- **FR-006**: System MUST perform a sensitivity analysis by re-running the dynamic state extraction with a 20 TR window length and comparing results. (See US-3)
- **FR-007**: System MUST explicitly label all statistical associations as "associational" and not causal in the final output. (See US-3)
- **FR-008**: System MUST define the structural network thresholding strategy as proportional density (e.g., [deferred] density) and perform a sensitivity analysis on this threshold (±5%) to ensure result robustness. (See US-3)

### Key Entities

- **Subject**: Represents a single participant from the HCP dataset, containing unique ID, structural connectivity matrix, and fMRI time series.
- **StructuralMetric**: Represents a derived graph property (e.g., global efficiency) for a specific subject.
- **DynamicMetric**: Represents a derived state property (e.g., mean dwell time) for a specific subject.
- **CorrelationResult**: Represents the statistical association (r, p-value, FDR-corrected p-value) between a structural and dynamic metric.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between structural global efficiency and dynamic state stability (hypothesized to be stable) is measured against the null hypothesis of no association (r=0) using the appropriate correlation method (Pearson or Spearman) and FDR-corrected p-values. (See US-2)
- **SC-002**: The robustness of dynamic state metrics is measured against the baseline (30 TR window) by calculating the absolute difference in correlation coefficients when using a 20 TR window. (See US-3)
- **SC-003**: The computational feasibility is measured against the GitHub Actions free-tier constraints (a limited number of CPU cores, a limited amount of RAM, a time limit) by verifying the total runtime and peak memory usage of the full pipeline via a generated resource usage report. (See US-3)
- **SC-004**: The methodological validity is measured against the requirement for observational inference by verifying that the final report contains explicit "associational" framing and no causal language. (See US-3)
- **SC-005**: The data completeness is measured against the total cohort size by calculating the percentage of subjects successfully processed, with exclusions explicitly categorized by reason (e.g., convergence failure, sparsity >90%). (See US-1)

## Assumptions

- The preprocessed dMRI and fMRI data from OpenNeuro contains sufficient signal quality for a cohort of subjects to yield valid structural connectivity matrices and time series for dynamic analysis.
- The Schaefer 200-region atlas is compatible with the spatial resolution and parcellation of the provided HCP data derivatives.
- The sliding-window correlation method with a 30 TR window is a valid approximation for capturing dynamic functional connectivity states in resting-state fMRI.
- The sample size of a sufficient number of subjects provides sufficient statistical power to detect moderate effect sizes after FDR correction, or that the study is explicitly framed as exploratory if power is limited.
- The k-means clustering algorithm with k=5 is an appropriate choice for identifying the dominant recurring connectivity states in this dataset, and the resulting states are hypothesized to be biologically meaningful rather than mere methodological artifacts.
- All required Python libraries (nilearn, numpy, pandas, networkx, scikit-learn, statsmodels) can be installed and run within a reasonable time limit on a CPU-only runner.
- The structural connectivity matrices provided in the HCP derivatives require explicit thresholding (proportional density) to be suitable for graph metric calculation, and the results will be robust to small variations in this threshold.