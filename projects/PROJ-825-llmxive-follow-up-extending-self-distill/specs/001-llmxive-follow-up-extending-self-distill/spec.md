# Feature Specification: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Feature Branch**: `001-llmxive-student-only-gating`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Does replacing the teacher-student confidence gap in Self-Distilled Agentic Reinforcement Learning (SDAR) with a student-only heuristic (token entropy and retrieved context stability) preserve the majority of the performance gains in multi-turn agent tasks?"

## User Scenarios & Testing

### User Story 1 - Execute Student-Only Gating Training Loop (Priority: P1)

As a researcher, I want to train the "Student-Only Gating" variant of SDAR on the ALFWorld and WebShop environments using only the student model's internal entropy and retrieved context stability as gating signals, so that I can eliminate the computational cost of the teacher model forward pass while maintaining training stability.

**Why this priority**: This is the core hypothesis test. Without successfully running the student-only variant and collecting its steps-to-threshold data, no comparison or cost analysis is possible. It is the minimum viable experiment.

**Independent Test**: Can be fully tested by initiating a training run with the `--variant student-only` flag on a single environment (e.g., ALFWorld) and verifying that the training loop completes without teacher model calls, logging the specific gating scores derived solely from student entropy and context similarity.

**Acceptance Scenarios**:

1. **Given** the ALFWorld environment is configured and the Qwen2.5-1.7B student model is loaded, **When** the training loop executes for a fixed number of [deferred] training steps OR until the average per-episode cumulative reward reaches 0.8 for 3 consecutive episodes (whichever comes first), **Then** the system must log gating scores ($g_t$) calculated exclusively from token entropy ($H_t$) and context stability ($S_t$) without invoking any teacher model.
2. **Given** a training run is active, **When** the retrieved context is noisy or irrelevant, **Then** the student-only gate must correctly down-weight low-confidence tokens based on the cosine similarity metric $S_t$, preventing the accumulation of noisy distillation signals.

### User Story 2 - Compare Baseline vs. Student-Only Performance (Priority: P2)

As a researcher, I want to run the original dual-model SDAR baseline and the proposed student-only variant in parallel (or sequentially with identical seeds) and compare their task success rates and steps-to-threshold speeds, so that I can quantify the performance retention of the student-only approach.

**Why this priority**: This directly addresses the research question regarding the necessity of the teacher signal. It provides the primary metric (performance gap) to validate the hypothesis.

**Independent Test**: Can be fully tested by executing two distinct training jobs (Baseline SDAR and Student-Only) on the same environment and generating a comparison report that lists final task success rates and the number of steps required to reach average per-episode cumulative reward 0.8.

**Acceptance Scenarios**:

1. **Given** two training runs (Baseline SDAR and Student-Only) completed on WebShop with identical hyperparameters and random seeds, **When** the results are aggregated, **Then** the system must output a comparison table showing the final task success rate for both variants and the percentage difference between them.
2. **Given** the training curves are generated, **When** the convergence speed is analyzed, **Then** the system must report the number of training steps required for each variant to achieve an average per-episode cumulative reward threshold of 0.8, allowing for a direct speed comparison.

### User Story 3 - Validate Computational Efficiency and Statistical Significance (Priority: P3)

As a researcher, I want to measure the per-step computational cost (CPU time and memory) of the student-only variant against the baseline and perform statistical hypothesis testing on the performance results, so that I can confirm the >60% cost reduction and determine if the performance difference is statistically significant.

**Why this priority**: This validates the "edge device" motivation and ensures the results are scientifically rigorous, not just anecdotal. It confirms the trade-off is favorable.

**Independent Test**: Can be fully tested by profiling the training loop's CPU usage and memory footprint during execution and running a Mann-Whitney U test on the collected success rates from multiple independent runs.

**Acceptance Scenarios**:

1. **Given** the training execution logs, **When** the computational cost is profiled, **Then** the system must report the average CPU time per step and peak memory usage for the student-only variant, showing a reduction of at least 60% compared to the baseline (calculated as the mean of 5 independent runs).
2. **Given** the final task success rates from 5 independent runs of both variants, **When** a Mann-Whitney U test (or bootstrapping) is performed, **Then** the system must output the p-value to determine if the performance difference is statistically significant at the p < 0.05 level.

