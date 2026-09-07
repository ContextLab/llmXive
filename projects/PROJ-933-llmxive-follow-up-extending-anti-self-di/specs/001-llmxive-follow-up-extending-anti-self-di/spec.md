# Feature Specification: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-08-01  
**Status**: Draft  
**Input**: User description: "Does the 'deliberation reward' mechanism of Anti-Self-Distillation (AntiSD) generalize to non-verifiable reasoning domains where the privileged context consists of diverse, high-quality rationales rather than a single ground-truth solution?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Context Simulation (Priority: P1)

The system MUST successfully ingest the "UltraFeedback" and "Dolly" datasets, filter for prompts with ≥ 4 distinct annotated high-quality reasoning traces, and simulate the "privileged context" by randomly sampling one rationale per prompt while retaining the remaining rationales as the target distribution.

**Why this priority**: This is the foundational step; without a valid multi-solution dataset (≥ 4 traces) and a correctly constructed training/evaluation split (privileged vs. unselected), the AntiSD mechanism cannot be tested against the research question.

**Independent Test**: The system can be tested by loading the dataset, performing the split, and outputting a JSON report confirming the count of prompts, the number of rationales per prompt (≥ 4), and the statistical distribution of the selected privileged contexts.

**Acceptance Scenarios**:

1. **Given** the UltraFeedback and Dolly datasets are available, **When** the data loader runs, **Then** it outputs a filtered dataset where every prompt has ≥ 4 distinct annotated reasoning traces.
2. **Given** a prompt with 4+ rationales, **When** the context simulator runs, **Then** it randomly selects exactly 1 rationale as the "privileged context" $c$ and marks the other ≥ 3 as the "target distribution" for diversity validation.
3. **Given** the dataset is loaded, **When** the system computes basic statistics, **Then** it reports the average number of tokens per rationale and the frequency of deliberation tokens (e.g., "Wait", "However") in the target distribution.

---

### User Story 2 - AntiSD Signal Computation and Training Loop (Priority: P2)

The system MUST implement a custom PyTorch training loop to compute the AntiSD advantage signal (ascending Jensen-Shannon divergence) and run the on-policy RL training loop for a sufficient number of steps per prompt using a CPU-optimized setup., with full or partial fine-tuning of the transformer weights.

**Why this priority**: This implements the core hypothesis test. It distinguishes the AntiSD approach from standard self-distillation and generates the training trajectories necessary for evaluation.

**Independent Test**: The system can be tested by running the training loop on a single prompt, logging the loss curves (standard vs. AntiSD), and verifying that: (a) the dot product of the AntiSD gradient vector and the standard loss gradient vector is negative, and (b) the JS divergence metric increases over a consecutive sequence of steps.

**Acceptance Scenarios**:

1. **Given** a transformer model and a sampled privileged context, **When** the training loop executes 500 steps, **Then** it logs the Pointwise Mutual Information (PMI) and Jensen-Shannon divergence at every step without requiring GPU acceleration.
2. **Given** the AntiSD mechanism is active, **When** the gradient update is computed, **Then** the system ascends the divergence (maximizes difference) rather than descending it (minimizing difference), verified by a negative gradient dot product.
3. **Given** the training completes, **Then** the system outputs the final policy parameters and the full trajectory log containing token probabilities for the 500 steps.

---

### User Story 3 - Diversity Measurement, Quality Validation, and Statistical Analysis (Priority: P3)

The system MUST compute pairwise BLEU scores and semantic similarity between generated trajectories and the *unselected* diverse rationales, AND validate the "Reasoning Quality" using a Human Evaluation Proxy. It must then apply a Wilcoxon signed-rank test to compare the mean deliberation token frequency, trajectory diversity, and reasoning quality score between AntiSD and standard self-distillation conditions.

**Why this priority**: This provides the empirical evidence required to answer the research question. It validates whether the mechanism successfully maintains entropy and diversity in multi-solution settings while ensuring the output represents genuine reasoning improvement (validated by human consensus) rather than just divergence from a single sample.

**Independent Test**: The system can be tested by taking a set of generated trajectories, computing the diversity and quality metrics against the Human Evaluation Proxy, and outputting the Wilcoxon p-value, effect size, and correlation coefficient.

