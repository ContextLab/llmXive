# Feature Specification: llmXive follow-up: extending "MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proacti"

**Feature Branch**: `001-llmxive-long-horizon-context`  
**Created**: 2026-09-07  
**Status**: Draft  
**Input**: User description: "Does the 'Context-as-Action' (ConAct) mechanism in mobile GUI agents suffer from information decay in ultra-long horizons (50+ steps) where folded history discards critical cross-app dependencies, and can a semantic recall module restore success rates by retrieving relevant historical context?"

## User Scenarios & Testing

### User Story 1 - Synthetic Ultra-Long Horizon Benchmark Generation (Priority: P1)

The system must programmatically construct a synthetic test dataset by chaining existing mobile app workflows from the MemGUI dataset to create trajectories of 50–100 steps, ensuring that critical information required for a step is explicitly available only in a historical step (e.g., 10+ steps prior).

**Why this priority**: Without a reproducible, ultra-long horizon dataset that specifically targets cross-app dependency failures, the experiment cannot be conducted. This is the foundational data layer for both the baseline and the recall-enhanced evaluation.

**Independent Test**: The generation script runs successfully, outputs a JSONL file of multiple trajectories, and an automated validation script asserts that dependency links exist for >95% of trajectories.

**Acceptance Scenarios**:

1. **Given** the MemGUI-3K dataset is available, **When** the generation script executes with a target horizon of 50 steps, **Then** the output contains at least 50 synthetic trajectories where the final step depends on information from step 10 or earlier.
2. **Given** a generated trajectory, **When** the context window is artificially truncated to exclude steps 1–40, **Then** the ground-truth answer for step 60 becomes unanswerable without external retrieval.
3. **Given** a generated subset of 10 trajectories, **When** reviewed by a human expert or an expert-system validator, **Then** at least 80% are rated as "semantically plausible" for real-world mobile tasks, ensuring the synthetic data is not trivial.

---

### User Story 2 - Baseline ConAct Execution & Decay Measurement (Priority: P2)

The system must execute the standard MemGUI-8B-SFT agent (using the Context-as-Action mechanism) on the synthetic benchmark using a CPU-only inference pipeline, recording the step-by-step success rate and identifying the exact step where "information decay" causes a failure.

**Why this priority**: This establishes the control group performance. It quantifies the "information decay" phenomenon hypothesized in the research question, providing the baseline against which the recall module's efficacy is measured.

**Independent Test**: The baseline agent runs on the synthetic set without GPU acceleration, completes the execution log, and the success rate drops by >15% between step 30 and step 60 (or confirms no significant drop if the hypothesis is false).

**Acceptance Scenarios**:

1. **Given** the synthetic benchmark and the frozen MemGUI-8B-SFT weights, **When** the baseline agent executes, **Then** the system logs a success rate trend across steps.
2. **Given** a failed trajectory, **When** the execution log is analyzed, **Then** the first failure point is recorded and attributed to missing context from a step >10 indices prior.
3. **Given** the baseline execution results, **When** analyzed, **Then** the system reports whether a statistically significant decay (p < 0.05) was observed; if not, the result is recorded as "null result: no significant decay" without invalidating the study design.

---

### User Story 3 - Semantic Recall Augmentation & Efficacy Validation (Priority: P3)