### Edge Cases

- What happens when the retrieved context is completely irrelevant (random noise), causing the context stability score ($S_t$) to be near zero? The system must rely on token entropy ($H_t$) to gate the signal, preventing the model from learning from garbage context.
- How does the system handle environments where the student model consistently outputs high-confidence but incorrect tokens (low entropy, high error)? The gating mechanism must not blindly trust low entropy; the design assumes the correlation between entropy and correctness holds, but this edge case may require a fallback or manual intervention if the correlation breaks.
- What if the CPU memory limit is exceeded during the retrieval of large context windows? The system must implement a chunking strategy or limit the context window size to ensure the process does not crash the CI runner.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the Student-Only gating mechanism $g_t = \sigma(\alpha H_t + \beta S_t)$ using student token entropy ($H_t$) and retrieved context stability ($S_t$) without invoking a teacher model. (See US-1)
- **FR-002**: System MUST execute the training loop for both the Baseline SDAR (dual-model) and Proposed Student-Only variants on the ALFWorld and WebShop environments for a fixed number of [deferred] training steps. (See US-2)
- **FR-003**: System MUST log per-step computational metrics including CPU time, memory usage, and the specific values of $H_t$ and $S_t$ for every training step. (See US-3)
- **FR-004**: System MUST persist all baseline training artifacts (including teacher-student gap scores and student heuristics) to a shared storage location to ensure retrievability for cross-variant performance analysis. (See US-2)
- **FR-005**: System MUST perform a statistical hypothesis test (prioritizing Mann-Whitney U test or bootstrapping for small-n bounded data; t-test only if normality is confirmed) on the final task success rates of the two variants to determine significance at p < 0.05. (See US-3)
- **FR-006**: System MUST handle cases where the retrieved context is noisy by ensuring the gating score $g_t$ remains bounded and does not produce NaN values during the sigmoid activation. (See US-1)

### Key Entities

- **TrainingRun**: Represents a single execution of the RL loop, containing metadata (variant type, environment, hyperparameters) and collected metrics (success rate, steps, cost).
- **GatingSignal**: Represents the computed gate value $g_t$ for a specific token, containing the entropy component ($H_t$), stability component ($S_t$), and the final weighted score.
- **EnvironmentTask**: Represents a specific task instance in ALFWorld or WebShop, containing the goal description, initial state, and the expected trajectory for reward calculation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task success rate of the Student-Only variant is measured against the Baseline SDAR variant to determine if it achieves ≥80% of the baseline's performance improvement over GRPO, where performance improvement is defined as (Success_Student - Success_GRPO) ≥ 0.8 × (Success_Baseline - Success_GRPO). (See US-2)
- **SC-002**: Per-step computational cost (CPU time) of the Student-Only variant is measured against the Baseline SDAR variant to verify a reduction of ≥60%. (See US-3)
- **SC-003**: The p-value from the statistical hypothesis test on success rates is measured against a conventional significance threshold to determine if the performance difference is statistically significant. (See US-3)
- **SC-004**: The convergence speed (steps to reach average per-episode cumulative reward ≥ 0.8) of the Student-Only variant is measured against the Baseline SDAR variant to assess training efficiency. (See US-2)

## Assumptions

- The Qwen student model is sufficiently small to run on a CPU-only GitHub Actions runner (multi-core, constrained RAM) within the job time limit, even with the overhead of the dense retriever.
- The ALFWorld and WebShop environments can be downloaded and executed without external network dependencies beyond the initial cloning, fitting within standard disk storage constraints.
- **Hypothesis H1**: The student token entropy ($H_t$) and retrieved context stability ($S_t$) are positively correlated with the correctness of the token. This is a testable hypothesis to be validated by the performance results, not a precondition for the experiment's validity.
- The dense retriever using `sentence-transformers` (quantized) or `rank_bm25` can be executed on CPU without exceeding the memory constraints of the free-tier runner.
- The "Student-Only" variant does not require any pre-computed teacher labels or teacher model checkpoints, relying entirely on the student's internal state and the environment feedback.
- The correlation between the student heuristic and the teacher gap is strong enough that the Student-Only variant achieves high performance retention; if not, the hypothesis will be rejected, but the experiment is still valid.