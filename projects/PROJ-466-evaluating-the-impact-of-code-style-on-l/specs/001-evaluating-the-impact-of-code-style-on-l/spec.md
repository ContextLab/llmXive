# Feature Specification: Evaluating the Impact of Code Style on LLM Code Generation Diversity

**Feature Branch**: `001-eval-code-style-diversity`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "How do explicit stylistic constraints in prompts modulate the structural diversity of solutions in the latent search space of generative language models for code?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Execute Generation & Filtering Pipeline (Priority: P1)

A researcher needs to generate code samples for a specific subset of HumanEval tasks under a single style constraint (e.g., Strict PEP8) and filter out samples that fail functional unit tests to ensure only valid solutions are analyzed.

**Why this priority**: This is the foundational data acquisition step. Without generating valid code samples, no diversity metrics or statistical comparisons can be computed. It isolates the core "generate-and-filter" loop.

**Independent Test**: Run the pipeline for 10 HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

**Acceptance Scenarios**:

1. **Given** a configuration specifying 10 tasks and the "Strict PEP8" style, **When** the generation job runs, **Then** the system produces exactly 5 samples per task, executes the unit tests, and retains only the samples where the test suite passes.
2. **Given** a task where all 5 generated samples fail the unit tests, **When** the job completes, **Then** the system logs a warning for that task and excludes it from the output CSV, preventing downstream errors in metric calculation.

---

### User Story 2 – Compute Structural Diversity Metrics (Priority: P2)

A researcher wants to quantify the structural variance of the valid code samples generated under different style constraints using AST edit distance and n-gram entropy.

**Why this priority**: This transforms raw code into the quantitative variables required for the research hypothesis. It is independent of the statistical testing logic and focuses purely on measurement validity.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric (e.g., mean pairwise distance) for that task.

**Acceptance Scenarios**:

1. **Given** 5 valid Python code samples for a single task, **When** the metric computation module runs, **Then** the system calculates the pairwise AST edit distance for all 10 unique pairs and the average n-gram entropy, storing these values in a results table.
2. **Given** two samples that are syntactically identical but differ only in whitespace, **When** the AST distance is calculated, **Then** the system returns a distance of 0 (or near-zero if normalized), correctly reflecting structural equivalence.

---

### User Story 3 – Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

A researcher needs to determine if the differences in diversity scores between Neutral, Strict PEP8, and Minified styles are statistically significant and robust to threshold variations.

**Why this priority**: This addresses the core research question (causal/associational impact) and ensures methodological soundness by validating that results are not artifacts of arbitrary cutoffs.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the Kruskal-Wallis H-test is performed, followed by a sensitivity analysis sweeping a decision threshold, and that the final report includes p-values and sensitivity plots.

**Acceptance Scenarios**:

1. **Given** diversity score distributions for three style groups, **When** the statistical module executes, **Then** the system performs a Kruskal-Wallis H-test, reports a p-value, and if significant, runs a Dunn's post-hoc test with Bonferroni correction.
2. **Given** a decision threshold (e.g., "significant difference") defined in the config, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold across values {0.01, 0.05, 0.1} and reports how the count of "significant" tasks varies, ensuring the finding is not threshold-dependent.

---

### Edge Cases

