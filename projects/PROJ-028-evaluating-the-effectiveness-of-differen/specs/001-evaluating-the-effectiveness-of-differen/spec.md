# Feature Specification: Evaluating Prompting Strategies for Code Generation

**Feature Branch**: `001-evaluate-prompting-strategies`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of Different Prompting Strategies for Code Generation on resource-constrained models"

## User Scenarios & Testing

### User Story 1 - Zero-Shot Baseline Execution (Priority: P1)

The system must execute the MBPP test suite using the zero-shot prompting strategy against the `Salesforce/codegen-350M-mono` model across **3 independent random seeds** to establish a reproducible performance baseline. This is the foundational step; without a valid baseline, comparative analysis is impossible.

**Why this priority**: P1. This represents the control condition. If the system cannot successfully generate and execute code in the simplest prompting mode across multiple seeds, no further comparisons can be made. It validates the entire pipeline (data loading, model inference, code execution sandbox, and metric calculation).

**Independent Test**: The system can be tested by running the pipeline with `--strategy zero-shot` and `--seeds 3` on a fixed subset of up to 500 MBPP tasks. Success is defined by the generation of multiple valid JSON reports containing pass@k and pass@ scores for each task, with no runtime errors exceeding a reasonable timeout threshold per execution.

**Acceptance Scenarios**:

1. **Given** the MBPP dataset is loaded and the model is initialized on CPU, **When** the system processes a task with a zero-shot prompt for seed 1, **Then** the system generates code, executes it against unit tests within 10 seconds, and records a pass/fail result.
2. **Given** a task where the generated code raises a runtime error, **When** the execution wrapper catches the exception, **Then** the task is marked as failed, and the error log is stored without crashing the batch process.
3. **Given** the model inference exceeds memory limits, **When** the system detects RAM usage approaching 6.5 GB, **Then** the system automatically switches to 16-bit precision (if supported) or triggers garbage collection, ensuring the process continues without a silent crash.

---

### User Story 2 - Few-Shot and Chain-of-Thought Comparison (Priority: P2)

The system must execute the same MBPP test suite using Few-Shot (3 examples) and Chain-of-Thought (CoT) prompting strategies, **generating k=10 independent samples per task** for each strategy, to generate comparative performance data.

**Why this priority**: P2. This enables the core research question: determining if advanced prompting strategies outperform the baseline. It depends on the stability of the baseline (US-1) but introduces the variable manipulation required for the study.

**Independent Test**: The system can be tested by running the pipeline with `--strategy few-shot` and `--strategy cot` on the same up to 500-task subset. Success is defined by the generation of comparable JSON reports where `pass@1` and `pass@10` scores are calculated (based on k=10 samples) for each strategy, allowing for a direct statistical comparison.

**Acceptance Scenarios**:

1. **Given** the Few-Shot prompt template with 3 examples is selected, **When** the system processes a task, **Then** the prompt includes the examples and the target question, and the system generates **10 distinct code samples**, each evaluated against the unit tests.
2. **Given** the Chain-of-Thought prompt template is selected, **When** the system processes a task, **Then** the prompt explicitly requests a step-by-step reasoning process before the code block, and the system generates **10 distinct code samples**, extracting and evaluating the final code block from each.
3. **Given** the system runs both strategies on the same tasks, **When** the batch completes, **Then** the output includes a consolidated report mapping each task ID to its pass/fail status across all three strategies (Zero-shot, Few-shot, CoT) for all 3 seeds.

---

### User Story 3 - Statistical Analysis and Resource Reporting (Priority: P3)

