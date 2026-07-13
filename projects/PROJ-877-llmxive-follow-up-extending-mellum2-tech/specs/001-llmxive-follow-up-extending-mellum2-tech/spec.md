# Feature Specification: llmXive follow-up: extending "Mellum2 Technical Report"

**Feature Branch**: `001-llmxive-complexity-loss`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Mellum2 Technical Report'"

## User Scenarios & Testing

### User Story 1 - Correlation Analysis of Code Complexity and Prediction Loss (Priority: P1)

**Journey**: A researcher downloads a subset of public code repositories, runs static analysis to label chunks with cyclomatic complexity and nesting depth, processes them through a frozen LLM to measure per-token loss, and generates a scatter plot with regression lines showing the correlation between these metrics.

**Why this priority**: This is the core research question. Without establishing the existence and strength of the correlation, no further analysis of thresholds or regimes is possible. It delivers the primary hypothesis test.

**Independent Test**: The system can be fully tested by executing the data pipeline on a fixed sample of repositories and verifying that a correlation coefficient (Pearson/Spearman) is computed and a scatter plot is generated, regardless of the specific value of the correlation.

**Acceptance Scenarios**:

1. **Given** a subset of 500 Python repositories with static complexity labels, **When** the system processes them through the frozen LLM, **Then** a correlation coefficient between cyclomatic complexity and prediction loss is calculated and reported.
2. **Given** the same dataset, **When** the system generates the visualization, **Then** the plot displays data points, a regression line, and axis labels identifying "Cyclomatic Complexity" and "Prediction Loss (Perplexity)".
3. **Given** a held-out validation set of Java repositories, **When** the system runs the analysis, **Then** the correlation is computed independently to verify cross-language consistency.

---

### User Story 2 - Non-Linear Threshold Detection (Priority: P2)

**Journey**: The researcher applies piecewise regression or change-point detection algorithms to the correlation data to identify specific structural thresholds where the relationship between complexity and loss shifts from linear to non-linear, and generates a sensitivity analysis report for these thresholds.

**Why this priority**: This addresses the "distinct regimes of reasoning" part of the research question. It moves beyond simple correlation to identify actionable breakpoints for dynamic resource allocation.

**Independent Test**: The system can be tested by running the change-point detection on the P1 output and verifying that either a threshold value is identified OR a linear model is preferred (AIC/BIC difference > 2), and a sensitivity analysis (sweeping the threshold) is performed.

**Acceptance Scenarios**:

1. **Given** the correlation data from User Story 1, **When** the change-point detection algorithm runs, **Then** at least one threshold value (e.g., nesting depth = 4) is identified where the slope of the relationship changes significantly, OR the system reports that a linear model is preferred.
2. **Given** an identified threshold, **When** the sensitivity analysis runs, **Then** the system reports how the inconsistency rate or false-positive rate varies across a swept range of thresholds (e.g., ±0.05, ±0.1 around the identified point).
3. **Given** the sensitivity results, **When** the report is generated, **Then** it includes a justification for the chosen threshold based on community standards or the observed data distribution.

---

### User Story 3 - Statistical Significance and Power Validation (Priority: P3)

**Journey**: The researcher performs a permutation test to determine if the observed correlations and detected thresholds are significantly different from random chance, and documents the power limitations of the study given the dataset size and compute constraints.

**Why this priority**: This ensures the methodological soundness of the findings. Without statistical validation, the observed patterns could be artifacts of the specific dataset or random noise.

**Independent Test**: The system can be tested by running the permutation test (shuffling labels) and verifying that a p-value is calculated and reported, along with a statement on statistical power.

**Acceptance Scenarios**:

1. **Given** the observed correlation coefficient, **When** the permutation test runs (e.g., 1,000 permutations), **Then** a p-value is calculated indicating the probability of observing such a correlation by chance.
2. **Given** the sample size ([deferred] repos) and compute constraints, **When** the power analysis runs, **Then** the system reports whether the study is adequately powered to detect the observed effect size or notes the limitation.
3. **Given** multiple hypothesis tests (e.g., testing both cyclomatic complexity and nesting depth), **When** the correction runs, **Then** a multiple-comparison correction (e.g., Bonferroni or FDR) is applied and the adjusted p-values are reported.

---

### Edge Cases

