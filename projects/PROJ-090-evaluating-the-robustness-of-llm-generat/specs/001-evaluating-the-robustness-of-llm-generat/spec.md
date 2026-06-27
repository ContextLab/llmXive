# Feature Specification: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Feature Branch**: `001-evaluating-robustness-llm-code`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Robustness of LLM-Generated Code to Input Perturbations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Perturbation Generation (Priority: P1)

The system MUST download the HumanEval dataset and programmatically generate perturbed prompt variants for each task to establish the experimental conditions.

**Why this priority**: This is the foundational step; without the dataset and perturbed inputs, no inference or evaluation can occur. It defines the scope of the study (HumanEval tasks) and the independent variables (perturbation types).

**Independent Test**: The pipeline can be tested by verifying the presence of the HumanEval JSON files and the existence of 3 generated variant prompts per task in the local storage, without running any model inference.

**Acceptance Scenarios**:

1. **Given** the HumanEval dataset is accessible via HuggingFace Datasets, **When** the ingestion script runs, **Then** all programming tasks are downloaded locally.
2. **Given** a base prompt for a task, **When** the perturbation module runs, **Then** a small number of variants (character swap, synonym replacement, word order shuffle) are generated per task. 

The research question is: Can large language models be effectively used to generate adversarial examples for evaluating the robustness of text classification models?
The method is: We will generate adversarial examples using three text transformation techniques: character swap, synonym replacement, and word order shuffle. These examples will then be used to test the performance of several state-of-the-art text classification models.
References: [DOI: 10.1609/aimag.v37i3.2753] (Goodfellow et al., 2014)..

---

### User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

The system MUST execute the StarCoder2 model on CPU hardware without CUDA dependencies and run the generated code in a sandboxed environment to capture pass/fail results.

**Why this priority**: This is the core experimental engine. It must respect the compute constraints (7 GB RAM, 6 hours) while producing the raw data (code correctness) needed for analysis.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status within a defined timeout, independent of statistical analysis.

**Acceptance Scenarios**:

1. **Given** a perturbed prompt, **When** the model inference runs, **Then** the code is generated without CUDA errors and within the 7 GB RAM limit.
2. **Given** generated code, **When** the sandbox executor runs, **Then** the test suite is executed with a 10-second timeout per test case, returning pass/fail status.

---

### User Story 3 - Statistical Analysis and Error Classification (Priority: P3)

The system MUST calculate pass@1 rates, apply McNemar's test for paired comparison, and classify errors to determine the impact of perturbations on robustness.

**Why this priority**: This delivers the scientific value of the project. It transforms raw execution logs into interpretable research findings regarding robustness and error types.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results into the analysis script and verifying the statistical output (p-values, error counts) matches expected calculations.

**Acceptance Scenarios**:

1. **Given** paired success/failure counts for original vs. perturbed prompts, **When** McNemar's test runs, **Then** a p-value is returned indicating statistical significance.
2. **Given** a failed execution, **When** the error classifier runs, **Then** the failure is tagged as syntax, logic, or hallucination.

---

### Edge Cases

- What happens when the sandbox execution times out? (System MUST record this as a failure).
- How does system handle model inference OOM errors? (System MUST log the error and skip the sample to continue the batch).
- What happens if HumanEval download fails? (System MUST retry up to 3 times before halting).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the HumanEval dataset (164 tasks) from HuggingFace Datasets (`openai_humaneval`). (See US-1)
- **FR-002**: System MUST generate exactly 3 perturbation variants per task (character swap, synonym replacement, word order shuffle). (See US-1)
- **FR-003**: System MUST perform model inference using a CPU-verified configuration (no CUDA dependencies, ≤3B parameters) to fit within 7 GB RAM. (See US-2)
- **FR-004**: System MUST execute generated code in a sandboxed environment with a 10-second timeout per test case. (See US-2)
- **FR-005**: System MUST limit total generations to a predetermined number of samples to ensure completion within 6 hours. (See US-2)
- **FR-006**: System MUST calculate pass@1 rates for original vs. perturbed prompts. (See US-3)
- **FR-007**: System MUST apply McNemar's test to compare paired success/failure counts between original and perturbed conditions. (See US-3)
- **FR-008**: System MUST apply multiple-comparison correction (e.g., Bonferroni) when testing >1 hypothesis across perturbation types. (See US-3)
- **FR-009**: System MUST classify failures into syntax, logic, or hallucination types for a subset of samples. (See US-3)

### Key Entities

- **Task**: A programming problem from HumanEval containing a function signature, docstring, and test cases.
- **Prompt**: The text input sent to the model, existing in original or perturbed states.
- **Generation**: The code output produced by the model for a specific prompt.
- **Result**: The execution outcome (pass/fail/error) of the generated code against test cases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pass@1 degradation is measured against the original prompt baseline to quantify robustness loss. (See US-3)
- **SC-002**: Statistical significance is measured against the McNemar's test p-value threshold (α = 0.05) to validate associational claims. (See US-3)
- **SC-003**: Total job runtime is measured against the 6-hour GitHub Actions free-tier limit. (See US-2)
- **SC-004**: Memory usage is measured against the 7 GB RAM constraint during inference. (See US-2)
- **SC-005**: Sample count is measured against the 500-sample limit to ensure feasibility. (See US-2)

## Assumptions

- The HumanEval dataset is accessible via HuggingFace Datasets without authentication barriers in the CI environment.
- The GitHub Actions runner provides Docker or subprocess sandboxing capabilities for code execution.
- A StarCoder2 model variant (e.g., 1.5B or 3B) is available in a format compatible with CPU inference without requiring CUDA-specific quantization libraries (e.g., `bitsandbytes` CPU build).
- The perturbation rules (synonym replacement, etc.) are deterministic and do not alter the semantic intent of the original task beyond the intended noise.
- The 500-sample limit is sufficient to achieve statistical power for McNemar's test given the expected effect size.
- Network bandwidth in the CI environment is sufficient to download the model weights (~2-4 GB) within the 6-hour window.
