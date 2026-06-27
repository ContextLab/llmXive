# Feature Specification: Self-improving LLM: recursive architecture refinement and re‑training

**Feature Branch**: `001-self-improving-llm-recursive-architectur`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "recursive architecture modification and re-training for LLM performance improvement"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1)

The researcher MUST be able to download a base model (GPT-2 124M), apply a single architectural modification, re-train on OpenWebText subset, and evaluate performance on GSM8K, ARC-Challenge, and Wikitext-2 calibration benchmarks. This establishes the fundamental pipeline before iterating.

**Why this priority**: Without a working single cycle, no recursive behavior can be studied. This is the minimum viable experiment that delivers the core research question answer for one iteration.

**Independent Test**: Can be fully tested by executing the pipeline once and verifying that performance metrics are recorded and compared against the pre-modification baseline.

**Acceptance Scenarios**:

1. **Given** a GPT-2 124M checkpoint is available on HuggingFace, **When** the pipeline downloads it and modifies the architecture (e.g., add one transformer layer), **Then** the modified model MUST be re-trained for 1 epoch on OpenWebText and evaluated on all three benchmarks within 2 hours on CPU.
2. **Given** baseline metrics are recorded before modification, **When** the modified model completes training, **Then** the system MUST output accuracy for GSM8K, ARC-Challenge, and ECE for Wikitext-2 with ≥3 decimal precision.
3. **Given** paired bootstrap statistical testing is configured, **When** baseline and post-modification metrics are available, **Then** the system MUST compute p-values for performance differences with significance threshold α = 0.05.

---

### User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

The researcher MUST be able to iterate the refinement process three times, recording performance after each cycle to identify whether gains persist, plateau, or degrade. This tests the core hypothesis about recursive improvement sustainability.

**Why this priority**: The research question specifically asks about persistence across cycles. Three cycles is the minimum to detect non-linear trajectories (improvement → plateau → degradation).

**Independent Test**: Can be fully tested by executing the pipeline for 3 consecutive cycles and verifying that performance metrics form a time-series with detectable trends.

**Acceptance Scenarios**:

1. **Given** cycle 1 completes successfully, **When** the pipeline proceeds to cycle 2, **Then** the system MUST apply a new architectural modification (distinct from cycle 1) while keeping total parameter count ≤30% above original GPT-2 baseline.
2. **Given** all three cycles complete, **When** performance metrics are aggregated, **Then** the system MUST output a performance trajectory table with cycle number, parameter count, GSM8K accuracy, ARC-Challenge accuracy, ECE, FLOPs, and training time.
3. **Given** performance trajectories are recorded, **When** analysis completes, **Then** the system MUST fit a decay model and report the cycle number where performance first plateaus (≤1% improvement) or degrades (≥1% drop) from peak.

---

### User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

The researcher MUST be able to compute cost-effectiveness metrics (performance per FLOP, performance per training hour) to determine whether recursive refinement is computationally viable compared to alternative improvement strategies.

**Why this priority**: Even if performance improves, the method is only valuable if it is compute-efficient. This analysis determines practical applicability.

**Independent Test**: Can be fully tested by computing trade-off ratios from recorded metrics and verifying that resource constraints are documented.

**Acceptance Scenarios**:

1. **Given** performance metrics and FLOPs are recorded for each cycle, **When** trade-off analysis executes, **Then** the system MUST compute performance-per-FLOP for GSM8K accuracy and ECE improvement.
2. **Given** training time is recorded for each cycle, **When** trade-off analysis executes, **Then** the system MUST compute performance-per-hour for each benchmark.
3. **Given** the complete pipeline runs on GitHub Actions free tier, **When** job execution completes, **Then** total wall-clock time MUST be ≤6 hours and peak RAM usage MUST be ≤7 GB.

---

### Edge Cases