- **What happens when** the static analysis tool fails to parse a specific file format or contains syntax errors? The system MUST skip the file, log the error, and continue processing the remaining files without crashing.
- **How does system handle** a dataset where the complexity metrics are constant (e.g., all files have nesting depth ≤ 2)? The system MUST detect the lack of variance and report that no correlation can be computed, suggesting a different dataset or metric.
- **What happens when** the LLM inference fails for a specific chunk (e.g., timeout or OOM)? The system MUST retry up to 3 times with exponential backoff, then skip the chunk and log the failure, ensuring the analysis continues on the remaining data.
- **How does system handle** language-specific biases? The system MUST stratify the analysis by programming language (Python, Java, etc.) to ensure the correlation is not driven by a single language's syntax.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a subset of [deferred] public repositories from the `codeparrot/github-code` dataset on HuggingFace, ensuring the total dataset size fits within the 14 GB disk limit. (See US-1)
- **FR-002**: System MUST run static analysis tools (CodeQL and tree-sitter) on the downloaded repositories to generate per-chunk labels for "cyclomatic complexity," "nesting depth," and "repetition ratio." (See US-1)
- **FR-003**: System MUST process the labeled chunks through a frozen, open-weight LLM (e.g., Llama-3-8B or Mistral-7B) available via HuggingFace, recording per-token loss and prediction entropy for each chunk without GPU acceleration, completing inference within 60 seconds per chunk and total pipeline execution within 6 hours. (See US-1)
- **FR-004**: System MUST compute Pearson and Spearman correlation coefficients between the static complexity metrics and the measured prediction difficulty across the entire dataset. (See US-1)
- **FR-005**: System MUST apply piecewise regression or change-point detection algorithms to identify specific structural thresholds where the relationship between complexity and loss shifts from linear to non-linear, controlling for token frequency and n-gram probability. (See US-2)
- **FR-006**: System MUST perform a sensitivity analysis for any identified threshold by sweeping the complexity metric value over a small concrete set (e.g., absolute diff in metric value ∈ {0.01, 0.05, 0.1}) and reporting how the headline rates vary. (See US-2)
- **FR-007**: System MUST perform a cluster-robust permutation test (e.g., a sufficient number of block permutations at the repository level) to determine if the observed correlations and detected thresholds are significantly different from random chance. (See US-3)
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) when reporting results from >1 hypothesis test to control family-wise error. (See US-3)
- **FR-009**: System MUST validate the correlation and thresholds by testing on a held-out set of code from a different repository structure (e.g., switching from Python to Java) to ensure the relationship is structural. (See US-1)
- **FR-010**: System MUST normalize per-token loss by the n-gram probability of the token sequence to isolate structural uncertainty from token frequency bias. (See US-1)
- **FR-011**: System MUST validate the complexity-loss proxy by computing the correlation between the computed metrics and a human-labeled complexity benchmark (e.g., CodeXGLUE) on a representative sample. (See US-3)

### Key Entities

- **CodeChunk**: A segment of source code with associated static analysis labels (cyclomatic complexity, nesting depth, repetition ratio) and LLM inference metrics (per-token loss, entropy).
- **Threshold**: A specific value of a complexity metric (e.g., nesting depth = 4) where the relationship between complexity and prediction loss changes non-linearly.
- **CorrelationResult**: The statistical output (coefficient, p-value) describing the relationship between a specific complexity metric and prediction difficulty.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between static complexity metrics and prediction loss is measured against the null hypothesis of zero correlation using a permutation test. (See US-1)
- **SC-002**: The identified structural threshold is measured by the maximum shift in the identified threshold value when the dataset is perturbed by [deferred] (must be ≤ 0.05 units). (See US-2)
- **SC-003**: The statistical significance of the findings is measured against the family-wise error rate (FWER) after applying multiple-comparison correction. (See US-3)
- **SC-004**: The cross-language consistency of the correlation is measured by comparing the correlation coefficients between the training set (Python) and the held-out validation set (Java). (See US-1)
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 h per job) to ensure the entire analysis completes without GPU acceleration. (See Assumptions)

## Assumptions

- The `codeparrot/github-code` dataset contains sufficient Python and Java code to reach the [deferred] repository target within the 14 GB disk limit.
- The Llama-8B or Mistral-7B model can be loaded and run in inference mode on a CPU-only environment within the 6-hour time limit for the sampled dataset, with a maximum of 60 seconds per chunk.
- Static analysis tools (CodeQL, tree-sitter) can successfully parse the majority of the downloaded code samples without requiring language-specific configuration beyond defaults.
- The relationship between code complexity and prediction loss is not confounded by external factors such as code comments or documentation density, which are assumed to be negligible or uniformly distributed.
- The "frozen" LLM used for inference does not require fine-tuning or parameter updates, ensuring the computational cost is limited to forward passes only.
- The dataset contains a sufficient variety of complexity levels (from boilerplate to highly nested logic) to detect non-linear thresholds; if the dataset is homogenous, the analysis will report a null result.
- The GitHub Actions free-tier runner provides stable network connectivity for downloading the dataset and the LLM model weights.
- The static analysis metrics (cyclomatic complexity, nesting depth) are well-defined and consistent across the different programming languages in the dataset.
- The "prediction difficulty" (loss/entropy) is a valid proxy for "reasoning depth" as assumed in the research question, validated by a correlation with a human-labeled benchmark.
- The permutation test and multiple-comparison correction methods are appropriate for the hierarchical nature of code data when using block permutation at the repository level.
- Token frequency and n-gram probability are significant confounders that must be controlled for to isolate structural complexity effects.