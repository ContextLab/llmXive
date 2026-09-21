# Feature Specification: Statistical Power Analysis of Openly Available fMRI Datasets

**Feature Branch**: `001-statistical-power-analysis`  
**Created**: 2026-08-12  
**Status**: Draft  
**Input**: User description: "Statistical Power Analysis of Openly Available fMRI Datasets"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducibility Pipeline Execution (Priority: P1)

**Journey**: A researcher selects a specific cognitive paradigm from a curated list of OpenNeuro datasets. The system downloads the raw data, runs a standardized fMRIPrep preprocessing pipeline, fits a General Linear Model (GLM) to a simulated sample size (e.g., N=20) achieved by random subsampling from datasets with N > 20, and performs a split-half validation to determine if the effect is "replicated" in the held-out test set.

**Why this priority**: This is the core engine of the project. Without the ability to execute the end-to-end pipeline (download → preprocess → model → validate), no statistical analysis can occur. It represents the Minimum Viable Product (MVP) for the research tool.

**Independent Test**: This story can be fully tested by running the pipeline on a single, small, pre-verified OpenNeuro dataset (e.g., ds000030) with a fixed sample size subset (N=10) and verifying that the script outputs a binary replication status (0 or 1) without crashing or requiring GPU resources.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID and a requested sample size N=20, **When** the pipeline executes on a standard GitHub Actions free-tier runner (CPU, 7 GB RAM), **Then** the system downloads the raw data, preprocesses it using fMRIPrep, and outputs a binary replication result (0 or 1) within 6 hours for the reference dataset ds000030.
2. **Given** a dataset that exceeds the A memory constraint will be imposed to evaluate system performance under limited RAM availability. Research Question: How does memory limitation affect system scalability? Method: Controlled resource-constrained experiments. References: [Insert DOI/arXiv/author-year here]. of the runner, **When** the pipeline attempts to load the full data, **Then** the system automatically samples a subset of subjects to fit within memory constraints and logs the sampling action.

---

### User Story 2 - Power Curve Generation (Priority: P2)

**Journey**: The researcher requests an analysis across a range of sample sizes (e.g., N=10, 20, 40, 60) for a specific task. The system iterates through these sizes, performing the split-half validation for each, and aggregates the results to generate a power curve showing the empirical probability of replication vs. sample size.

**Why this priority**: This extends the P1 capability to answer the primary research question regarding the "non-linear relationship between sample size and replication probability." It transforms a single data point into a trend analysis.

**Independent Test**: This story can be tested by running the pipeline on one dataset with three distinct sample size configurations (N=10, N=20, N=40) and verifying that the output contains three distinct power estimates and that the trend (monotonic increase) is mathematically consistent with the inputs.

**Acceptance Scenarios**:

1. **Given** a dataset and a list of target sample sizes [10, 20, 40], **When** the analysis completes, **Then** the system outputs a table where each row corresponds to a sample size and contains the empirical replication rate (0.0 to 1.0) calculated from a sufficient number of bootstrapped iterations per size.
2. **Given** a dataset where the effect size is near zero, **When** the power curve is generated, **Then** the replication rate remains below 0.05 across all sample sizes, correctly reflecting the lack of signal.

---

### User Story 3 - Preprocessing Sensitivity Analysis (Priority: P3)

**Journey**: The researcher investigates how preprocessing choices affect power. The system re-runs the analysis on the same dataset using two different smoothing kernel sizes (e.g., 4mm vs. 8mm) while keeping the sample size constant, comparing the resulting effect sizes and replication rates.

**Why this priority**: This addresses the secondary research question regarding "methodological variations" and "preprocessing pipeline choice." It is lower priority because the primary goal is establishing the sample size threshold first.

**Independent Test**: This story can be tested by running the P1 pipeline on a single dataset with two distinct smoothing parameters and verifying that the output reports two different effect size estimates and a calculated difference metric.

**Acceptance Scenarios**:

1. **Given** a dataset and a fixed sample size N=30, **When** the system runs the analysis with smoothing kernels of 4mm and 8mm, **Then** the output reports the Cohen's d for both conditions and the absolute difference in replication rates.
2. **Given** a scenario where the smoothing kernel change leads to a shift in the estimated effect size, **When** the analysis completes, **Then** the system flags this as a "High Sensitivity" result in the summary report if the absolute difference in replication rates exceeds a substantial percentage point threshold.

---

### Edge Cases

- **What happens when** the OpenNeuro dataset is incomplete or contains corrupted NIfTI files?
  - The system must detect the corruption during the download/validation phase, skip the affected subjects, and proceed with the remaining valid subjects, logging a warning. If fewer than a sufficient number of valid subjects remain, the job fails gracefully with an explicit error code.