The system must implement a lightweight "selective recall" module using `all-MiniLM-L6-v2` to retrieve relevant historical snippets based on the current goal (derived solely from the agent's current state, not ground-truth metadata), inject them into the prompt, and re-execute the agent to measure the improvement in success rates compared to the baseline.

**Why this priority**: This addresses the core hypothesis: whether a lightweight retrieval patch can mitigate information decay. The success of the entire project hinges on demonstrating a statistically significant improvement.

**Independent Test**: The recall-enhanced agent runs on the same synthetic set, and the success rate in the 50–100 step range is at least 15% higher than the baseline (if the baseline decay hypothesis holds).

**Acceptance Scenarios**:

1. **Given** the synthetic benchmark and the recall module, **When** the agent executes a 60-step trajectory, **Then** the system injects a "memory flash" containing context retrieved via similarity search on the current goal state.
2. **Given** the execution results of both baseline and recall-enhanced agents, **When** a paired statistical test is applied, **Then** the result shows a p-value < 0.05 indicating significant improvement (if applicable).

---

### Edge Cases

- What happens if the semantic similarity score for a historical snippet is ambiguous (e.g., multiple snippets exceed the threshold)?
- How does the system handle a scenario where the required context is not present in the folded history at all (hallucination check)?
- What is the behavior if the memory retrieval latency causes the total step time to exceed the 6-hour CI job limit (timeout handling)?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST construct a synthetic benchmark of ≥50 trajectories with horizons between 50 and 100 steps, ensuring explicit cross-app dependencies exist (See US-1).
- **FR-002**: The system MUST execute the baseline ConAct agent on the synthetic benchmark using only CPU resources (no GPU/CUDA) and record step-level success/failure (See US-2).
- **FR-003**: The system MUST implement a semantic recall module using the `all-MiniLM-L6-v2` model to generate embeddings and retrieve historical snippets based on the agent's current goal state, ensuring the retrieval query is NOT derived from ground-truth dependency metadata (See US-3).
- **FR-004**: The system MUST inject retrieved historical snippets into the agent's prompt as "memory flashes" when the similarity score exceeds a defined threshold (See US-3).
- **FR-005**: The system MUST perform a Wilcoxon signed-rank test (non-parametric) as the primary analysis to compare the success rates of the baseline vs. recall-enhanced agents; a paired t-test is permitted only as a secondary check if normality is confirmed (See US-3).
- **FR-006**: The system MUST measure and log peak memory footprint and inference latency for both configurations to ensure the recall module adds <10% overhead (See US-3).
- **FR-007**: The system MUST validate the realism of the synthetic trajectories by running a subset (≥10) through a human-in-the-loop or expert-system review, requiring ≥80% "plausibility" approval before full benchmark execution (See US-1).

### Key Entities

- **SyntheticTrajectory**: A sequence of mobile GUI states and actions spanning 50–100 steps, with annotated "dependency links" indicating which past step provides context for a future step.
- **MemoryFlash**: A retrieved text snippet from the folded history, containing the specific context needed to resolve the current step, injected into the prompt.
- **ExecutionLog**: A structured record of the agent's decision process, success/failure status per step, and latency metrics for a single trajectory.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The baseline success rate decline is measured against a quantitative threshold: a drop of >15% in success rate between step 30 and step 60 (See US-2).
- **SC-002**: The improvement in success rate for the recall-enhanced agent is measured against the baseline (target: ≥15% increase) (See US-3).
- **SC-003**: The statistical significance of the difference between baseline and recall-enhanced agents is measured against the p < 0.05 threshold (See US-3).
- **SC-004**: The peak memory footprint of the recall-enhanced agent is measured against the baseline agent memory footprint, with a deferred limit for the acceptable increase (See US-3).
- **SC-005**: The total execution time for the full benchmark (baseline + recall) is measured against the CI job limit (See US-2, US-3).

## Assumptions

- The MemGUI dataset and the pre-trained MemGUI-SFT model weights (quantized to a reduced precision) are accessible via Hugging Face and can be loaded into a standard memory footprint.
- The synthetic benchmark construction can be performed deterministically by chaining existing workflows without requiring new data collection or human annotation.
- The `all-MiniLM-L6-v2` sentence transformer is sufficient for retrieving relevant context from folded history in the mobile GUI domain.
- The "Context-as-Action" mechanism in the baseline agent is implemented exactly as described in the original MemGUI paper, with no hidden modifications.
- The execution environment (GitHub Actions runner) provides sufficient disk space to store the dataset, model weights, and logs.
- We assume the sample size (n=50) is sufficient to detect a meaningful difference in success rates with p < 0.05; if not, the result is interpreted as "inconclusive due to power" rather than "no effect."
- The "information decay" phenomenon is primarily driven by the loss of specific facts in the folded history, not by a degradation of the model's reasoning capabilities over time.
- The low-bit quantization of the base model does not significantly alter the agent's behavior compared to the original higher-bit version used in the baseline study.
- The synthetic trajectories generated are representative of real-world ultra-long-horizon mobile tasks, provided the plausibility validation (FR-007) passes.
- The semantic similarity threshold for triggering a "memory flash" can be set to a fixed value (e.g., 0.75) without extensive tuning, as the primary goal is to test the *presence* of retrieval, not the optimal threshold.