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

1. **Given** a list of valid problem IDs from the Codeforces benchmark with C++ reference submissions, **When** the system queries the HuggingFace API for LLM generation (CodeLlama-7B and StarCoder-15B) and retrieves the human reference, **Then** a paired dataset entry is created containing the human source file, one LLM source file per model, and a unique problem ID.
2. **Given** a problem ID where the LLM generation fails or times out, **When** the system retries the generation up to 3 times, **Then** the system logs the failure and excludes that specific pair from the final dataset, ensuring no partial or null data enters the fuzzing pipeline.

---

### User Story 2 - Automated Fuzzing Execution (Priority: P2)

The system MUST compile both human and LLM code snippets with sanitizer instrumentation, generate a per-snippet fuzzing harness, and execute them against a standardized fuzzing harness (libFuzzer/AFL++) within a constrained compute environment. This delivers the raw security data (crashes, errors).

**Why this priority**: This is the core measurement mechanism. It transforms static code into dynamic security evidence. It must be robust against compilation errors and runtime crashes.

**Independent Test**: The system can be tested by processing a single known-vulnerable code snippet (synthetic) and a safe snippet, verifying that the fuzzer runs for the allocated time, detects the crash in the vulnerable one, and reports no crash detected within the 30-minute budget for the safe one.

**Acceptance Scenarios**:

1. **Given** a paired dataset entry (Human source, LLM source), **When** the system compiles both with `-O0 -g` plus ASan/UBSan instrumentation flags and runs the fuzzer for 30 minutes per binary, **Then** the system outputs a log file containing the number of crashes, unique stack traces, and execution time for each binary.
2. **Given** a code snippet that fails to compile, **When** the compilation step is executed, **Then** the system skips the fuzzing step for that snippet, records a "compile_fail" status, and proceeds to the next pair without halting the batch.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST aggregate the fuzzing results, perform paired non-parametric statistical tests (Wilcoxon signed-rank as primary; Mann-Whitney U and Kolmogorov-Smirnov as secondary sensitivity analyses), and generate a visual report comparing the security posture of LLM vs. Human code.

**Why this priority**: This converts raw logs into the research answer. It validates the hypothesis and provides the final deliverable.