**Acceptance Scenarios**:

1. **Given** 50 generated trajectories per prompt, **When** the diversity metric runs, **Then** it computes the mean pairwise BLEU score and semantic similarity against the set of *unselected* rationales.
2. **Given** the results from both AntiSD and standard self-distillation runs, **When** the statistical analysis runs, **Then** it performs a Wilcoxon signed-rank test and reports the p-value for the difference in deliberation token frequency and reasoning quality score.
3. **Given** the analysis is complete, **When** the final report is generated, **Then** it explicitly states whether the null hypothesis (no difference in diversity or quality) is rejected at the $\alpha=0.05$ level, and whether a positive correlation exists between deliberation token frequency and the Human Evaluation Proxy Score.

---

### Edge Cases

- What happens if a prompt in the dataset has fewer than 4 annotated rationales? (System MUST skip this prompt as per FR-016).
- How does the system handle the scenario where the "privileged context" sampled is identical to one of the "unselected" rationales by chance? (System MUST detect and re-sample or exclude to ensure independence).
- What occurs if the CPU-only training exceeds the 6-hour CI limit? (System MUST implement a hard timeout at 5.5 hours and log a "timeout" status with partial results).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and filter the UltraFeedback and Dolly datasets to retain only prompts with ≥ 4 distinct high-quality reasoning traces (See US-1).
- **FR-002**: System MUST randomly sample exactly one rationale per prompt to serve as the "privileged context" $c$ and separate the remaining rationales as the target distribution (See US-1).
- **FR-003**: System MUST compute the Pointwise Mutual Information (PMI) and Jensen-Shannon divergence between the student distribution and the **teacher distribution**, where the teacher distribution is defined as the **average logit distribution over all unselected rationales** for a given prompt, computed via the Inference-Only Pass (See US-2).
- **FR-004**: System MUST implement gradient inversion to ascend (maximize) the Jensen-Shannon divergence for the AntiSD condition and descend it for the standard condition (See US-2).
- **FR-005**: System MUST compute pairwise BLEU scores and semantic similarity between generated trajectories and the set of *unselected* rationales to measure diversity (See US-3).
- **FR-006**: System MUST perform a Wilcoxon signed-rank test comparing the mean deliberation token frequency and reasoning quality score between the AntiSD and standard self-distillation conditions (See US-3).
- **FR-007**: System MUST enforce a hard runtime limit of 5.5 hours per job to ensure compatibility with the 6-hour CI constraint (See US-2).
- **FR-008**: System MUST utilize a **custom PyTorch training loop** capable of token-level gradient inversion and fine-tuning transformer weights (full or partial), avoiding libraries like `stable-baselines3` that do not support this mechanism (See US-2).
- **FR-009**: System MUST report the frequency of specific deliberation tokens (e.g., "Wait", "Let's think", "However") in the output trajectories (See US-3).
- **FR-010**: System MUST compute a "Human Evaluation Proxy Score" for generated trajectories by comparing them against a human-annotated subset of the unselected rationales to measure alignment with consensus (See US-3).
- **FR-011**: System MUST calculate and report the Pearson correlation coefficient between the frequency of deliberation tokens and the Human Evaluation Proxy Score to validate the proxy hypothesis (See US-3).
- **FR-012**: System MUST exclude any prompt that does not have at least 3 unselected rationales (i.e., total traces < 4) from the analysis to ensure statistical stability (See US-1).
- **FR-013**: System MUST perform a power analysis prior to the main statistical test to confirm the sample size (N) is sufficient (≥ 30) to detect an effect size of Cohen's d = 0.5 with power ≥ 0.8 (See US-3).
- **FR-014**: System MUST execute an **Inference-Only Pass** on all unselected rationales for each prompt before training begins to generate the logits required for the Teacher Distribution calculation (See FR-003).
- **FR-015**: System MUST generate a "Human Evaluation Proxy" by sampling 100 generated trajectories and having 3 independent human raters score them for "reasoning coherence" and "consensus alignment" on a 1-5 Likert scale, using the median score as the Quality metric (See FR-010).
- **FR-016**: System MUST exclude prompts with fewer than 4 total annotated reasoning traces from the dataset (See FR-001).
- **FR-017**: System MUST use the Wilcoxon signed-rank test (non-parametric) instead of a t-test for all statistical comparisons due to likely non-normal distributions and small sample sizes (See FR-006).
- **FR-018**: System MUST report the calculated statistical power (1 - $\beta$) for the observed effect size and sample size in the final analysis report (See FR-013).

