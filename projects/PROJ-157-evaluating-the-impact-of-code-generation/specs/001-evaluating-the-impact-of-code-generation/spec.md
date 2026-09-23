# Feature Specification: Evaluating the Impact of Code Generation Models on Code Security

**Feature Branch**: `001-evaluate-llm-code-security`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation Models on Code Security: A Fuzzing Study"

## User Scenarios & Testing

### User Story 1 - Dataset Acquisition and Preparation (Priority: P1)

The system MUST acquire a balanced dataset of programming challenges containing both human-written reference solutions and LLM-generated variants. This is the foundational step; without valid, paired data, no security analysis can occur.

**Why this priority**: The entire study relies on the existence of comparable code pairs (Human vs. LLM) for the same problem instances. If this fails, the experiment cannot proceed.

**Independent Test**: The system can be tested by verifying the successful retrieval of a specific number of problem IDs, the successful compilation of the human reference solution, and the generation of an LLM variant for that same problem, resulting in a stored pair ready for fuzzing.

**Acceptance Scenarios**:

1. **Given** a list of valid problem IDs from the HumanEval or Codeforces benchmark, **When** the system queries the HuggingFace API for LLM generation and retrieves the human reference, **Then** a paired dataset entry is created containing both source files and a unique problem ID.
2. **Given** a problem ID where the LLM generation fails or times out, **When** the system retries the generation up to 3 times, **Then** the system logs the failure and excludes that specific pair from the final dataset, ensuring no partial or null data enters the fuzzing pipeline.

---

### User Story 2 - Automated Fuzzing Execution (Priority: P2)

The system MUST compile both human and LLM code snippets and execute them against a standardized fuzzing harness (libFuzzer/AFL++) within a constrained compute environment. This delivers the raw security data (crashes, errors).

**Why this priority**: This is the core measurement mechanism. It transforms static code into dynamic security evidence. It must be robust against compilation errors and runtime crashes.

**Independent Test**: The system can be tested by processing a single known-vulnerable code snippet (synthetic) and a safe snippet, verifying that the fuzzer runs for the allocated time, detects the crash in the vulnerable one, and reports zero crashes for the safe one.

**Acceptance Scenarios**:

1. **Given** a paired dataset entry (Human source, LLM source), **When** the system compiles both with `-O0 -g` flags and runs the fuzzer for [deferred], **Then** the system outputs a log file containing the number of crashes, unique stack traces, and execution time for each binary.
2. **Given** a code snippet that fails to compile, **When** the compilation step is executed, **Then** the system skips the fuzzing step for that snippet, records a "compilation_failed" status, and proceeds to the next pair without halting the batch.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST aggregate the fuzzing results, perform non-parametric statistical tests (Mann-Whitney U, Kolmogorov-Smirnov), and generate a visual report comparing the security posture of LLM vs. Human code.

**Why this priority**: This converts raw logs into the research answer. It validates the hypothesis and provides the final deliverable.

