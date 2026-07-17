# Feature Specification: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

**Feature Branch**: `001-llmxive-multilingual-logic-transfer`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages'"

## User Scenarios & Testing

### User Story 1 - Core Logic Anchor Inference (Priority: P1)

The researcher needs to execute the primary experiment: extracting the initial algorithmic steps from the ground-truth Python solution to form a "Partial Logic Trace," injecting this trace as a few-shot anchor into a prompt for a target language (e.g., Rust) where the model previously failed, and re-generating the full solution to test if the partial logic scaffolding enables correct completion.

**Why this priority**: This is the core hypothesis test. It distinguishes between "can the model translate syntax" (trivial) and "can the model complete logic from a partial scaffold" (non-trivial). The Partial Logic Trace prevents the tautology of providing the full answer.

**Independent Test**: The system can be tested by running the inference pipeline on a single, known-failed task from the Multi-LCB dataset, verifying that the model outputs a syntactically valid code snippet in the target language when provided the Partial Logic Trace, and that the output passes the test suite only if it correctly infers the remaining steps.

**Acceptance Scenarios**:

1. **Given** a task from Multi-LCB where the model failed in Rust but succeeded in Python, **When** the system constructs a prompt with the problem statement and the Partial Logic Trace (first 3 steps of the Python solution), **Then** the model generates a Rust code snippet that attempts to complete the logic.
2. **Given** a task where the model failed in Kotlin, **When** the system provides the Partial Logic Trace, **Then** the system outputs the generated Kotlin code without raising a timeout or memory error on the CPU-only runner.
3. **Given** a valid Partial Logic Trace, **When** the prompt instructs "complete the logic based on these steps," **Then** the output retains the algorithmic structure implied by the trace while adapting syntax to the target language.

---

### User Story 2 - Automated Execution & Pass@1 Verification (Priority: P2)

The researcher needs to automatically execute the generated code snippets in a sandboxed environment to determine if the logic anchor actually improved the correctness (Pass@1) compared to the blind baseline.

**Why this priority**: Generating code is insufficient; the study relies on objective correctness metrics. This step transforms raw generations into the quantitative data required for statistical analysis.

**Independent Test**: The system can be tested by feeding a known correct Rust solution into the execution harness and verifying that the test suite passes, and conversely, that a syntactically broken solution fails the harness.

**Acceptance Scenarios**:

1. **Given** a generated code snippet in Rust, **When** the execution harness runs the Multi-LCB test suite, **Then** the system returns a binary "Pass" or "Fail" status based on test case outcomes.
2. **Given** a generated snippet that causes a runtime panic or compilation error, **When** the harness executes it, **Then** the system records the failure type (e.g., "Runtime Error," "Compile Error") without crashing the runner.
3. **Given** a batch of 200 tasks, **When** the verification step completes, **Then** the system produces a structured log mapping each task ID to its Pass/Fail status in both "blind" and "guided" conditions.

---

### User Story 3 - Statistical Significance & Error Categorization (Priority: P3)

