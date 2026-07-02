# Feature Specification: Leveraging LLMs for Automated Test Case Generation from Natural Language Requirements

**Feature Branch**: `001-llm-test-generation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Can large language models (LLMs) generate executable unit tests from natural language software requirements that achieve comparable code coverage to manually written tests?"

## User Scenarios & Testing

### User Story 1 - LLM Test Generation Pipeline (Priority: P1)

As a researcher, I want the system to ingest bug fix descriptions from the Defects4J dataset and generate corresponding JUnit test code snippets using a CPU-optimized LLM, so that I can evaluate the baseline capability of LLMs to translate bug reports into testable code without manual intervention.

**Why this priority**: This is the core functionality. Without the ability to generate syntactically valid tests from bug reports, no coverage comparison or statistical analysis can occur. It delivers the primary artifact for the research question.

**Independent Test**: The system can be tested by running the generation script on a fixed subset of requirements and verifying that the output directory contains valid Java files that compile without syntax errors.

**Acceptance Scenarios**:

1. **Given** a bug fix description from Defects4J, **When** the system prompts the LLM, **Then** the output is a syntactically valid JUnit test class in Java that compiles successfully.
2. **Given** a bug fix description that is ambiguous, **When** the system prompts the LLM, **Then** the output is a syntactically valid test class (even if logically incomplete) that does not crash the compiler.
3. **Given** the system is running on a CPU-only environment with ≤7GB RAM, **When** the generation process starts, **Then** the process completes without an OutOfMemoryError.

---

### User Story 2 - Coverage Measurement and Comparison (Priority: P2)

As a researcher, I want the system to execute the generated tests against the target source code and calculate code coverage percentages using JaCoCo, comparing these results against the baseline manual tests, so that I can quantify the efficacy of the LLM-generated tests.

**Why this priority**: This provides the metric (code coverage) required to answer the research question. It transforms the generated code into empirical data.

**Independent Test**: The system can be tested by running the execution pipeline on a pre-generated test set and verifying that a coverage report (XML/HTML) is produced and that a summary CSV file named `coverage_metrics.csv` containing coverage percentages for both generated and manual tests is generated.

**Acceptance Scenarios**:

1. **Given** a set of generated test files and the corresponding source code, **When** the execution runner compiles and runs the tests, **Then** the JaCoCo agent collects coverage data and generates a valid report.
2. **Given** a set of generated tests and the existing manual baseline tests, **When** the comparison module runs, **Then** a file named `coverage_metrics.csv` is produced containing columns for `project_id`, `test_type` (generated/manual), and `coverage_percentage`.
3. **Given** a generated test that fails to compile, **When** the execution runner attempts to run it, **Then** the test is marked as "failed to compile" with [deferred] coverage contribution, and the pipeline continues without crashing.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

As a researcher, I want the system to perform a statistical test on the coverage metrics between generated and manual tests (preferring a paired t-test, but falling back to Wilcoxon signed-rank if normality assumptions fail) and generate a final report summarizing the statistical significance, the percentage of manual coverage achieved, and the assertion density, so that I can draw conclusions about the LLM's performance.

**Why this priority**: This delivers the final scientific output required to answer the research question (statistical significance and relative performance).

**Independent Test**: The system can be tested by providing a `coverage_metrics.csv` file and verifying that the output includes a p-value, a mean difference, a test type (t-test or Wilcoxon), and a formatted conclusion statement.

**Acceptance Scenarios**:

1. **Given** a `coverage_metrics.csv` of paired coverage data (generated vs. manual), **When** the analysis script runs, **Then** a normality test (Shapiro-Wilk) is performed; if p ≥ 0.05, a paired t-test is executed; otherwise, a Wilcoxon signed-rank test is executed, and the result (p-value) is reported.
2. **Given** the results of the statistical test, **When** the report is generated, **Then** it explicitly reports the calculated ratio of generated-to-manual coverage and indicates whether this ratio falls within the hypothesis range of 40-60% (with [deferred] as the minimum acceptable threshold).
3. **Given** the dataset size is small (< 30 samples), **When** the analysis runs, **Then** the system logs a warning about statistical power limitations but proceeds with the selected test, and a post-hoc power analysis is included in the report.

---

### Edge Cases

- What happens when the LLM generates code that compiles but contains logical errors causing infinite loops during test execution? (System must enforce a timeout of 30 seconds per test execution).
- How does the system handle requirements that reference non-existent methods or classes in the target project? (System must capture the compilation error and record [deferred] coverage for that specific test).
- What happens if the Defects4J dataset extraction fails for a specific project version? (System must skip the project, log the error, and proceed to the next sample without halting the entire pipeline).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract bug fix descriptions from the Defects4J issue tracker data and format them as prompts for the LLM, acknowledging that these represent fix specifications rather than feature requirements. (See US-1)
- **FR-002**: System MUST load the quantized 2.7B parameter Phi-2 model using `llama.cpp` and ensure it operates within 7GB RAM constraints without requiring GPU acceleration. (See US-1)
- **FR-003**: System MUST compile and execute generated JUnit test code against the target source code within a bounded timeout of 30 seconds per test to prevent infinite loops. (See US-2)
- **FR-004**: System MUST calculate code coverage for generated tests and baseline manual tests using JaCoCo and output a structured CSV file named `coverage_metrics.csv`. (See US-2)
- **FR-005**: System MUST perform a statistical test on the coverage metrics (paired t-test if normality holds, otherwise Wilcoxon signed-rank) and generate a final report containing the p-value and the ratio of generated-to-manual coverage. (See US-3)
- **FR-006**: System MUST implement a retry mechanism for test execution failures with a configurable limit before marking the test as failed. (See US-2)
- **FR-007**: System MUST support a configurable sample limit and enforce a hard stop when the cumulative execution time exceeds a configured duration or the sample count reaches the configured limit. (See US-3)
- **FR-008**: System MUST perform a Shapiro-Wilk test on the differences in coverage percentages to verify normality before selecting the statistical test method. (See US-3)
- **FR-009**: System MUST calculate and report the 'assertion density' (number of assertions per line of code) for generated tests to validate test quality. (See US-2)
- **FR-010**: System MUST perform a post-hoc power analysis to report the achieved statistical power for the observed effect size. (See US-3)

### Key Entities

- **BugFixDescription**: A natural language description of a bug fix or feature extracted from Defects4J issue trackers, used as the input for test generation.
- **GeneratedTest**: A JUnit test class produced by the LLM based on a BugFixDescription.
- **CoverageMetric**: A numerical value representing the percentage of code lines executed by a specific set of tests, measured by JaCoCo.
- **AnalysisResult**: A statistical summary containing the mean coverage difference, p-value, confidence interval, test type used, and achieved power.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Code coverage of LLM-generated tests is measured against the code coverage of manually written baseline tests for the same project, as defined by the Defects4J dataset, and recorded in `coverage_metrics.csv`. (See US-2)
- **SC-002**: Statistical significance of the coverage difference is measured using a paired t-test (if normality holds) or Wilcoxon signed-rank test (if normality fails) with a conventional significance threshold, comparing the generated and manual coverage distributions. (See US-3)
- **SC-003**: The percentage of the manual baseline coverage achieved by LLM-generated tests is measured against a hypothesis range, with [deferred] defined as the minimum acceptable threshold. (See US-3)
- **SC-004**: System resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier constraints to ensure feasibility. (See US-1)
- **SC-005**: The rate of syntactically valid test generation is measured as the ratio of successfully compiled tests to total prompts sent, with the specific target threshold to be determined during the analysis phase. (See US-1)
- **SC-006**: The assertion density of generated tests is measured and reported to assess test quality beyond simple code coverage. (See US-2)

## Assumptions

- The Defects4J dataset contains bug fix descriptions that are sufficiently detailed to serve as inputs for test generation, though they represent fix specifications rather than feature requirements.
- The `llama.cpp` implementation of the Phi-2 model can be quantized to fit within 7GB RAM while maintaining acceptable inference speed on a 2-core CPU. (Constitution Mandate: Phi-2 is the required model).
- The JaCoCo coverage agent can successfully instrument the generated test classes and the target source code within the Maven/Gradle build environment of the GitHub Actions runner.
- The sample size is the intended experimental design limit, but the system supports configuration; a power analysis will be performed post-hoc to validate sufficiency.
- The GitHub Actions free-tier runner provides sufficient disk space to store the Defects4J dataset, the model weights, and the build artifacts for the configured sample size.
- The "bug fix descriptions" extracted from Defects4J are not heavily corrupted or missing, and the mapping between issues and specific bug fixes is reliable.