The system must perform statistical analysis (**McNemar's test**) on the collected pass rates and generate a report detailing resource utilization (RAM, CPU time) to ensure compliance with CI constraints. If resource limits are exceeded, the system must log the violation and **continue execution** to preserve statistical power.

**Why this priority**: P3. This synthesizes the data into the final research output. It confirms the validity of the findings (statistical significance) and verifies the feasibility of the method on free-tier hardware.

**Independent Test**: The system can be tested by running the full analysis script on the generated JSON results. Success is defined by the production of a summary report containing the p-value for the difference between strategies (via McNemar's test), the mean pass rates, peak memory usage logs, and a flag indicating if resource limits were exceeded.

**Acceptance Scenarios**:

1. **Given** the pass/fail results for all three strategies across 3 seeds, **When** the statistical analysis module runs, **Then** it calculates the mean pass@1 and pass@10 for each strategy and performs **McNemar's test** on the paired binary outcomes, outputting the p-value.
2. **Given** the execution logs, **When** the resource monitor aggregates data, **Then** it reports the peak RAM usage (in GB) and total runtime (in seconds) for the entire batch.
3. **Given** the total runtime exceeds 6 hours or RAM exceeds 7 GB, **When** the system finalizes the report, **Then** it flags the result as "Resource Constraint Warning" in the final report but **continues processing** to completion to ensure valid statistical power.

---

### Edge Cases

- **Timeout Handling**: What happens when the generated code enters an infinite loop? The system must strictly enforce a bounded timeout per task execution using `resource.setrlimit`. If exceeded, the task is marked as failed, and the process continues to the next task.
- **Model Output Parsing**: How does the system handle model outputs that do not contain a code block or contain multiple code blocks? The parser must use a deterministic regex strategy to extract the *first* valid Python code block. If extraction fails, the task is marked as failed.
- **Dataset Variability**: What happens if the MBPP dataset contains tasks with missing unit tests? The system must skip such tasks and log a warning, excluding them from the statistical sample size calculation.
- **Memory Pressure**: How does the system handle scenarios where the 350M model + tokenizer + data loading exceeds 6.5 GB RAM? The system must implement a batch size of 1, monitor memory, and if usage > 6.5 GB, automatically attempt to switch to 16-bit precision or trigger forced garbage collection.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the MBPP dataset from HuggingFace `google-research-datasets/mbpp`, filter to the test split, and select **up to 500 tasks** deterministically (or all available if <500). The system MUST run the evaluation across **3 independent random seeds** to ensure reproducibility (See US-1).
- **FR-002**: System MUST load the `Salesforce/codegen-350M-mono` model in **32-bit floating point (FP32)** on CPU by default, ensuring no CUDA/GPU dependencies are invoked. If memory usage exceeds 6.5 GB, the system MUST automatically switch to **16-bit floating point (FP16)** if supported by the inference library (See US-1).
- **FR-003**: System MUST generate prompts for three distinct strategies: Zero-shot, Few-shot (3 examples), and Chain-of-Thought. For Few-shot and CoT strategies, the system MUST generate **k=10 independent samples** per task to enable `pass@10` calculation (See US-2).
- **FR-004**: System MUST execute generated code in an isolated environment (subprocess) with a strict **10-second timeout** and **500MB memory limit** per execution, enforced via Python's `resource` module and `cgroups` where available, to prevent hangs (See US-1).
- **FR-005**: System MUST calculate `pass@1` and `pass@10` metrics for each task and aggregate them by strategy and seed, storing results in a structured JSON format (See US-2).
- **FR-006**: System MUST perform **McNemar's test** to compare the mean pass rates between the Zero-shot baseline and the CoT strategy, outputting the p-value for the paired binary outcomes (See US-3).
- **FR-007**: System MUST log peak RAM usage and total wall-clock time for the entire inference and evaluation pipeline. If limits are exceeded, the system MUST log a "Resource Constraint Warning" but **continue execution** (See US-3).

### Key Entities

- **Task**: Represents a single code generation problem from MBPP, containing the problem description, entry code, and unit tests.
- **Prompt**: The text string constructed by combining the strategy template with the Task data.
- **Generation**: The output text produced by the model given a Prompt.
- **ExecutionResult**: A record containing the pass/fail status, execution time, and any error output for a specific Generation against a Task.
- **StrategyReport**: An aggregate entity containing mean pass rates, standard deviations, and statistical test results for a specific prompting strategy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in mean `pass@1` between Chain-of-Thought and Zero-shot strategies is measured against the null hypothesis (no difference) using **McNemar's test** with alpha=0.05 (See US-3).
- **SC-002**: The peak RAM usage of the inference pipeline is measured against the 7 GB constraint of the GitHub Actions free runner, with a flag indicating if the limit was exceeded (See US-3).
- **SC-003**: The total runtime of the full evaluation (up to 500 tasks, 3 strategies, 3 seeds) is measured against the 6-hour job limit of the CI environment, with a flag indicating if the limit was exceeded (See US-3).
- **SC-004**: The execution timeout rate (percentage of tasks failing due to >10s timeout) is **measured and reported** by the system (See US-1).
- **SC-005**: The parsing success rate (percentage of generations where valid code is extracted) is **measured and reported** by the system (See US-2).

## Assumptions

- **Assumption about dataset variables**: The MBPP dataset contains all necessary variables (problem description, test cases, and ground truth) to evaluate code generation performance without external data augmentation.
- **Assumption about model capability**: The `Salesforce/codegen-350M-mono` model is capable of generating syntactically valid Python code for the MBPP test suite, even if the semantic correctness varies.
- **Assumption about execution environment**: The GitHub Actions free-tier runner provides a Linux environment with `docker` or `subprocess` capabilities sufficient to isolate Python execution, and the 10-second timeout is enforceable via `resource.setrlimit`.
- **Assumption about statistical validity**: The sample size of **up to 500 tasks** across **3 random seeds** is sufficient to detect a meaningful difference in pass rates with p < 0.05, given the expected variance in code generation tasks.
- **Assumption about resource limits**: The 350M model (approx. **1.4GB weights** in FP32) plus the tokenizer and dataset will fit within 6 GB of RAM. If memory pressure is detected, the fallback to a reduced-precision format will ensure the experiment completes within the designated memory constraint.
- **Assumption about inference precision**: Running the model in default 32-bit precision on CPU will not cause numerical instability or overflow errors during inference. If memory constraints are encountered, 16-bit precision is assumed to be a valid scientific alternative.
- **Assumption about engineering targets**: The system aims for an execution timeout rate of **<5%** and a parsing success rate of **≥90%** as engineering goals, but the system's success is defined by its ability to measure these rates accurately, not by achieving them.