The researcher needs to compare the Pass@1 rates between the blind and guided conditions using a paired statistical test (McNemar's or bootstrap) and categorize the remaining failures to understand the nature of the transfer error.

**Why this priority**: This delivers the final scientific conclusion. It determines if the observed improvement is statistically significant and provides qualitative insights into *why* the transfer might still fail (e.g., library misuse vs. logic drift).

**Independent Test**: The system can be tested by feeding it a pre-computed dataset of paired Pass/Fail results and verifying that the statistical test returns a p-value and that error categories are assigned based on the failure logs and explicit anchor-step verification.

**Acceptance Scenarios**:

1. **Given** paired Pass/Fail data for 200 tasks, **When** the analysis module runs a paired McNemar's test, **Then** the system outputs a p-value indicating statistical significance (p < 0.05) or non-significance.
2. **Given** a set of failed generations, **When** the error analysis module processes them, **Then** each failure is classified into "Syntax Error," "Library Misuse," "Runtime Error," or "Logic Transfer Failure" based on defined log patterns and explicit verification of anchor steps.
3. **Given** the full analysis results, **When** the report is generated, **Then** it includes a summary table comparing Pass@1 rates and the distribution of error types in the "guided" condition.

### Edge Cases

- **What happens when** the model generates code that compiles but hangs indefinitely (infinite loop) during execution? The system MUST enforce a strict timeout (e.g., a bounded duration per test case) to prevent runner exhaustion.
- **How does the system handle** a target language (e.g., a niche Rust crate) not present in the standard Multi-LCB sandbox environment? The system MUST log this as a "Environment Missing Dependency" error rather than a logic failure.
- **What happens when** the Partial Logic Trace extraction fails (e.g., the Python solution is too short)? The system MUST skip that task and log an "Anchor Extraction Failed" error, ensuring the dataset size is adjusted dynamically.

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct few-shot prompts that include the problem statement, the model's previous failed output (for context), and the **Partial Logic Trace** (first 3 algorithmic steps extracted from the ground-truth Python solution) as the logic anchor for every task in the evaluation set (See US-1).
- **FR-001.1**: System MUST extract the Partial Logic Trace by parsing the ground-truth Python solution into an AST, identifying the first several distinct algorithmic operations (e.g., initialization, loop entry, recursive call), and serializing them into **pseudo-code or Python syntax** (NOT the target language) to serve as the anchor (See US-1).
- **FR-002**: System MUST execute generated code snippets in a CPU-isolated sandbox using the Multi-LCB execution harness to verify correctness against test cases (See US-2).
- **FR-003**: System MUST enforce a hard timeout of 10 seconds per test case execution to prevent infinite loops from exhausting the free-tier CPU resources (See US-2).
- **FR-004**: System MUST categorize every failed generation into one of four types based on the following deterministic rules (See US-3):
    1. **Syntax Error**: Compilation fails (log contains "error:" or "failed to compile").
    2. **Library Misuse**: Runtime import error or missing module (log contains "ModuleNotFoundError", "ImportError", or "linker error").
    3. **Runtime Error**: Execution crashes or hangs (log contains "RuntimeError", "Panic", "Timeout", or "Segmentation fault").
    4. **Logic Transfer Failure**: Execution **Passes** all test cases BUT the generated code fails to implement at least one of the 3 specific algorithmic steps listed in the **Partial Logic Trace** anchor (verified via keyword/control-flow matching) (See US-3).
- **FR-005**: System MUST perform a paired statistical test (McNemar's or bootstrap) comparing the Pass@1 rates of the "blind" (re-measured) vs. "guided" conditions to determine statistical significance (See US-3).
- **FR-006**: System MUST limit the dataset to a diverse set of algorithmic tasks selected via the following protocol (See US-1):
    1. **Initial Pool**: Select tasks where the model previously failed in the target language (blind Pass@1 < 1.0) AND succeeded in Python.
    2. **Stochasticity Filter**: Re-run the "blind" condition multiple times for each candidate task. Include the task only if it fails in **≥ 2 of the 3** blind runs.
    3. **Attrition Handling**: If the filtered set is < 200, sample replacements from the next available pool of tasks (excluding those already rejected) until a sufficient target number of tasks is reached, maintaining the stratified sampling constraint (no single Topic > 30% of the set).
    4. **Stratification**: Ensure the final set is stratified by Difficulty (Easy/Medium/Hard), Topic (e.g., DP, Graphs, Math), and Language Pair (See US-1).
- **FR-006.1**: System MUST re-run the "blind" condition on a representative set of selected tasks to establish an empirical baseline Pass@1, accounting for model stochasticity (See US-3).

### Key Entities

- **EvaluationTask**: Represents a single algorithmic problem containing the problem statement, ground-truth solutions in multiple languages, and the model's previous failed output.
- **PartialLogicTrace**: Represents the first 3 algorithmic steps extracted from the ground-truth Python solution, serialized as pseudo-code or Python for use as a prompt anchor.
- **GenerationResult**: Represents the output of the LLM for a specific task and condition (blind/guided), including the code string, execution status (Pass/Fail), error type, and anchor-step verification status.
- **StatisticalReport**: Aggregates the Pass@1 metrics, p-values from the paired test, and the distribution of error categories.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Recovery Rate (Pass@k in "guided" condition) is measured against the re-measured "blind" Pass@k for the same 200 tasks. The metric is defined as: `Pass@1_guided - Pass@1_blind` (See US-2).
- **SC-002**: Statistical significance (p-value) is measured against the standard alpha threshold using a paired McNemar's test (See US-3).
- **SC-003**: Error distribution (Syntax vs. Runtime vs. Logic Transfer Failure vs. Library) is measured against the total count of failures in the "guided" condition to identify the dominant failure mode (See US-3).
- **SC-004**: Total Execution Time is measured against a hard constraint of ≤ 6 hours on a **GitHub Actions free-tier runner (multi-core, 7GB RAM)**. The system passes if the total time to process all 200 tasks is ≤ 6 hours under these specific hardware constraints (See US-1).
- **SC-005**: Sandbox Stability Rate (percentage of tasks where the runner did not crash or hang) is measured against a threshold of ≥ 99% (See US-2).

## Assumptions

- **Assumption about data**: The Multi-LCB dataset contains ground-truth Python solutions for all selected tasks that are verified to be correct and executable.
- **Assumption about compute**: The selected models (e.g., LlamaB, CodeLlamaB) can be quantized (e.g., low-bit or standard precision via `bitsandbytes` is NOT used; instead, standard CPU quantization or smaller context windows) to run within a memory footprint compatible with the GitHub Actions free tier (2-core, 7GB RAM) without GPU acceleration.
- **Assumption about methodology**: The study treats the presence of the Partial Logic Trace as an observational intervention; findings will be framed as associational improvements in code generation, not causal proof of "reasoning transfer," unless the design explicitly includes randomization (which is not present here).
- **Assumption about variables**: The Multi-LCB dataset provides sufficient test cases to perform a statistically powered paired test (n=200) after applying the 3-run stochasticity filter, without requiring external data collection.
- **Assumption about thresholds**: The timeout per test case is sufficient to detect infinite loops while allowing complex algorithmic solutions to execute.; this threshold is based on standard competitive programming time limits.
- **Assumption about error categorization**: The execution harness logs (stderr/exit codes) are sufficiently granular to distinguish between "Syntax Errors" (compilation failures), "Library Misuse" (runtime import errors), and "Runtime Errors". "Logic Transfer Failure" is detected by verifying the presence of specific algorithmic steps from the anchor in the generated code.