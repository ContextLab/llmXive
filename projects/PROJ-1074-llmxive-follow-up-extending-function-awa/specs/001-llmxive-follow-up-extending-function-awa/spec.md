# Feature Specification: llmXive Follow-up: Function-Aware FIM for Non-Code Domains

**Feature Branch**: `001-fim-non-code-transfer`  
**Created**: 2026-07-21  
**Status**: Draft  
**Input**: User description: "Does the function-call inductive bias learned via Function-Aware Fill-in-the-Middle (FIM) transfer to non-code domains (e.g., logical deduction chains or math proofs) when the mid-training corpus consists of structured, function-like reasoning traces, or is the performance gain strictly dependent on syntactic code patterns?"

## User Scenarios & Testing

### User Story 1 - Synthetic Logical Dataset Construction (Priority: P1)

As a researcher, I need to convert the GSM8K math dataset into a pseudo-code format where deduction steps are wrapped as `def step_N(): return derived_fact` blocks, so that I can apply the Function-Aware FIM mechanism to non-code reasoning traces while testing on the distinct LogiQA logic dataset.

**Why this priority**: This is the foundational prerequisite. Without the synthetic "logical function call" dataset, the mid-training phase cannot occur. Strict domain separation (Train: GSM8K, Test: LogiQA) is required to prove the model learns structural bias rather than memorizing specific logical patterns.

**Independent Test**: The dataset construction pipeline can be tested by running it on a small subset of GSMK, verifying the output format (valid pseudo-code with dependency graphs), and ensuring the total token count matches the target (a sufficient volume of examples) within a 1% tolerance.

**Acceptance Scenarios**:

1. **Given** the raw GSM8K dataset, **When** the conversion script is executed, **Then** the output is a JSONL file where every intermediate reasoning step is wrapped in a `def step_N():` block with a return statement containing the derived fact.
2. **Given** the generated pseudo-code, **When** the dependency graph extractor runs, **Then** it correctly identifies `step_N` calls as function dependencies, enabling the FIM masking logic to target function bodies.
3. **Given** the training split, **When** a random sample is inspected, **Then** no answer keys from the original datasets are exposed in the training context, preventing data leakage.

---

### User Story 2 - CPU-Tractable Mid-Training Execution (Priority: P2)

As a researcher, I need to perform a single epoch of Function-Aware FIM mid-training on a small open-source model (≤150M parameters, e.g., TinyLlama-110M) using the synthetic dataset on a CPU-only environment (specifically the GitHub Actions free-tier runner: multiple vCPUs, ~7GB RAM), so that I can induce the structural inductive bias without exceeding resource limits.

**Why this priority**: This is the core experimental intervention. It tests whether the structural bias can be learned on non-code data. It must succeed within the strict hardware constraints (2 vCPU, ~7GB RAM, ≤6h) to be feasible. A Natural Language Control group (trained on the same data as plain text) is included to isolate syntax from structure.

**Independent Test**: The training script can be tested by running a single epoch on a subset of the data (e.g., a representative sample) and verifying that the process completes without OOM errors, does not attempt to load CUDA, generates a `masking_map.json` artifact, and finishes within 30 minutes for the subset (extrapolating to <6h for full data).

**Acceptance Scenarios**:

1. **Given** the TinyLlama-110M model (or equivalent ≤150M) and the synthetic dataset, **When** the training job starts on the GitHub Actions free-tier runner (2 vCPU, 7GB RAM), **Then** the process runs entirely on CPU and completes within the 6-hour time limit.
2. **Given** the FIM masking logic, **When** a batch is processed, **Then** the masked tokens in the training batch correspond exactly to the token spans of the function bodies identified in the `masking_map.json` artifact.
3. **Given** the memory constraints, **When** the model loads, **Then** it uses default precision (float32) and does not attempt 8-bit/4-bit quantization which requires CUDA libraries.

---

### User Story 3 - Statistical Evaluation of Transferability (Priority: P3)

As a researcher, I need to evaluate the mid-trained model (FIM), the Natural Language Control, and the Baseline against independent non-code benchmarks (LogiQA) and perform statistical significance testing, so that I can determine if the performance gain is structural or syntactic.

**Why this priority**: This provides the answer to the research question. It validates the hypothesis by comparing the FIM-trained model's performance against controls on independent non-code tasks.

**Independent Test**: The evaluation pipeline can be tested by running it on a mock dataset with known scores, verifying that the paired t-test (or Wilcoxon) is calculated correctly, that the report includes the `is_significant` boolean, and that the results distinguish between the FIM group and the control group.

**Acceptance Scenarios**:

1. **Given** the trained models (FIM, NL-Control, Baseline), **When** they are evaluated on LogiQA, **Then** the accuracy scores are recorded for each random seed.
2. **Given** the set of accuracy scores across multiple seeds, **When** the statistical analysis runs, **Then** a paired t-test (or Wilcoxon signed-rank test) is performed to calculate and report the p-value and test statistic.
3. **Given** the evaluation results, **When** the report is generated, **Then** it explicitly outputs a boolean field `is_significant` set to `true` if p < 0.05, or `false` otherwise, and includes the calculated p-value.

---

### Edge Cases

