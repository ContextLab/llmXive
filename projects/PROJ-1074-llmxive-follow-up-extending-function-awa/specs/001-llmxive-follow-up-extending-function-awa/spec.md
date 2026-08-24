# Feature Specification: llmXive Follow-up: Function-Aware FIM for Non-Code Domains

**Feature Branch**: `001-fim-non-code-transfer`  
**Created**: 2026-07-21  
**Status**: Draft  
**Input**: User description: "Does the function-call inductive bias learned via Function-Aware Fill-in-the-Middle (FIM) transfer to non-code domains (e.g., logical deduction chains or math proofs) when the mid-training corpus consists of structured, function-like reasoning traces, or is the performance gain strictly dependent on syntactic code patterns?"

## User Scenarios & Testing

### User Story 1 - Synthetic Logical Dataset Construction (Priority: P1)

As a researcher, I need to convert standard math and logic datasets (GSM8K, LogiQA) into a pseudo-code format where deduction steps are wrapped as `def step_N(): return derived_fact` blocks, so that I can apply the Function-Aware FIM mechanism to non-code reasoning traces.

**Why this priority**: This is the foundational prerequisite. Without the synthetic "logical function call" dataset, the mid-training phase cannot occur, and the core hypothesis cannot be tested. It is the first step in the experimental pipeline.

**Independent Test**: The dataset construction pipeline can be tested by running it on a small subset of GSM8K, verifying the output format (valid pseudo-code with dependency graphs), and ensuring the total token count matches the target (500k examples) within a 1% tolerance.

**Acceptance Scenarios**:

1. **Given** the raw GSM8K and LogiQA datasets, **When** the conversion script is executed, **Then** the output is a JSONL file where every intermediate reasoning step is wrapped in a `def step_N():` block with a return statement containing the derived fact.
2. **Given** the generated pseudo-code, **When** the dependency graph extractor runs, **Then** it correctly identifies `step_N` calls as function dependencies, enabling the FIM masking logic to target function bodies.
3. **Given** the training split, **When** a random sample is inspected, **Then** no answer keys from the original datasets are exposed in the training context, preventing data leakage.

---

### User Story 2 - CPU-Tractable Mid-Training Execution (Priority: P2)

As a researcher, I need to perform a single epoch of Function-Aware FIM mid-training on a small coding model (e.g., Qwen2.5-Coder-1.5B) using the synthetic logical dataset on a CPU-only environment, so that I can induce the structural inductive bias without exceeding resource limits.

**Why this priority**: This is the core experimental intervention. It tests whether the structural bias can be learned on non-code data. It must succeed within the strict hardware constraints (2 CPU, ~7GB RAM, ≤6h) to be feasible.

**Independent Test**: The training script can be tested by running a single epoch on a subset of the data (e.g., 10k examples) and verifying that the process completes without OOM errors, does not attempt to load CUDA, and finishes within 30 minutes for the subset (extrapolating to <6h for full data).

**Acceptance Scenarios**:

1. **Given** the Qwen2.5-Coder-1.5B model and the synthetic dataset, **When** the training job starts on a GitHub Actions runner, **Then** the process runs entirely on CPU (no CUDA/GPU errors) and completes within the 6-hour time limit.
2. **Given** the FIM masking logic, **When** a batch is processed, **Then** the masking targets function bodies and arguments based on the logical dependency graph, not random tokens.
3. **Given** the memory constraints, **When** the model loads, **Then** it uses default precision (float32) and does not attempt 8-bit/4-bit quantization which requires CUDA libraries.

---

### User Story 3 - Statistical Evaluation of Transferability (Priority: P3)

As a researcher, I need to evaluate the mid-trained model against control groups (standard Causal LM and Baseline) on non-code benchmarks (LogiQA, BFCL) and perform statistical significance testing, so that I can determine if the performance gain is structural or syntactic.

**Why this priority**: This provides the answer to the research question. It validates the hypothesis by comparing the FIM-trained model's performance against controls on independent non-code tasks.

**Independent Test**: The evaluation pipeline can be tested by running it on a mock dataset with known scores, verifying that the paired t-test (or Wilcoxon) is calculated correctly and that the results distinguish between the FIM group and the control group.

**Acceptance Scenarios**:

1. **Given** the trained models (FIM, Control, Baseline), **When** they are evaluated on LogiQA and BFCL, **Then** the accuracy scores are recorded for each random seed.
2. **Given** the set of accuracy scores across multiple seeds, **When** the statistical analysis runs, **Then** a paired t-test (or Wilcoxon signed-rank test) is performed to determine if the FIM group's mean accuracy is significantly different from the Control group (p < 0.05).
3. **Given** the evaluation results, **When** the report is generated, **Then** it explicitly states whether the performance gain is statistically significant and attributes the finding to structural generalization or syntactic dependency.

