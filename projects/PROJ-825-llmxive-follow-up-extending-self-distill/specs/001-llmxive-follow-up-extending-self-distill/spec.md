# Feature Specification: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Feature Branch**: `001-llmxive-student-only-gating`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Does replacing the teacher-student confidence gap in Self-Distilled Agentic Reinforcement Learning (SDAR) with a student-only heuristic (token entropy and retrieved context stability) preserve the majority of the performance gains in multi-turn agent tasks?"

## Research Question & Hypothesis

**RQ**: *Can a student‑only gating mechanism based on token entropy (Hₜ) and retrieved‑context stability (Sₜ) retain most of the performance benefits of the original teacher‑student confidence‑gap signal in SDAR across multi‑turn tasks?*  

**Hypothesis**: The student‑only variant will achieve **≥ 80 %** of the baseline SDAR performance improvement while reducing per‑step CPU cost by **≥ 60 %**. The study is observational/comparative; no causal inference beyond this measured relationship is claimed.

## User Scenarios & Testing

### User Story 1 - Execute Student-Only Gating Training Loop (US-1) (Priority: P1)

As a researcher, I want to train the "Student-Only Gating" variant of SDAR on the ALFWorld and WebShop environments using only the student model's internal entropy and retrieved context stability as gating signals, so that I can eliminate the computational cost of the teacher model forward pass while maintaining training stability.

**Why this priority**: This is the core hypothesis test. Without successfully running the student‑only variant and collecting its steps‑to‑threshold data, no comparison or cost analysis is possible. It is the minimum viable experiment.

**Independent Test**: Can be fully tested by initiating a training run with the `--variant student-only` flag on a single environment (e.g., ALFWorld) and verifying that the training loop completes without teacher model calls, logging the specific gating scores derived solely from student entropy and context similarity.

**Acceptance Scenarios**:

1. **Given** the ALFWorld environment is configured and the Qwen series student model is loaded, **When** the training loop executes for a fixed **10 000** training steps, **Then** the system must log gating scores ($g_t$) calculated exclusively from token entropy ($H_t$) and context stability ($S_t$) without invoking any teacher model.  
2. **Given** a training run is active, **When** the retrieved context is noisy or irrelevant, **Then** the student‑only gate must correctly down‑weight low‑confidence tokens based on the cosine similarity metric $S_t$, preventing the accumulation of noisy distillation signals.

### User Story 2 - Compare Baseline vs. Student-Only Performance (US-2) (Priority: P2)

As a researcher, I want to run the original dual‑model SDAR baseline and the proposed student‑only variant in parallel (or sequentially with identical seeds) and compare their task success rates and steps‑to‑threshold speeds, so that I can quantify the performance retention of the student‑only approach.

**Why this priority**: This directly addresses the research question regarding the necessity of the teacher signal. It provides the primary metric (performance gap) to validate the hypothesis.

**Independent Test**: Can be fully tested by executing two distinct training jobs (Baseline SDAR and Student‑Only) on the same environment and generating a comparison report that lists final task success rates and the number of steps required to reach average per‑episode cumulative reward **0.8**.

**Acceptance Scenarios**:

1. **Given** two training runs (Baseline SDAR and Student‑Only) completed on WebShop with identical hyperparameters and random seeds, **When** the results are aggregated, **Then** the system must output a comparison table showing the final task success rate for both variants and the percentage difference between them.  
2. **Given** the training curves are generated, **When** the convergence speed is analyzed, **Then** the system must report the number of training steps required for each variant to achieve an average per‑episode cumulative reward of **0.8**, allowing for a direct speed comparison.

### User Story 3 - Validate Computational Efficiency, Statistical Significance, and Correlation (US-3) (Priority: P3)

As a researcher, I want to measure the per‑step computational cost (CPU time and memory) of the student‑only variant against the baseline and perform statistical hypothesis testing on the performance results, as well as quantify how well the student‑only heuristic correlates with the original teacher‑student confidence‑gap scores, so that I can confirm the >60 % cost reduction, determine statistical significance, and assess the added value of the teacher signal.

**Why this priority**: This validates the “edge‑device” motivation, ensures scientific rigor, and directly addresses the scope‑mandated correlation analysis.

**Independent Test**: Can be fully tested by profiling the training loop's CPU usage and memory footprint during execution, running a Mann‑Whitney U test on the collected success rates from multiple independent runs, and computing the Pearson correlation coefficient between the student‑only gating scores and the teacher‑student gap scores.

**Acceptance Scenarios**:

1. **Given** the training execution logs, **When** the computational cost is profiled, **Then** the system must report the average CPU time per step and peak memory usage for the student‑only variant, showing a reduction of **≥ 60 %** compared to the baseline (calculated as the mean of **20** independent runs per variant).  
2. **Given** the final task success rates from multiple independent runs of both variants, **When** a Mann‑Whitney U test (or bootstrapping) is performed, **Then** the system must output the p‑value and confirm statistical significance at **p < 0.05**.  
3. **Given** the logged teacher‑student confidence‑gap scores and the student‑only heuristic scores for each step, **When** the Pearson correlation coefficient is computed, **Then** the system must report **r ≥ 0.6** (indicating a strong positive relationship).

### Edge Cases