### Key Entities

- **Prompt**: A natural language query from the dataset, associated with multiple annotated reasoning traces.
- **Privileged Context ($c$)**: A single rationale randomly sampled from a prompt's traces, used as the teacher condition for the student model.
- **Target Distribution**: The set of remaining rationales for a prompt, used as the ground truth for diversity validation.
- **Teacher Distribution**: The average logit distribution derived from all unselected rationales for a prompt, computed via the Inference-Only Pass (FR-014), used for JS divergence calculation.
- **Human Evaluation Proxy**: A quality metric derived from human raters scoring generated trajectories for "reasoning coherence" and "consensus alignment" (FR-015), used to validate quality in non-verifiable domains.
- **Trajectory**: A sequence of tokens generated by the student model during the RL training loop.
- **Deliberation Token**: A specific token identified as a marker of reasoning depth (e.g., "Wait", "However").
- **Self-Consistency Score**: (Deprecated) Replaced by Human Evaluation Proxy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The frequency of deliberation tokens in the AntiSD condition must show a **positive Pearson correlation (r ≥ 0.3)** with the Human Evaluation Proxy Score, measured against the standard self-distillation condition using the Wilcoxon signed-rank test (See FR-006, FR-009, FR-011, FR-015).
- **SC-002**: The trajectory diversity (pairwise BLEU and semantic similarity) of the AntiSD condition must be significantly different from the standard self-distillation condition when measured against the set of unselected rationales (See FR-005).
- **SC-003**: The statistical significance (p-value) of the difference in deliberation token frequency and reasoning quality score must be measured against the threshold of $\alpha=0.05$ using the Wilcoxon signed-rank test (See FR-006, FR-017).
- **SC-004**: The total training time per prompt must be measured against the 6-hour CI limit to ensure feasibility (See FR-007).
- **SC-005**: The peak memory usage during the training loop must be **< 6.5 GB** to allow for CI overhead, measured against the 7 GB RAM limit of the free-tier runner (See FR-008).
- **SC-006**: The Human Evaluation Proxy Score of AntiSD-generated trajectories must be **≥ 0.2 points higher** (on a 1-5 Likert scale) than standard self-distillation trajectories when compared against the human-annotated subset, validated via the Wilcoxon signed-rank test (See FR-010, FR-015).
- **SC-007**: The power analysis (FR-013) must confirm that the sample size (N) is **≥ 30** to achieve a statistical power of **≥ 0.8** for the observed effect size (See FR-013, FR-018).

## Assumptions

- The "UltraFeedback" and "Dolly" datasets contain sufficient prompts with ≥ 4 distinct annotated high-quality reasoning traces to support statistical power (sample size $\ge$ 30 prompts).
- A small pre-trained transformer (e.g., `distilbert-base` or a compact model) is sufficient to demonstrate the gradient inversion mechanism **with full or partial fine-tuning of the model weights** (not frozen) on a CPU.
- The "privileged context" simulation (random sampling) adequately approximates the stochastic nature of diverse rationales in multi-solution domains.
- The CPU-only environment (2 cores, 7 GB RAM) is sufficient to run 500 steps of on-policy RL per prompt for the selected small model size **with weight updates**.
- The definition of "deliberation tokens" (e.g., "Wait", "Let's think") is consistent across the UltraFeedback and Dolly datasets and serves as a valid proxy for reasoning depth **only if correlated with the Human Evaluation Proxy Score**.
- The Jensen-Shannon divergence calculation is numerically stable when the student and teacher distributions are identical or near-identical.
- **In Non-Verifiable Domains**: The "Human Evaluation Proxy" (consensus alignment) is an acceptable substitute for "correctness" (Gold Standard) because, in ethical dilemmas, quality is defined by consensus among human raters rather than a single ground truth.
- The Inference-Only Pass (FR-014) can be completed within 30 minutes of the total CI time budget.