**Independent Test**: The system can be tested by feeding it a pre-computed CSV of crash counts (simulated) and verifying that the output report contains the correct statistical p-value, effect size (Cliff's Δ), and the required visualizations.

**Acceptance Scenarios**:

1. **Given** a CSV of per-problem crash counts and severity scores for both groups, **When** the analysis script runs, **Then** it outputs a Markdown report containing the Wilcoxon signed-rank test result (p-value, one test per model on paired per-problem crash-count differences), Cliff's Δ effect size, and a box-plot image comparing the distributions.
2. **Given** a dataset where the sample size is insufficient for statistical significance (p > 0.05), **When** the analysis runs, **Then** the report explicitly states "No statistically significant difference found" and includes the calculated p-value and effect size to support the null hypothesis.

### Edge Cases

- **What happens when the LLM generates non-compilable code?** The pipeline must detect compilation errors, skip fuzzing for that specific instance, and log the error type (e.g., syntax error, missing header) without crashing the entire batch.
- **How does the system handle a fuzzer hang or infinite loop?** The system must enforce a hard timeout (30 minutes) per binary. If the fuzzer exceeds this, the process is killed, and the result is recorded as "timeout" rather than "no crash."
- **What if the statistical test assumptions are violated?** The system must default to non-parametric tests (Wilcoxon signed-rank, Mann-Whitney U) which do not assume normal distribution, ensuring validity even with skewed crash data.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve human reference solutions (Codeforces C++ submissions) and generate LLM variants from at least two distinct models (CodeLlama-7B and StarCoder-15B) for at least 50 distinct programming challenge problems per model to ensure statistical power (See US-1).
- **FR-002**: System MUST compile all code snippets using `gcc`/`clang` with flags `-O0 -g` inside a Docker container to ensure deterministic binary generation (See US-2).
- **FR-003**: System MUST execute the fuzzing harness (libFuzzer or AFL++) on each binary for a fixed duration of 30 minutes per binary, enforced by a hard timeout, within a total compute budget of ≤ 6 hours per batch run (See US-2).
- **FR-004**: System MUST parse crash logs to extract unique stack traces and map them to vulnerability categories (e.g., buffer overflow, use-after-free) (See US-2).
- **FR-005**: System MUST perform a Wilcoxon signed-rank test on the paired per-problem crash-count differences between the Human reference and each model's LLM variant (one test per model; the pairing unit is the problem, and each pair consists of the human reference solution and that model's generated variant for the same problem). Mann-Whitney U and Kolmogorov-Smirnov tests on the group distributions MUST also be reported as secondary unpaired sensitivity analyses, with Cliff's Δ effect size calculated for each comparison (See US-3).
- **FR-006**: System MUST generate a final Markdown report containing box-plots of crash counts and a summary of statistical findings (p-values, effect sizes) (See US-3).
- **FR-007**: System MUST explicitly frame all statistical findings as associational comparisons, avoiding causal language unless randomization is proven (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (Holm-Bonferroni) within each metric family when testing more than one hypothesis (crash count AND severity). The report MUST state that crash count and severity are mechanically coupled (severity is derived per crash via the triage rubric), so severity findings are conditional on crash findings and do not constitute independent evidence (See US-3).
- **FR-009**: System MUST compute a severity score for each unique security-relevant crash using a simplified CVSS-like rubric: an ordinal 1-4 scale (1=Low, 2=Medium, 3=High, 4=Critical) assigned from (a) the vulnerability category mapped from the stack trace (FR-004) and (b) an exploitability/impact judgment (e.g., write vs. read access, controllability of the faulting input). The full rubric table MUST be included in the analysis documentation and applied identically to both groups (See US-2, US-3).
- **FR-010**: System MUST generate a per-snippet coverage-instrumented fuzzing harness (an `LLVMFuzzerTestOneInput` wrapper invoking the snippet's exposed functions with fuzzer-supplied inputs) and compile all binaries with AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan) instrumentation, so that memory-safety violations are reliably detected as crashes (See US-2).
- **FR-011**: System MUST triage every detected crash and classify it as either security-relevant (a sanitizer-confirmed memory-safety violation: buffer overflow, use-after-free, invalid free, etc.) or input-assumption failure (e.g., assertion/abort on out-of-contract input). Only security-relevant crashes (per FR-009 severity scoring) MUST be counted in the primary crash-count outcome; both classes MUST be reported separately (See US-2, US-3).

### Key Entities

- **ProblemPair**: Represents a single challenge instance containing the `problem_id`, `human_source_code`, `llm_source_code` per model (i.e., one field per generating model: `llm_source_code[model_name]`), and `generation_timestamp`. The pairing unit for statistical tests is the problem; each (problem, model) pair compares the human reference against that model's variant.
- **FuzzResult**: Represents the outcome of a fuzzing run, containing `binary_id`, `crash_count` (security-relevant crashes only, per FR-011), `unique_stack_traces`, `severity_scores` (per-problem aggregate: the maximum rubric score among that problem's security-relevant crashes for the given source, per FR-009), and `execution_status` (success/timeout/compile_fail).
- **StatisticalSummary**: Aggregated metrics including `p_value`, `effect_size`, `test_method`, and `conclusion_text`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The paired per-problem difference in crash counts between each model's LLM variants and the Human references is measured against the null hypothesis of no difference using the Wilcoxon signed-rank test, one test per model (See FR-005).
- **SC-002**: The distribution shape difference in per-problem aggregate severity scores is measured against the assumption of identical distributions using the Kolmogorov-Smirnov test, reported as a secondary analysis with the coupling caveat of FR-008 (See FR-005, FR-008).
- **SC-003**: The magnitude of the security difference is measured against the effect size threshold of |Cliff's Δ| > 0.14 (small effect) to determine practical significance (See FR-005).
- **SC-004**: The family-wise error rate is measured against the corrected alpha level (α_corrected = 0.05 after Holm-Bonferroni) to ensure statistical validity when testing multiple metrics within a family (See FR-008).
- **SC-005**: The reproducibility of the pipeline is measured against the requirement that [deferred: observed rate] of compilable code pairs produce a valid FuzzResult log, with a target of ≥ 95% (See FR-003).
- **SC-006**: Dataset acquisition is measured against the FR-001 minimum of 50 valid paired problem entries per model, and the pair-integrity rate (complete pairs with no partial or null data, per the US-1 no-partial-data rule) is measured against a target of [deferred] of retained entries (See FR-001, US-1).

## Assumptions

- **Dataset Availability**: It is assumed that the Codeforces dataset contains a sufficient number of problems (≥ 50) with executable C++ reference solutions that can be compiled with standard flags. HumanEval is excluded because its reference solutions are Python and cannot be compiled by gcc/clang.
- **API Stability**: It is assumed that the HuggingFace inference APIs for CodeLlama-7B and StarCoder-15B will remain available and responsive during the data generation phase without rate-limiting that halts the experiment.
- **Compute Constraints**: The analysis assumes that the GitHub Actions free-tier runner (multiple CPU cores, ~7 GB RAM) is sufficient to compile and fuzz the code snippets within the 30-minute per-binary timeout and the ≤ 6-hour total batch budget, provided the code complexity is bounded by the benchmark problems.
- **Fuzzing Efficacy**: It is assumed that a 30-minute fuzzing window with ASan/UBSan instrumentation (FR-010) is sufficient to expose the majority of memory safety vulnerabilities in the short, algorithmic code snippets typical of programming challenges.
- **Construct Validity**: Crash count is a proxy for security posture, not a direct measure. To mitigate bias, only sanitizer-confirmed memory-safety violations are counted as the primary outcome (FR-011), and severity is scored via the fixed rubric of FR-009; residual construct-validity limitations MUST be acknowledged in the final report.
- **Variable Fit**: The dataset contains the necessary variables (code source, problem ID) to perform the comparison; no external variables (e.g., developer experience) are required as the comparison is strictly binary (LLM vs. Human, per model).
- **Inference Framing**: The study assumes an observational design; therefore, any observed differences are framed as associations between "code generation source" and "vulnerability count," not as causal proof that LLMs "cause" insecurity without further controlled experimentation.