- What happens when the retrieved context is completely irrelevant (random noise), causing the context stability score ($S_t$) to be near zero? The system must rely on token entropy ($H_t$) to gate the signal, preventing the model from learning from garbage context.  
- How does the system handle environments where the student model consistently outputs high‑confidence but incorrect tokens (low entropy, high error)? The gating mechanism must not blindly trust low entropy; the design assumes the correlation between entropy and correctness holds, but this edge case may require a fallback or manual intervention if the correlation breaks.  
- What if the CPU memory limit is exceeded during the retrieval of large context windows? The system must implement a chunking strategy or limit the context window size to ensure the process does not crash the CI runner.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the Student‑Only gating mechanism $g_t = \sigma(\alpha H_t + \beta S_t)$ using student token entropy ($H_t$) and retrieved context stability ($S_t$) without invoking a teacher model. (See US-1)  
- **FR-002**: System MUST execute the training loop for both the Baseline SDAR (dual‑model) and Proposed Student‑Only variants on the ALFWorld and WebShop environments for a fixed number of **10 000** training steps. (See US-2)  
- **FR-003**: System MUST log per‑step computational metrics including CPU time, peak memory usage, and the specific values of $H_t$ and $S_t$ for every training step. (See US-3)  
- **FR-004**: System MUST persist all baseline training artifacts (including teacher‑student gap scores and student heuristics) to a shared storage location to ensure retrievability for cross‑variant performance analysis. (See US-2)  
- **FR-005**: System MUST perform a statistical hypothesis test (prioritizing Mann‑Whitney U test or bootstrapping for small‑n bounded data; t‑test only if normality is confirmed) on the final task success rates of the two variants to determine significance at **p < 0.05**. (See US-3)  
- **FR-006**: System MUST handle cases where the retrieved context is noisy by ensuring the gating score $g_t$ remains bounded and does not produce NaN values during the sigmoid activation. (See US-1)  
- **FR-007**: System MUST compute the Pearson correlation coefficient $r$ between the student‑only heuristic score $g_t$ and the original teacher‑student confidence‑gap score for each step, and log this value per run. (See US-3)  
- **FR-008**: System MUST record the baseline SDAR success metric (Success\_Baseline) for each environment to enable the comparative calculation required by SC‑001. (See US-2)  
- **FR-009**: System MUST ensure that all runs are executed on CPU‑only GitHub Actions runners using an 8‑bit quantized Qwen model; any attempt to fall back to GPU must be aborted and flagged as a failure. (See Assumptions)

### Key Entities

- **TrainingRun**: Represents a single execution of the RL loop, containing metadata (variant type, environment, hyperparameters) and collected metrics (success rate, steps, cost).  
- **GatingSignal**: Represents the computed gate value $g_t$ for a specific token, containing the entropy component ($H_t$), stability component ($S_t$), and the final weighted score.  
- **EnvironmentTask**: Represents a specific task instance in ALFWorld or WebShop, containing the goal description, initial state, and the expected trajectory for reward calculation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task success rate of the Student‑Only variant is measured against the Baseline SDAR variant to determine if it achieves **≥ 80 %** of the baseline’s performance improvement over the baseline itself, i.e.  
  \[
  \frac{\text{Success}_{\text{Student}} - \text{Success}_{\text{Baseline}}}{\text{Success}_{\text{Baseline}}} \ge 0.80
  \]  
  (See US-2)  
- **SC-002**: Per‑step computational cost (CPU time) of the Student‑Only variant is measured against the Baseline SDAR variant over a fixed **10 000**‑step horizon to verify a reduction of **≥ 60 %**. (See US-3)  
- **SC-003**: The p‑value from the statistical hypothesis test on success rates is measured against the conventional significance threshold **p < 0.05** to determine if the performance difference is statistically significant. (See US-3)  
- **SC-004**: The convergence speed (steps to reach average per‑episode cumulative reward **≥ 0.8**) of the Student‑Only variant is measured against the Baseline SDAR variant to assess training efficiency. (See US-2)  
- **SC-005**: Pearson correlation coefficient $r$ between the student‑only heuristic scores and the original teacher‑student confidence‑gap scores is measured; a value **r ≥ 0.6** is required to demonstrate a strong positive relationship. (See US-3)

## Assumptions

- The Qwen student model is sufficiently small to run on a CPU‑only GitHub Actions runner (multi‑core, constrained RAM) within the job time limit, even with the overhead of the dense retriever.  
- The ALFWorld and WebShop environments can be downloaded and executed without external network dependencies beyond the initial cloning, fitting within standard disk storage constraints.  
- **Hypothesis H1**: The student token entropy ($H_t$) and retrieved context stability ($S_t$) are positively correlated with the correctness of the token. This is a testable hypothesis to be validated by the correlation analysis (FR‑007), not a precondition for the experiment's validity.  
- The dense retriever using `sentence-transformers` (quantized) or `rank_bm25` can be executed on CPU without exceeding the memory constraints of the free‑tier runner.  
- The "Student‑Only" variant does not require any pre‑computed teacher labels or teacher model checkpoints, relying entirely on the student's internal state and the environment feedback.  
- A minimum of **20** independent runs per variant (40 total) will be performed to achieve statistical power ≥ 0.8 for detecting the targeted effect sizes (α = 0.05). This number follows conventional power analysis for Mann‑Whitney U tests with expected medium effect sizes.  
- All runs are forced to stay on CPU; attempts to switch to a GPU (e.g., Kaggle T4) will cause the job to fail, ensuring comparable CPU‑time measurements across variants.  
