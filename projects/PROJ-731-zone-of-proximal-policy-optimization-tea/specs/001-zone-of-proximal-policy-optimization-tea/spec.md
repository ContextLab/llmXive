# Feature Specification: Zone of Proximal Policy Optimization

**Feature Branch**: `001-zone-proximal-policy-optimization`  
**Created**: 2026-06-23  
**Status**: Draft  
**Input**: Research investigation into how teacher-provided prompt demonstrations influence sample-efficiency of small language models trained with PPO

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core PPO Training Loop with Variable Prompt Sizes (Priority: P1)

The researcher MUST be able to run the PPO training loop with four different teacher prompt demonstration sizes (ranging from none to large-scale) and log performance metrics at regular intervals.

**Why this priority**: This is the foundational capability that enables the entire research question to be tested. Without this, no comparative analysis across prompt-size conditions is possible.

**Independent Test**: Can be fully tested by executing a single training run with one prompt-size condition (e.g., 10k prompts) and verifying that benchmark scores are logged at regular intervals during PPO training.

**Acceptance Scenarios**:

1. **Given** the student model is initialized and a prompt-teacher buffer is loaded with 10k examples, **When** the PPO training loop executes for 100 iterations, **Then** performance metrics (average reward, KL divergence, benchmark scores) are logged to disk
2. **Given** the training is running on a GitHub Actions CPU-only runner with limited processing resources (few cores, ~7GB RAM), **When** a job time limit is reached, **Then** the current checkpoint is saved and all logged metrics are persisted

---

### User Story 2 - Benchmark Evaluation at Regular Intervals (Priority: P2)

The researcher MUST be able to evaluate the student model on three standard benchmark suites (lambada_openai, truthful_qa, mmlu) at regular intervals during PPO training and record accuracy metrics.

**Why this priority**: Sample-efficiency is measured as performance per fixed number of PPO steps., which requires periodic evaluation. This enables the core dependent variable measurement.

**Independent Test**: Can be tested by running evaluation on a fixed checkpoint across all three benchmarks and verifying that exact-match or accuracy scores are computed and stored.

**Acceptance Scenarios**:

1. **Given** the student model has completed 200 PPO steps, **When** evaluation is triggered on lambada_openai, truthful_qa, and mmlu test splits, **Then** accuracy scores for each benchmark are recorded with step count metadata
2. **Given** evaluation is running on CPU-only hardware, **When** the evaluation completes within 30 minutes per benchmark suite, **Then** results are appended to the training log without GPU acceleration

---

### User Story 3 - Statistical Analysis for Diminishing Returns (Priority: P3)

The researcher MUST be able to analyze performance-per-step curves across prompt-size conditions to detect diminishing returns. The system MUST log the raw data required for this analysis (performance curves per seed) to enable post-hoc statistical testing.

**Why this priority**: This enables the hypothesis test (does more prompts improve sample-efficiency?) and detection of the expected plateau effect. Lower priority because it depends on successful data collection from US-1 and US-2.

**Independent Test**: Can be tested by providing synthetic performance-per-step data across 4 conditions and verifying that the logged data structure allows for the computation of performance curves and variance.

**Acceptance Scenarios**:

1. **Given** performance-per-step data from multiple independent seeds per prompt-size condition, **When** the training run completes, **Then** the system logs a CSV/JSON file containing step, seed, prompt_size, and benchmark accuracy for every evaluation point
2. **Given** the logged data, **When** the researcher performs a post-hoc statistical test (e.g., permutation test or descriptive analysis), **Then** the researcher can compute performance differences and confidence intervals

---

### Edge Cases

