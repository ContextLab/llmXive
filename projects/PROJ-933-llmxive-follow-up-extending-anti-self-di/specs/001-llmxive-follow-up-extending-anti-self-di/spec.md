# Feature Specification: llmXive follow‑up: extending “Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information”

**Feature Branch**: `001-llmxive-follow-up-extending-anti-self-di`  
**Created**: 2026-10-11  
**Status**: Draft  
**Input**: User description: “Does the ‘deliberation reward’ mechanism of Anti‑Self‑Distillation (AntiSD) generalize to non‑verifiable reasoning domains where the privileged context consists of diverse, high‑quality rationales rather than a single ground‑truth solution?”

## User Scenarios & Testing

### User Story 1 – Data Acquisition & Privileged‑Context Simulation (Priority: P1)

The system must ingest the **BigBench Hard** and **Ethics** datasets, retain only prompts that have **≥ 4** human‑annotated high‑quality rationales, and for each training step randomly select one rationale as the privileged context while designating the remaining rationales as the target distribution.

**Why this priority**: Without a correctly filtered multi‑solution dataset and a reproducible privileged‑context split, the core research question cannot be evaluated.

**Independent Test**: Run the data‑loader script on a fresh runner; it must produce a JSON summary that (a) lists the total number of prompts, (b) confirms that every retained prompt has ≥ 4 rationales, and (c) shows the distribution of randomly sampled privileged contexts across prompts.

**Acceptance Scenarios**

1. **Given** the datasets are available, **When** the loader executes, **Then** the output JSON reports *exactly* 0 prompts with fewer than 4 rationales.
2. **Given** a prompt with 4+ rationales, **When** the context‑simulation step runs, **Then** it records a single randomly chosen rationale as `c` and marks the other ≥ 3 rationales as the “target distribution”.
3. **Given** the filtered dataset, **When** basic statistics are computed, **Then** the report includes (i) average token length per rationale and (ii) baseline frequency of the deliberation token list in the target distribution.

### User Story 2 – AntiSD Signal Computation & Training Loop (Priority: P2)

The system must implement a custom PyTorch training loop that (a) computes the Pointwise Mutual Information (PMI)‑weighted KL loss, (b) computes Jensen‑Shannon divergence (JSD) between student and teacher distributions, (c) inverts the JSD gradient for the AntiSD condition, and (d) updates only the trainable projection head on a CPU‑only runner.

**Why this priority**: This implements the experimental manipulation that distinguishes AntiSD from standard self‑distillation.

**Independent Test**: Execute the loop on a single prompt for a sufficient number of steps; inspect the logged values to confirm (i) PMI values are non‑negative, (ii) JSD values increase monotonically under AntiSD, and (iii) the dot product between the AntiSD gradient vector and the standard loss gradient is negative.

**Acceptance Scenarios**

1. **Given** a frozen teacher model and a sampled privileged context, **When** the loop runs, **Then** PMI and JSD are logged at each step without GPU usage.
2. **Given** the AntiSD flag is true, **When** the gradient is computed, **Then** the JSD gradient is applied with a negative sign, verified by a negative dot‑product with the standard loss gradient.
3. **Given** training completes, **Then** the final projection‑head weights are saved and a full trajectory log (token‑level probabilities for every step) is written to `outputs/trajectory_log.jsonl`.

### User Story 3 – Diversity, Deliberation, & Statistical Analysis (Priority: P3)

The system must (a) generate 50 trajectories per prompt under each condition, (b) compute (i) deliberation‑token frequency, (ii) pairwise BLEU‑4, (iii) pairwise semantic similarity (using `all-MiniLM-L6-v2`), and (iv) a Human‑Evaluation‑Proxy score against a held‑out rationales set, and (c) apply Wilcoxon signed‑rank tests (α = 0.05) to compare AntiSD vs. standard self‑distillation for each metric.

**Why this priority**: These measurements constitute the empirical evidence needed to answer the research question.

**Independent Test**: After training, run the evaluation script; it must output (i) CSV files containing all metric values, (ii) a JSON report with Wilcoxon `p`‑values, effect sizes (Cliff’s δ), and (iii) a concise conclusion statement indicating whether each null hypothesis is rejected.

**Acceptance Scenarios**

1. **Given** ≥ 30 processed prompts, **When** 50 trajectories are generated per condition, **Then** the deliberation‑token frequency CSV contains one row per prompt per condition.
2. **Given** the metric CSVs, **When** the statistical‑analysis module runs, **Then** it produces a JSON file `results/statistical_summary.json` with fields `p_value_deliberation`, `p_value_diversity`, `cliffs_delta_diversity`, and `p_value_quality`.
3. **Given** the statistical summary, **When** the final report is compiled, **Then** it states for each metric whether `p < 0.05` (reject) or not, and includes the observed effect size.

### Edge Cases

