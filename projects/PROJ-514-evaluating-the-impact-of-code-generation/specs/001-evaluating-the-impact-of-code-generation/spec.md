# Feature Specification: Evaluating Code Generation Impact on Code Smell Frequency

**Feature Branch**: `001-code-smell-comparison`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Smell Frequency"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Collection & Sample Preparation (Priority: P1)

The researcher MUST be able to collect a balanced dataset of human-written and LLM-generated code samples from equivalent contexts to enable comparison.

**Why this priority**: This is the foundational step; without valid, comparable samples, no analysis can occur. It directly addresses the research question's need for "equivalent software contexts."

**Independent Test**: Can be fully tested by verifying the existence of a structured directory containing exactly 50 human commit samples and 50 LLM generation samples, with metadata logging the source repository and task ID.

**Acceptance Scenarios**:

1. **Given** a list of 50 public GitHub repositories, **When** the system executes the collection script, **Then** it retrieves ≥ 20 recent commits per repository for human-written samples.
2. **Given** 50 standard programming tasks, **When** the system queries the LLM API, **Then** it generates 50 distinct code samples within 60 seconds per request.
3. **Given** the collected samples, **When** the system validates the dataset, **Then** it confirms ≥ 95% of samples are syntactically valid Python or Java files.

---

### User Story 2 - Static Analysis Execution (Priority: P2)

The researcher MUST be able to run static analysis tools on all code samples to extract code smell metrics without exceeding CI resource limits.

**Why this priority**: This transforms raw code into measurable data (smell frequencies). It is critical for the methodology but secondary to data collection.

**Independent Test**: Can be fully tested by running the analysis pipeline on a subset of 10 samples and verifying the output JSON contains smell counts for all four target categories (Long Method, Duplicated Code, Feature Envy, Long Parameter List).

**Acceptance Scenarios**:

1. **Given** a valid code sample file, **When** the static analysis tool runs, **Then** it completes within 5 minutes per file on a CPU-only runner.
2. **Given** the full dataset (1000+ functions), **When** the analysis runs in parallel, **Then** total execution time does not exceed 4 hours.
3. **Given** memory constraints, **When** the tool processes a file, **Then** it does not consume more than 2 GB of RAM per process.

---

### User Story 3 - Statistical Comparison & Reporting (Priority: P3)

The researcher MUST be able to generate a final report that compares smell frequencies between sources using appropriate statistical methods and visualizations.

**Why this priority**: This delivers the research outcome (the answer to the question). It relies on US-1 and US-2 being complete.

**Independent Test**: Can be fully tested by generating the final PDF/Markdown report and verifying it contains the required statistical tables, effect sizes, and visualizations without causal language.

**Acceptance Scenarios**:

1. **Given** the smell frequency metrics, **When** the statistical module runs, **Then** it performs Mann-Whitney U tests (or t-tests if normality holds) for each smell category.
2. **Given** multiple hypothesis tests (4 smell types), **When** the p-values are calculated, **Then** they are adjusted using Bonferroni correction to control family-wise error rate ≤ 0.05.
3. **Given** the final results, **When** the report is rendered, **Then** it includes box plots comparing distributions and explicitly states findings as "associational" rather than causal.

---

### Edge Cases

- What happens when a GitHub repository is archived or deleted during collection? (System skips and logs failure; requires ≥ 95% success rate).
- How does system handle LLM API rate limits or timeouts? (System implements exponential backoff with max 3 retries per task).
- What happens if static analysis fails on a specific file (e.g., syntax error in LLM output)? (System logs the error and excludes the file from analysis, tracking exclusion rate).
- How does system handle non-normal distribution of smell counts? (System defaults to Mann-Whitney U test rather than t-test).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect ≥ 50 human-written code samples from GitHub repositories with ≥ 100 stars and ≥ 5 years of history, using shallow clones (depth 20) to ensure dataset-variable fit for the analysis. (See US-1)
- **FR-002**: System MUST generate ≥ 50 LLM code samples using a public API (e.g., HuggingFace Inference API) for equivalent programming tasks, ensuring no local GPU dependencies. (See US-1)
- **FR-003**: System MUST execute static analysis using PMD or SonarQube CLI on CPU-only runners, enforcing a hard memory limit of 2 GB per process to fit the compute box. (See US-2)
- **FR-004**: System MUST apply multiple-comparison correction (e.g., Bonferroni) to all statistical tests to maintain family-wise error rate ≤ 0.05 across the 4 smell categories. (See US-3)
- **FR-005**: System MUST enforce a sensitivity analysis on the "Long Method" threshold, sweeping values ∈ {100, 150, 200} lines to verify result stability against cutoff justification. (See US-3)
- **FR-006**: System MUST format all output findings using associational language (e.g., "associated with", "correlated with") rather than causal claims, reflecting the observational study design. (See US-3)

### Key Entities

- **CodeSample**: Represents a single unit of code (human or LLM), attributes: `source_type`, `repository_id`, `task_id`, `language`, `file_path`.
- **SmellMetric**: Represents the output of static analysis, attributes: `sample_id`, `smell_type` (Long Method, Duplicated, etc.), `count`, `threshold_used`.
- **StatResult**: Represents the comparison outcome, attributes: `smell_type`, `p_value`, `effect_size`, `confidence_interval`, `correction_method`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the target of 100 total samples (50 human + 50 LLM), requiring ≥ 95% availability. (See US-1)
- **SC-002**: Analysis success rate is measured against the total number of submitted files, requiring ≥ 90% successful metric extraction without crashes. (See US-2)
- **SC-003**: Statistical validity is measured against the requirement for corrected p-values and effect sizes (Cohen's d), ensuring no uncorrected multiple testing. (See US-3)
- **SC-004**: Compute feasibility is measured against the CI runner limits, requiring total job duration ≤ 6 hours and peak RAM ≤ 7 GB. (See US-2)
- **SC-005**: Threshold robustness is measured against the sensitivity sweep results, requiring the primary finding (significant vs. non-significant) to remain stable across threshold ∈ {100, 150, 200}. (See US-3)

## Assumptions

- [Assumption about data source]: Public GitHub repositories selected will remain accessible during the collection window (≥ 95% uptime).
- [Assumption about LLM API]: The external LLM API (e.g., HuggingFace) will remain available and within free-tier limits for 50 inference requests.
- [Assumption about static analysis]: Standard PMD/SonarQube defaults for code smell detection (e.g., 100 lines for Long Method) are accepted as community-standard baselines without further tuning.
- [Assumption about inference framing]: The study design is observational; therefore, all results are interpreted as associations between generation source and smell frequency, not causal effects of the LLM.
- [Assumption about compute]: The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) is sufficient for the specified sample size (1000 functions) using CPU-tractable static analysis tools.