---

### Edge Cases

- **What happens when** the synthetic pseudo-code conversion creates circular dependencies in the logical steps? **System handles** this by detecting cycles in the dependency graph and flattening them into sequential steps before masking.
- **How does system handle** the scenario where the CPU-only training exceeds the 6-hour limit? **System handles** this by failing the job with a clear error message, triggering a retry with a smaller batch size or reduced dataset subset (if power analysis allows).
- **What happens when** the dataset lacks sufficient variance in logical depth? **System handles** this by flagging the dataset construction as `[NEEDS CLARIFICATION: does the synthetic corpus have sufficient logical depth variation?]` and halting training until resolved.

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct a synthetic dataset of 500k logical deduction examples where intermediate steps are formatted as `def step_N(): return fact` blocks, derived from GSM8K and LogiQA (See US-1).
- **FR-002**: System MUST perform a single epoch of Function-Aware FIM mid-training on a small open-source coding model (e.g., Qwen2.5-Coder-1.5B) using only CPU resources, ensuring no GPU/CUDA dependencies (See US-2).
- **FR-003**: System MUST mask function bodies and arguments in the synthetic dataset based on the logical dependency graph, not random token positions (See US-2).
- **FR-004**: System MUST evaluate all model variants (FIM, Control, Baseline) on independent non-code benchmarks (LogiQA, BFCL) to measure generalization (See US-3).
- **FR-005**: System MUST perform statistical significance testing (paired t-test or Wilcoxon) across multiple random seeds to compare FIM performance against the control group (See US-3).
- **FR-006**: System MUST enforce a memory constraint of ≤7 GB RAM and a time constraint of ≤6 hours for the entire training and evaluation pipeline (See US-2).

### Key Entities

- **SyntheticLogicalDataset**: The training corpus containing logical reasoning traces formatted as pseudo-code functions with dependency graphs.
- **MidTrainedModel**: The coding model (e.g., Qwen2.5-Coder-1.5B) after the single epoch of FIM mid-training on the synthetic dataset.
- **ControlModel**: The baseline model trained with standard causal language modeling on the same synthetic data.
- **EvaluationBenchmark**: The set of non-code reasoning tasks (LogiQA, BFCL) used to test transferability.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The mean accuracy of the FIM-trained model on LogiQA and BFCL is measured against the mean accuracy of the Control Group (standard Causal LM) to determine transferability (See FR-004).
- **SC-002**: The statistical significance (p-value) of the performance difference between the FIM and Control groups is measured against the threshold of p < 0.05 using a paired t-test or Wilcoxon test (See FR-005).
- **SC-003**: The total wall-clock time for the mid-training and evaluation pipeline is measured against the 6-hour limit on a GitHub Actions free-tier runner (See FR-006).
- **SC-004**: The memory usage peak during training is measured against the 7 GB RAM limit to ensure CPU-tractability (See FR-006).
- **SC-005**: The rate of successful dependency graph construction is measured against [deferred] to ensure no data leakage or format errors in the synthetic dataset (See FR-001).

## Assumptions

- **Assumption about data availability**: The GSM8K and LogiQA datasets are accessible and can be converted into the required pseudo-code format without copyright or licensing restrictions for research use.
- **Assumption about model compatibility**: The Qwen2.5-Coder-1.5B (or similar 1.5B-3B parameter model) is available in a format compatible with CPU-only training (e.g., HuggingFace `transformers` with default precision) and fits within 7 GB RAM.
- **Assumption about logical structure**: The logical deduction chains in GSM8K and LogiQA can be unambiguously decomposed into sequential "function calls" (steps) where the dependency graph is well-defined and acyclic.
- **Assumption about compute limits**: The GitHub Actions free-tier runner provides sufficient CPU stability to complete a 1-epoch training run on 500k examples within 6 hours, assuming a batch size of ≤32 and sequence length ≤2048.
- **Assumption about baseline performance**: The baseline model (no mid-training) and control model (standard Causal LM) will establish a performance floor, ensuring that any observed gain in the FIM group is attributable to the FIM objective and not random variance.
- **Assumption about statistical power**: A sample size of 500k examples and evaluation across ≥3 random seeds provides sufficient statistical power to detect a medium effect size (Cohen's d ≈ 0.5) with α = 0.05.
