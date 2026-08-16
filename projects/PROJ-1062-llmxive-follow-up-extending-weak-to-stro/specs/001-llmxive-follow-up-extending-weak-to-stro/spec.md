# Feature Specification: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

**Feature Branch**: `001-cross-arch-distillation`  
**Created**: 2026-08-13  
**Status**: Draft  
**Input**: User description: "Does the implicit reward signal derived from a weak teacher's policy shift retain its efficacy when transferred to a student model with a fundamentally different architectural inductive bias (e.g., from a dense Transformer to a Mixture-of-Experts or a state-space model), or does the signal degrade due to representational misalignment?"

## User Scenarios & Testing

### User Story 1 - Cross-Architecture Signal Transfer Validation (Priority: P1)

**Description**: As a researcher, I want to compute the implicit reward signal from a dense Transformer teacher and apply it to train a Mixture-of-Experts (MoE) student model on a controlled reasoning subset, so that I can determine if the "policy shift" signal transfers across fundamentally different architectural inductive biases.

**Why this priority**: This is the core hypothesis test of the project. Without establishing whether the signal transfers to *any* non-Transformer architecture, the universality claim cannot be evaluated. It isolates the primary variable: architectural mismatch.

**Independent Test**: Execute the distillation loop for the MoE student using the Transformer-derived implicit reward. Compare the resulting log-probability improvement on the AIME subset against a baseline MoE model trained only on the teacher's final distribution.

**Acceptance Scenarios**:

1. **Given** a pre-trained A sparse mixture-of-experts (MoE) student with a moderate parameter count. and a dense Transformer teacher with pre-RL and post-RL checkpoints, **When** the system computes the log-ratio implicit reward and trains the MoE student for 500 steps on the AIME subset, **Then** the MoE student's log-probability of ground-truth reasoning steps must be recorded and compared to the baseline.
2. **Given** the trained MoE student, **When** the system evaluates it on the held-out AIME problems, **Then** the system must output a scalar metric representing the performance gain relative to the baseline, clearly labeled as either "Direct-OPD" or "Baseline".

---

### User Story 2 - State-Space Model (SSM) Signal Transfer Validation (Priority: P2)

**Description**: As a researcher, I want to replicate the signal transfer experiment using a State-Space Model (SSM) student (e.g., Mamba) instead of an MoE, so that I can verify if the transferability of the implicit reward is consistent across different non-Transformer families.

**Why this priority**: This extends the validity of the findings beyond a single alternative architecture. If the signal works for MoE but fails for SSM (or vice versa), it provides specific insights into which architectural features (sparsity vs. recurrence) support or hinder the transfer of RL-induced behavioral shifts.

**Independent Test**: Execute the identical distillation loop for a SSM student using the same Transformer-derived implicit reward. Compare performance gains against the SSM baseline.

**Acceptance Scenarios**:

1. **Given** a pre-trained 1.3B parameter SSM student and the same dense Transformer teacher, **When** the system computes the implicit reward and trains the SSM student on the AIME subset, **Then** the system must record the log-probability improvement and flag the result as "SSM-Direct-OPD" or "SSM-Baseline".
2. **Given** the results from the MoE and SSM experiments, **When** the system aggregates the data, **Then** it must produce a comparative summary text block indicating whether the signal degradation (if any) is consistent across both MoE and SSM architectures.

---

### User Story 3 - Statistical Significance & Multiplicity Correction (Priority: P3)

**Description**: As a researcher, I want to perform a statistical significance test (paired t-test or Wilcoxon) on the performance gains between the Direct-OPD and Baseline groups, applying a correction for multiple comparisons, so that I can confidently assert whether the observed improvements are due to the signal or random variance.

**Why this priority**: Empirical claims require statistical rigor. Since we are testing two distinct architectures (MoE and SSM) against a baseline, we are effectively running multiple hypothesis tests. Without correction, the risk of false positives increases, invalidating the "universality" or "degradation" conclusions.

**Independent Test**: Calculate the p-value for the difference in performance gains for both MoE and SSM groups. Apply a Bonferroni or Holm-Bonferroni correction for the two tests. Report the adjusted p-value.

**Acceptance Scenarios**:

1. **Given** the performance gain distributions for the Direct-OPD and Baseline groups for both MoE and SSM, **When** the system performs a paired t-test (or Wilcoxon signed-rank test if normality fails) with cluster-robust standard errors, **Then** it must output the raw p-value and the adjusted p-value (corrected for 2 comparisons).
2. **Given** the adjusted p-values, **When** the system evaluates significance at an alpha level of 0.05, **Then** it must clearly classify the result as "Statistically Significant" or "Not Significant" for each architecture.

---

### Edge Cases

- **What happens when** the implicit reward signal is numerically unstable (e.g., log of zero probability) for certain tokens in the MoE/SSM vocabularies?
  - *Handling*: The system must implement an epsilon-smoothing mechanism (e.g., adding a small positive constant) to probabilities before log-ratio computation to prevent NaN errors, ensuring the training loop does not crash.
- **How does the system handle** memory overflow if the MoE/SSM model batch size is too large for the 7GB RAM limit of the free-tier runner?
  - *Handling*: The system must enforce a maximum batch size constraint with gradient accumulation to simulate larger batches without exceeding physical memory limits. If dynamic reduction is triggered, it must fall back to this hard limit.