- What happens when the NAS routine proposes a modification that exceeds the [deferred] parameter count constraint? The system MUST reject the modification and sample an alternative within the constraint.
- How does the system handle training failure on a specific cycle? The system MUST retry up to 2 times with the same modification; after 2 failed attempts, the cycle MUST be logged as failed and the pipeline MUST proceed to the next cycle with a new modification.
- What happens when paired bootstrap p-values are exactly 0.05? The system MUST treat p = 0.05 as non-significant (strictly p < 0.05 required for significance claim).
- How does the system handle dataset availability issues (e.g., HuggingFace API rate limits)? The system MUST implement exponential backoff with initial wait = 30 seconds, max retries = 5, and fail the job if all retries exhausted.
- What happens when performance degradation occurs in cycle 2? The system MUST record the degradation cycle and terminate early if degradation ≥5% from baseline, logging this as an early-stop condition.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download GPT-2 124M checkpoint from HuggingFace and load it into CPU-compatible PyTorch environment (See US-1)
- **FR-002**: System MUST apply exactly one architectural modification per refinement cycle (e.g., add transformer layer, increase feed-forward dimension by [deferred]) (See US-2)
- **FR-003**: System MUST constrain total parameter count increase to ≤30% above original GPT-2 baseline across all cycles (See US-2)
- **FR-004**: System MUST re-train each modified model for exactly 1 epoch on OpenWebText subset with AdamW optimizer, batch size 32, learning rate 5e-5 (See US-1)
- **FR-005**: System MUST evaluate each cycle on GSM8K (reasoning accuracy), ARC-Challenge (reasoning accuracy), and Wikitext-2 held-out set (calibration ECE) (See US-1)
- **FR-006**: System MUST perform paired bootstrap statistical comparison between successive cycles with significance threshold α = 0.05 (See US-1)
- **FR-007**: System MUST repeat the modify-train-evaluate loop for multiple refinement cycles (See US-2)
- **FR-008**: System MUST record FLOPs and parameter count for each cycle to enable cost-effectiveness analysis (See US-3)
- **FR-009**: System MUST fit a decay model to performance trajectories and report the cycle number where performance first plateaus (≤1% improvement) or degrades (≥1% drop) (See US-2)
- **FR-010**: System MUST compute performance-per-FLOP and performance-per-hour metrics for each cycle (See US-3)
- **FR-011**: System MUST implement exponential backoff for HuggingFace API calls with initial wait = 30 seconds and max retries = 5 (See US-1)
- **FR-012**: System MUST retry failed training runs up to 2 times before logging cycle failure (See US-2)

### Key Entities

- **ModelCheckpoint**: Represents a trained model instance with attributes: cycle_number, parameter_count, architecture_modification, training_time, flops
- **PerformanceMetric**: Represents evaluation results with attributes: cycle_number, benchmark_name (GSM8K/ARC-Challenge/Wikitext-2), accuracy_or_ECE, p_value_vs_baseline
- **RefinementCycle**: Represents one iteration of the pipeline with attributes: cycle_number, pre_modification_params, post_modification_params, training_duration, evaluation_results, success_status

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reasoning accuracy improvement on GSM8K and ARC-Challenge is measured against the pre-modification baseline using paired bootstrap (p < 0.05) (See US-1)
- **SC-002**: Calibration error (ECE) on Wikitext-2 is measured against the pre-modification baseline using paired bootstrap (p < 0.05) (See US-1)
- **SC-003**: Performance trajectory persistence is measured across 3 cycles by fitting a decay model and identifying the cycle where improvement ≤1% or degradation ≥1% (See US-2)
- **SC-004**: Cost-effectiveness is measured as performance-per-FLOP and performance-per-hour, compared across cycles to identify diminishing returns (See US-3)
- **SC-005**: Compute feasibility is measured by total wall-clock time ≤6 hours and peak RAM usage ≤7 GB on GitHub Actions free tier (See US-3)

---

## Assumptions

- HuggingFace Datasets (OpenWebText subset, GSM8K, ARC-Challenge, Wikitext-2) will remain publicly accessible without authentication requirements during the 6-hour execution window
- PyTorch CPU backend will support GPT-2 124M model loading and training within the 7 GB RAM constraint without requiring quantization or GPU acceleration
- The NNI (Neural Network Intelligence) library will be available in the GitHub Actions environment or installable within the job time budget
- Paired bootstrap testing with 1000 resamples will complete within the remaining time budget after model training (estimated ≤30 minutes)
- The [deferred] parameter count constraint is sufficient to explore meaningful architectural variations while staying within compute limits
- OpenWebText subset of sufficient scale provides adequate training signal for detecting performance changes after 1 epoch of fine-tuning
- The improvement criterion is fixed (performance on held-out OOD benchmarks) and NOT subject to modification during the 3-cycle experiment
- Verification logic (evaluation on benchmarks) is logically separate from generative logic (NAS modification proposal) to prevent infinite regression
- No CUDA, CUDA-accelerated operations, or 8-bit/4-bit quantization will be required or invoked
- The GitHub Actions free-tier runner will provide the specified multiple CPU cores, ~7 GB RAM, and ~14 GB disk without resource contention from other jobs