- **Memory Overflow**: The system MUST detect memory pressure and reduce the batch size dynamically until the memory limit is respected.
- **Syntax Errors in Prompts**: The system MUST catch AST parsing errors, log the task ID and style, and skip the specific sample without crashing the pipeline.
- **Zero-Variance Groups**: The system MUST detect zero variance in a group and skip the statistical test for that group, logging a "Zero Variance" warning.
- **Timeout**: The system MUST enforce a per-task timeout of 5 minutes; if exceeded, the system MUST log a timeout error and skip the task.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the HumanEval benchmark (subset of ≤164 tasks) from HuggingFace `openai/human-eval` and cache it locally to ensure reproducibility. (See US-1)
- **FR-002**: System MUST support three distinct style profiles (Neutral, Strict PEP8, Aggressive Minification) defined by prompt templates, ensuring the style variable is the only changing input across groups. (See US-1)
- **FR-003**: System MUST generate exactly 5 code samples per task per style using temperature sampling (T=0.7) with a fixed random seed (seed=42) for reproducibility. (See US-1)
- **FR-004**: System MUST execute generated code against the official HumanEval unit tests and discard any samples that fail, ensuring diversity metrics are computed only on functionally valid solutions. (See US-1)
- **FR-005**: System MUST compute token-level n-gram entropy and pairwise AST edit distance for all valid samples within a style group, aggregating results to a task-level diversity score. (See US-2)
- **FR-006**: System MUST perform a Kruskal-Wallis H-test to compare diversity distributions across the three style groups, explicitly framing findings as **causal impact within the model's response distribution** due to the controlled manipulation of the prompt style. (See US-3)
- **FR-007**: System MUST implement a sensitivity analysis that sweeps the statistical significance threshold (α) across a range of conventional values and reports the variation in the count of significant findings to justify the chosen cutoff. (See US-3)
- **FR-008**: System MUST use the `Salesforce/codegenB-mono` model (or larger if memory permits) and MUST determine the maximum safe batch size at runtime by probing memory usage, starting with a target of 50 but reducing iteratively until the 7 GB limit is respected. If the pass rate for a style group is < 1%, the system MUST halt and log a "Model Incapability" warning. (See US-1, US-2, US-3)
- **FR-009**: System MUST output a structured CSV containing the task ID, style profile, sample ID, functional pass status, and computed diversity metrics (AST distance, n-gram entropy). (See US-2)
- **FR-010**: System MUST generate a summary report (PDF/HTML) containing the statistical test results (H-statistic, p-value), post-hoc comparisons, and sensitivity analysis plots. (See US-3)
- **FR-011**: System MUST report the functional pass rate for each style group in the final summary. (See US-1)
- **FR-012**: System MUST handle memory overflow by dynamically reducing the batch size by discrete steps until the RAM limit is respected, logging each reduction. (See Edge Cases)
- **FR-013**: System MUST catch AST parsing errors, log the task ID and style, and skip the specific sample without crashing the pipeline. (See Edge Cases)
- **FR-014**: System MUST detect zero variance in a group, skip the statistical test for that group, and log a "Zero Variance" warning. (See Edge Cases)
- **FR-015**: System MUST enforce a per-task timeout of 5 minutes; if exceeded, the system MUST log a timeout error and skip the task. (See Edge Cases)
- **FR-016**: System MUST report the functional pass rate per style group and flag the analysis as "Potentially Biased" if the pass rate difference between any two groups exceeds 10 percentage points. (See US-1, US-2)
- **FR-017**: System MUST compute the Pearson correlation coefficient between AST distance and n-gram entropy; if the correlation is > 0.9, the system MUST report that the metrics are collinear and suggest using only AST distance for the primary analysis. (See US-2)

### Key Entities

- **Task**: A single programming problem from the HumanEval benchmark, identified by a unique ID and associated unit tests.
- **Sample**: A single code snippet generated by the LLM for a specific task under a specific style constraint.
- **Style Profile**: A configuration defining the prompt instructions (Neutral, PEP8, Minified) applied to the model.
- **Diversity Metric**: A quantitative value (AST distance or n-gram entropy) representing the structural variance of samples within a group.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system MUST successfully execute the Kruskal-Wallis H-test and report the H-statistic and p-value for the comparison of diversity scores across the three style groups, regardless of the p-value magnitude. (Reference: Statistical output from FR-006, See US-3)
- **SC-002**: The system MUST record the range of the count of significant tasks across the threshold sweep and report this range in the final summary. (Reference: Sensitivity report from FR-007, See US-3)
- **SC-003**: The system MUST report the functional pass rate for each style group in the final summary. (Reference: Pass rate log from FR-011, See US-1)
- **SC-004**: The total runtime of the end-to-end pipeline (generation, filtering, metric computation, analysis) must be ≤ 6 hours on a standard GitHub Actions free-tier runner. (Reference: CI job duration log, See US-1, US-2, US-3)
- **SC-005**: The memory footprint of the pipeline must not exceed a predefined upper bound at any point, verified by monitoring logs during the execution of the largest batch. (Reference: Memory usage log, See FR-008)

## Assumptions

- The `Salesforce/codegen-2B-mono` model is sufficiently small to run in 16-bit precision on a CPU-only environment with ≤7 GB RAM without requiring GPU acceleration or quantization libraries that depend on CUDA, provided dynamic batch sizing is used.
- The HumanEval benchmark unit tests are sufficient proxies for "functional correctness" and do not require additional test generation or manual validation.
- The "Strict PEP8" and "Aggressive Minification" prompts can be constructed such that they do not introduce syntax errors in the generated code that are unrelated to the style constraint itself.
- The study is a **controlled experiment** where the prompt style is the manipulated independent variable; the analysis infers **causal impact within the model's response distribution**, not general human behavior.
- The fixed GitHub Actions timeout is a hard limit; if the full 164 tasks exceed this, the system will process a representative subset (e.g., 50 tasks) as defined in the configuration, and the results will be scaled accordingly.
- AST parsing libraries (e.g., `ast` in Python) are robust enough to handle the generated code samples without crashing on minor formatting anomalies, provided the code passes the unit tests.