- **What happens when** the SSM model's architecture prevents standard attention-based probability alignment?
  - *Handling*: The system must verify that the probability output dimensions match the reward calculation logic; if the output dimension mismatch > 0 or log-probability variance < 1e-9, it must report a specific architecture incompatibility error and halt the process.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the implicit reward signal as the log-ratio of output probabilities between the post-RL and pre-RL checkpoints of the dense Transformer teacher for every token in the AIME 2024 subset (See US-1).
- **FR-002**: System MUST initialize and load a 1B parameter MoE student and a B SSM student with pre-trained weights available on HuggingFace using int8 quantization and CPU offloading to fit within 7GB RAM (See US-1, US-2).
- **FR-003**: System MUST execute an on-policy distillation training loop where the MoE and SSM students update parameters to maximize the computed implicit reward signal, restricted to CPU-only execution, generating max 64 tokens per prompt for a sufficient number of training steps (See US-1, US-2).
- **FR-004**: System MUST train a separate baseline for each student architecture using only the final output distribution of the teacher (standard distillation) without the implicit reward signal (See US-1, US-2).
- **FR-005**: System MUST evaluate both Direct-OPD and Baseline models on the AIME subset by calculating the log-probability improvement of ground-truth reasoning steps (prefix-only) (See US-1, US-2, US-3).
- **FR-006**: System MUST perform a statistical significance test (paired t-test or Wilcoxon signed-rank) comparing the performance gains of Direct-OPD vs. Baseline for each architecture, using cluster-robust standard errors and applying a multiple-comparison correction (e.g., Bonferroni) for the two tests (See US-3).
- **FR-007**: System MUST enforce a memory constraint of ≤7GB RAM and a compute time limit of ≤6 hours per job, automatically reducing batch sizes if limits are approached, falling back to a hard limit of a minimal number (See US-1, US-2).
- **FR-008**: System MUST generate a comparative summary text block aggregating MoE and SSM results, explicitly stating whether signal degradation is consistent across architectures (See US-2).
- **FR-009**: System MUST evaluate final performance on a held-out set of unseen problems to ensure the validation target is distinct from the training signal source (See US-1, US-2).

### Key Entities

- **Implicit Reward Signal**: A scalar value derived from the log-ratio of probabilities between teacher checkpoints, representing the "policy shift" to be distilled.
- **Student Model**: The target model (MoE or SSM) undergoing training to maximize the implicit reward.
- **Baseline Model**: A control student model trained only on the teacher's final distribution, serving as the comparison point.
- **AIME Subset**: The fixed dataset of 200 reasoning problems used for training and evaluation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The log-probability improvement of ground-truth reasoning steps is measured for Direct-OPD vs. Baseline groups, with success defined as improvement > 0 and p < 0.05 (See FR-005, US-1, US-2).
- **SC-002**: The statistical significance of the performance difference is measured against the adjusted p-value (corrected for multiple comparisons) with a threshold of α = 0.05 (See FR-006, US-3).
- **SC-003**: The computational feasibility is measured against the 7GB RAM and 6-hour time limit, with the reference being the CI runner's resource constraints (See FR-007, US-1, US-2).
- **SC-004**: The presence of multiple-comparison correction is measured against the requirement to adjust p-values for two hypothesis tests (MoE and SSM), with the reference being standard statistical practice (See FR-006, US-3).
- **SC-005**: The validity of the dataset-variable fit is measured by confirming the AIME 2024 subset contains the necessary reasoning steps for evaluation, with the reference being the dataset documentation (See FR-001, US-1).
- **SC-006**: The validity of the log-probability metric is measured against human-verified correctness labels on a held-out subset, ensuring the metric is not tautological. (See FR-009).

## Assumptions

- **Assumption about data/environment**: The HuggingFace repositories for the Qwen-based teacher checkpoints and the Mixtral/Mamba student models are publicly accessible and compatible with the CPU-only environment of the GitHub Actions runner.
- **Assumption about scope boundaries**: The study is limited to the AIME subset.; generalization to other datasets or larger problem sets is out of scope for this specific experiment.
- **Assumption about target users**: The "users" of this system are researchers validating the Direct-OPD hypothesis; the output is a statistical report, not a deployed application for end-users.
- **Assumption about target architecture**: The 1B MoE (Mixtral variant) and 1.3B SSM (Mamba) models are sufficiently small to fit within 7GB RAM when loaded in int8 precision with small batch sizes and gradient accumulation.
- **Assumption about statistical power**: A sample size sufficient to detect a moderate effect size will be employed. with the chosen statistical test, or the limitations of power are explicitly acknowledged in the final report.
- **Assumption about inference framing**: Since the study is observational regarding architectural transfer (no random assignment of architecture), any conclusions about "efficacy" will be framed as associational, not causal, unless the methodology explicitly includes randomization (which it does not).
- **Assumption about threshold justification**: No arbitrary decision cutoffs (e.g., for "success" in transfer) are introduced without justification; the primary metric is the continuous log-probability improvement, and significance is determined by standard statistical thresholds (α=0.05).
- **Assumption about measurement validity**: The AIME 2024 dataset provides a validated, objective measure of reasoning capability suitable for evaluating the transfer of RL-induced behavioral shifts, consistent with the "Weak-to-Strong Generalization" literature which uses log-probability of ground-truth tokens as a primary proxy for reasoning transfer, provided it is validated against human labels (see SC-006).