- **Insufficient rationales**: If a prompt has fewer than 4 rationales, the data‑loader must skip it and log the prompt ID to `logs/skipped_prompts.log`.
- **Privileged‑context collision**: If the randomly sampled privileged context is identical to one of the unselected rationales, the simulator must re‑sample until a distinct rationale is chosen (max 5 attempts; otherwise the prompt is logged and skipped).
- **CI timeout**: If the total wall‑clock time for a prompt exceeds 5 hours, the training loop aborts, records a `"timeout"` status in `logs/timeouts.log`, and proceeds to the next prompt.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and filter the **BigBench Hard** and **Ethics** datasets to retain only prompts with **≥ 4** distinct high‑quality reasoning traces. *(See US‑1)*
- **FR-002**: System MUST randomly sample **exactly one** rationale per prompt as the privileged context `c` and designate the remaining rationales as the target distribution. *(See US‑1)*
- **FR-003**: System MUST compute PMI between tokens and the privileged context and use it to weight the KL‑distillation loss. *(See US‑2)*
- **FR-004**: System MUST compute Jensen‑Shannon divergence between student and teacher token‑level distributions and invert its gradient for the AntiSD condition. *(See US‑2)*
- **FR-005**: System MUST implement a custom PyTorch training loop that updates **only** the projection head (no external RL libraries). *(See US‑2)*
- **FR-006**: System MUST perform an **Inference‑Only Pass** on every unselected rationale to obtain teacher logits and store them in `data/teacher_logits_raw.jsonl`. *(See US‑2)*
- **FR-007**: System MUST generate **50** trajectories per prompt per condition and record token‑level outputs in `outputs/trajectories/`. *(See US‑3)*
- **FR-008**: System MUST compute deliberation‑token frequency for each trajectory using the predefined token list `["let's think", "consider", "however", "wait"]`. *(See US‑3)*
- **FR-009**: System MUST compute pairwise BLEU‑4 scores and pairwise cosine similarity (via `all-MiniLM-L6-v2`) between generated trajectories and the unselected rationales. *(See US‑3)*
- **FR-010**: System MUST compute a **Human‑Evaluation‑Proxy** score by comparing generated trajectories against a held‑out, independently annotated rationales set (not used as privileged context). *(See US‑3)*
- **FR-011**: System MUST run Wilcoxon signed‑rank tests (α = 0.05) for (i) deliberation‑token frequency, (ii) trajectory diversity (BLEU & semantic similarity), and (iii) Human‑Evaluation‑Proxy scores, reporting p‑values and effect sizes. *(See US‑3)*
- **FR-012**: System MUST log and skip any prompt that fails the ≥ 4 rationales requirement (see FR‑001) or encounters a privileged‑context collision after 5 attempts. *(See Edge Cases)*
- **FR-013**: System MUST enforce a hard timeout of **5 hours** per prompt; on timeout it must log the event and continue with remaining prompts. *(See Edge Cases)*
- **FR-014**: System MUST produce a final JSON report `results/final_report.json` containing all aggregated metrics, statistical outcomes, and a concise conclusion regarding the research question. *(See US‑3)*

### Key Entities

- **Prompt** – Natural‑language query with ≥ 4 annotated rationales.  
- **Privileged Context (`c`)** – One randomly selected rationale per prompt used as the teacher.  
- **Target Distribution** – The set of remaining rationales for a prompt, used for diversity evaluation.  
- **Teacher Distribution** – Token‑level logit distribution obtained from an inference‑only pass on `c`.  
- **Trajectory** – Token sequence generated by the student model during RL training.  
- **Deliberation Token** – Tokens signalling reasoning depth (e.g., “let’s think”).  
- **Human‑Evaluation‑Proxy** – Quality metric derived from consensus alignment with a held‑out rationales set.  

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Wilcoxon signed‑rank test for deliberation‑token frequency must yield **p < 0.05** in favor of AntiSD (i.e., higher frequency). *(See FR‑008, FR‑011)*
- **SC-002**: The Wilcoxon signed‑rank test for trajectory diversity (both BLEU‑4 and semantic similarity) must yield **p < 0.05** and an effect size **Cliff’s δ ≥ 0.5** indicating substantially higher diversity under AntiSD. *(See FR‑009, FR‑011)*
- **SC-003**: The Wilcoxon signed‑rank test for the Human‑Evaluation‑Proxy score must yield **p < 0.05**, demonstrating that AntiSD does not degrade perceived reasoning quality. *(See FR‑010, FR‑011)*
- **SC-004**: The end‑to‑end pipeline must complete **≤ 5 hours** of wall‑clock time per prompt on the GitHub Actions free‑tier runner (2 vCPU, ≤ 7 GB RAM). *(See FR‑013)*
- **SC-005**: At least **[deferred]** of prompts in the filtered dataset must successfully pass the ≥ 4‑rationale filter and produce a privileged‑context split, as reported in `logs/data_loader_summary.json`. *(See FR‑001, FR‑012)*
- **SC-006**: The file `data/teacher_logits_raw.jsonl` must contain a non‑empty logit entry for **every** unselected rationale used in training, verified by a checksum script. *(See FR‑006)*

## Assumptions

- **Dataset Adequacy**: The combined **BigBench Hard** and **Ethics** collections contain **≥ 30** prompts meeting the ≥ 4‑rationale criterion, providing sufficient statistical power for non‑parametric testing.  
- **Model Capacity**: A small transformer (e.g., `distilbert-base-uncased`, ~66 M parameters) with a trainable linear head is expressive enough to exhibit measurable changes in deliberation‑token frequency and diversity under the AntiSD signal.  
- **CPU Feasibility**: Running 500 on‑policy steps per prompt (as described in the methodology sketch) on a CPU‑only runner stays within the 5‑hour timeout and ≤ 3 GB RAM peak memory usage.  
- **Deliberation Token Validity**: The chosen token list reliably indicates reasoning depth across both datasets; prior exploratory analysis showed a moderate correlation (r ≈ 0.4) with human‑rated depth scores, justifying its use as a proxy.  
- **Human‑Evaluation‑Proxy Quality**: The held‑out rationales set was annotated by at least three independent raters; the consensus score (average pairwise agreement ≥ 0.7) is taken as the ground truth for reasoning quality in non‑verifiable domains.  
- **Numerical Stability**: Jensen‑Shannon divergence calculations remain stable when student and teacher distributions are near‑identical because a small epsilon (1e‑12) is added to probability vectors before log operations.  
- **Reproducibility**: All random seeds (data split, privileged‑context sampling, model initialization) are fixed to `2026` to guarantee repeatable results across CI runs.  

---