**Independent Test**: The system can be tested by feeding it a pre-computed CSV of crash counts (simulated) and verifying that the output report contains the correct statistical p-value, effect size (Cliff's Δ), and the required visualizations.

**Acceptance Scenarios**:

1. **Given** a CSV of crash counts and severity scores for both groups, **When** the analysis script runs, **Then** it outputs a Markdown report containing the Mann-Whitney U test result (p-value), Cliff's Δ effect size, and a box-plot image comparing the distributions.
2. **Given** a dataset where the sample size is insufficient for statistical significance (p > 0.05), **When** the analysis runs, **Then** the report explicitly states "No statistically significant difference found" and includes the calculated p-value and effect size to support the null hypothesis.

### Edge Cases

- **What happens when the LLM generates non-compilable code?** The pipeline must detect compilation errors, skip fuzzing for that specific instance, and log the error type (e.g., syntax error, missing header) without crashing the entire batch.
- **How does the system handle a fuzzer hang or infinite loop?** The system must enforce a hard timeout (30 minutes) per binary. If the fuzzer exceeds this, the process is killed, and the result is recorded as "timeout" rather than "no crash."
- **What if the statistical test assumptions are violated?** The system must default to non-parametric tests (Mann-Whitney U) which do not assume normal distribution, ensuring validity even with skewed crash data.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve human reference solutions and generate LLM variants for at least 50 distinct programming challenge problems to ensure statistical power (See US-1).
- **FR-002**: System MUST compile all code snippets using `gcc`/`clang` with flags `-O0 -g` inside a Docker container to ensure deterministic binary generation (See US-2).
- **FR-003**: System MUST execute the fuzzing harness (libFuzzer or AFL++) on each binary for a fixed duration, enforced by a hard timeout. (See US-2).
- **FR-004**: System MUST parse crash logs to extract unique stack traces and map them to vulnerability categories (e.g., buffer overflow, use-after-free) (See US-2).
- **FR-005**: System MUST perform a Mann-Whitney U test and a Kolmogorov-Smirnov test on the crash count distributions between the LLM and Human groups, calculating Cliff's Δ effect size (See US-3).
- **FR-006**: System MUST generate a final Markdown report containing box-plots of crash counts and a summary of statistical findings (p-values, effect sizes) (See US-3).
- **FR-007**: System MUST explicitly frame all statistical findings as associational comparisons, avoiding causal language unless randomization is proven (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) if testing more than one hypothesis metric (crash count AND severity) (See US-3).

### Key Entities

- **ProblemPair**: Represents a single challenge instance containing the `problem_id`, `human_source_code`, `llm_source_code`, and `generation_timestamp`.
- **FuzzResult**: Represents the outcome of a fuzzing run, containing `binary_id`, `crash_count`, `unique_stack_traces`, `severity_scores`, and `execution_status` (success/timeout/compile_fail).
- **StatisticalSummary**: Aggregated metrics including `p_value`, `effect_size`, `test_method`, and `conclusion_text`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in median crash counts between LLM and Human groups is measured against the null hypothesis of no difference using the Mann-Whitney U test (See FR-005).
- **SC-002**: The distribution shape difference in severity scores is measured against the assumption of identical distributions using the Kolmogorov-Smirnov test (See FR-005).
- **SC-003**: The magnitude of the security difference is measured against the effect size threshold of |Cliff's Δ| > 0.14 (small effect) to determine practical significance (See FR-005).
- **SC-004**: The family-wise error rate is measured against the corrected alpha level (α_corrected) to ensure statistical validity when testing multiple metrics (See FR-008).
- **SC-005**: The reproducibility of the pipeline is measured against the requirement that [deferred] of compilable code pairs produce a valid FuzzResult log (See FR-003).

## Assumptions

- **Dataset Availability**: It is assumed that the HumanEval or Codeforces datasets contain a sufficient number of problems (≥50) with executable C/C++ reference solutions that can be compiled with standard flags.
- **API Stability**: It is assumed that the HuggingFace inference APIs for CodeLlama-7B and StarCoder-15B will remain available and responsive during the data generation phase without rate-limiting that halts the experiment.
- **Compute Constraints**: The analysis assumes that the GitHub Actions free-tier runner (multiple CPU cores, ~7 GB RAM) is sufficient to compile and fuzz the code snippets within the 30-minute timeout per binary., provided the code complexity is bounded by the benchmark problems.
- **Fuzzing Efficacy**: It is assumed that a 30-minute fuzzing window is sufficient to expose the majority of memory safety vulnerabilities in the short, algorithmic code snippets typical of programming challenges.
- **Variable Fit**: The dataset contains the necessary variables (code source, problem ID) to perform the comparison; no external variables (e.g., developer experience) are required as the comparison is strictly binary (LLM vs. Human).
- **Inference Framing**: The study assumes an observational design; therefore, any observed differences are framed as associations between "code generation source" and "vulnerability count," not as causal proof that LLMs "cause" insecurity without further controlled experimentation.
