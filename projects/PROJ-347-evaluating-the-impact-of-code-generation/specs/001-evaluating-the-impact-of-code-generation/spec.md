# Feature Specification: Evaluating the Impact of Code Generation on Software Security: A Static Analysis Study

**Feature Branch**: `001-eval-llm-code-security`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Software Security: A Static Analysis Study"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preparation (Priority: P1)

The system MUST ingest human-written vulnerable code samples from a public dataset (e.g., Devign or CodeXGLUE) and generate functionally equivalent code samples using a public LLM API based on standardized prompts.

**Why this priority**: This is the foundational step; without a paired dataset of human vs. LLM code for identical functionality, no comparative analysis can occur. It delivers the primary research asset.

**Independent Test**: The system can be tested by verifying that for every human code sample in the input batch, a corresponding LLM-generated sample exists in the output directory, both pass syntax validation, and functional equivalence is confirmed via unit test execution or semantic similarity scoring.

**Acceptance Scenarios**:

1. **Given** a list of 50 human-written vulnerable code snippets, **When** the ingestion pipeline runs, **Then** exactly 50 LLM-generated vulnerable snippets are produced in the output directory, each corresponding to a human snippet by functionality.
2. **Given** a generated code snippet that fails syntax validation, **When** the pipeline processes it, **Then** the snippet is flagged as "invalid" and excluded from the subsequent static analysis phase, with a count logged.
3. **Given** the LLM API returns an error or timeout for a specific prompt, **When** the pipeline retries (up to 3 times), **Then** the system logs the failure and moves to the next prompt without halting the entire batch.
4. **Given** a pair of human and LLM code samples, **When** functional equivalence is verified, **Then** the system confirms they pass a shared unit test suite with ≥ 90% code coverage OR achieve a semantic similarity score ≥ 0.85 (using a standard embedding model); samples failing this check are excluded from the analysis set.

---

### User Story 2 - Static Analysis Execution (Priority: P2)

The system MUST execute multiple open-source static analysis tools (Semgrep, SonarQube community edition) against both the human-written and LLM-generated code sets within the GitHub Actions free-tier constraints.

**Why this priority**: This step applies the measurement instrument. It must be robust enough to handle different code styles and tool outputs without crashing the CI environment, delivering the raw vulnerability data.

**Independent Test**: The system can be tested by running the analysis toolchain against a small, known test set of 10 code samples and verifying that the output JSON files contain structured vulnerability findings (type, severity, line number, rule-id) for each tool, and that memory constraints are respected.

**Acceptance Scenarios**:

1. **Given** a batch of 100 code samples (50 human, 50 LLM), **When** the static analysis runner executes, **Then** the process completes within 30 minutes on a standard GHA runner (well within the 6-hour hard job limit), and output JSON files are generated for each tool.
2. **Given** a code sample that triggers a known false positive in a specific tool, **When** the analysis runs, **Then** the finding is recorded in the output with a "rule-id" and a "confidence" score (extracted from Semgrep's JSON `confidence` field or mapped from SonarQube severity) to allow for later filtering.
3. **Given** the memory usage of a static analysis tool exceeds 6 GB (the safety buffer threshold) during execution, **When** the tool runs, **Then** the system terminates the specific tool process, logs an "OOM" error for that sample, and proceeds with the remaining samples to prevent total job failure (which would exceed the storage capacity limit).

---

### User Story 3 - Statistical Comparison and Reporting (Priority: P3)

The system MUST aggregate the vulnerability findings, calculate rates (injection, auth bypass, etc.), and perform statistical tests (McNemar's test or stratified Chi-square) to compare LLM vs. human code vulnerability distributions, accounting for the paired design.

**Why this priority**: This delivers the final research insight. It transforms raw data into the answer to the research question.

**Independent Test**: The system can be tested by feeding it a synthetic dataset with known differences (e.g., [deferred] vulnerability rate in LLM, [deferred] in human) and verifying that the statistical test returns a p-value < 0.05 using the correct paired test, and the visualization correctly reflects the disparity.

**Acceptance Scenarios**:

1. **Given** the aggregated vulnerability counts for both code sources, **When** the statistical module runs, **Then** a p-value is calculated for each vulnerability category using McNemar's test (or a stratified test by `functionality_id`), and a result is marked "statistically significant" if p < 0.05.
2. **Given** a vulnerability category with zero occurrences in one group (e.g., no auth bypass in human code), **When** the statistical test is performed, **Then** the system automatically switches from McNemar's to an exact paired test (e.g., exact McNemar's) to handle small cell counts.
3. **Given** the final analysis results, **When** the report generator runs, **Then** a Markdown report is produced containing a summary table of vulnerability rates, a bar chart image (SVG/PNG) visualizing the distribution comparison, and a subsection detailing the results of the manual audit/fuzzing validation on the sampled subset.

---

### Edge Cases

- What happens when the LLM API returns code that is syntactically valid but logically infinite loops or hangs during static analysis? (Handled by timeout constraints in User Story 2).
- How does the system handle a dataset where the "ground truth" vulnerability labels for human code are missing or ambiguous? (Handled by filtering logic in User Story 1; only labeled samples are processed).
- What if the static analysis tool detects a vulnerability in LLM code that is a false positive due to the code's novel structure? (Handled by the "confidence" field in User Story 2; sensitivity analysis in FR-004 addresses this; manual audit validates true positives).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest human-written vulnerable code samples and generate corresponding LLM-generated vulnerable code samples for identical functionality, verifying functional equivalence via unit test execution (≥ 90% coverage) or semantic similarity ≥ 0.85 (See US-1).
- **FR-002**: System MUST execute static analysis tools (Semgrep, SonarQube) on both code sets within a 6-hour hard job limit, terminating any process exceeding 6 GB memory (safety buffer) to prevent hitting the 7 GB hard limit (See US-2).
- **FR-003**: System MUST aggregate vulnerability findings by type (e.g., Injection, Auth) and source (Human vs. LLM) into a structured dataset, including `rule-id` and `confidence` fields extracted or mapped from tool outputs (See US-3).
- **FR-004**: System MUST perform statistical comparison using a paired test (McNemar's) or stratified analysis by `functionality_id` on vulnerability rates, explicitly framing results as associational due to the observational nature of the study; additionally, the system MUST select a random subset (≥ 10%) of flagged samples for manual audit or fuzzing to validate true vulnerability status (See US-3).
- **FR-005**: System MUST generate a final report containing vulnerability rate tables, visualizations of the distribution differences, and the results of the validation audit/fuzzing (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis for any vulnerability detection thresholds (e.g., confidence scores), sweeping a small set of cutoff values (e.g., 0.0, 0.5, 0.9) to report variation in false-positive rates (See US-2, US-3).
- **FR-007**: System MUST handle cases where the dataset lacks specific vulnerability labels by excluding those samples from the ground-truth comparison (See US-1).

### Key Entities

- **CodeSample**: Represents a single unit of code (human or LLM) with attributes: `source` (human/llm), `functionality_id`, `syntax_valid` (bool), `raw_content`, `functional_equivalence_verified` (bool).
- **VulnerabilityFinding**: Represents a detected issue with attributes: `code_sample_id`, `tool_source`, `vulnerability_type`, `severity`, `line_number`, `confidence_score`, `rule_id`, `validated_by_audit` (bool, optional).
- **AnalysisResult**: Represents the aggregated outcome with attributes: `vulnerability_type`, `human_count`, `llm_count`, `total_samples`, `p_value`, `is_significant`, `test_method` (e.g., "McNemar's").

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of valid, analyzable code samples generated by the LLM MUST be ≥ 85% of the total number of prompts sent (See FR-001, US-1).
- **SC-002**: The discrepancy in vulnerability detection rates between LLM and human code is measured against the statistical significance threshold (p < 0.05) using McNemar's test or a stratified test (See FR-004, US-3).
- **SC-003**: The stability of vulnerability classification rates is measured against a sensitivity sweep of detection confidence thresholds (e.g., 0.0 to 0.9) to ensure findings are not artifacts of a single cutoff (See FR-006, US-2).
- **SC-004**: The computational feasibility is measured against the 7 GB hard RAM limit and 6-hour job limit on a standard GitHub Actions runner (See FR-002, US-2).
- **SC-005**: The completeness of the vulnerability profile is measured against the requirement that at least 5 distinct vulnerability types from the OWASP Top 10 set present in the ground-truth dataset must be detected by the static analysis tools (See FR-003, US-3).

## Assumptions

- The public datasets (Devign/CodeXGLUE) contain sufficient samples with known vulnerability labels to achieve a sample size that allows for meaningful statistical comparison (power calculation deferred to implementation, but assumption is that N > 100 per group is feasible).
- The LLM API used for generation provides deterministic or sufficiently stable outputs for standardized prompts to allow for reproducible code generation.
- The static analysis tools (Semgrep, SonarQube) function correctly on CPU-only environments without requiring GPU acceleration or specialized hardware.
- The "ground truth" for human-written code in the selected dataset is accurate enough to serve as a baseline for comparison, acknowledging that static analysis tools may have false positives/negatives in both groups, and that the manual audit/fuzzing subset will provide an independent validation layer.
- The research design is observational; therefore, any observed differences in vulnerability patterns are interpreted as associations between code source and vulnerability type, not causal effects, unless randomization is explicitly introduced in future iterations.
- The LLM API does not filter out prompts related to security vulnerabilities (e.g., "write a vulnerable SQL query") to the extent that it prevents the generation of the necessary test cases; if it does, the assumption is that the prompts will be framed as "educational examples of security flaws."