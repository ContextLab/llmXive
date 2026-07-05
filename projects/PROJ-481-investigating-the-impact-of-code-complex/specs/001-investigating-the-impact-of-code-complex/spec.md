# Feature Specification: Investigating the Impact of Code Complexity on LLM Code Understanding

**Feature Branch**: `001-code-complexity-llm-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Code Complexity on LLM Code Understanding"

## User Scenarios & Testing

### User Story 1 - Compute Static Complexity Metrics on Code Corpus (Priority: P1)

The system must ingest a public code dataset (e.g., CodeSearchNet or BigCodeBench), parse individual functions, and compute static complexity metrics (Cyclomatic Complexity, Halstead metrics, Cognitive Complexity) for every function.

**Why this priority**: This is the foundational data layer. Without accurate, computed complexity metrics linked to code samples, no correlation analysis can occur. It is the prerequisite for all subsequent modeling.

**Independent Test**: Can be tested by running the metric computation pipeline on a small, manually verified subset of code (e.g., 50 functions) and verifying the output CSV matches manual calculations or known tool outputs (e.g., `radon`).

**Acceptance Scenarios**:

1. **Given** a valid code repository or dataset containing Python functions, **When** the metric computation script runs, **Then** a structured dataset (CSV/JSON) is produced containing at least 5,000 functions with columns for Cyclomatic Complexity, Halstead Volume, and Cognitive Complexity.
2. **Given** a function with invalid syntax, **When** the script attempts to parse it, **Then** the function is skipped or flagged as an error without crashing the entire pipeline, and the error is logged.
3. **Given** the computed metrics, **When** a statistical summary is generated, **Then** the distribution of complexity scores is visible, confirming the dataset contains a range of complexity levels (low to high).

---

### User Story 2 - Execute LLM Code Understanding Tasks and Record Accuracy (Priority: P2)

The system must run selected open-source LLMs (e.g., CodeLlama-7B, StarCoder-3B) on the computed dataset to perform code understanding tasks (summarization, bug detection, function completion) and compare outputs against ground truth to calculate accuracy scores.

**Task Definition Clarification**: For "function completion", the ground truth is the *original* source code, making this a **reconstruction task** measuring fidelity. For "summarization" and "bug detection", ground truth consists of independent human annotations (e.g., distinct summaries or bug reports) to measure abstract understanding. The study explicitly distinguishes between "reconstruction fidelity" (generation) and "independent understanding" (QA) to avoid category errors.

**Why this priority**: This generates the dependent variable (model accuracy). Without this step, the relationship between complexity and performance cannot be measured.

**Independent Test**: Can be tested by running the inference pipeline on a fixed, small subset of functions with known ground truth answers and verifying the accuracy metrics (ROUGE-L, F, BLEU) are calculated correctly.

**Acceptance Scenarios**:

1. **Given** a dataset of functions with ground truth labels, **When** the LLM inference script runs on a CPU-only environment, **Then** the system produces a results file linking each function ID to its model output and calculated accuracy score for the specified task.
2. **Given** a model inference timeout or memory limit on the CPU runner, **When** the script encounters a failure, **Then** the specific function is marked as "timeout/fail" and the pipeline continues to the next item without halting.
3. **Given** multiple models are selected, **When** the inference completes, **Then** the results are tagged with the specific model ID used to generate them.

---

### User Story 3 - Correlate Complexity Metrics with Model Accuracy and Identify Thresholds (Priority: P3)

The system must perform statistical analysis to correlate complexity metrics with accuracy scores, identify specific complexity thresholds where performance degrades significantly using change-point detection, and generate visualizations.

**Why this priority**: This delivers the core research insight (the "answer" to the research question). It synthesizes the data from the previous steps into actionable findings.

**Independent Test**: Can be tested by running the analysis script on a mock dataset with a pre-defined negative correlation and verifying the output correlation coefficient and threshold markers match expectations.

**Acceptance Scenarios**:

1. **Given** the combined dataset of complexity metrics and accuracy scores, **When** the analysis script runs, **Then** a correlation matrix and scatter plots are generated showing the relationship between complexity and accuracy.
2. **Given** a user-defined accuracy drop threshold (e.g., <70% baseline), **When** the script identifies complexity levels, **Then** it reports the specific complexity value (e.g., Cyclomatic > 15) where the accuracy drop occurs.
3. **Given** the statistical analysis, **When** the report is generated, **Then** it includes confidence intervals for the correlation coefficients and a statement on statistical significance (p-value).

---

### Edge Cases

- What happens when the dataset contains functions with zero complexity (e.g., single-line returns)? The system must handle these without division-by-zero errors in metric calculations.
- How does the system handle LLMs that produce hallucinated outputs or non-code text for code tasks? The accuracy calculation must robustly handle non-matching output types by assigning **score = 0 (treated as a mismatch)** and setting **hallucination_flag = true**.
- What happens if the dataset size exceeds the RAM limit

The research question, method, and references remain unchanged. of the free-tier runner? The system must implement chunking or sampling strategies to process data in batches.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute Cyclomatic Complexity, Halstead Volume, and Cognitive Complexity for every function in the target dataset using static analysis tools (e.g., `radon`). (See US-1)
- **FR-002**: System MUST execute LLM inference for code summarization, bug detection, and function completion tasks using CPU-tractable models (e.g., via `llama.cpp`) without requiring GPU acceleration. For "function completion", the task is explicitly defined as **reconstruction** where ground truth is the original source code. For "summarization" and "bug detection", ground truth must be independent human annotations. (See US-2)
- **FR-003**: System MUST calculate accuracy metrics (ROUGE-L, F1, BLEU) by comparing LLM outputs against provided ground truth labels for each function. For reconstruction tasks, this measures **reconstruction fidelity**; for QA tasks, it measures **independent understanding**. (See US-2)
- **FR-004**: System MUST perform statistical correlation analysis (Pearson/Spearman) between computed complexity metrics and calculated accuracy scores. (See US-3)
- **FR-005**: System MUST identify and report specific complexity thresholds where model accuracy drops below **[deferred] of the dataset's mean accuracy** with a sensitivity analysis sweeping the threshold over a range of values (e.g., ±0.05, ±0.1). Threshold identification MUST use **segmented regression (change-point detection)** to provide inferential statistical evidence of a structural break, not just descriptive sweeping. (See US-3)
- **FR-006**: System MUST generate visualizations (scatter plots, threshold markers) linking complexity metrics to accuracy outcomes. (See US-3)

### Key Entities

- **CodeFunction**: Represents a single function from the dataset, containing source code, metadata, and computed complexity scores.
- **InferenceResult**: Represents the output of an LLM run, containing the generated text, accuracy score, model ID used, and a `hallucination_flag` boolean.
- **ComplexityMetric**: Represents a specific metric (e.g., Cyclomatic) and its numerical value for a given function.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between static complexity metrics and LLM accuracy is measured against the statistical significance threshold (p < 0.05) to determine if a relationship exists. (See US-3)
- **SC-002**: The specific complexity threshold value where accuracy degradation accelerates is measured against the **segmented regression change-point detection** results to ensure robustness of the identified boundary. (See US-3)
- **SC-003**: The dataset coverage is measured against the target of N ≥ 5,000 valid functions to ensure sufficient statistical power for correlation analysis. (See US-1)
- **SC-004**: The inference pipeline runtime is measured against the free-tier CI runner's time limit to ensure feasibility without GPU. **Pass condition: runtime < 6 hours**. (See US-2)
- **SC-005**: The multiple-comparison error rate is measured against the family-wise error correction method (e.g., Bonferroni or False Discovery Rate) applied to the hypothesis tests across different tasks. (See US-3)

## Assumptions

- The public code datasets (CodeSearchNet or BigCodeBench) contain sufficient ground truth labels for the selected tasks (summarization, bug detection, completion) to calculate accuracy.
- Open-source models like CodeLlama-7B or StarCoder-3B can be quantized or loaded in a way that fits within the The GitHub Actions free-tier runner has a constrained RAM limit. on CPU.
- Static analysis tools (e.g., `radon`) are compatible with the programming languages present in the dataset and can compute Cognitive Complexity without crashing on edge-case syntax.
- The relationship between code complexity and LLM performance is associative; causal claims will not be made due to the observational nature of the dataset.
- The "acceptable baseline" accuracy for threshold analysis is defined as **[deferred] of the mean accuracy** across the dataset, as no specific community standard exists for this metric yet.
- The dataset does not include variables such as developer experience or runtime performance; the study design **intentionally excludes** these potential confounders. This limitation implies that observed correlations may be confounded by omitted variables (e.g., complex code might be written by less experienced developers), and the results are interpreted as associations within the static code domain only.