- **What happens when** the synthetic pseudo-code conversion creates circular dependencies in the logical steps? **System handles** this by detecting cycles in the dependency graph (using topological sort) and excluding the example from the dataset before training.
- **How does system handle** the scenario where the CPU-only training exceeds the 6-hour limit? **System handles** this by failing the job with a clear error message, triggering a retry with a smaller batch size or reduced dataset subset (if power analysis allows).
- **What happens when** the dataset lacks sufficient variance in logical depth? **System handles** this by running a depth-distribution validator on the generated corpus. If the distribution histogram does not match the target profile (min depth 3, max 10, ≥20% depth ≥7), the build fails with error code `VAR-001` and the message: "Depth distribution mismatch: expected ≥20% samples at depth ≥7, observed [X]%."

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct a synthetic dataset of logical deduction examples derived from GSM8K where intermediate steps are formatted as `def step_N(): return fact` blocks. The system MUST validate that the logical dependency graph is acyclic by performing a topological sort (length must equal step count) and MUST verify that the LogiQA test set has zero overlap with any GSM8K examples or intermediate caches. If overlap > 0, the build MUST fail (See US-1).
- **FR-002**: System MUST perform a single epoch of Function-Aware FIM mid-training on a model with ≤150M parameters (e.g., TinyLlama-110M) using only CPU resources, ensuring no GPU/CUDA dependencies (See US-2).
- **FR-003**: System MUST mask function bodies and arguments in the synthetic dataset based on the logical dependency graph, not random token positions (See US-2).
- **FR-004**: System MUST evaluate all model variants (FIM, Natural Language Control, Baseline) on independent non-code benchmarks (LogiQA) to measure generalization (See US-3).
- **FR-005**: System MUST perform statistical significance testing (paired t-test or Wilcoxon) across multiple random seeds to compare FIM performance against the Natural Language Control group (See US-3).
- **FR-006**: System MUST enforce a time constraint of ≤6 hours for the mid-training phase on the GitHub Actions free-tier runner (See US-2).
- **FR-007**: System MUST enforce a time constraint of ≤2 hours for the evaluation phase on the GitHub Actions runner (See US-3).
- **FR-008**: System MUST generate a `masking_map.json` artifact for every training batch, mapping function IDs to token spans, to verify masking correctness (See US-2).

### Key Entities

- **SyntheticLogicalDataset**: The training corpus containing logical reasoning traces formatted as pseudo-code functions with dependency graphs.
- **MidTrainedModel**: The coding model (e.g., TinyLlama-110M) after the single epoch of FIM mid-training on the synthetic dataset.
- **NLControlModel**: The baseline model trained with standard causal language modeling on the same synthetic data formatted as natural language.
- **EvaluationBenchmark**: The set of non-code reasoning tasks (LogiQA) used to test transferability.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The mean accuracy of the FIM-trained model on LogiQA is measured against the mean accuracy of the Natural Language Control Group to determine transferability (See FR-004).
- **SC-002**: The statistical significance (p-value) of the performance difference between the FIM and NL-Control groups is measured against the threshold of p < 0.05 using a paired t-test or Wilcoxon test (See FR-005).
- **SC-003**: The total wall-clock time for the mid-training pipeline is measured against the 6-hour limit on a GitHub Actions free-tier runner (See FR-006).
- **SC-004**: The memory usage peak during training is measured against the 7 GB RAM limit to ensure CPU-tractability (See FR-006).
- **SC-005**: The rate of successful dependency graph construction (successful_graphs / total_examples) is measured against a target of [deferred] (no failures allowed) to ensure no data leakage or format errors in the synthetic dataset (See FR-001).
- **SC-006**: The overlap between training (GSM8K) and test (LogiQA) problems is measured against a target of [deferred] to ensure domain separation (See US-1).

## Assumptions

- **Assumption about data availability**: The GSM8K and LogiQA datasets are accessible and can be converted into the required pseudo-code format without copyright or licensing restrictions for research use.
- **Assumption about model compatibility**: A model with ≤150M parameters (e.g., TinyLlama-110M) is available in a format compatible with CPU-only training (e.g., HuggingFace `transformers` with default precision) and fits within 7 GB RAM.
- **Assumption about logical structure**: The logical deduction chains in GSM8K can be unambiguously decomposed into sequential "function calls" (steps) where the dependency graph is well-defined and acyclic. Non-linear examples are detected by topological sort failure and excluded.
- **Assumption about compute limits**: The GitHub Actions free-tier runner (2 vCPU, 7GB RAM) provides sufficient CPU stability to complete a 1-epoch training run on [deferred] examples with a ≤150M parameter model within 6 hours, assuming a batch size of ≤32 and sequence length ≤2048.
- **Assumption about baseline performance**: The baseline model (no mid-training) and Natural Language Control model will establish a performance floor, ensuring that any observed gain in the FIM group is attributable to the FIM objective and not random variance.
- **Assumption about statistical power**: A sample size of [deferred] examples and evaluation across ≥3 random seeds provides sufficient statistical power to detect a medium effect size (Cohen's d ≈ 0.5) with α = 0.05.
- **Assumption about domain separation**: The GSM8K (Math) and LogiQA (Logic) datasets are disjoint sets with no overlapping problems or reasoning patterns that would allow direct memorization of test answers from training data.