- **How does the system handle** datasets where the original sample size is smaller than the requested simulation size (e.g., requesting N=50 from a dataset with N=12)?
  - The system must clamp the requested sample size to the available data (N=12) and log a "Data Limitation" warning, rather than failing or attempting to hallucinate data.
- **What happens when** the GLM fitting fails to converge for a specific bootstrap iteration?
  - The system must discard the failed iteration, increment a counter of "failed iterations," and proceed. If the failure rate exceeds a significant proportion of total iterations, the job flags the result as "Unreliable" but still outputs the available data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw fMRI data and metadata from OpenNeuro for all available paradigms from a curated list of up to 15, ensuring the data fits within the disk constraint by streaming or sampling if necessary. (See US-1)
- **FR-002**: System MUST execute fMRIPrep (or equivalent CPU-tractable preprocessing) with a standardized configuration, supporting at least two distinct smoothing kernel sizes as configurable parameters. (See US-3)
- **FR-003**: System MUST implement a split-half validation loop that randomly partitions subjects into training and test sets, estimates effect size (Cohen's d) on the training set, and tests significance on the held-out test set. Replication success is defined as the effect size direction AND magnitude (within ±20% of the training estimate) matching between train and test sets. (See US-1)
- **FR-004**: System MUST perform bootstrapping with a minimum of 50 iterations per sample size configuration to generate a stable empirical probability of replication. (See US-2)
- **FR-005**: System MUST fit a Logistic Regression model with replication success as the outcome and sample size, preprocessing variant, and estimated noise level as fixed effects, using only CPU-optimized libraries (e.g., `statsmodels` or `scikit-learn`). (See US-2)
- **FR-006**: System MUST enforce a hard memory limit by automatically downsampling the dataset (random subject selection) if the full dataset exceeds the available system resources. (See US-1)

### Key Entities

- **Dataset**: Represents an OpenNeuro study, containing attributes: `dataset_id`, `paradigm_type`, `original_sample_size`, `raw_data_path`.
- **SimulationConfig**: Represents a single run configuration, containing attributes: `sample_size_target`, `smoothing_kernel`, `num_iterations` (>= 50), `random_seed`.
- **ReplicationResult**: Represents the outcome of a single simulation, containing attributes: `effect_size_est`, `p_value`, `replication_success` (binary), `smoothing_kernel_used`.
- **PowerCurve**: Represents the aggregated analysis for a paradigm, containing attributes: `paradigm_type`, `sample_sizes_tested`, `empirical_rates` (list of floats).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The empirical replication rate (binary success/fail) is measured against the consistency of effect direction and magnitude between train and test sets to ensure the metric reflects true predictive power. (See US-1)
- **SC-002**: The non-linear relationship between sample size and replication probability is measured against the bootstrapped power curve generated for at least 5 distinct cognitive paradigms. (See US-2)
- **SC-003**: The impact of preprocessing choices on effect size is measured against the absolute difference in Cohen's d between the two smoothing conditions. (See US-3)
- **SC-004**: The validity of the statistical model is measured against the convergence of the Logistic Regression likelihood function and the absence of multicollinearity (VIF < 5) among fixed effects. (See US-2)
- **SC-005**: The computational feasibility is measured against the total wall-clock time of the analysis, which must not exceed a practical threshold on a standard GitHub Actions free-tier runner (A configuration with a limited number of CPU cores and constrained RAM.). (See US-1)

## Assumptions

- **Assumption about data availability**: OpenNeuro datasets are assumed to contain sufficient raw data (BIDS format) and metadata for the selected 15 cognitive paradigms; if a specific paradigm is missing, the system will skip it and log a warning.
- **Assumption about preprocessing**: The fMRIPrep container is assumed to be available and runnable on the GitHub Actions free-tier runner without requiring GPU acceleration; if the standard container fails due to resource constraints, the system will fallback to a simplified CPU-only preprocessing script.
- **Assumption about statistical validity**: The split-half validation method is assumed to be a valid proxy for "replication" in the absence of independent external datasets; the results are framed as associational rather than causal.
- **Assumption about sample size limits**: The maximum sample size simulated will be capped at the original sample size of the largest available dataset in the selected set (e.g., N=100), and no extrapolation beyond observed data will be performed.
- **Assumption about threshold justification**: The significance threshold (alpha) is fixed based on community standards.; a sensitivity analysis sweeping alpha over a range of small values will be performed to verify robustness. This analysis is required to ensure observed power curves are robust to alpha selection and not artifacts of a specific threshold.
- **Assumption about power correction**: Given the multiple hypothesis tests (across 15 paradigms and multiple sample sizes), a multiple-comparison correction method (e.g., Bonferroni or Benjamini-Hochberg FDR) will be applied to the final model results to control the family-wise error rate.