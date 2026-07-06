# Feature Specification: Quantifying the Impact of Codebase Age on LLM Code Understanding

**Feature Branch**: `001-quantify-age-impact`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Codebase Age on LLM Code Understanding"

## User Scenarios & Testing

### User Story 1 - Core Data Extraction and Age Calculation (Priority: P1)

The system MUST extract up to 200 function-level code snippets from each of at least 3 distinct open-source Python repositories (up to 5) and calculate the "median commit age" for each snippet based on the file's git history.

**Why this priority**: This is the foundational data layer. Without accurate age metadata and consistent snippet extraction, no analysis can occur. It represents the "input" phase of the research pipeline.

**Independent Test**: Can be fully tested by running the extraction script against a known set of 3 to 5 repositories and verifying the output CSV contains exactly `200 × N` rows (where N is the number of successfully processed repositories), with non-null `median_commit_age` and `snippet_content` columns.

**Acceptance Scenarios**:

1. **Given** a list of 3 to 5 valid GitHub repository URLs, **When** the extraction script runs, **Then** it outputs a CSV with `200 × N` rows, where each row has a calculated `median_commit_age` in days and the corresponding code snippet.
2. **Given** a repository with no git history (or inaccessible history), **When** the script attempts extraction, **Then** it logs a specific error for that repository, skips it, and proceeds to the next one, ensuring at least 3 repositories are processed to meet the minimum data floor.
3. **Given** a repository with mixed file types, **When** the parser extracts snippets, **Then** it strictly filters for Python `.py` files and ignores all other extensions.

---

### User Story 2 - CPU-Only Inference and Metric Generation (Priority: P2)

The system MUST run a quantized small-scale CodeLLM (e.g., CodeGen-350M or TinyLlama) on a CPU-only environment to generate perplexity scores and functional correctness rates for each extracted snippet.

**Why this priority**: This is the core "experiment" phase. It must execute within the 6-hour free-CPU budget and without GPU dependencies. It generates the dependent variables (perplexity, correctness) needed for correlation.

**Independent Test**: Can be fully tested by running the inference script on a subset of 10 snippets and verifying the output file contains `perplexity` (float > 1.0 or NaN) and `functional_correctness_rate` (float in [0.0, 1.0] or NaN) columns, with execution time recorded per snippet.

**Acceptance Scenarios**:

1. **Given** a CSV of up to 1,000 code snippets (5 repos × 200), **When** the inference script runs on a standard GitHub Actions ubuntu-latest runner (2-core, 7GB RAM), **Then** it completes the full batch in ≤ 6 hours and outputs a results CSV with `perplexity` and `functional_correctness_rate` for every row.
2. **Given** a snippet that causes a model timeout or memory overflow, **When** the script encounters it, **Then** it logs the failure, records `NaN` for metrics, and proceeds to the next snippet without terminating the job.
3. **Given** the requirement for CPU-only execution, **When** the script initializes the model, **Then** it explicitly disables CUDA/GPU device maps and allows 8-bit/4-bit quantization (via `bitsandbytes` or `llama.cpp`) to fit the model in RAM and meet the time budget.

---

### User Story 3 - Statistical Correlation and Reporting (Priority: P3)

The system MUST perform a Spearman rank correlation analysis between the calculated `median_commit_age` and the generated `perplexity`/`functional_correctness_rate` metrics, producing a final report with correlation coefficients and p-values.

**Why this priority**: This delivers the final research insight (the answer to the research question). It synthesizes the data from US-1 and US-2 into a scientific conclusion.

**Independent Test**: Can be fully tested by feeding the script a pre-calculated results CSV and verifying the generated JSON/Markdown report contains `spearman_correlation_age_perplexity` and `spearman_correlation_age_correctness` with valid numeric values.

**Acceptance Scenarios**:

1. **Given** a results CSV with `median_commit_age`, `perplexity`, and `functional_correctness_rate`, **When** the analysis script runs, **Then** it outputs a report stating the Spearman correlation coefficient (rho) and p-value for both metrics.
2. **Given** a dataset where the correlation is not statistically significant (p-value > 0.05), **When** the analysis runs, **Then** the report explicitly flags the result as "No significant correlation" rather than forcing a positive interpretation.
3. **Given** missing data points (NaNs) from the inference step, **When** the analysis runs, **Then** it automatically excludes rows with missing values from the correlation calculation without raising an error.

---

### Edge Cases