- What happens when the GPT-NeoX model exceeds the 7GB RAM limit during PPO rollouts? → System MUST sample a subset of the prompt-teacher buffer (e.g., a random subset) and log a warning with the tag 'MEMORY_FALLBACK' to distinguish it from the intentional large-scale condition
- How does system handle missing teacher exemplars for certain inputs? → System MUST fall back to the correctness-only reward component and log the missing-exemplar rate
- What happens when benchmark evaluation fails due to dataset access issues? → System MUST retry up to 3 times with 60-second delays before marking the evaluation as failed and continuing training
- How does system handle convergence failures (KL divergence > 0.5)? → System MUST reduce learning rate by a significant factor and log the adaptation event

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute PPO training with clipped-surrogate loss and KL-penalty for a maximum of 1,000 iterations or 6 hours (whichever comes first) (See US-1)
- **FR-002**: System MUST support a range of discrete prompt-size conditions for teacher demonstration examples, including a zero-example baseline and varying magnitudes of demonstration data. (See US-1)
- **FR-003**: System MUST compute a correctness reward (binary 0/1 based on reference match) as the sole reward signal (See US-1)
- **FR-004**: System MUST evaluate the student model on lambada_openai, truthful_qa, and mmlu test splits at regular intervals during training. (See US-2)
- **FR-005**: System MUST record performance-perk-steps metrics for each benchmark with seed identifier and step count (See US-2)
- **FR-006**: System MUST log performance curves (accuracy vs. step count) for each seed and prompt-size condition to enable post-hoc statistical comparison (See US-3)
- **FR-007**: System MUST log performance curves to enable piecewise-linear regression analysis (See US-3)

### Key Entities

- **Training Run**: Represents one complete PPO training execution with a specific prompt-size condition and random seed; attributes include prompt_size (k/10k/50k/200k), seed (integer), step_count (integer), and logged_metrics (array)
- **Performance Metric**: Represents a benchmark evaluation result at a specific training step; attributes include benchmark_name (lambada_openai/truthful_qa/mmlu), accuracy (float), step_count (integer), and seed (integer)
- **Prompt Buffer**: Represents the teacher demonstration dataset for a given condition; attributes include size (0k/10k/50k/200k), source_dataset (openassistant/oasst1), and sample_count (integer)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Sample-efficiency (benchmark accuracy per [deferred] PPO steps) is measured against the 0-prompt baseline condition (See US-3)
- **SC-002**: Statistical significance of performance differences is measured via post-hoc analysis with p < 0.05 threshold (See US-3)
- **SC-003**: Diminishing-returns plateau is measured via piecewise-linear regression breakpoint with confidence intervals (See US-3)
- **SC-004**: Compute feasibility is measured against the standard GitHub Actions job duration limit and 7GB RAM constraint (See US-1)
- **SC-005**: Reproducibility is measured by running 3 independent seeds per prompt-size condition and verifying coefficient of variation (CV) < 0.05 on final benchmark scores (See US-2)

## Assumptions

- The OpenAssistant prompt-response dataset (openassistant/oasst) contains sufficient teacher demonstration examples for various prompt-size conditions.
- The GPT-NeoX model can be loaded and executed within standard memory constraints on CPU-only hardware.; if memory constraints are encountered, the prompt buffer will be sampled to a reduced subset of examples with a 'MEMORY_FALLBACK' log tag
- The three benchmark suites (lambada_openai, truthful_qa, mmlu) are accessible via HuggingFace Datasets without requiring paid API access
- Since this is an observational study (no random assignment to prompt-size conditions), all findings will be framed as ASSOCIATIONAL rather than causal claims
- For multiple comparisons across 4 conditions and 3 benchmarks, the analysis will apply family-wise error correction (Bonferroni or Holm-Bonferroni) to maintain α = 0.05
- Power analysis for the statistical comparison is deferred; the multi-seed design is a pragmatic choice for CPU-tractable replication, with acknowledgement that larger N would improve statistical power
- The correctness reward requires reference answers; if reference coverage is incomplete for certain benchmark items, those items will be excluded from the correctness calculation and logged
- The GPT-NeoX checkpoint is available on HuggingFace at the time of execution; if unavailable, the implementation will fall back to the next smallest public GPT-NeoX variant
- All training and evaluation will run on GitHub Actions free-tier runners (2 CPU cores, ~7GB RAM, ≤6h per job); no GPU, CUDA, or accelerator dependencies are permitted