# Feature Specification: Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code

**Feature Branch**: `001-llm-analysis-tradeoffs`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion & Validation (Priority: P1)

The System MUST be able to download and verify the integrity of the target code datasets (HumanEval, CodeXGLUE, BigCode) locally before analysis begins.

**Why this priority**: Without validated data, no analysis can occur; this is the foundational step for the entire research workflow.

**Independent Test**: Can be fully tested by executing the download script and verifying file checksums without running any analysis tools.

**Acceptance Scenarios**:

1. **Given** the download script is invoked, **When** it accesses the public repositories, **Then** it MUST retrieve a minimum viable sample size of ≥ 500 code snippets distributed across Python, JavaScript, and Java.
2. **Given** the datasets are downloaded, **When** the integrity check runs, **Then** it MUST confirm all files match expected checksums.
3. **Given** a dataset file is corrupted, **When** the validation script runs, **Then** it MUST halt and report the specific file error.

---

### User Story 2 - Analysis Pipeline Execution (Priority: P1)

The System MUST execute both static and dynamic analysis tools on the downloaded code snippets within resource constraints.

**Why this priority**: This generates the core data (defect detections) required to answer the research question.

**Independent Test**: Can be fully tested by running the analysis container on a sample of 10 snippets and verifying output logs exist.

**Acceptance Scenarios**:

1. **Given** valid code snippets are present, **When** the static analysis tools (CodeQL, SonarQube) run, **Then** they MUST produce detection logs within 15 minutes. If CodeQL or SonarQube fail, the System MUST attempt a fallback static analyzer (e.g., ESLint, PyLint) or log a 'tool_failure'.
2. **Given** valid code snippets are present, **When** the dynamic analysis tool (test runner, e.g., pytest) executes the unit test oracle, **Then** it MUST produce execution results within 30 minutes. If no unit test exists for a snippet, the System MUST mark the snippet as 'untestable_dynamic' and exclude it from functional correctness metrics. (Note: The unit tests serve as the oracle for functional correctness, not the analysis tool itself).
3. **Given** the analysis runs, **When** resource limits are reached (CPU > 2 cores, RAM > 7 GB), **Then** the process MUST terminate with a resource error code.

---

### User Story 3 - Results Aggregation & Statistical Reporting (Priority: P2)

The System MUST be able to view aggregated metrics and statistical significance tests comparing the two analysis methods.

**Why this priority**: This transforms raw logs into interpretable research findings.

**Independent Test**: Can be fully tested by processing a mock log file and verifying the statistical report contains p-values and F1-scores.

**Acceptance Scenarios**:

1. **Given** analysis logs exist, **When** the aggregation script runs, **Then** it MUST calculate precision, recall, and F1-score for both methods.
2. **Given** aggregated metrics exist, **When** the statistical test runs, **Then** it MUST apply McNemar's test and report a p-value.
3. **Given** the statistical test completes, **When** the sensitivity analysis runs, **Then** it MUST report detection rates for α ∈ {0.01, 0.05, 0.1}.

---

### Edge Cases

- What happens when a code snippet times out during dynamic execution? (System MUST mark as 'timeout' and exclude from runtime metrics).
- How does system handle static tool crashes? (System MUST retry up to 3 times, then log 'tool_failure' and attempt fallback if configured).
- What happens if a dataset download fails? (System MUST abort and alert Researcher within 5 minutes).
- What happens if a snippet lacks unit tests? (System MUST mark as 'untestable_dynamic' and exclude from functional correctness metrics).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a minimum viable sample size of ≥ 500 code snippets from HumanEval, CodeXGLUE, and BigCode repositories, distributed across Python, JavaScript, and Java (See US-1)
- **FR-002**: System MUST execute CodeQL and SonarQube static analysis on all snippets; if these fail, the System MUST attempt a fallback static analyzer that produces a log in the standard schema, or log 'tool_failure' (See US-2)
- **FR-003**: System MUST execute dynamic unit tests from HumanEval benchmarks on all snippets to determine functional correctness pass/fail status; if no unit test exists, the System MUST mark the snippet as 'untestable_dynamic' and exclude it from functional correctness metrics (See US-2)
- **FR-004**: System MUST compute precision, recall, and F1-score for both analysis methods (See US-3)
- **FR-005**: System MUST apply McNemar's test with α=0.05 on the intersection of code snippets where both static and dynamic analysis produced a valid result; if the intersection is biased by language (e.g., only Python), the System MUST stratify the test by language and report results for each subset with n ≥ 30 (See US-3)
- **FR-006**: System MUST enforce CPU ≤ 2 cores, RAM ≤ 7 GB, and duration ≤ 6 hours (See US-2)
- **FR-007**: System MUST sweep α over the set {0.01, 0.05, 0.1} and report detection rate variation (See US-3)
- **FR-008**: System MUST apply a multiplicity adjustment (e.g., Bonferroni correction or FDR control) when testing multiple metrics to control Type I error (See US-3)

### Key Entities *(include if feature involves data)*

- **Code Snippet**: The unit of analysis containing source code and associated test cases.
- **Detection Log**: The output record containing vulnerability/error flags from analysis tools.
- **Statistical Report**: The aggregated output containing metrics and p-values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Analysis pipeline completes within 6 hours of start time (See US-2)
- **SC-002**: Statistical report is generated containing p-values for McNemar's test and sensitivity analysis results (See US-3)
- **SC-003**: Dataset covers ≥ 3 programming languages (Python, JavaScript, Java) (See US-1)
- **SC-004**: Sensitivity analysis report includes rates for α ∈ {0.01, 0.05, 0.1} (See US-3)

## Assumptions

- GitHub Actions free-tier runner is available with a standard multi-core CPU configuration and a moderate amount of RAM.
- CodeQL CLI is pre-installed or installable within 15 minutes on the runner.
- HumanEval and CodeXGLUE datasets are accessible without authentication.
- Ground truth for functional correctness exists in HumanEval test suites.
- **Ground truth for security vulnerabilities is NOT available in the selected datasets; dynamic analysis is limited to functional correctness.**
- Static analysis is the primary method for security vulnerability detection; dynamic analysis is limited to functional correctness.
- Findings are framed as associational due to the observational nature of the dataset.
- Static and dynamic analysis tools are treated as independent measurement modalities.
- Dataset variable fit is confirmed (HumanEval contains code + tests).
- Multiplicity is addressed via McNemar's test for paired comparisons and FR-008 for multiple metrics.
- Threshold α=0.05 is justified by community-standard statistical significance.
- Sensitivity analysis sweep (α ∈ {0.01, 0.05, 0.1}) is computationally trivial.
- A minimum viable sample size is assumed to ensure statistical power.
- **The study compares Static Security Detection vs. Dynamic Functional Correctness as distinct metrics; functional correctness is NOT a proxy for security vulnerability.**
- Snippets without unit tests are excluded from functional correctness metrics and do not invalidate the analysis.