- What happens if a repository's git history is so sparse that `median_commit_age` cannot be calculated for a specific file? (Handled: If < 2 commits, assign the age of the single commit or 0; flag as 'low_confidence_age' but include in analysis if valid).
- How does the system handle code snippets that are too short (e.g., < 50 tokens) to meaningfully calculate perplexity or run tests? (Handled: Filter out snippets < 50 tokens before inference).
- What if the 6-hour CPU limit is exceeded due to a slow model version? (Handled: The script includes a hard timeout per snippet; if total time approaches 5.5 hours, it stops new inferences and finalizes the report with available data, marking the run as 'incomplete' if the 800-snippet minimum is not met).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract up to 200 function-level Python snippets from each of at least 3 distinct repositories (up to 5), calculating the `median_commit_age` for each snippet based on the file's git history. The total target is [deferred] snippets, with a minimum viable dataset of sufficient size to support robust analysis. (See US-1)
- **FR-002**: System MUST execute a small-scale CodeLLM (e.g., CodeGen-350M) on a CPU-only environment, allowing 8-bit/4-bit quantization to fit memory constraints, without requiring CUDA or GPU accelerators. (See US-2)
- **FR-003**: System MUST calculate `perplexity` and `functional_correctness_rate` for every processed snippet. For `functional_correctness_rate`, the system MUST attempt to execute the snippet against its associated unit tests; if tests are missing, it MUST generate a synthetic semantic validation (syntax + type check) to assign a binary valid/invalid score. (See US-2)
- **FR-004**: System MUST perform a Spearman rank correlation analysis between `median_commit_age` and both `perplexity` and `functional_correctness_rate` metrics. (See US-3)
- **FR-005**: System MUST generate a final report containing the correlation coefficients (rho) and p-values, explicitly stating whether a significant correlation exists. (See US-3)
- **FR-006**: System MUST handle inference failures (timeouts/memory errors) by logging the error, recording `NaN` for metrics, and continuing to the next snippet without crashing the batch. (See US-2)
- **FR-007**: System MUST enforce a total execution time cap of 6 hours on a 2-core CPU runner. If the time limit is reached before the minimum 800 snippets are processed, the system MUST stop new inferences, finalize the report with available data, and mark the run as 'incomplete'. The time limit takes precedence over the minimum snippet count. (See US-2)

### Key Entities

- **Repository**: A source code project identified by a GitHub URL, characterized by its `median_commit_age`.
- **Snippet**: A code extract from a repository, approximately 200 tokens in length, linked to a specific `median_commit_age`. (Note: '200' in FR-001 refers to the count of snippets per repo; '200 tokens' refers to the approximate length).
- **InferenceResult**: A record containing the `snippet_id`, `perplexity` score, and `functional_correctness_rate` derived from model execution.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman correlation coefficient (rho) between `median_commit_age` and `perplexity` is measured against the null hypothesis (rho = 0) to determine statistical significance. (See FR-004, US-3)
- **SC-002**: The Spearman correlation coefficient (rho) between `median_commit_age` and `functional_correctness_rate` is measured against the null hypothesis (rho = 0) to determine statistical significance. (See FR-004, US-3)
- **SC-003**: The total inference execution time is measured against the 6-hour limit on a 2-core CPU runner to verify feasibility. (See FR-007, US-2)
- **SC-004**: The data completeness rate is measured against a target of ≥ 95% valid data points. A 'valid data point' is defined as a snippet from the set that passed the pre-inference length filter (≥ 50 tokens) that has non-NaN metrics. This target is a community standard for data quality in empirical software engineering to ensure robust correlation analysis. (See FR-006, US-2)

## Assumptions

- **Assumption about data source**: Public GitHub repositories selected for this study contain accessible git history and valid Python code that can be parsed by a static analyzer.
- **Assumption about model capability**: The selected small-scale CodeLLM (e.g., CodeGen-350M) is sufficiently capable of generating perplexity scores and semantic validation on standard Python code without requiring fine-tuning.
- **Assumption about compute environment**: The GitHub Actions free-tier runner provides stable 2-core CPU performance and sufficient RAM (~7 GB) to load the small model and process the dataset sequentially.
- **Assumption about temporal validity**: The "median commit age" of a file is a valid proxy for the "age" of the code logic within that file, assuming the file has not undergone a complete rewrite that resets its semantic age.
- **Assumption about correlation framing**: Any observed correlation between code age and model performance is interpreted as an *associational* relationship, not a causal one, as this is an observational study without random assignment of code ages.
- **Assumption about metric validity**: The `functional_correctness_rate` (based on unit tests or synthetic validation) is a more valid measure of 'understanding' than `token_match_accuracy` (exact string reconstruction), which may be confounded by training data overlap.
- **Assumption about threshold justification**: The threshold for "statistical significance" is set at p < 0.05, consistent with standard community practices in empirical software engineering research.